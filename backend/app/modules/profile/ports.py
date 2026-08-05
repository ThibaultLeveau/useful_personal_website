"""Inward-facing profile persistence and transaction ports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.modules.audit.domain import AuditEntry
    from app.modules.media.ports import MediaRepositoryPort
    from app.modules.profile.domain import ProfileSnapshot, ProfileValues


class ProfileState(Protocol):
    """Mutable profile state used only inside an application transaction."""

    id: UUID
    full_name: str | None
    professional_title: str | None
    short_biography: str | None
    full_biography: str | None
    profile_image_id: UUID | None
    location: str | None
    availability: str | None
    email: str | None
    social_links: list[dict[str, str]]
    github_url: str | None
    linkedin_url: str | None
    personal_values: list[str]
    work_preferences: list[str]
    resume_url: str | None
    contact_preference: str
    public_fields: list[str]
    created_at: datetime
    updated_at: datetime
    version: int


class ProfileRepositoryPort(Protocol):
    """Singleton profile persistence operations."""

    async def get(self, *, for_update: bool = False) -> ProfileState:
        """Load the migration-created singleton shell."""
        ...

    def replace(self, state: ProfileState, values: ProfileValues, *, now: datetime) -> None:
        """Replace allow-listed fields and advance the integer version."""
        ...

    def snapshot(self, state: ProfileState) -> ProfileSnapshot:
        """Return an immutable transport-neutral snapshot."""
        ...


class AuditPort(Protocol):
    """Insert-only audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage an allow-listed fact."""
        ...


class ProfileUnitOfWork(Protocol):
    """One profile operation transaction."""

    profile: ProfileRepositoryPort
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


class ProfileUnitOfWorkFactory(Protocol):
    """Create a fresh profile transaction."""

    def __call__(self) -> ProfileUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
