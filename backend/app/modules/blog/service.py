"""Blog commands, immutable publication, taxonomy, preview, export, and projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.content_policy import ContentDocument, parse_content
from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.concurrency import require_matching_version
from app.common.domain.pagination import Page, PageRequest
from app.common.domain.temporal import require_utc
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.blog.domain import (
    AdminPostQuery,
    AdminPostView,
    BlogValidationError,
    Post,
    PostReferenceSummary,
    PostRevision,
    PostSnapshot,
    PostValues,
    PublicPost,
    PublicPostQuery,
    PublicPostReference,
    Taxonomy,
    TaxonomyKind,
    TaxonomyReferenceSummary,
    derive_post_lifecycle,
    normalize_blog_slug,
    post_seo,
    require_mutable_post_revision,
    validate_post_values,
    validate_taxonomy,
)
from app.modules.identity.domain import uuid7
from app.modules.media.domain import (
    MediaOwnerType,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.modules.blog.ports import BlogUnitOfWork, BlogUnitOfWorkFactory

_READ_POLICY = AccessPolicy(
    resource="blog",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_WRITE_POLICY = AccessPolicy(
    resource="blog",
    action="write",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_NOT_PUBLISHED = "not_published"
_TAXONOMY_NOT_FOUND = "taxonomy_not_found"
_TAXONOMY_UNAVAILABLE = "taxonomy_unavailable"
_TAXONOMY_KIND_MISMATCH = "taxonomy_kind_mismatch"
_RELATED_POST_NOT_FOUND = "related_post_not_found"
_RELATED_POST_UNAVAILABLE = "related_post_unavailable"
_RELATED_POST_SELF_REFERENCE = "related_post_self_reference"


class BlogNotFoundError(Exception):
    """The requested blog resource does not exist in the authorized scope."""


class BlogSlugConflictError(Exception):
    """A normalized post or taxonomy route identity already exists."""


class BlogRelationError(Exception):
    """A revision relation set is incomplete or unavailable."""

    def __init__(self, code: str) -> None:
        """Retain one stable relation code."""
        super().__init__("blog relation rejected")
        self.code = code


class BlogPublicationError(Exception):
    """A lifecycle action is invalid for the current state."""

    def __init__(self, code: str) -> None:
        """Retain one stable lifecycle code."""
        super().__init__("blog publication action rejected")
        self.code = code


class BlogTaxonomyUsageError(Exception):
    """A taxonomy still belongs to one or more retained revisions."""

    def __init__(self, usage_count: int) -> None:
        """Retain the bounded administrator-visible conflict count."""
        super().__init__("blog taxonomy remains in use")
        self.usage_count = usage_count


class BlogIdempotencyRejectedError(Exception):
    """An idempotent blog command conflicts or remains in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain only the shared admission decision."""
        super().__init__("blog idempotency admission rejected")
        self.decision = decision


class BlogIntegrityError(Exception):
    """Stored source derivations do not match the frozen content policy."""


@dataclass(frozen=True, slots=True)
class PostPreview:
    """Private draft preview with policy provenance and no public cacheability."""

    post_id: UUID
    title: str
    excerpt: str
    author_display: str
    cover_media_id: UUID | None
    content: ContentDocument


@dataclass(frozen=True, slots=True)
class PostSourceExport:
    """Exact normalized draft source download contract."""

    post_id: UUID
    source: str
    checksum: str
    policy_name: str
    policy_version: str
    reading_minutes: int
    filename: str
    content_type: str = "text/markdown; charset=utf-8"


@dataclass(frozen=True, slots=True)
class CreatePostCommand:
    """Idempotent creation of one stable route and revision-one draft."""

    actor: ActorContext
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    slug: str
    values: PostValues
    visible: bool = True


@dataclass(frozen=True, slots=True)
class SavePostDraftCommand:
    """Optimistic complete replacement of the mutable draft."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None
    values: PostValues


@dataclass(frozen=True, slots=True)
class PublishPostCommand:
    """Idempotent publication now or at an absolute UTC instant."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ReschedulePostCommand:
    """Idempotent schedule-metadata-only update."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime


@dataclass(frozen=True, slots=True)
class UnpublishPostCommand:
    """Idempotent removal of public eligibility."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class SetPostVisibilityCommand:
    """Optimistic visibility update independent from publication."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None
    visible: bool


@dataclass(frozen=True, slots=True)
class ReorderPostsCommand:
    """Idempotent complete replacement of administrator post order."""

    actor: ActorContext
    request_id: str
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class DeletePostCommand:
    """Optimistic post soft delete distinct from unpublish."""

    actor: ActorContext
    request_id: str
    post_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class CreateTaxonomyCommand:
    """Idempotent creation of one stable tag or category."""

    actor: ActorContext
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    kind: TaxonomyKind
    name: str
    slug: str
    visible: bool = True


@dataclass(frozen=True, slots=True)
class UpdateTaxonomyCommand:
    """Optimistic update of taxonomy presentation and visibility."""

    actor: ActorContext
    request_id: str
    taxonomy_id: UUID
    if_match: str | None
    name: str
    slug: str
    visible: bool


@dataclass(frozen=True, slots=True)
class ReorderTaxonomiesCommand:
    """Idempotent complete replacement of one taxonomy order."""

    actor: ActorContext
    request_id: str
    kind: TaxonomyKind
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class DeleteTaxonomyCommand:
    """Optimistic deletion of one unused taxonomy."""

    actor: ActorContext
    request_id: str
    taxonomy_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class _IdempotencyFact:
    actor: ActorContext
    route: str
    key: str
    payload: bytes
    now: datetime


@dataclass(frozen=True, slots=True)
class _AuditFact:
    actor: ActorContext
    request_id: str
    event_type: str
    resource_type: str
    resource_id: UUID
    version: int
    fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CompletionFact:
    resource_type: str
    resource_id: UUID
    resource_version: int
    updated_at: datetime
    status: int
    code: str


class BlogService:
    """Authorize and transact the complete M7 blog capability."""

    def __init__(
        self,
        uow_factory: BlogUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind deterministic transaction, time, and ID seams."""
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def list_admin_posts(
        self,
        actor: ActorContext,
        query: AdminPostQuery,
    ) -> Page[AdminPostView]:
        """Return one allow-listed administrator post page."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            page = await uow.blog.list_admin_posts(query)
            now = await uow.blog.database_now()
        return Page(
            items=tuple(
                AdminPostView(item, derive_post_lifecycle(item, database_now=now))
                for item in page.items
            ),
            metadata=page.metadata,
        )

    async def get_admin_post(self, actor: ActorContext, post_id: UUID) -> AdminPostView:
        """Return one complete administrator post snapshot."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get_post(uow, post_id)
            now = await uow.blog.database_now()
        return AdminPostView(snapshot, derive_post_lifecycle(snapshot, database_now=now))

    async def admin_view(self, snapshot: PostSnapshot) -> AdminPostView:
        """Pair a mutation result with authoritative database-time lifecycle."""
        async with self._uow_factory() as uow:
            now = await uow.blog.database_now()
        return AdminPostView(snapshot, derive_post_lifecycle(snapshot, database_now=now))

    async def preview(self, actor: ActorContext, post_id: UUID) -> PostPreview:
        """Render only the current draft through the private policy boundary."""
        view = await self.get_admin_post(actor, post_id)
        values = view.snapshot.draft.values
        content = self._verified_content(values)
        return PostPreview(
            post_id,
            values.title,
            values.excerpt,
            values.author_display,
            values.cover_media_id,
            content,
        )

    async def export_source(self, actor: ActorContext, post_id: UUID) -> PostSourceExport:
        """Export exact canonical draft source without lifecycle or creator metadata."""
        view = await self.get_admin_post(actor, post_id)
        values = view.snapshot.draft.values
        content = self._verified_content(values)
        return PostSourceExport(
            post_id=post_id,
            source=content.source,
            checksum=content.rendered.source_checksum,
            policy_name=content.rendered.policy_name,
            policy_version=content.rendered.policy_version,
            reading_minutes=content.reading_minutes,
            filename=f"{view.snapshot.post.slug}.md",
        )

    async def create_post(self, command: CreatePostCommand) -> PostSnapshot:
        """Create an immutable post route identity and mutable draft."""
        require_authorized(command.actor, _WRITE_POLICY)
        slug = normalize_blog_slug(command.slug)
        values = validate_post_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/posts",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_post(uow, decision)
            if replay is not None:
                return replay
            if await uow.blog.post_slug_exists(slug):
                raise BlogSlugConflictError
            ordered = await uow.blog.list_ordered_posts(for_update=True)
            post_id = self._id_factory()
            revision_id = self._id_factory()
            values = validate_post_values(values, post_id=post_id)
            await self._validate_relations(uow, post_id, values)
            actor_id = self._actor_id(command.actor)
            post = Post(
                id=post_id,
                slug=slug,
                visible=command.visible,
                position=len(ordered),
                draft_revision_id=revision_id,
                published_revision_id=None,
                publish_at=None,
                unpublished_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            revision = PostRevision(
                id=revision_id,
                post_id=post_id,
                revision_number=1,
                based_on_revision_id=None,
                values=values,
                frozen=False,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            await self._replace_revision_media(uow, revision, now=now, public=False)
            await uow.blog.add_post(post, revision)
            snapshot = PostSnapshot(post, revision, None)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_created",
                    "blog_post",
                    post.id,
                    post.version,
                    ("content", "relations", "visible"),
                ),
            )
            await self._complete(
                uow,
                decision,
                _CompletionFact(
                    "blog_post",
                    post.id,
                    post.version,
                    post.updated_at,
                    201,
                    "blog.post_created",
                ),
            )
            await uow.commit()
            return snapshot

    async def save_post_draft(self, command: SavePostDraftCommand) -> PostSnapshot:
        """Replace only the mutable draft under aggregate concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_post_values(command.values, post_id=command.post_id)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            require_mutable_post_revision(snapshot.draft)
            await self._validate_relations(uow, command.post_id, values)
            proposed = PostRevision(
                id=snapshot.draft.id,
                post_id=snapshot.draft.post_id,
                revision_number=snapshot.draft.revision_number,
                based_on_revision_id=snapshot.draft.based_on_revision_id,
                values=values,
                frozen=False,
                created_by=snapshot.draft.created_by,
                created_at=snapshot.draft.created_at,
                updated_at=now,
            )
            await self._replace_revision_media(uow, proposed, now=now, public=False)
            updated = await uow.blog.save_post_draft(snapshot, values, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.draft_saved",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    ("content", "relations", "seo"),
                ),
            )
            await uow.commit()
            return updated

    async def publish_post(self, command: PublishPostCommand) -> PostSnapshot:
        """Freeze the draft, point publication, and create one mutable copy."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.blog.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/posts/{post_id}/actions/publish",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_post(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            require_mutable_post_revision(snapshot.draft)
            values = validate_post_values(snapshot.draft.values, post_id=command.post_id)
            await self._validate_relations(uow, command.post_id, values)
            publish_at = now if command.publish_at is None else require_utc(command.publish_at)
            updated = await uow.blog.publish_post(
                snapshot,
                publish_at=publish_at,
                next_revision_id=self._id_factory(),
                actor_id=self._actor_id(command.actor),
                now=now,
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            if updated.published is None:
                raise BlogPublicationError(_NOT_PUBLISHED)
            await self._replace_revision_media(uow, updated.published, now=now, public=True)
            await self._replace_revision_media(uow, updated.draft, now=now, public=False)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_published",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    ("published_revision", "publish_at"),
                ),
            )
            await self._complete_post(uow, decision, updated, "blog.post_published")
            await uow.commit()
            return updated

    async def reschedule_post(self, command: ReschedulePostCommand) -> PostSnapshot:
        """Change only publication schedule metadata."""
        require_authorized(command.actor, _WRITE_POLICY)
        publish_at = require_utc(command.publish_at)
        async with self._uow_factory() as uow:
            now = await uow.blog.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/posts/{post_id}/actions/reschedule",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_post(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            if snapshot.post.published_revision_id is None:
                raise BlogPublicationError(_NOT_PUBLISHED)
            updated = await uow.blog.reschedule_post(snapshot, publish_at=publish_at, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_rescheduled",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    ("publish_at",),
                ),
            )
            await self._complete_post(uow, decision, updated, "blog.post_rescheduled")
            await uow.commit()
            return updated

    async def unpublish_post(self, command: UnpublishPostCommand) -> PostSnapshot:
        """Clear public eligibility without deleting revision history."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.blog.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/posts/{post_id}/actions/unpublish",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_post(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            if snapshot.post.published_revision_id is None:
                raise BlogPublicationError(_NOT_PUBLISHED)
            updated = await uow.blog.unpublish_post(snapshot, now=now)
            if snapshot.published is not None:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_unpublished",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    ("published_revision",),
                ),
            )
            await self._complete_post(uow, decision, updated, "blog.post_unpublished")
            await uow.commit()
            return updated

    async def set_post_visibility(self, command: SetPostVisibilityCommand) -> PostSnapshot:
        """Set visibility independently from publication state."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            updated = await uow.blog.set_post_visibility(
                snapshot,
                visible=command.visible,
                now=now,
            )
            if updated.published is not None:
                await self._replace_revision_media(
                    uow,
                    updated.published,
                    now=now,
                    public=command.visible,
                )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_visibility_changed",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    ("visible",),
                ),
            )
            await uow.commit()
            return updated

    async def reorder_posts(self, command: ReorderPostsCommand) -> tuple[Post, ...]:
        """Replace complete post order under one lock and idempotency record."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/posts/actions/reorder",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            current = await uow.blog.list_ordered_posts(for_update=True)
            if not current:
                raise BlogNotFoundError
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return current
            require_matching_version(command.if_match, current_version=current[0].version)
            self._require_complete_order(command.ordered_ids, tuple(item.id for item in current))
            updated = await uow.blog.reorder_posts(command.ordered_ids, now=now)
            first = updated[0]
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.posts_reordered",
                    "blog_post",
                    first.id,
                    first.version,
                    ("position",),
                ),
            )
            await self._complete(
                uow,
                decision,
                _CompletionFact(
                    "blog_post",
                    first.id,
                    first.version,
                    first.updated_at,
                    200,
                    "blog.posts_reordered",
                ),
            )
            await uow.commit()
            return updated

    async def delete_post(self, command: DeletePostCommand) -> PostSnapshot:
        """Soft-delete a post as an explicit action separate from unpublish."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get_post(uow, command.post_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.post.version)
            updated = await uow.blog.soft_delete_post(snapshot, now=now)
            await self._replace_revision_media(
                uow,
                snapshot.draft,
                now=now,
                public=False,
                active=False,
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.post_deleted",
                    "blog_post",
                    updated.post.id,
                    updated.post.version,
                    (),
                ),
            )
            await uow.commit()
            return updated

    async def list_taxonomies(
        self,
        actor: ActorContext,
        kind: TaxonomyKind,
    ) -> tuple[Taxonomy, ...]:
        """Return ordered nondeleted tags or categories to an administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return await uow.blog.list_taxonomies(kind)

    async def create_taxonomy(self, command: CreateTaxonomyCommand) -> Taxonomy:
        """Create one stable taxonomy identity in deterministic order."""
        require_authorized(command.actor, _WRITE_POLICY)
        name, slug = validate_taxonomy(kind=command.kind, name=command.name, slug=command.slug)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/taxonomies",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return await self._replayed_taxonomy(uow, decision)
            if await uow.blog.taxonomy_slug_exists(command.kind, slug):
                raise BlogSlugConflictError
            current = await uow.blog.list_taxonomies(command.kind, for_update=True)
            taxonomy = Taxonomy(
                id=self._id_factory(),
                kind=command.kind,
                name=name,
                slug=slug,
                position=len(current),
                visible=command.visible,
                created_at=now,
                updated_at=now,
                version=1,
            )
            await uow.blog.add_taxonomy(taxonomy)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.taxonomy_created",
                    "blog_taxonomy",
                    taxonomy.id,
                    taxonomy.version,
                    ("kind", "name", "slug", "visible"),
                ),
            )
            await self._complete(
                uow,
                decision,
                _CompletionFact(
                    "blog_taxonomy",
                    taxonomy.id,
                    taxonomy.version,
                    taxonomy.updated_at,
                    201,
                    "blog.taxonomy_created",
                ),
            )
            await uow.commit()
            return taxonomy

    async def update_taxonomy(self, command: UpdateTaxonomyCommand) -> Taxonomy:
        """Update a taxonomy label/slug/visibility under optimistic concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            taxonomy = await self._get_taxonomy(uow, command.taxonomy_id, for_update=True)
            require_matching_version(command.if_match, current_version=taxonomy.version)
            name, slug = validate_taxonomy(
                kind=taxonomy.kind,
                name=command.name,
                slug=command.slug,
            )
            if await uow.blog.taxonomy_slug_exists(
                taxonomy.kind,
                slug,
                excluding_id=taxonomy.id,
            ):
                raise BlogSlugConflictError
            updated = await uow.blog.update_taxonomy(
                taxonomy,
                name=name,
                slug=slug,
                visible=command.visible,
                now=self._clock(),
            )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.taxonomy_updated",
                    "blog_taxonomy",
                    updated.id,
                    updated.version,
                    ("name", "slug", "visible"),
                ),
            )
            await uow.commit()
            return updated

    async def reorder_taxonomies(
        self,
        command: ReorderTaxonomiesCommand,
    ) -> tuple[Taxonomy, ...]:
        """Replace one complete taxonomy order with retry safety."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/blog/taxonomies/actions/reorder",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            current = await uow.blog.list_taxonomies(command.kind, for_update=True)
            if not current:
                raise BlogNotFoundError
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return current
            require_matching_version(command.if_match, current_version=current[0].version)
            self._require_complete_order(command.ordered_ids, tuple(item.id for item in current))
            updated = await uow.blog.reorder_taxonomies(
                command.kind,
                command.ordered_ids,
                now=now,
            )
            first = updated[0]
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.taxonomies_reordered",
                    "blog_taxonomy",
                    first.id,
                    first.version,
                    ("position",),
                ),
            )
            await self._complete(
                uow,
                decision,
                _CompletionFact(
                    "blog_taxonomy",
                    first.id,
                    first.version,
                    first.updated_at,
                    200,
                    "blog.taxonomies_reordered",
                ),
            )
            await uow.commit()
            return updated

    async def delete_taxonomy(self, command: DeleteTaxonomyCommand) -> Taxonomy:
        """Soft-delete only a taxonomy unused by retained revisions."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            taxonomy = await self._get_taxonomy(uow, command.taxonomy_id, for_update=True)
            require_matching_version(command.if_match, current_version=taxonomy.version)
            usage_count = await uow.blog.taxonomy_usage_count(taxonomy.id)
            if usage_count:
                raise BlogTaxonomyUsageError(usage_count)
            updated = await uow.blog.soft_delete_taxonomy(taxonomy, now=self._clock())
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "blog.taxonomy_deleted",
                    "blog_taxonomy",
                    updated.id,
                    updated.version,
                    (),
                ),
            )
            await uow.commit()
            return updated

    async def public_list(self, query: PublicPostQuery) -> Page[PublicPost]:
        """Project one public page with public-only facets and related summaries."""
        async with self._uow_factory() as uow:
            page = await uow.blog.list_public_posts(query)
            taxonomy_ids = self._relation_ids(page.items, "tag_ids") + self._relation_ids(
                page.items,
                "category_ids",
            )
            taxonomies = await uow.blog.taxonomy_reference_summaries(
                tuple(dict.fromkeys(taxonomy_ids))
            )
            related = await uow.blog.post_reference_summaries(
                self._relation_ids(page.items, "related_post_ids")
            )
        return Page(
            items=tuple(self._public(item, taxonomies, related) for item in page.items),
            metadata=page.metadata,
        )

    async def public_detail(self, slug: str) -> PublicPost:
        """Resolve one effective article or indistinguishable not-found."""
        normalized = normalize_blog_slug(slug)
        if normalized != slug:
            raise BlogNotFoundError
        async with self._uow_factory() as uow:
            snapshot = await uow.blog.get_public_post_by_slug(slug)
            if snapshot is None:
                raise BlogNotFoundError
            revision = self._published(snapshot)
            taxonomy_ids = revision.values.tag_ids + revision.values.category_ids
            taxonomies = await uow.blog.taxonomy_reference_summaries(
                tuple(dict.fromkeys(taxonomy_ids))
            )
            related = await uow.blog.post_reference_summaries(revision.values.related_post_ids)
        return self._public(snapshot, taxonomies, related)

    async def reference_summaries(
        self,
        post_ids: tuple[UUID, ...],
    ) -> tuple[PostReferenceSummary, ...]:
        """Resolve every stable post reference or fail the complete set."""
        if len(post_ids) != len(set(post_ids)):
            raise BlogNotFoundError
        async with self._uow_factory() as uow:
            summaries = await uow.blog.post_reference_summaries(post_ids)
        if {item.id for item in summaries} != set(post_ids):
            raise BlogNotFoundError
        return summaries

    async def _validate_relations(
        self,
        uow: BlogUnitOfWork,
        post_id: UUID,
        values: PostValues,
    ) -> None:
        taxonomy_ids = values.tag_ids + values.category_ids
        summaries = await uow.blog.taxonomy_reference_summaries(taxonomy_ids)
        summary_map = {item.id: item for item in summaries}
        if set(summary_map) != set(taxonomy_ids):
            raise BlogRelationError(_TAXONOMY_NOT_FOUND)
        if any(item.deleted for item in summaries):
            raise BlogRelationError(_TAXONOMY_UNAVAILABLE)
        if any(summary_map[item].kind is not TaxonomyKind.TAG for item in values.tag_ids):
            raise BlogRelationError(_TAXONOMY_KIND_MISMATCH)
        if any(summary_map[item].kind is not TaxonomyKind.CATEGORY for item in values.category_ids):
            raise BlogRelationError(_TAXONOMY_KIND_MISMATCH)
        related = await uow.blog.post_reference_summaries(values.related_post_ids)
        if {item.id for item in related} != set(values.related_post_ids):
            raise BlogRelationError(_RELATED_POST_NOT_FOUND)
        if any(item.deleted for item in related):
            raise BlogRelationError(_RELATED_POST_UNAVAILABLE)
        if post_id in values.related_post_ids:
            raise BlogRelationError(_RELATED_POST_SELF_REFERENCE)

    @staticmethod
    def _relation_ids(snapshots: tuple[PostSnapshot, ...], field: str) -> tuple[UUID, ...]:
        return tuple(
            dict.fromkeys(
                relation_id
                for snapshot in snapshots
                for relation_id in getattr(BlogService._published(snapshot).values, field)
            )
        )

    @staticmethod
    def _verified_content(values: PostValues) -> ContentDocument:
        content = parse_content(values.source)
        if (
            content.reading_minutes != values.reading_minutes
            or content.rendered.source_checksum != values.content_checksum
            or content.rendered.policy_name != values.content_policy_name
            or content.rendered.policy_version != values.content_policy_version
        ):
            raise BlogIntegrityError
        return content

    @classmethod
    def _public(
        cls,
        snapshot: PostSnapshot,
        taxonomies: tuple[TaxonomyReferenceSummary, ...],
        related: tuple[PostReferenceSummary, ...],
    ) -> PublicPost:
        revision = cls._published(snapshot)
        values = revision.values
        if snapshot.post.publish_at is None:
            raise BlogNotFoundError
        taxonomy_map = {item.id: item.public for item in taxonomies if item.public is not None}
        related_map = {item.id: item.public for item in related if item.public is not None}
        seo_title, seo_description = post_seo(values)
        return PublicPost(
            id=snapshot.post.id,
            slug=snapshot.post.slug,
            title=values.title,
            excerpt=values.excerpt,
            author_display=values.author_display,
            rendered=cls._verified_content(values).rendered,
            reading_minutes=values.reading_minutes,
            published_at=snapshot.post.publish_at,
            seo_title=seo_title,
            seo_description=seo_description,
            canonical_url=values.canonical_url,
            cover_media_id=values.cover_media_id,
            tags=tuple(
                taxonomy_map[item]
                for item in values.tag_ids
                if item in taxonomy_map and taxonomy_map[item] is not None
            ),
            categories=tuple(
                taxonomy_map[item]
                for item in values.category_ids
                if item in taxonomy_map and taxonomy_map[item] is not None
            ),
            related_posts=tuple(
                related_map[item]
                for item in values.related_post_ids
                if item in related_map and related_map[item] is not None
            ),
        )

    @staticmethod
    async def _replace_revision_media(
        uow: BlogUnitOfWork,
        revision: PostRevision,
        *,
        now: datetime,
        public: bool,
        active: bool = True,
    ) -> None:
        values = revision.values
        usages = (
            (
                MediaUse(
                    asset_id=values.cover_media_id,
                    owner_type=MediaOwnerType.BLOG_POST_REVISION,
                    owner_id=revision.id,
                    role=MediaUsageRole.BLOG_COVER,
                    position=0,
                    purpose=MediaUsePurpose.MEANINGFUL,
                    alt_text=f"{values.title} article cover",
                    caption=None,
                    active=active,
                    public=public,
                ),
            )
            if values.cover_media_id is not None
            else ()
        )
        await uow.media.replace_owner_usages(
            owner_type=MediaOwnerType.BLOG_POST_REVISION.value,
            owner_id=revision.id,
            usages=usages,
            now=now,
        )

    @staticmethod
    def _published(snapshot: PostSnapshot) -> PostRevision:
        revision = snapshot.published
        if revision is None or revision.id != snapshot.post.published_revision_id:
            raise BlogNotFoundError
        return revision

    @staticmethod
    async def _get_post(
        uow: BlogUnitOfWork,
        post_id: UUID,
        *,
        for_update: bool = False,
    ) -> PostSnapshot:
        snapshot = await uow.blog.get_post(post_id, for_update=for_update)
        if snapshot is None:
            raise BlogNotFoundError
        return snapshot

    @staticmethod
    async def _get_taxonomy(
        uow: BlogUnitOfWork,
        taxonomy_id: UUID,
        *,
        for_update: bool = False,
    ) -> Taxonomy:
        taxonomy = await uow.blog.get_taxonomy(taxonomy_id, for_update=for_update)
        if taxonomy is None or taxonomy.deleted_at is not None:
            raise BlogNotFoundError
        return taxonomy

    @staticmethod
    def _require_complete_order(proposed: tuple[UUID, ...], current: tuple[UUID, ...]) -> None:
        if len(proposed) != len(set(proposed)):
            raise BlogValidationError(path="items", code="duplicate_id")
        if set(proposed) != set(current):
            raise BlogValidationError(path="items", code="incomplete_order")

    @staticmethod
    def _actor_id(actor: ActorContext) -> UUID:
        if actor.actor_id is None:
            raise BlogNotFoundError
        return actor.actor_id

    @staticmethod
    async def _acquire(
        uow: BlogUnitOfWork,
        fact: _IdempotencyFact,
    ) -> IdempotencyDecision:
        decision = await uow.idempotency.acquire(
            IdempotencyRequest.create(
                actor=fact.actor,
                route=fact.route,
                key=fact.key,
                canonical_payload=fact.payload,
                requested_at=fact.now,
            )
        )
        if decision.decision not in {
            IdempotencyDecisionType.ACQUIRED,
            IdempotencyDecisionType.REPLAY,
        }:
            raise BlogIdempotencyRejectedError(decision)
        return decision

    async def _replayed_post(
        self,
        uow: BlogUnitOfWork,
        decision: IdempotencyDecision,
    ) -> PostSnapshot | None:
        if decision.decision is not IdempotencyDecisionType.REPLAY:
            return None
        if decision.outcome is None or decision.outcome.resource_id is None:
            raise BlogNotFoundError
        return await self._get_post(uow, decision.outcome.resource_id)

    async def _replayed_taxonomy(
        self,
        uow: BlogUnitOfWork,
        decision: IdempotencyDecision,
    ) -> Taxonomy:
        if decision.outcome is None or decision.outcome.resource_id is None:
            raise BlogNotFoundError
        return await self._get_taxonomy(uow, decision.outcome.resource_id)

    @staticmethod
    async def _complete_post(
        uow: BlogUnitOfWork,
        decision: IdempotencyDecision,
        snapshot: PostSnapshot,
        code: str,
    ) -> None:
        await BlogService._complete(
            uow,
            decision,
            _CompletionFact(
                "blog_post",
                snapshot.post.id,
                snapshot.post.version,
                snapshot.post.updated_at,
                200,
                code,
            ),
        )

    @staticmethod
    async def _complete(
        uow: BlogUnitOfWork,
        decision: IdempotencyDecision,
        fact: _CompletionFact,
    ) -> None:
        if decision.record_id is None:
            raise BlogNotFoundError
        await uow.idempotency.complete(
            decision.record_id,
            IdempotencyOutcome(
                response_status=fact.status,
                result_code=fact.code,
                resource_type=fact.resource_type,
                resource_id=fact.resource_id,
                resource_version=fact.resource_version,
            ),
            completed_at=fact.updated_at,
        )

    def _audit(self, uow: BlogUnitOfWork, fact: _AuditFact) -> None:
        uow.audit.append(
            AuditEntry(
                id=uuid7(),
                event_type=fact.event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=fact.actor.actor_id,
                actor_label_snapshot=None,
                resource_type=fact.resource_type,
                resource_id=fact.resource_id,
                request_id=fact.request_id,
                occurred_at=self._clock(),
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata={"version": fact.version, "fields": ",".join(fact.fields)},
                schema_version=1,
            )
        )


class BlogReferenceFacade:
    """Stable provider boundary for configurable pages and later modules."""

    def __init__(self, service: BlogService) -> None:
        """Bind to the blog application service."""
        self._service = service

    async def resolve(
        self,
        post_ids: tuple[UUID, ...],
    ) -> tuple[PostReferenceSummary, ...]:
        """Resolve all requested stable post IDs or fail the complete set."""
        return await self._service.reference_summaries(post_ids)

    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[PostReferenceSummary, ...]:
        """Return bounded latest effective posts for page blocks."""
        del featured
        page = await self._service.public_list(PublicPostQuery(PageRequest(page_size=maximum)))
        return tuple(
            PostReferenceSummary(
                id=item.id,
                slug=item.slug,
                title=item.title,
                visible=True,
                deleted=False,
                public=PublicPostReference(item.id, item.slug, item.title, item.excerpt),
            )
            for item in page.items
        )
