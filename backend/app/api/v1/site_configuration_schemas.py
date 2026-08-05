"""Strict admin/public schemas for M3 site configuration."""

from __future__ import annotations

import re
from datetime import datetime  # noqa: TC003 - Pydantic resolves runtime annotations.
from typing import Annotated, Never, Self
from urllib.parse import urlsplit
from uuid import UUID  # noqa: TC003 - Pydantic resolves runtime annotations.
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.navigation.domain import FooterItemKind, LinkKind, LinkTarget
from app.modules.profile.domain import ContactPreference, PublicProfileField
from app.modules.settings.domain import AnalyticsProvider, ThemePolicy

ShortText = Annotated[str, Field(min_length=1, max_length=160)]
LongText = Annotated[str, Field(min_length=1, max_length=10_000)]
Label = Annotated[str, Field(min_length=1, max_length=80)]
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 ()-]{5,30}$")
_PLAUSIBLE_ID_PATTERN = re.compile(
    r"^(?=.{4,80}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
_GOOGLE_ID_PATTERN = re.compile(r"^G-[A-Z0-9]{6,20}$")
_CONTROL_CHARACTER_BOUNDARY = 32


def _invalid(message: str) -> Never:
    """Raise one validator-compatible error without leaking input."""
    raise ValueError(message)


def _optional_https_url(value: str | None) -> str | None:
    if value is None:
        return None
    if value != value.strip() or any(
        ord(character) < _CONTROL_CHARACTER_BOUNDARY for character in value
    ):
        _invalid("URL must be canonical HTTPS")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or "\\" in value
    ):
        _invalid("URL must be canonical HTTPS")
    return value


def _reject_url_whitespace(value: object) -> object:
    if isinstance(value, str) and value != value.strip():
        _invalid("URL must not contain surrounding whitespace")
    return value


def _optional_email(value: str | None) -> str | None:
    if value is not None and _EMAIL_PATTERN.fullmatch(value) is None:
        _invalid("email address is invalid")
    return value


class StrictModel(BaseModel):
    """Reject mass-assigned or typoed fields on every mutation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SocialLinkInput(StrictModel):
    """A labelled public HTTPS destination."""

    label: Label
    url: Annotated[str, Field(min_length=8, max_length=2048)]

    _reject_url_whitespace = field_validator("url", mode="before")(_reject_url_whitespace)
    _validate_url = field_validator("url")(_optional_https_url)


class ProfileUpdateRequest(StrictModel):
    """Complete administrator profile replacement."""

    full_name: ShortText | None = None
    professional_title: ShortText | None = None
    short_biography: Annotated[str, Field(min_length=1, max_length=600)] | None = None
    full_biography: LongText | None = None
    profile_image_id: UUID | None = None
    location: ShortText | None = None
    availability: Annotated[str, Field(min_length=1, max_length=240)] | None = None
    email: Annotated[str, Field(min_length=3, max_length=320)] | None = None
    social_links: Annotated[list[SocialLinkInput], Field(max_length=12)] = Field(
        default_factory=list
    )
    github_url: Annotated[str, Field(min_length=8, max_length=2048)] | None = None
    linkedin_url: Annotated[str, Field(min_length=8, max_length=2048)] | None = None
    personal_values: Annotated[list[ShortText], Field(max_length=20)] = Field(default_factory=list)
    work_preferences: Annotated[list[ShortText], Field(max_length=20)] = Field(default_factory=list)
    resume_url: Annotated[str, Field(min_length=8, max_length=2048)] | None = None
    contact_preference: ContactPreference = ContactPreference.NONE
    public_fields: set[PublicProfileField] = Field(default_factory=set)

    _validate_email = field_validator("email")(_optional_email)
    _reject_url_whitespace = field_validator(
        "github_url",
        "linkedin_url",
        "resume_url",
        mode="before",
    )(_reject_url_whitespace)
    _validate_urls = field_validator("github_url", "linkedin_url", "resume_url")(
        _optional_https_url
    )

    @field_validator("personal_values", "work_preferences")
    @classmethod
    def unique_text_values(cls, value: list[str]) -> list[str]:
        """Reject duplicate ordered values after whitespace normalization."""
        if len(set(value)) != len(value):
            _invalid("values must be unique")
        return value

    @field_validator("social_links")
    @classmethod
    def unique_social_links(cls, value: list[SocialLinkInput]) -> list[SocialLinkInput]:
        """Reject duplicate labels or destinations."""
        labels = {link.label.casefold() for link in value}
        urls = {link.url for link in value}
        if len(labels) != len(value) or len(urls) != len(value):
            _invalid("social links must be unique")
        return value


class ProfileData(ProfileUpdateRequest):
    """Complete administrator profile resource."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    version: int = Field(ge=1)


class PublicProfileData(StrictModel):
    """Public allow-list with unapproved values omitted, never redacted/null."""

    configured: bool
    full_name: str | None = None
    professional_title: str | None = None
    short_biography: str | None = None
    full_biography: str | None = None
    profile_image_id: UUID | None = None
    location: str | None = None
    availability: str | None = None
    email: str | None = None
    social_links: list[SocialLinkInput] | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    personal_values: list[str] | None = None
    work_preferences: list[str] | None = None
    resume_url: str | None = None
    contact_preference: ContactPreference | None = None


class WebsiteSettingsUpdateRequest(StrictModel):
    """Complete non-secret website-settings replacement."""

    website_name: Annotated[str, Field(min_length=1, max_length=120)] | None = None
    default_title: ShortText | None = None
    default_description: Annotated[str, Field(min_length=1, max_length=320)] | None = None
    logo_media_id: UUID | None = None
    favicon_media_id: UUID | None = None
    social_image_media_id: UUID | None = None
    default_locale: Annotated[str, Field(min_length=2, max_length=35)] = "en"
    timezone: Annotated[str, Field(min_length=1, max_length=64)] = "UTC"
    theme_policy: ThemePolicy = ThemePolicy.SYSTEM
    primary_color: str | None = None
    accent_color: str | None = None
    contact_email: Annotated[str, Field(min_length=3, max_length=320)] | None = None
    contact_phone: Annotated[str, Field(min_length=6, max_length=32)] | None = None
    social_links: Annotated[list[SocialLinkInput], Field(max_length=12)] = Field(
        default_factory=list
    )
    seo_title_suffix: Annotated[str, Field(min_length=1, max_length=80)] | None = None
    seo_description: Annotated[str, Field(min_length=1, max_length=320)] | None = None
    analytics_provider: AnalyticsProvider = AnalyticsProvider.NONE
    analytics_public_id: Annotated[str, Field(min_length=4, max_length=80)] | None = None
    public_availability: Annotated[str, Field(min_length=1, max_length=240)] | None = None

    _validate_contact_email = field_validator("contact_email")(_optional_email)

    @field_validator("default_locale")
    @classmethod
    def valid_locale(cls, value: str) -> str:
        """Accept a bounded IETF language tag subset."""
        if _LOCALE_PATTERN.fullmatch(value) is None:
            _invalid("locale must be an IETF language tag")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        """Require an installed IANA timezone identifier."""
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            _invalid("timezone must be an IANA identifier")
        return value

    @field_validator("primary_color", "accent_color")
    @classmethod
    def valid_color(cls, value: str | None) -> str | None:
        """Accept only a six-digit CSS hex color token."""
        if value is not None and _HEX_COLOR_PATTERN.fullmatch(value) is None:
            _invalid("color must use #RRGGBB")
        return value.upper() if value is not None else None

    @field_validator("contact_phone")
    @classmethod
    def valid_phone(cls, value: str | None) -> str | None:
        """Accept a conservative human-readable international phone value."""
        if value is not None and _PHONE_PATTERN.fullmatch(value) is None:
            _invalid("phone number is invalid")
        return value

    @model_validator(mode="after")
    def valid_analytics_pair(self) -> Self:
        """Allow only public identifiers for the selected provider."""
        identifier = self.analytics_public_id
        if self.analytics_provider is AnalyticsProvider.NONE:
            if identifier is not None:
                _invalid("analytics identifier requires an allow-listed provider")
        elif self.analytics_provider is AnalyticsProvider.PLAUSIBLE:
            if identifier is None or _PLAUSIBLE_ID_PATTERN.fullmatch(identifier) is None:
                _invalid("Plausible identifier must be a public domain")
        elif identifier is None or _GOOGLE_ID_PATTERN.fullmatch(identifier) is None:
            _invalid("Google Analytics identifier is invalid")
        return self


class WebsiteSettingsData(WebsiteSettingsUpdateRequest):
    """Complete administrator website-settings resource."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    version: int = Field(ge=1)


class PublicSiteSettingsData(StrictModel):
    """Public site settings plus the public footer projection."""

    configured: bool
    website_name: str | None = None
    default_title: str | None = None
    default_description: str | None = None
    logo_media_id: UUID | None = None
    favicon_media_id: UUID | None = None
    social_image_media_id: UUID | None = None
    default_locale: str
    timezone: str
    theme_policy: ThemePolicy
    primary_color: str | None = None
    accent_color: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    social_links: list[SocialLinkInput]
    seo_title_suffix: str | None = None
    seo_description: str | None = None
    analytics_provider: AnalyticsProvider
    analytics_public_id: str | None = None
    public_availability: str | None = None
    footer: PublicFooterData


class NavigationItemInput(StrictModel):
    """One complete flat navigation node."""

    id: UUID
    parent_id: UUID | None = None
    label: Label
    link_kind: LinkKind
    href: Annotated[str, Field(min_length=1, max_length=2048)]
    target: LinkTarget = LinkTarget.SAME_WINDOW
    visible: bool = True
    position: int = Field(ge=0, le=1024)

    _reject_href_whitespace = field_validator("href", mode="before")(_reject_url_whitespace)


class NavigationItemData(NavigationItemInput):
    """One persisted navigation node."""

    version: int = Field(ge=1)


class NavigationReplaceRequest(StrictModel):
    """Complete primary navigation replacement."""

    items: Annotated[list[NavigationItemInput], Field(max_length=408)]


class NavigationData(StrictModel):
    """Versioned primary navigation aggregate."""

    id: UUID
    items: list[NavigationItemData]
    version: int = Field(ge=1)


class PublicNavigationItemData(StrictModel):
    """One visible public destination without edit-only state."""

    key: UUID
    parent_key: UUID | None = None
    label: str
    href: str
    target: LinkTarget


class PublicNavigationData(StrictModel):
    """Visible primary navigation without aggregate versions or flags."""

    items: list[PublicNavigationItemData]


class FooterItemInput(StrictModel):
    """One footer link."""

    id: UUID
    label: Label
    link_kind: LinkKind
    item_kind: FooterItemKind = FooterItemKind.LINK
    href: Annotated[str, Field(min_length=1, max_length=2048)]
    target: LinkTarget = LinkTarget.SAME_WINDOW
    visible: bool = True
    position: int = Field(ge=0, le=1024)

    _reject_href_whitespace = field_validator("href", mode="before")(_reject_url_whitespace)


class FooterItemData(FooterItemInput):
    """One persisted footer link."""

    version: int = Field(ge=1)


class FooterColumnInput(StrictModel):
    """One ordered footer column."""

    id: UUID
    title: Label
    visible: bool = True
    position: int = Field(ge=0, le=1024)
    items: Annotated[list[FooterItemInput], Field(max_length=16)]


class FooterColumnData(StrictModel):
    """One persisted footer column."""

    id: UUID
    title: str
    visible: bool
    position: int
    items: list[FooterItemData]
    version: int = Field(ge=1)


class FooterReplaceRequest(StrictModel):
    """Complete footer replacement."""

    copyright_text: Annotated[str, Field(min_length=1, max_length=240)] | None = None
    columns: Annotated[list[FooterColumnInput], Field(max_length=8)]


class FooterData(StrictModel):
    """Versioned footer aggregate."""

    id: UUID
    copyright_text: str | None = None
    columns: list[FooterColumnData]
    version: int = Field(ge=1)


class PublicFooterItemData(StrictModel):
    """One visible public footer destination."""

    label: str
    item_kind: FooterItemKind
    href: str
    target: LinkTarget


class PublicFooterColumnData(StrictModel):
    """One visible public footer column."""

    title: str
    items: list[PublicFooterItemData]


class PublicFooterData(StrictModel):
    """Visible footer content without edit-only identifiers or versions."""

    copyright_text: str | None = None
    columns: list[PublicFooterColumnData]


PublicSiteSettingsData.model_rebuild()
