"""Inward-facing persistence ports for the blog capability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.common.domain.pagination import Page
    from app.modules.audit.domain import AuditEntry
    from app.modules.blog.domain import (
        AdminPostQuery,
        Post,
        PostReferenceSummary,
        PostRevision,
        PostSnapshot,
        PostValues,
        PublicPostQuery,
        Taxonomy,
        TaxonomyKind,
        TaxonomyReferenceSummary,
    )
    from app.modules.media.ports import MediaRepositoryPort


class BlogRepositoryPort(Protocol):
    """Revision-safe post and taxonomy persistence without transaction ownership."""

    async def database_now(self) -> datetime:
        """Return PostgreSQL transaction time in UTC."""
        ...

    async def post_slug_exists(self, slug: str) -> bool:
        """Check the stable case-insensitive post route identity."""
        ...

    async def taxonomy_slug_exists(
        self,
        kind: TaxonomyKind,
        slug: str,
        *,
        excluding_id: UUID | None = None,
    ) -> bool:
        """Check a case-insensitive identity within one taxonomy kind."""
        ...

    async def list_admin_posts(self, query: AdminPostQuery) -> Page[PostSnapshot]:
        """Return one bounded administrator post page."""
        ...

    async def list_public_posts(self, query: PublicPostQuery) -> Page[PostSnapshot]:
        """Return only effective public snapshots."""
        ...

    async def get_post(
        self,
        post_id: UUID,
        *,
        for_update: bool = False,
    ) -> PostSnapshot | None:
        """Load one post aggregate and its required revisions."""
        ...

    async def get_public_post_by_slug(self, slug: str) -> PostSnapshot | None:
        """Resolve an effective public slug without existence leakage."""
        ...

    async def list_ordered_posts(self, *, for_update: bool = False) -> tuple[Post, ...]:
        """Return all nondeleted posts in deterministic admin order."""
        ...

    async def post_reference_summaries(
        self,
        post_ids: tuple[UUID, ...],
    ) -> tuple[PostReferenceSummary, ...]:
        """Resolve post labels and optional public summaries."""
        ...

    async def taxonomy_reference_summaries(
        self,
        taxonomy_ids: tuple[UUID, ...],
    ) -> tuple[TaxonomyReferenceSummary, ...]:
        """Resolve tag/category labels and optional public summaries."""
        ...

    async def list_taxonomies(
        self,
        kind: TaxonomyKind,
        *,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> tuple[Taxonomy, ...]:
        """Return one ordered taxonomy collection."""
        ...

    async def get_taxonomy(
        self,
        taxonomy_id: UUID,
        *,
        for_update: bool = False,
    ) -> Taxonomy | None:
        """Load one taxonomy identity."""
        ...

    async def taxonomy_usage_count(self, taxonomy_id: UUID) -> int:
        """Count nondeleted revisions that retain the taxonomy identity."""
        ...

    async def add_post(self, post: Post, revision: PostRevision) -> None:
        """Stage one aggregate and revision-one draft atomically."""
        ...

    async def save_post_draft(
        self,
        snapshot: PostSnapshot,
        values: PostValues,
        *,
        now: datetime,
    ) -> PostSnapshot:
        """Replace only the current mutable revision values."""
        ...

    async def publish_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> PostSnapshot:
        """Freeze, point, and copy the next mutable draft."""
        ...

    async def reschedule_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> PostSnapshot:
        """Change schedule metadata only."""
        ...

    async def unpublish_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        """Remove public eligibility while retaining history."""
        ...

    async def set_post_visibility(
        self,
        snapshot: PostSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> PostSnapshot:
        """Set visibility independently from publication state."""
        ...

    async def reorder_posts(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Post, ...]:
        """Replace the complete nondeleted admin order."""
        ...

    async def soft_delete_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        """Remove eligibility without destroying revision history."""
        ...

    async def add_taxonomy(self, taxonomy: Taxonomy) -> None:
        """Stage a stable tag or category."""
        ...

    async def update_taxonomy(
        self,
        taxonomy: Taxonomy,
        *,
        name: str,
        slug: str,
        visible: bool,
        now: datetime,
    ) -> Taxonomy:
        """Update mutable taxonomy presentation under concurrency."""
        ...

    async def reorder_taxonomies(
        self,
        kind: TaxonomyKind,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Taxonomy, ...]:
        """Replace one complete nondeleted taxonomy order."""
        ...

    async def soft_delete_taxonomy(self, taxonomy: Taxonomy, *, now: datetime) -> Taxonomy:
        """Soft-delete an unused taxonomy identity."""
        ...


class AuditPort(Protocol):
    """Insert-only controlled blog audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed audit fact."""
        ...


class BlogUnitOfWork(Protocol):
    """One atomic blog application transaction."""

    blog: BlogRepositoryPort
    media: MediaRepositoryPort
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


class BlogUnitOfWorkFactory(Protocol):
    """Create a fresh blog transaction."""

    def __call__(self) -> BlogUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
