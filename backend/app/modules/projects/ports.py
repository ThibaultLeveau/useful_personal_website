"""Inward-facing persistence and provider ports for projects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.common.domain.pagination import Page
    from app.modules.audit.domain import AuditEntry
    from app.modules.experiences.domain import ExperienceReferenceSummary
    from app.modules.media.ports import MediaRepositoryPort
    from app.modules.projects.domain import (
        AdminProjectQuery,
        Project,
        ProjectReferenceSummary,
        ProjectRevision,
        ProjectSnapshot,
        ProjectValues,
        PublicProjectQuery,
    )
    from app.modules.skills.domain import SkillReferenceSummary


class ProjectRepositoryPort(Protocol):
    """Revision-safe project persistence without transaction ownership."""

    async def database_now(self) -> datetime:
        """Return PostgreSQL transaction time in UTC."""
        ...

    async def slug_exists(self, slug: str) -> bool:
        """Check the immutable case-insensitive route identity."""
        ...

    async def list_admin(self, query: AdminProjectQuery) -> Page[ProjectSnapshot]:
        """Return one bounded administrator page."""
        ...

    async def list_public(self, query: PublicProjectQuery) -> Page[ProjectSnapshot]:
        """Return only effective public project snapshots."""
        ...

    async def get(self, project_id: UUID, *, for_update: bool = False) -> ProjectSnapshot | None:
        """Load one project aggregate and required revisions."""
        ...

    async def get_public_by_slug(self, slug: str) -> ProjectSnapshot | None:
        """Resolve an effective public slug without existence leakage."""
        ...

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Project, ...]:
        """Return all nondeleted projects in deterministic curated order."""
        ...

    async def reference_summaries(
        self,
        project_ids: tuple[UUID, ...],
    ) -> tuple[ProjectReferenceSummary, ...]:
        """Resolve provider-owned labels and effective public summaries."""
        ...

    async def related_graph_would_cycle(
        self,
        source_id: UUID,
        target_ids: tuple[UUID, ...],
        *,
        maximum_nodes: int,
    ) -> bool:
        """Check the bounded stable-ID graph under transaction serialization."""
        ...

    async def add(self, project: Project, revision: ProjectRevision) -> None:
        """Stage aggregate and revision one atomically."""
        ...

    async def save_draft(
        self,
        snapshot: ProjectSnapshot,
        values: ProjectValues,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        """Replace only current mutable revision values."""
        ...

    async def publish(
        self,
        snapshot: ProjectSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ProjectSnapshot:
        """Freeze, point, and copy the next mutable draft."""
        ...

    async def reschedule(
        self,
        snapshot: ProjectSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> ProjectSnapshot:
        """Change only schedule metadata."""
        ...

    async def unpublish(
        self,
        snapshot: ProjectSnapshot,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        """Clear public eligibility while retaining revisions."""
        ...

    async def set_visibility(
        self,
        snapshot: ProjectSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> ProjectSnapshot:
        """Set visibility independently from lifecycle."""
        ...

    async def set_featured(
        self,
        snapshot: ProjectSnapshot,
        *,
        featured: bool,
        now: datetime,
    ) -> ProjectSnapshot:
        """Set featured independently from lifecycle."""
        ...

    async def reorder(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Project, ...]:
        """Replace complete nondeleted curated order."""
        ...

    async def soft_delete(
        self,
        snapshot: ProjectSnapshot,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        """Remove eligibility without destroying revision history."""
        ...


class SkillReferencePort(Protocol):
    """Accepted M4 provider surface."""

    async def resolve(self, skill_ids: tuple[UUID, ...]) -> tuple[SkillReferenceSummary, ...]:
        """Resolve all skill IDs or fail the complete set."""
        ...


class ExperienceReferencePort(Protocol):
    """Accepted M5 provider surface."""

    async def resolve(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Resolve all experience IDs or fail the complete set."""
        ...


class AuditPort(Protocol):
    """Insert-only controlled project audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed audit fact."""
        ...


class ProjectsUnitOfWork(Protocol):
    """One project application transaction."""

    projects: ProjectRepositoryPort
    audit: AuditPort
    idempotency: IdempotencyStore
    media: MediaRepositoryPort

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


class ProjectsUnitOfWorkFactory(Protocol):
    """Create a fresh project transaction."""

    def __call__(self) -> ProjectsUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
