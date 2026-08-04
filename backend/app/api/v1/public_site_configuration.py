"""Unauthenticated, cache-bounded public site configuration API."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request, Response

from app.api.v1.conventions import success
from app.api.v1.schemas import ErrorEnvelope, SuccessEnvelope
from app.api.v1.site_configuration_schemas import (
    PublicFooterColumnData,
    PublicFooterData,
    PublicFooterItemData,
    PublicNavigationData,
    PublicNavigationItemData,
    PublicProfileData,
    PublicSiteSettingsData,
    SocialLinkInput,
)
from app.common.errors import ApiError
from app.modules.navigation.service import NavigationService
from app.modules.profile.service import ProfileService
from app.modules.settings.domain import AnalyticsProvider
from app.modules.settings.service import WebsiteSettingsService

if TYPE_CHECKING:
    from app.modules.navigation.domain import FooterTree, NavigationTree
    from app.modules.profile.domain import PublicProfile
    from app.modules.settings.domain import PublicSiteSettings

router = APIRouter(prefix="/public", tags=["Public site"])

_PUBLIC_CACHE_CONTROL = "public, max-age=60, s-maxage=300, stale-while-revalidate=300"
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_PUBLIC_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}


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


def _set_public_cache(response: Response) -> None:
    response.headers["Cache-Control"] = _PUBLIC_CACHE_CONTROL


def _public_profile_data(profile: PublicProfile) -> PublicProfileData:
    values = (
        profile.full_name,
        profile.professional_title,
        profile.short_biography,
        profile.full_biography,
        profile.profile_image_id,
        profile.location,
        profile.availability,
        profile.email,
        profile.social_links,
        profile.github_url,
        profile.linkedin_url,
        profile.personal_values,
        profile.work_preferences,
        profile.resume_url,
        profile.contact_preference,
    )
    return PublicProfileData(
        configured=any(value is not None for value in values),
        full_name=profile.full_name,
        professional_title=profile.professional_title,
        short_biography=profile.short_biography,
        full_biography=profile.full_biography,
        profile_image_id=profile.profile_image_id,
        location=profile.location,
        availability=profile.availability,
        email=profile.email,
        social_links=(
            [SocialLinkInput(label=link.label, url=link.url) for link in profile.social_links]
            if profile.social_links is not None
            else None
        ),
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        personal_values=(
            list(profile.personal_values) if profile.personal_values is not None else None
        ),
        work_preferences=(
            list(profile.work_preferences) if profile.work_preferences is not None else None
        ),
        resume_url=profile.resume_url,
        contact_preference=profile.contact_preference,
    )


def _public_navigation_data(tree: NavigationTree) -> PublicNavigationData:
    return PublicNavigationData(
        items=[
            PublicNavigationItemData(
                key=item.id,
                parent_key=item.parent_id,
                label=item.label,
                href=item.href,
                target=item.target,
            )
            for item in tree.items
        ]
    )


def _public_footer_data(tree: FooterTree) -> PublicFooterData:
    return PublicFooterData(
        copyright_text=tree.copyright_text,
        columns=[
            PublicFooterColumnData(
                title=column.title,
                items=[
                    PublicFooterItemData(
                        label=item.label,
                        item_kind=item.item_kind,
                        href=item.href,
                        target=item.target,
                    )
                    for item in column.items
                ],
            )
            for column in tree.columns
        ],
    )


def _public_site_data(
    settings: PublicSiteSettings,
    footer: FooterTree,
) -> PublicSiteSettingsData:
    configured = (
        any(
            (
                settings.website_name,
                settings.default_title,
                settings.default_description,
                settings.logo_media_id,
                settings.favicon_media_id,
                settings.social_image_media_id,
                settings.primary_color,
                settings.accent_color,
                settings.contact_email,
                settings.contact_phone,
                settings.social_links,
                settings.seo_title_suffix,
                settings.seo_description,
                settings.analytics_public_id,
                settings.public_availability,
                footer.copyright_text,
                footer.columns,
            )
        )
        or settings.analytics_provider is not AnalyticsProvider.NONE
    )
    return PublicSiteSettingsData(
        configured=configured,
        website_name=settings.website_name,
        default_title=settings.default_title,
        default_description=settings.default_description,
        logo_media_id=settings.logo_media_id,
        favicon_media_id=settings.favicon_media_id,
        social_image_media_id=settings.social_image_media_id,
        default_locale=settings.default_locale,
        timezone=settings.timezone,
        theme_policy=settings.theme_policy,
        primary_color=settings.primary_color,
        accent_color=settings.accent_color,
        contact_email=settings.contact_email,
        contact_phone=settings.contact_phone,
        social_links=[
            SocialLinkInput(label=link.label, url=link.url) for link in settings.social_links
        ],
        seo_title_suffix=settings.seo_title_suffix,
        seo_description=settings.seo_description,
        analytics_provider=settings.analytics_provider,
        analytics_public_id=settings.analytics_public_id,
        public_availability=settings.public_availability,
        footer=_public_footer_data(footer),
    )


@router.get(
    "/profile",
    operation_id="public_profile_get",
    response_model=SuccessEnvelope[PublicProfileData],
    response_model_exclude_none=True,
    responses=_PUBLIC_RESPONSES,
)
async def public_profile_get(
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicProfileData]:
    """Return only profile fields explicitly approved for publication."""
    data = _public_profile_data(await _profile_service(request).public_get())
    _set_public_cache(response)
    return success(request, data)


@router.get(
    "/site",
    operation_id="public_site_get",
    response_model=SuccessEnvelope[PublicSiteSettingsData],
    response_model_exclude_none=True,
    responses=_PUBLIC_RESPONSES,
)
async def public_site_get(
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicSiteSettingsData]:
    """Return safe public settings and the visible footer."""
    settings = await _settings_service(request).public_get()
    footer = await _navigation_service(request).public_footer_get()
    _set_public_cache(response)
    return success(request, _public_site_data(settings, footer))


@router.get(
    "/navigation",
    operation_id="public_navigation_get",
    response_model=SuccessEnvelope[PublicNavigationData],
    responses=_PUBLIC_RESPONSES,
)
async def public_navigation_get(
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicNavigationData]:
    """Return only visible destinations, independent of caller credentials."""
    tree = await _navigation_service(request).public_navigation_get()
    _set_public_cache(response)
    return success(request, _public_navigation_data(tree))
