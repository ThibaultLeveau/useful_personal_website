"""Authenticated profile, settings, navigation, and footer API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.conventions import (
    map_common_error,
    map_idempotency_decision,
    set_private_no_store,
    set_resource_etag,
    success,
)
from app.api.v1.schemas import ErrorEnvelope, SuccessEnvelope
from app.api.v1.site_configuration_schemas import (
    FooterColumnData,
    FooterColumnInput,
    FooterData,
    FooterItemData,
    FooterItemInput,
    FooterReplaceRequest,
    NavigationData,
    NavigationItemData,
    NavigationItemInput,
    NavigationReplaceRequest,
    ProfileData,
    ProfileUpdateRequest,
    SocialLinkInput,
    WebsiteSettingsData,
    WebsiteSettingsUpdateRequest,
)
from app.common.domain.actors import ActorContext
from app.common.domain.concurrency import (
    InvalidPreconditionError,
    PreconditionRequiredError,
    ResourceVersionConflictError,
)
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.common.security.authorization import AuthorizationDeniedError
from app.modules.identity.domain import SessionView  # noqa: TC001 - FastAPI runtime annotation.
from app.modules.media.domain import MediaStateError
from app.modules.navigation.domain import (
    FooterColumn,
    FooterItem,
    FooterTree,
    NavigationItem,
    NavigationTree,
    TreeValidationError,
)
from app.modules.navigation.service import (
    IdempotencyRejectedError,
    NavigationService,
    ReplaceFooterCommand,
    ReplaceNavigationCommand,
)
from app.modules.profile.domain import ProfileSnapshot, ProfileValues
from app.modules.profile.domain import SocialLink as ProfileSocialLink
from app.modules.profile.service import ProfileService, UpdateProfileCommand
from app.modules.settings.domain import SocialLink as SettingsSocialLink
from app.modules.settings.domain import WebsiteSettingsSnapshot, WebsiteSettingsValues
from app.modules.settings.service import UpdateWebsiteSettingsCommand, WebsiteSettingsService

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Site configuration"])

_ADMIN_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.BAD_REQUEST): {"model": ErrorEnvelope},
    int(HTTPStatus.UNAUTHORIZED): {"model": ErrorEnvelope},
    int(HTTPStatus.FORBIDDEN): {"model": ErrorEnvelope},
    int(HTTPStatus.CONFLICT): {"model": ErrorEnvelope},
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.PRECONDITION_REQUIRED): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_UNSAFE_OPENAPI = {
    "parameters": [
        {
            "name": "Origin",
            "in": "header",
            "required": True,
            "description": "Exact configured trusted HTTPS origin.",
            "schema": {"type": "string", "format": "uri"},
        }
    ]
}
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_SITE_MUTATION_ERRORS = (
    AuthorizationDeniedError,
    PreconditionRequiredError,
    InvalidPreconditionError,
    ResourceVersionConflictError,
    TreeValidationError,
    IdempotencyRejectedError,
    MediaStateError,
)


@dataclass(frozen=True, slots=True)
class TreeMutationHeaders:
    """Validated concurrency and idempotency headers for tree replacement."""

    idempotency_key: str
    if_match: str | None


def tree_mutation_headers(
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> TreeMutationHeaders:
    """Collect the headers shared by navigation and footer replacement."""
    return TreeMutationHeaders(idempotency_key=idempotency_key, if_match=if_match)


def _profile_service(request: Request) -> ProfileService:
    service = getattr(request.app.state, "profile_service", None)
    if not isinstance(service, ProfileService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _settings_service(request: Request) -> WebsiteSettingsService:
    service = getattr(request.app.state, "website_settings_service", None)
    if not isinstance(service, WebsiteSettingsService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _navigation_service(request: Request) -> NavigationService:
    service = getattr(request.app.state, "navigation_service", None)
    if not isinstance(service, NavigationService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _profile_data(snapshot: ProfileSnapshot) -> ProfileData:
    return ProfileData(
        id=snapshot.id,
        full_name=snapshot.full_name,
        professional_title=snapshot.professional_title,
        short_biography=snapshot.short_biography,
        full_biography=snapshot.full_biography,
        profile_image_id=snapshot.profile_image_id,
        location=snapshot.location,
        availability=snapshot.availability,
        email=snapshot.email,
        social_links=[
            SocialLinkInput(label=link.label, url=link.url) for link in snapshot.social_links
        ],
        github_url=snapshot.github_url,
        linkedin_url=snapshot.linkedin_url,
        personal_values=list(snapshot.personal_values),
        work_preferences=list(snapshot.work_preferences),
        resume_url=snapshot.resume_url,
        contact_preference=snapshot.contact_preference,
        public_fields=set(snapshot.public_fields),
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
        version=snapshot.version,
    )


def _profile_values(payload: ProfileUpdateRequest) -> ProfileValues:
    return ProfileValues(
        full_name=payload.full_name,
        professional_title=payload.professional_title,
        short_biography=payload.short_biography,
        full_biography=payload.full_biography,
        profile_image_id=payload.profile_image_id,
        location=payload.location,
        availability=payload.availability,
        email=payload.email,
        social_links=tuple(
            ProfileSocialLink(label=link.label, url=link.url) for link in payload.social_links
        ),
        github_url=payload.github_url,
        linkedin_url=payload.linkedin_url,
        personal_values=tuple(payload.personal_values),
        work_preferences=tuple(payload.work_preferences),
        resume_url=payload.resume_url,
        contact_preference=payload.contact_preference,
        public_fields=frozenset(payload.public_fields),
    )


def _settings_data(snapshot: WebsiteSettingsSnapshot) -> WebsiteSettingsData:
    return WebsiteSettingsData(
        id=snapshot.id,
        website_name=snapshot.website_name,
        default_title=snapshot.default_title,
        default_description=snapshot.default_description,
        logo_media_id=snapshot.logo_media_id,
        favicon_media_id=snapshot.favicon_media_id,
        social_image_media_id=snapshot.social_image_media_id,
        default_locale=snapshot.default_locale,
        timezone=snapshot.timezone,
        theme_policy=snapshot.theme_policy,
        primary_color=snapshot.primary_color,
        accent_color=snapshot.accent_color,
        contact_email=snapshot.contact_email,
        contact_phone=snapshot.contact_phone,
        social_links=[
            SocialLinkInput(label=link.label, url=link.url) for link in snapshot.social_links
        ],
        seo_title_suffix=snapshot.seo_title_suffix,
        seo_description=snapshot.seo_description,
        analytics_provider=snapshot.analytics_provider,
        analytics_public_id=snapshot.analytics_public_id,
        public_availability=snapshot.public_availability,
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
        version=snapshot.version,
    )


def _settings_values(payload: WebsiteSettingsUpdateRequest) -> WebsiteSettingsValues:
    return WebsiteSettingsValues(
        website_name=payload.website_name,
        default_title=payload.default_title,
        default_description=payload.default_description,
        logo_media_id=payload.logo_media_id,
        favicon_media_id=payload.favicon_media_id,
        social_image_media_id=payload.social_image_media_id,
        default_locale=payload.default_locale,
        timezone=payload.timezone,
        theme_policy=payload.theme_policy,
        primary_color=payload.primary_color,
        accent_color=payload.accent_color,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        social_links=tuple(
            SettingsSocialLink(label=link.label, url=link.url) for link in payload.social_links
        ),
        seo_title_suffix=payload.seo_title_suffix,
        seo_description=payload.seo_description,
        analytics_provider=payload.analytics_provider,
        analytics_public_id=payload.analytics_public_id,
        public_availability=payload.public_availability,
    )


def _navigation_item(item: NavigationItemInput) -> NavigationItem:
    return NavigationItem(
        id=item.id,
        parent_id=item.parent_id,
        label=item.label,
        link_kind=item.link_kind,
        href=item.href,
        target=item.target,
        visible=item.visible,
        position=item.position,
    )


def _navigation_data(tree: NavigationTree) -> NavigationData:
    return NavigationData(
        id=tree.id,
        items=[
            NavigationItemData(
                id=item.id,
                parent_id=item.parent_id,
                label=item.label,
                link_kind=item.link_kind,
                href=item.href,
                target=item.target,
                visible=item.visible,
                position=item.position,
                version=item.version,
            )
            for item in tree.items
        ],
        version=tree.version,
    )


def _footer_item(item: FooterItemInput) -> FooterItem:
    return FooterItem(
        id=item.id,
        label=item.label,
        link_kind=item.link_kind,
        item_kind=item.item_kind,
        href=item.href,
        target=item.target,
        visible=item.visible,
        position=item.position,
    )


def _footer_column(column: FooterColumnInput) -> FooterColumn:
    return FooterColumn(
        id=column.id,
        title=column.title,
        visible=column.visible,
        position=column.position,
        items=tuple(_footer_item(item) for item in column.items),
    )


def footer_data(tree: FooterTree) -> FooterData:
    """Project the versioned footer tree to its strict API schema."""
    return FooterData(
        id=tree.id,
        copyright_text=tree.copyright_text,
        columns=[
            FooterColumnData(
                id=column.id,
                title=column.title,
                visible=column.visible,
                position=column.position,
                items=[
                    FooterItemData(
                        id=item.id,
                        label=item.label,
                        link_kind=item.link_kind,
                        item_kind=item.item_kind,
                        href=item.href,
                        target=item.target,
                        visible=item.visible,
                        position=item.position,
                        version=item.version,
                    )
                    for item in column.items
                ],
                version=column.version,
            )
            for column in tree.columns
        ],
        version=tree.version,
    )


def _canonical(payload: BaseModel, if_match: str | None) -> bytes:
    value = {"if_match": if_match, "body": payload.model_dump(mode="json")}
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _map_site_error(error: Exception) -> ApiError:
    if isinstance(error, MediaStateError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, TreeValidationError):
        return ApiError.from_code(
            "VALIDATION_FAILED",
            details={
                "fields": [
                    {
                        "path": f"body.{error.path}",
                        "code": error.code,
                        "message": "Value is invalid.",
                    }
                ]
            },
        )
    if isinstance(error, IdempotencyRejectedError):
        return map_idempotency_decision(error.decision)
    return map_common_error(error)


@router.get(
    "/profile",
    operation_id="admin_profile_get",
    response_model=SuccessEnvelope[ProfileData],
    responses=_ADMIN_RESPONSES,
)
async def admin_profile_get(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ProfileData]:
    """Return complete private profile state."""
    snapshot = await _profile_service(request).admin_get(_actor(session))
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.version)
    return success(request, _profile_data(snapshot))


@router.put(
    "/profile",
    operation_id="admin_profile_update",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[ProfileData],
    responses=_ADMIN_RESPONSES,
)
async def admin_profile_update(
    payload: ProfileUpdateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[ProfileData]:
    """Replace profile state with explicit publication decisions."""
    try:
        snapshot = await _profile_service(request).update(
            UpdateProfileCommand(
                actor=_actor(session),
                if_match=if_match,
                request_id=get_request_id(request),
                values=_profile_values(payload),
            )
        )
    except _SITE_MUTATION_ERRORS as error:
        raise _map_site_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.version)
    return success(request, _profile_data(snapshot))


@router.get(
    "/settings",
    operation_id="admin_website_settings_get",
    response_model=SuccessEnvelope[WebsiteSettingsData],
    responses=_ADMIN_RESPONSES,
)
async def admin_settings_get(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[WebsiteSettingsData]:
    """Return complete non-secret settings."""
    snapshot = await _settings_service(request).admin_get(_actor(session))
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.version)
    return success(request, _settings_data(snapshot))


@router.put(
    "/settings",
    operation_id="admin_website_settings_update",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[WebsiteSettingsData],
    responses=_ADMIN_RESPONSES,
)
async def admin_settings_update(
    payload: WebsiteSettingsUpdateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[WebsiteSettingsData]:
    """Replace allow-listed settings; secret-capable extras are rejected."""
    try:
        snapshot = await _settings_service(request).update(
            UpdateWebsiteSettingsCommand(
                actor=_actor(session),
                if_match=if_match,
                request_id=get_request_id(request),
                values=_settings_values(payload),
            )
        )
    except _SITE_MUTATION_ERRORS as error:
        raise _map_site_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.version)
    return success(request, _settings_data(snapshot))


@router.get(
    "/navigation",
    operation_id="admin_navigation_get",
    response_model=SuccessEnvelope[NavigationData],
    responses=_ADMIN_RESPONSES,
)
async def admin_navigation_get(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[NavigationData]:
    """Return the complete primary navigation tree."""
    tree = await _navigation_service(request).admin_navigation_get(_actor(session))
    set_private_no_store(response)
    set_resource_etag(response, version=tree.version)
    return success(request, _navigation_data(tree))


@router.put(
    "/navigation",
    operation_id="admin_navigation_replace",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[NavigationData],
    responses=_ADMIN_RESPONSES,
)
async def admin_navigation_replace(
    payload: NavigationReplaceRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[TreeMutationHeaders, Depends(tree_mutation_headers)],
) -> SuccessEnvelope[NavigationData]:
    """Atomically replace the complete navigation tree."""
    service = _navigation_service(request)
    actor = _actor(session)
    current = await service.admin_navigation_get(actor)
    try:
        tree = await service.replace_navigation(
            ReplaceNavigationCommand(
                actor=actor,
                if_match=headers.if_match,
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                tree=NavigationTree(
                    id=current.id,
                    items=tuple(_navigation_item(item) for item in payload.items),
                    version=current.version,
                ),
            )
        )
    except _SITE_MUTATION_ERRORS as error:
        raise _map_site_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=tree.version)
    return success(request, _navigation_data(tree))


@router.get(
    "/footer",
    operation_id="admin_footer_get",
    response_model=SuccessEnvelope[FooterData],
    responses=_ADMIN_RESPONSES,
)
async def admin_footer_get(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[FooterData]:
    """Return the complete footer tree."""
    tree = await _navigation_service(request).admin_footer_get(_actor(session))
    set_private_no_store(response)
    set_resource_etag(response, version=tree.version)
    return success(request, footer_data(tree))


@router.put(
    "/footer",
    operation_id="admin_footer_replace",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[FooterData],
    responses=_ADMIN_RESPONSES,
)
async def admin_footer_replace(
    payload: FooterReplaceRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[TreeMutationHeaders, Depends(tree_mutation_headers)],
) -> SuccessEnvelope[FooterData]:
    """Atomically replace the complete footer tree."""
    service = _navigation_service(request)
    actor = _actor(session)
    current = await service.admin_footer_get(actor)
    try:
        tree = await service.replace_footer(
            ReplaceFooterCommand(
                actor=actor,
                if_match=headers.if_match,
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                tree=FooterTree(
                    id=current.id,
                    copyright_text=payload.copyright_text,
                    columns=tuple(_footer_column(column) for column in payload.columns),
                    version=current.version,
                ),
            )
        )
    except _SITE_MUTATION_ERRORS as error:
        raise _map_site_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=tree.version)
    return success(request, footer_data(tree))
