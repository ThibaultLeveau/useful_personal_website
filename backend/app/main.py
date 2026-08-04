"""FastAPI application factory and baseline transport composition."""

from __future__ import annotations

from contextlib import asynccontextmanager
from http import HTTPStatus
from time import perf_counter
from typing import TYPE_CHECKING

import structlog.contextvars
from fastapi import FastAPI

from app.api.v1.errors import register_exception_handlers
from app.api.v1.router import api_v1_router
from app.common.health import ReadinessProbe, UnconfiguredReadinessProbe
from app.common.observability import configure_logging, get_logger
from app.common.request_context import REQUEST_ID_HEADER, select_request_id
from app.config import Environment, Settings
from app.infrastructure.database import DatabaseConfig, DatabaseRuntime, create_database_runtime
from app.infrastructure.database.api_access_uow import SqlAlchemyApiTokenUnitOfWorkFactory
from app.infrastructure.database.audit_uow import SqlAlchemyAuditQueryUnitOfWorkFactory
from app.infrastructure.database.blog_uow import SqlAlchemyBlogUnitOfWorkFactory
from app.infrastructure.database.contacts_uow import SqlAlchemyContactUnitOfWorkFactory
from app.infrastructure.database.experiences_uow import (
    SqlAlchemyExperiencesUnitOfWorkFactory,
)
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.infrastructure.database.media_eligibility import DatabasePublicMediaEligibility
from app.infrastructure.database.media_uow import SqlAlchemyMediaUnitOfWorkFactory
from app.infrastructure.database.pages_uow import SqlAlchemyPagesUnitOfWorkFactory
from app.infrastructure.database.projects_uow import SqlAlchemyProjectsUnitOfWorkFactory
from app.infrastructure.database.site_configuration_uow import (
    SqlAlchemySiteConfigurationUnitOfWorkFactory,
)
from app.infrastructure.database.skills_uow import SqlAlchemySkillsUnitOfWorkFactory
from app.infrastructure.storage.image_processing import PillowImageProcessor
from app.infrastructure.storage.media_factory import build_media_storage
from app.modules.api_access.service import ApiTokenConfiguration, ApiTokenService
from app.modules.audit.service import AuditQueryService
from app.modules.blog.service import BlogReferenceFacade, BlogService
from app.modules.contacts.service import ContactConfiguration, ContactService
from app.modules.experiences.service import ExperienceReferenceFacade, ExperiencesService
from app.modules.identity.security import PasswordManager
from app.modules.identity.service import IdentityService, IdentityServiceConfiguration
from app.modules.media.service import MediaService
from app.modules.navigation.service import NavigationService
from app.modules.pages.service import PageService
from app.modules.profile.service import ProfileService
from app.modules.projects.service import ProjectReferenceFacade, ProjectsService
from app.modules.settings.service import WebsiteSettingsService
from app.modules.skills.service import SkillReferenceFacade, SkillsService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import Request, Response
    from starlette.middleware.base import RequestResponseEndpoint


API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def _application_lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Dispose shared database resources without running data commands."""
    try:
        yield
    finally:
        database_runtime = getattr(application.state, "database_runtime", None)
        if isinstance(database_runtime, DatabaseRuntime):
            await database_runtime.dispose()


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if not isinstance(template, str):
        return "<unmatched>"
    if template.startswith("/") and not template.startswith(API_V1_PREFIX):
        return f"{API_V1_PREFIX}{template}"
    return template


async def _request_context_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = select_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    started_at = perf_counter()
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    logger = get_logger()
    try:
        response = await call_next(request)
    except Exception:
        logger.error(  # noqa: TRY400 - exception text is deliberately excluded from logs.
            "request.failed",
            duration_ms=round((perf_counter() - started_at) * 1000, 3),
            method=request.method,
            route=_route_template(request),
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        raise
    else:
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        settings = request.app.state.settings
        if settings.environment is Environment.PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        logger.info(
            "request.completed",
            duration_ms=round((perf_counter() - started_at) * 1000, 3),
            method=request.method,
            route=_route_template(request),
            status=response.status_code,
        )
        return response
    finally:
        structlog.contextvars.clear_contextvars()


def create_app(  # noqa: PLR0915 - explicit composition root remains auditable.
    *,
    settings: Settings | None = None,
    readiness_probe: ReadinessProbe | None = None,
) -> FastAPI:
    """Build a fully configured application with injectable dependency probes."""
    resolved_settings = settings or Settings()
    configure_logging(resolved_settings.log_level)

    application = FastAPI(
        debug=resolved_settings.debug,
        docs_url=f"{API_V1_PREFIX}/docs",
        lifespan=_application_lifespan,
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
        redoc_url=None,
        servers=[{"url": "/", "description": "Same-origin API"}],
        title="Useful Personal Website API",
        version=resolved_settings.build_version,
    )
    application.state.settings = resolved_settings
    database_runtime: DatabaseRuntime | None = None
    if readiness_probe is None and resolved_settings.database_url is not None:
        database_runtime = create_database_runtime(
            DatabaseConfig(url=resolved_settings.database_url)
        )
    application.state.database_runtime = database_runtime
    identity_service: IdentityService | None = None
    if (
        database_runtime is not None
        and resolved_settings.csrf_signing_key is not None
        and resolved_settings.privacy_hmac_key is not None
    ):
        identity_service = IdentityService(
            SqlAlchemyIdentityUnitOfWorkFactory(database_runtime.session_factory),
            IdentityServiceConfiguration(
                csrf_signing_key=resolved_settings.csrf_signing_key.get_secret_value().encode(),
                privacy_hmac_key=resolved_settings.privacy_hmac_key.get_secret_value().encode(),
                password_manager=PasswordManager.create(),
            ),
        )
    application.state.identity_service = identity_service
    profile_service: ProfileService | None = None
    website_settings_service: WebsiteSettingsService | None = None
    navigation_service: NavigationService | None = None
    skills_service: SkillsService | None = None
    experiences_service: ExperiencesService | None = None
    projects_service: ProjectsService | None = None
    blog_service: BlogService | None = None
    page_service: PageService | None = None
    media_service: MediaService | None = None
    contact_service: ContactService | None = None
    api_token_service: ApiTokenService | None = None
    audit_query_service: AuditQueryService | None = None
    if database_runtime is not None:
        audit_query_service = AuditQueryService(
            SqlAlchemyAuditQueryUnitOfWorkFactory(database_runtime.session_factory)
        )
        site_uow_factory = SqlAlchemySiteConfigurationUnitOfWorkFactory(
            database_runtime.session_factory
        )
        profile_service = ProfileService(site_uow_factory.profile)
        website_settings_service = WebsiteSettingsService(site_uow_factory.settings)
        navigation_service = NavigationService(site_uow_factory.navigation)
        skills_service = SkillsService(
            SqlAlchemySkillsUnitOfWorkFactory(database_runtime.session_factory)
        )
        experiences_service = ExperiencesService(
            SqlAlchemyExperiencesUnitOfWorkFactory(database_runtime.session_factory),
            SkillReferenceFacade(skills_service),
        )
        projects_service = ProjectsService(
            SqlAlchemyProjectsUnitOfWorkFactory(database_runtime.session_factory),
            SkillReferenceFacade(skills_service),
            ExperienceReferenceFacade(experiences_service),
        )
        blog_service = BlogService(
            SqlAlchemyBlogUnitOfWorkFactory(database_runtime.session_factory)
        )
        page_service = PageService(
            SqlAlchemyPagesUnitOfWorkFactory(database_runtime.session_factory),
            SkillReferenceFacade(skills_service),
            ExperienceReferenceFacade(experiences_service),
            ProjectReferenceFacade(projects_service),
            BlogReferenceFacade(blog_service),
            profile_service,
        )
        media_storage = build_media_storage(resolved_settings)
        if media_storage is not None:
            media_service = MediaService(
                SqlAlchemyMediaUnitOfWorkFactory(database_runtime.session_factory),
                media_storage,
                PillowImageProcessor(),
                DatabasePublicMediaEligibility(database_runtime.session_factory),
            )
        if resolved_settings.privacy_hmac_key is not None:
            contact_service = ContactService(
                SqlAlchemyContactUnitOfWorkFactory(database_runtime.session_factory),
                ContactConfiguration(
                    policy_version=resolved_settings.contact_policy_version,
                    source=resolved_settings.contact_source,
                    minimum_completion_seconds=resolved_settings.contact_minimum_completion_seconds,
                    proof_ttl_seconds=resolved_settings.contact_proof_ttl_seconds,
                    hmac_key=resolved_settings.privacy_hmac_key.get_secret_value().encode(),
                    pseudonym_key_version=resolved_settings.contact_pseudonym_key_version,
                ),
            )
        if resolved_settings.token_digest_pepper is not None:
            api_token_service = ApiTokenService(
                SqlAlchemyApiTokenUnitOfWorkFactory(database_runtime.session_factory),
                ApiTokenConfiguration(
                    pepper=resolved_settings.token_digest_pepper.get_secret_value().encode(),
                    key_version=resolved_settings.token_digest_key_version,
                ),
            )
    application.state.profile_service = profile_service
    application.state.website_settings_service = website_settings_service
    application.state.navigation_service = navigation_service
    application.state.skills_service = skills_service
    application.state.experiences_service = experiences_service
    application.state.projects_service = projects_service
    application.state.blog_service = blog_service
    application.state.page_service = page_service
    application.state.media_service = media_service
    application.state.contact_service = contact_service
    application.state.api_token_service = api_token_service
    application.state.audit_query_service = audit_query_service
    application.state.readiness_probe = (
        readiness_probe
        or (database_runtime.readiness_probe if database_runtime is not None else None)
        or UnconfiguredReadinessProbe()
    )
    register_exception_handlers(application)
    application.middleware("http")(_request_context_middleware)
    application.include_router(api_v1_router, prefix=API_V1_PREFIX)
    return application


app = create_app()
