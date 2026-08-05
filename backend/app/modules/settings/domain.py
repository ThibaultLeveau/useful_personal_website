"""Website settings values and validation catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class ThemePolicy(StrEnum):
    """Site-wide initial theme selection policy."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class AnalyticsProvider(StrEnum):
    """Providers whose public identifiers are safe ordinary configuration."""

    NONE = "none"
    PLAUSIBLE = "plausible"
    GOOGLE_ANALYTICS = "google_analytics"


@dataclass(frozen=True, slots=True)
class SocialLink:
    """A labelled HTTPS public social destination."""

    label: str
    url: str


@dataclass(frozen=True, slots=True)
class WebsiteSettingsValues:
    """Validated non-secret replacement settings."""

    website_name: str | None
    default_title: str | None
    default_description: str | None
    logo_media_id: UUID | None
    favicon_media_id: UUID | None
    social_image_media_id: UUID | None
    default_locale: str
    timezone: str
    theme_policy: ThemePolicy
    primary_color: str | None
    accent_color: str | None
    contact_email: str | None
    contact_phone: str | None
    social_links: tuple[SocialLink, ...]
    seo_title_suffix: str | None
    seo_description: str | None
    analytics_provider: AnalyticsProvider
    analytics_public_id: str | None
    public_availability: str | None


@dataclass(frozen=True, slots=True)
class WebsiteSettingsSnapshot:
    """Complete administrator settings state."""

    id: UUID
    website_name: str | None
    default_title: str | None
    default_description: str | None
    logo_media_id: UUID | None
    favicon_media_id: UUID | None
    social_image_media_id: UUID | None
    default_locale: str
    timezone: str
    theme_policy: ThemePolicy
    primary_color: str | None
    accent_color: str | None
    contact_email: str | None
    contact_phone: str | None
    social_links: tuple[SocialLink, ...]
    seo_title_suffix: str | None
    seo_description: str | None
    analytics_provider: AnalyticsProvider
    analytics_public_id: str | None
    public_availability: str | None
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class PublicSiteSettings:
    """Public-only settings; deployment secrets are unrepresentable."""

    website_name: str | None
    default_title: str | None
    default_description: str | None
    logo_media_id: UUID | None
    favicon_media_id: UUID | None
    social_image_media_id: UUID | None
    default_locale: str
    timezone: str
    theme_policy: ThemePolicy
    primary_color: str | None
    accent_color: str | None
    contact_email: str | None
    contact_phone: str | None
    social_links: tuple[SocialLink, ...]
    seo_title_suffix: str | None
    seo_description: str | None
    analytics_provider: AnalyticsProvider
    analytics_public_id: str | None
    public_availability: str | None


def public_settings(snapshot: WebsiteSettingsSnapshot) -> PublicSiteSettings:
    """Project only deliberate, non-secret public settings."""
    return PublicSiteSettings(
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
        social_links=snapshot.social_links,
        seo_title_suffix=snapshot.seo_title_suffix,
        seo_description=snapshot.seo_description,
        analytics_provider=snapshot.analytics_provider,
        analytics_public_id=snapshot.analytics_public_id,
        public_availability=snapshot.public_availability,
    )
