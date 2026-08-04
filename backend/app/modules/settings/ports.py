"""Inward-facing website-settings persistence ports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.modules.audit.domain import AuditEntry
    from app.modules.media.ports import MediaRepositoryPort
    from app.modules.settings.domain import WebsiteSettingsSnapshot, WebsiteSettingsValues


class WebsiteSettingsState(Protocol):
    """Mutable non-secret settings state inside one transaction."""

    id: UUID
    website_name: str | None
    default_title: str | None
    default_description: str | None
    logo_media_id: UUID | None
    favicon_media_id: UUID | None
    social_image_media_id: UUID | None
    default_locale: str
    timezone: str
    theme_policy: str
    primary_color: str | None
    accent_color: str | None
    contact_email: str | None
    contact_phone: str | None
    social_links: list[dict[str, str]]
    seo_title_suffix: str | None
    seo_description: str | None
    analytics_provider: str
    analytics_public_id: str | None
    public_availability: str | None
    created_at: datetime
    updated_at: datetime
    version: int


class WebsiteSettingsRepositoryPort(Protocol):
    """Singleton website-settings persistence operations."""

    async def get(self, *, for_update: bool = False) -> WebsiteSettingsState:
        """Load the migration-created singleton shell."""
        ...

    def replace(
        self,
        state: WebsiteSettingsState,
        values: WebsiteSettingsValues,
        *,
        now: datetime,
    ) -> None:
        """Replace allow-listed fields and advance the integer version."""
        ...

    def snapshot(self, state: WebsiteSettingsState) -> WebsiteSettingsSnapshot:
        """Return an immutable transport-neutral snapshot."""
        ...


class AuditPort(Protocol):
    """Insert-only audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed fact."""
        ...


class WebsiteSettingsUnitOfWork(Protocol):
    """One website-settings operation transaction."""

    settings: WebsiteSettingsRepositoryPort
    media: MediaRepositoryPort
    audit: AuditPort

    async def __aenter__(self) -> Self:
        """Open one transaction and bind repositories."""
        ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work and release resources."""
        ...

    async def commit(self) -> None:
        """Commit the application operation."""
        ...


class WebsiteSettingsUnitOfWorkFactory(Protocol):
    """Create a fresh settings transaction."""

    def __call__(self) -> WebsiteSettingsUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
