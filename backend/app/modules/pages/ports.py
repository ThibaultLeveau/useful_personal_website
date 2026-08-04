"""Inward-facing transaction, persistence, and provider ports for pages."""

# Protocol methods intentionally keep their contracts adjacent and compact.
# ruff: noqa: D102, D105, PLR0913

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.modules.audit.domain import AuditEntry
    from app.modules.blog.domain import PostReferenceSummary
    from app.modules.experiences.domain import ExperienceReferenceSummary
    from app.modules.media.ports import MediaRepositoryPort
    from app.modules.pages.domain import (
        Page,
        PageBlock,
        PageBlockValues,
        PageReferenceTarget,
        PageRevision,
        PageRevisionValues,
        PageRouteKind,
        PageSnapshot,
    )
    from app.modules.pages.registry import BlockReference
    from app.modules.profile.domain import PublicProfile
    from app.modules.projects.domain import ProjectReferenceSummary
    from app.modules.skills.domain import SkillReferenceSummary


class PageRepositoryPort(Protocol):
    """Revision-safe page persistence without transaction ownership."""

    async def database_now(self) -> datetime: ...

    async def route_exists(
        self,
        route_kind: PageRouteKind,
        slug: str | None,
        *,
        excluding_id: UUID | None = None,
    ) -> bool: ...

    async def next_position(self) -> int: ...
    async def add_page(self, page: Page, revision: PageRevision) -> None: ...
    async def get_page(self, page_id: UUID, *, for_update: bool = False) -> PageSnapshot | None: ...
    async def get_public_home(self) -> PageSnapshot | None: ...
    async def get_public_custom(self, slug: str) -> PageSnapshot | None: ...
    async def list_pages(
        self, *, offset: int, limit: int
    ) -> tuple[tuple[PageSnapshot, ...], int]: ...

    async def reference_targets(self, ids: tuple[UUID, ...]) -> tuple[PageReferenceTarget, ...]: ...

    async def list_public_routes(
        self, *, offset: int, limit: int
    ) -> tuple[tuple[PageReferenceTarget, ...], int]: ...

    async def save_draft(
        self,
        snapshot: PageSnapshot,
        *,
        values: PageRevisionValues,
        route_kind: PageRouteKind,
        slug: str | None,
        visible: bool,
        navigation_visible: bool,
        now: datetime,
    ) -> PageSnapshot: ...

    async def add_block(
        self,
        snapshot: PageSnapshot,
        block: PageBlock,
        *,
        position: int,
        now: datetime,
    ) -> PageSnapshot: ...

    async def update_block(
        self,
        snapshot: PageSnapshot,
        block_id: UUID,
        values: PageBlockValues,
        references: tuple[BlockReference, ...],
        *,
        now: datetime,
    ) -> PageSnapshot: ...

    async def duplicate_block(
        self, snapshot: PageSnapshot, block_id: UUID, *, now: datetime
    ) -> PageSnapshot: ...

    async def set_block_visibility(
        self,
        snapshot: PageSnapshot,
        block_id: UUID,
        *,
        visible: bool,
        now: datetime,
    ) -> PageSnapshot: ...

    async def delete_block(
        self, snapshot: PageSnapshot, block_id: UUID, *, now: datetime
    ) -> PageSnapshot: ...

    async def reorder_blocks(
        self, snapshot: PageSnapshot, ordered_ids: tuple[UUID, ...], *, now: datetime
    ) -> PageSnapshot: ...

    async def publish(
        self,
        snapshot: PageSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> PageSnapshot: ...

    async def reschedule(
        self, snapshot: PageSnapshot, *, publish_at: datetime, now: datetime
    ) -> PageSnapshot: ...

    async def unpublish(self, snapshot: PageSnapshot, *, now: datetime) -> PageSnapshot: ...
    async def soft_delete(self, snapshot: PageSnapshot, *, now: datetime) -> PageSnapshot: ...


class AuditPort(Protocol):
    """Insert-only controlled page audit dependency."""

    def append(self, entry: AuditEntry) -> None: ...


class PagesUnitOfWork(Protocol):
    """One atomic page application transaction."""

    pages: PageRepositoryPort
    media: MediaRepositoryPort
    audit: AuditPort
    idempotency: IdempotencyStore

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...


class PagesUnitOfWorkFactory(Protocol):
    """Create a fresh page transaction."""

    def __call__(self) -> PagesUnitOfWork: ...


class SkillReferencePort(Protocol):
    """Released public-safe skill provider boundary."""

    async def resolve(self, ids: tuple[UUID, ...]) -> tuple[SkillReferenceSummary, ...]: ...
    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[SkillReferenceSummary, ...]: ...


class ExperienceReferencePort(Protocol):
    """Released public-safe experience provider boundary."""

    async def resolve(self, ids: tuple[UUID, ...]) -> tuple[ExperienceReferenceSummary, ...]: ...
    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[ExperienceReferenceSummary, ...]: ...


class ProjectReferencePort(Protocol):
    """Released public-safe project provider boundary."""

    async def resolve(self, ids: tuple[UUID, ...]) -> tuple[ProjectReferenceSummary, ...]: ...
    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[ProjectReferenceSummary, ...]: ...


class BlogReferencePort(Protocol):
    """Released public-safe post provider boundary."""

    async def resolve(self, ids: tuple[UUID, ...]) -> tuple[PostReferenceSummary, ...]: ...
    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[PostReferenceSummary, ...]: ...


class ProfilePublicPort(Protocol):
    """Released public-approved singleton profile boundary."""

    async def public_get(self) -> PublicProfile: ...
