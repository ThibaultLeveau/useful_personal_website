"""Inward-facing persistence and capability ports for experiences."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.common.domain.pagination import Page
    from app.modules.audit.domain import AuditEntry
    from app.modules.experiences.domain import (
        AdminExperienceQuery,
        Experience,
        ExperienceReferenceSummary,
        ExperienceRevision,
        ExperienceSnapshot,
        ExperienceValues,
        PublicExperienceQuery,
    )
    from app.modules.skills.domain import SkillReferenceSummary


class ExperienceRepositoryPort(Protocol):
    """Revision-safe persistence operations without commit ownership."""

    async def database_now(self) -> datetime:
        """Return PostgreSQL transaction time in UTC."""
        ...

    async def list_admin(self, query: AdminExperienceQuery) -> Page[ExperienceSnapshot]:
        """Return one filtered deterministic administrator page."""
        ...

    async def list_public(self, query: PublicExperienceQuery) -> Page[ExperienceSnapshot]:
        """Return only database-time-effective public snapshots."""
        ...

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Experience, ...]:
        """Return all nondeleted aggregates in curated order."""
        ...

    async def reference_summaries(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Resolve provider-owned labels and effective public summaries in input order."""
        ...

    async def get(
        self,
        experience_id: UUID,
        *,
        for_update: bool = False,
    ) -> ExperienceSnapshot | None:
        """Load one aggregate with current draft and optional publication."""
        ...

    async def add(self, experience: Experience, revision: ExperienceRevision) -> None:
        """Stage an aggregate and its first mutable draft atomically."""
        ...

    async def save_draft(
        self,
        snapshot: ExperienceSnapshot,
        values: ExperienceValues,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Replace only the current unfrozen draft and advance aggregate version."""
        ...

    async def publish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Freeze/point the draft and create exactly one copy-on-write draft."""
        ...

    async def reschedule(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Change only publication scheduling metadata."""
        ...

    async def unpublish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Clear public eligibility while retaining every revision."""
        ...

    async def set_visibility(
        self,
        snapshot: ExperienceSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Set independent aggregate visibility."""
        ...

    async def reorder(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Experience, ...]:
        """Apply one complete normalized nondeleted aggregate order."""
        ...

    async def soft_delete(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Remove public eligibility without destroying revision history."""
        ...


class SkillReferencePort(Protocol):
    """M4 facade shape; M5 cannot reach into skills persistence."""

    async def resolve(
        self,
        skill_ids: tuple[UUID, ...],
    ) -> tuple[SkillReferenceSummary, ...]:
        """Resolve every referenced skill or fail the complete set."""
        ...


class AuditPort(Protocol):
    """Insert-only controlled audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed audit fact."""
        ...


class ExperiencesUnitOfWork(Protocol):
    """One experience application transaction."""

    experiences: ExperienceRepositoryPort
    audit: AuditPort
    idempotency: IdempotencyStore

    async def __aenter__(self) -> Self:
        """Open one transaction and bind ports."""
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
        """Commit the complete application operation."""
        ...


class ExperiencesUnitOfWorkFactory(Protocol):
    """Create a fresh experience transaction."""

    def __call__(self) -> ExperiencesUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
