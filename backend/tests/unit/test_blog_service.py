"""M7 blog application tests over deterministic in-memory ports."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID

import pytest

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import Page, PageRequest, page_metadata
from app.modules.blog.domain import (
    AdminPostQuery,
    Post,
    PostReferenceSummary,
    PostRevision,
    PostSnapshot,
    PostValues,
    PublicPostQuery,
    PublicPostReference,
    PublicTaxonomyReference,
    Taxonomy,
    TaxonomyKind,
    TaxonomyReferenceSummary,
    validate_post_values,
)
from app.modules.blog.service import (
    BlogNotFoundError,
    BlogPublicationError,
    BlogRelationError,
    BlogService,
    BlogSlugConflictError,
    BlogTaxonomyUsageError,
    CreatePostCommand,
    CreateTaxonomyCommand,
    DeletePostCommand,
    DeleteTaxonomyCommand,
    PublishPostCommand,
    ReorderPostsCommand,
    ReorderTaxonomiesCommand,
    ReschedulePostCommand,
    SavePostDraftCommand,
    SetPostVisibilityCommand,
    UnpublishPostCommand,
    UpdateTaxonomyCommand,
)

if TYPE_CHECKING:
    from types import TracebackType

    from app.modules.audit.domain import AuditEntry
    from app.modules.blog.ports import BlogUnitOfWorkFactory

NOW = datetime(2026, 8, 4, 11, tzinfo=UTC)
ACTOR_ID = UUID("0198a13d-3000-7000-8000-000000000001")
POST_ID = UUID("0198a13d-3000-7000-8000-000000000002")
DRAFT_ID = UUID("0198a13d-3000-7000-8000-000000000003")
NEXT_DRAFT_ID = UUID("0198a13d-3000-7000-8000-000000000004")
RELATED_ID = UUID("0198a13d-3000-7000-8000-000000000005")
RELATED_DRAFT_ID = UUID("0198a13d-3000-7000-8000-000000000006")
TAG_ID = UUID("0198a13d-3000-7000-8000-000000000007")
CATEGORY_ID = UUID("0198a13d-3000-7000-8000-000000000008")
NEW_TAXONOMY_ID = UUID("0198a13d-3000-7000-8000-000000000009")
IDEMPOTENCY_ID = UUID("0198a13d-3000-7000-8000-000000000010")
EXTRA_TAG_ID = UUID("0198a13d-3000-7000-8000-000000000011")


def _values(
    *,
    source: str = "## Reliable publication\n\nA **safe**, revision-owned article.",
    related: tuple[UUID, ...] = (),
) -> PostValues:
    return PostValues(
        title="Reliable publication",
        excerpt="A practical guide to immutable public revisions.",
        source=source,
        author_display="Site owner",
        reading_minutes=0,
        content_checksum="",
        content_policy_name="",
        content_policy_version="",
        tag_ids=(TAG_ID,),
        category_ids=(CATEGORY_ID,),
        related_post_ids=related,
        seo_title=None,
        seo_description=None,
        canonical_url=None,
    )


class _FakeBlogRepository:
    def __init__(self) -> None:
        self.now = NOW
        self.posts: dict[UUID, PostSnapshot] = {}
        self.taxonomies: dict[UUID, Taxonomy] = {
            TAG_ID: Taxonomy(
                id=TAG_ID,
                kind=TaxonomyKind.TAG,
                name="Engineering",
                slug="engineering",
                position=0,
                visible=True,
                created_at=NOW,
                updated_at=NOW,
                version=1,
            ),
            CATEGORY_ID: Taxonomy(
                id=CATEGORY_ID,
                kind=TaxonomyKind.CATEGORY,
                name="Delivery",
                slug="delivery",
                position=0,
                visible=True,
                created_at=NOW,
                updated_at=NOW,
                version=1,
            ),
        }
        self.publish_calls = 0

    async def database_now(self) -> datetime:
        return self.now

    async def post_slug_exists(self, slug: str) -> bool:
        return any(item.post.slug.casefold() == slug.casefold() for item in self.posts.values())

    async def taxonomy_slug_exists(
        self,
        kind: TaxonomyKind,
        slug: str,
        *,
        excluding_id: UUID | None = None,
    ) -> bool:
        return any(
            item.kind is kind
            and item.slug.casefold() == slug.casefold()
            and item.id != excluding_id
            for item in self.taxonomies.values()
        )

    async def list_admin_posts(self, query: AdminPostQuery) -> Page[PostSnapshot]:
        rows = tuple(self.posts.values())
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def list_public_posts(self, query: PublicPostQuery) -> Page[PostSnapshot]:
        rows = tuple(
            item
            for item in self.posts.values()
            if item.post.visible
            and item.post.deleted_at is None
            and item.post.publish_at is not None
            and item.post.publish_at <= self.now
            and item.published is not None
            and (
                query.tag_slug is None
                or any(
                    taxonomy.slug == query.tag_slug
                    for taxonomy in self.taxonomies.values()
                    if taxonomy.id in item.published.values.tag_ids
                )
            )
        )
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def get_post(
        self,
        post_id: UUID,
        *,
        for_update: bool = False,
    ) -> PostSnapshot | None:
        del for_update
        return self.posts.get(post_id)

    async def get_public_post_by_slug(self, slug: str) -> PostSnapshot | None:
        page = await self.list_public_posts(PublicPostQuery(PageRequest(page_size=100)))
        return next((item for item in page.items if item.post.slug == slug), None)

    async def list_ordered_posts(self, *, for_update: bool = False) -> tuple[Post, ...]:
        del for_update
        return tuple(
            sorted(
                (item.post for item in self.posts.values() if item.post.deleted_at is None),
                key=lambda item: (item.position, item.id),
            )
        )

    async def post_reference_summaries(
        self,
        post_ids: tuple[UUID, ...],
    ) -> tuple[PostReferenceSummary, ...]:
        result: list[PostReferenceSummary] = []
        for identifier in post_ids:
            snapshot = self.posts.get(identifier)
            if snapshot is None:
                continue
            effective = (
                snapshot.post.visible
                and snapshot.post.deleted_at is None
                and snapshot.post.publish_at is not None
                and snapshot.post.publish_at <= self.now
                and snapshot.published is not None
            )
            result.append(
                PostReferenceSummary(
                    identifier,
                    snapshot.post.slug,
                    snapshot.draft.values.title,
                    snapshot.post.visible,
                    snapshot.post.deleted_at is not None,
                    (
                        PublicPostReference(
                            identifier,
                            snapshot.post.slug,
                            snapshot.published.values.title,
                            snapshot.published.values.excerpt,
                        )
                        if effective and snapshot.published is not None
                        else None
                    ),
                )
            )
        return tuple(result)

    async def taxonomy_reference_summaries(
        self,
        taxonomy_ids: tuple[UUID, ...],
    ) -> tuple[TaxonomyReferenceSummary, ...]:
        result: list[TaxonomyReferenceSummary] = []
        for identifier in taxonomy_ids:
            item = self.taxonomies.get(identifier)
            if item is None:
                continue
            result.append(
                TaxonomyReferenceSummary(
                    item.id,
                    item.kind,
                    item.name,
                    item.slug,
                    item.visible,
                    item.deleted_at is not None,
                    (
                        PublicTaxonomyReference(item.id, item.name, item.slug)
                        if item.visible and item.deleted_at is None
                        else None
                    ),
                )
            )
        return tuple(result)

    async def list_taxonomies(
        self,
        kind: TaxonomyKind,
        *,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> tuple[Taxonomy, ...]:
        del for_update
        return tuple(
            sorted(
                (
                    item
                    for item in self.taxonomies.values()
                    if item.kind is kind and (include_deleted or item.deleted_at is None)
                ),
                key=lambda item: (item.position, item.id),
            )
        )

    async def get_taxonomy(
        self,
        taxonomy_id: UUID,
        *,
        for_update: bool = False,
    ) -> Taxonomy | None:
        del for_update
        return self.taxonomies.get(taxonomy_id)

    async def taxonomy_usage_count(self, taxonomy_id: UUID) -> int:
        return sum(
            taxonomy_id in snapshot.draft.values.tag_ids + snapshot.draft.values.category_ids
            or (
                snapshot.published is not None
                and taxonomy_id
                in snapshot.published.values.tag_ids + snapshot.published.values.category_ids
            )
            for snapshot in self.posts.values()
        )

    async def add_post(self, post: Post, revision: PostRevision) -> None:
        self.posts[post.id] = PostSnapshot(post, revision, None)

    async def save_post_draft(
        self,
        snapshot: PostSnapshot,
        values: PostValues,
        *,
        now: datetime,
    ) -> PostSnapshot:
        draft = replace(
            snapshot.draft,
            values=values,
            based_on_revision_id=(
                snapshot.published.id
                if snapshot.published is not None and values == snapshot.published.values
                else None
            ),
            updated_at=now,
        )
        post = replace(snapshot.post, updated_at=now, version=snapshot.post.version + 1)
        updated = PostSnapshot(post, draft, snapshot.published)
        self.posts[post.id] = updated
        return updated

    async def publish_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> PostSnapshot:
        self.publish_calls += 1
        frozen = replace(snapshot.draft, frozen=True, updated_at=now)
        draft = PostRevision(
            id=next_revision_id,
            post_id=snapshot.post.id,
            revision_number=frozen.revision_number + 1,
            based_on_revision_id=frozen.id,
            values=frozen.values,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        post = replace(
            snapshot.post,
            draft_revision_id=draft.id,
            published_revision_id=frozen.id,
            publish_at=publish_at,
            unpublished_at=None,
            updated_at=now,
            version=snapshot.post.version + 1,
        )
        updated = PostSnapshot(post, draft, frozen)
        self.posts[post.id] = updated
        return updated

    async def reschedule_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> PostSnapshot:
        post = replace(
            snapshot.post,
            publish_at=publish_at,
            updated_at=now,
            version=snapshot.post.version + 1,
        )
        updated = replace(snapshot, post=post)
        self.posts[post.id] = updated
        return updated

    async def unpublish_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        post = replace(
            snapshot.post,
            published_revision_id=None,
            publish_at=None,
            unpublished_at=now,
            updated_at=now,
            version=snapshot.post.version + 1,
        )
        updated = PostSnapshot(post, snapshot.draft, None)
        self.posts[post.id] = updated
        return updated

    async def set_post_visibility(
        self,
        snapshot: PostSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> PostSnapshot:
        post = replace(
            snapshot.post,
            visible=visible,
            updated_at=now,
            version=snapshot.post.version + 1,
        )
        updated = replace(snapshot, post=post)
        self.posts[post.id] = updated
        return updated

    async def reorder_posts(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Post, ...]:
        result: list[Post] = []
        for position, identifier in enumerate(ordered_ids):
            snapshot = self.posts[identifier]
            post = replace(
                snapshot.post,
                position=position,
                updated_at=now,
                version=snapshot.post.version + 1,
            )
            self.posts[identifier] = replace(snapshot, post=post)
            result.append(post)
        return tuple(result)

    async def soft_delete_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        post = replace(
            snapshot.post,
            published_revision_id=None,
            publish_at=None,
            deleted_at=now,
            updated_at=now,
            version=snapshot.post.version + 1,
        )
        updated = PostSnapshot(post, snapshot.draft, None)
        self.posts[post.id] = updated
        return updated

    async def add_taxonomy(self, taxonomy: Taxonomy) -> None:
        self.taxonomies[taxonomy.id] = taxonomy

    async def update_taxonomy(
        self,
        taxonomy: Taxonomy,
        *,
        name: str,
        slug: str,
        visible: bool,
        now: datetime,
    ) -> Taxonomy:
        updated = replace(
            taxonomy,
            name=name,
            slug=slug,
            visible=visible,
            updated_at=now,
            version=taxonomy.version + 1,
        )
        self.taxonomies[updated.id] = updated
        return updated

    async def reorder_taxonomies(
        self,
        kind: TaxonomyKind,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Taxonomy, ...]:
        del kind
        result: list[Taxonomy] = []
        for position, identifier in enumerate(ordered_ids):
            item = self.taxonomies[identifier]
            updated = replace(
                item,
                position=position,
                updated_at=now,
                version=item.version + 1,
            )
            self.taxonomies[identifier] = updated
            result.append(updated)
        return tuple(result)

    async def soft_delete_taxonomy(self, taxonomy: Taxonomy, *, now: datetime) -> Taxonomy:
        updated = replace(
            taxonomy,
            deleted_at=now,
            visible=False,
            updated_at=now,
            version=taxonomy.version + 1,
        )
        self.taxonomies[updated.id] = updated
        return updated


class _FakeIdempotency:
    def __init__(self) -> None:
        self.requests: dict[tuple[bytes, str, bytes], tuple[bytes, UUID]] = {}
        self.outcomes: dict[UUID, IdempotencyOutcome] = {}

    async def acquire(self, request: IdempotencyRequest) -> IdempotencyDecision:
        key = (request.actor_digest, request.route, request.key_digest)
        existing = self.requests.get(key)
        if existing is None:
            self.requests[key] = (request.request_fingerprint, IDEMPOTENCY_ID)
            return IdempotencyDecision(IdempotencyDecisionType.ACQUIRED, IDEMPOTENCY_ID)
        fingerprint, record_id = existing
        if fingerprint != request.request_fingerprint:
            return IdempotencyDecision(IdempotencyDecisionType.PAYLOAD_CONFLICT)
        outcome = self.outcomes.get(record_id)
        if outcome is None:
            return IdempotencyDecision(IdempotencyDecisionType.IN_PROGRESS)
        return IdempotencyDecision(IdempotencyDecisionType.REPLAY, record_id, outcome)

    async def complete(
        self,
        record_id: UUID,
        outcome: IdempotencyOutcome,
        *,
        completed_at: datetime,
    ) -> None:
        del completed_at
        self.outcomes[record_id] = outcome

    async def purge_expired(self, *, before: datetime) -> int:
        del before
        return 0


class _FakeAudit:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class _FakeMediaRepository:
    def __init__(self) -> None:
        self.owner_usages: dict[tuple[str, UUID], tuple[object, ...]] = {}

    async def replace_owner_usages(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        usages: tuple[object, ...],
        now: datetime,
    ) -> None:
        del now
        self.owner_usages[(owner_type, owner_id)] = usages


class _FakeUnitOfWork:
    def __init__(self, repository: _FakeBlogRepository) -> None:
        self.blog = repository
        self.media = _FakeMediaRepository()
        self.audit = _FakeAudit()
        self.idempotency = _FakeIdempotency()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception_type, exception, traceback

    async def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def harness() -> tuple[BlogService, _FakeUnitOfWork]:
    """Build the service over one deterministic in-memory transaction boundary."""
    repository = _FakeBlogRepository()
    uow = _FakeUnitOfWork(repository)
    identifiers = iter((POST_ID, DRAFT_ID, NEXT_DRAFT_ID, NEW_TAXONOMY_ID))
    service = BlogService(
        cast("BlogUnitOfWorkFactory", lambda: uow),
        clock=lambda: NOW,
        id_factory=lambda: next(identifiers),
    )
    return service, uow


async def _create(service: BlogService, *, related: tuple[UUID, ...] = ()) -> PostSnapshot:
    return await service.create_post(
        CreatePostCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-create",
            idempotency_key="create-blog-post-001",
            canonical_payload=b"create",
            slug="Reliable Publication",
            values=_values(related=related),
        )
    )


def _related_snapshot(*, public: bool = False) -> PostSnapshot:
    values = validate_post_values(
        replace(_values(), title="Related article", tag_ids=(), category_ids=()),
        post_id=RELATED_ID,
    )
    revision = PostRevision(
        RELATED_DRAFT_ID,
        RELATED_ID,
        1,
        None,
        values,
        public,
        ACTOR_ID,
        NOW,
        NOW,
    )
    post = Post(
        id=RELATED_ID,
        slug="related-article",
        visible=True,
        position=1,
        draft_revision_id=RELATED_DRAFT_ID,
        published_revision_id=RELATED_DRAFT_ID if public else None,
        publish_at=NOW if public else None,
        unpublished_at=None,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    return PostSnapshot(post, replace(revision, frozen=False), revision if public else None)


@pytest.mark.asyncio
async def test_create_normalizes_slug_recomputes_content_and_audits(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Creation owns all derivations, relations, transaction, and safe audit facts."""
    service, uow = harness
    created = await _create(service)
    assert created.post.slug == "reliable-publication"
    assert created.draft.values.reading_minutes == 1
    assert len(created.draft.values.content_checksum) == 64
    assert [entry.event_type for entry in uow.audit.entries] == ["blog.post_created"]
    assert uow.commits == 1


@pytest.mark.asyncio
async def test_create_rejects_slug_collision_and_unknown_relation(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Stable identities and missing related targets fail before another commit."""
    service, uow = harness
    await _create(service)
    with pytest.raises(BlogSlugConflictError):
        await service.create_post(
            CreatePostCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-two",
                "create-blog-post-002",
                b"two",
                "Reliable Publication",
                _values(),
            )
        )
    assert uow.commits == 1


@pytest.mark.asyncio
async def test_missing_or_wrong_taxonomy_kind_is_rejected(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Revision taxonomy references resolve completely and preserve their kind."""
    service, _uow = harness
    with pytest.raises(BlogRelationError) as captured:
        await service.create_post(
            CreatePostCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-wrong-kind",
                "create-blog-post-wrong-kind",
                b"wrong-kind",
                "Wrong Kind",
                replace(_values(), tag_ids=(CATEGORY_ID,), category_ids=()),
            )
        )
    assert captured.value.code == "taxonomy_kind_mismatch"


@pytest.mark.asyncio
async def test_publish_replay_has_one_effect_and_copy_on_write_draft(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """A retry returns the same publication while live content remains frozen."""
    service, uow = harness
    created = await _create(service)
    command = PublishPostCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-publish",
        created.post.id,
        '"v1"',
        "publish-post-001",
        b"publish",
    )
    published = await service.publish_post(command)
    replay = await service.publish_post(command)
    assert published == replay
    assert published.published is not None
    assert published.published.frozen
    assert published.draft.id != published.published.id
    assert published.draft.values == published.published.values
    assert uow.blog.publish_calls == 1


@pytest.mark.asyncio
async def test_edit_after_publish_keeps_public_article_and_facets_frozen(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Draft source and taxonomy edits cannot leak until republished."""
    service, _uow = harness
    created = await _create(service)
    published = await service.publish_post(
        PublishPostCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-publish",
            created.post.id,
            '"v1"',
            "publish-post-001",
            b"publish",
        )
    )
    before = await service.public_detail(published.post.slug)
    revised = replace(
        published.draft.values,
        title="Private revised title",
        source="## Private revised source",
        tag_ids=(),
    )
    await service.save_post_draft(
        SavePostDraftCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-save",
            published.post.id,
            '"v2"',
            revised,
        )
    )
    after = await service.public_detail(published.post.slug)
    assert after == before
    assert after.title == "Reliable publication"
    assert tuple(item.slug for item in after.tags) == ("engineering",)


@pytest.mark.asyncio
async def test_preview_and_export_use_same_verified_draft_derivation(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Private preview and source export share checksum, policy, and reading time."""
    service, _uow = harness
    created = await _create(service)
    actor = ActorContext.administrator(ACTOR_ID)
    preview = await service.preview(actor, created.post.id)
    exported = await service.export_source(actor, created.post.id)
    assert preview.content.source == exported.source
    assert preview.content.rendered.source_checksum == exported.checksum
    assert preview.content.reading_minutes == exported.reading_minutes
    assert exported.filename == "reliable-publication.md"
    assert exported.content_type == "text/markdown; charset=utf-8"


@pytest.mark.asyncio
async def test_future_and_hidden_posts_never_enter_public_projection(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Database-time eligibility and visibility are applied before public projection."""
    service, _uow = harness
    created = await _create(service)
    future = await service.publish_post(
        PublishPostCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-future",
            created.post.id,
            '"v1"',
            "future-post-0001",
            b"future",
            NOW + timedelta(days=1),
        )
    )
    assert (await service.public_list(PublicPostQuery(PageRequest()))).metadata.total_items == 0
    hidden = await service.set_post_visibility(
        SetPostVisibilityCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-hide",
            post_id=future.post.id,
            if_match='"v2"',
            visible=False,
        )
    )
    assert hidden.post.visible is False


@pytest.mark.asyncio
async def test_unpublish_is_separate_and_idempotent(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Unpublish clears eligibility while retaining the copy-on-write draft."""
    service, _uow = harness
    created = await _create(service)
    published = await service.publish_post(
        PublishPostCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-publish",
            created.post.id,
            '"v1"',
            "publish-post-001",
            b"publish",
        )
    )
    command = UnpublishPostCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-unpublish",
        published.post.id,
        '"v2"',
        "unpublish-post-001",
        b"unpublish",
    )
    unpublished = await service.unpublish_post(command)
    replay = await service.unpublish_post(command)
    assert replay == unpublished
    assert unpublished.post.published_revision_id is None
    assert unpublished.draft.id == published.draft.id


@pytest.mark.asyncio
async def test_taxonomy_create_replays_and_used_taxonomy_cannot_be_deleted(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Taxonomy retries have one effect and retained revision use blocks deletion."""
    service, _uow = harness
    command = CreateTaxonomyCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-taxonomy",
        "create-taxonomy-001",
        b"taxonomy",
        TaxonomyKind.TAG,
        "API Design",
        "API Design",
    )
    created = await service.create_taxonomy(command)
    replay = await service.create_taxonomy(command)
    assert replay == created
    await _create(service)
    with pytest.raises(BlogTaxonomyUsageError) as captured:
        await service.delete_taxonomy(
            DeleteTaxonomyCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-delete-tag",
                TAG_ID,
                '"v1"',
            )
        )
    assert captured.value.usage_count == 1


@pytest.mark.asyncio
async def test_related_public_projection_omits_nonpublic_target(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Admin-valid related IDs never reveal a target until it is independently public."""
    service, uow = harness
    uow.blog.posts[RELATED_ID] = _related_snapshot()
    created = await _create(service, related=(RELATED_ID,))
    published = await service.publish_post(
        PublishPostCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-publish",
            created.post.id,
            '"v1"',
            "publish-post-001",
            b"publish",
        )
    )
    public = await service.public_detail(published.post.slug)
    assert public.related_posts == ()


@pytest.mark.asyncio
async def test_reschedule_visibility_delete_and_admin_reads_cover_distinct_lifecycle_actions(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Scheduling, visibility, and deletion remain independent optimistic actions."""
    service, uow = harness
    actor = ActorContext.administrator(ACTOR_ID)
    created = await _create(service)

    with pytest.raises(BlogPublicationError) as captured:
        await service.reschedule_post(
            ReschedulePostCommand(
                actor,
                "req-premature-reschedule",
                created.post.id,
                '"v1"',
                "premature-reschedule-001",
                b"premature",
                NOW + timedelta(hours=1),
            )
        )
    assert captured.value.code == "not_published"

    published = await service.publish_post(
        PublishPostCommand(
            actor,
            "req-publish-lifecycle",
            created.post.id,
            '"v1"',
            "publish-lifecycle-001",
            b"publish-lifecycle",
        )
    )
    schedule = NOW + timedelta(days=2)
    command = ReschedulePostCommand(
        actor,
        "req-reschedule",
        published.post.id,
        '"v2"',
        "reschedule-post-001",
        b"reschedule",
        schedule,
    )
    rescheduled = await service.reschedule_post(command)
    assert (await service.reschedule_post(command)) == rescheduled
    assert rescheduled.post.publish_at == schedule
    assert rescheduled.published == published.published

    hidden = await service.set_post_visibility(
        SetPostVisibilityCommand(
            actor,
            "req-hide",
            created.post.id,
            '"v3"',
            visible=False,
        )
    )
    deleted = await service.delete_post(
        DeletePostCommand(actor, "req-delete", created.post.id, '"v4"')
    )
    assert hidden.post.visible is False
    assert deleted.post.deleted_at == NOW
    assert deleted.post.published_revision_id is None
    assert (await service.get_admin_post(actor, created.post.id)).snapshot == deleted
    assert (await service.list_admin_posts(actor, AdminPostQuery(PageRequest()))).items
    assert await service.list_taxonomies(actor, TaxonomyKind.TAG)
    assert [entry.event_type for entry in uow.audit.entries][-3:] == [
        "blog.post_rescheduled",
        "blog.post_visibility_changed",
        "blog.post_deleted",
    ]
    with pytest.raises(BlogNotFoundError):
        await service.public_detail(created.post.slug)


@pytest.mark.asyncio
async def test_post_reorder_is_complete_and_replay_safe(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """A full post order is applied once and replay returns authoritative order."""
    service, uow = harness
    created = await _create(service)
    uow.blog.posts[RELATED_ID] = _related_snapshot()
    command = ReorderPostsCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-reorder-posts",
        '"v1"',
        "reorder-posts-001",
        b"reorder-posts",
        (RELATED_ID, created.post.id),
    )
    reordered = await service.reorder_posts(command)
    replay = await service.reorder_posts(command)
    assert tuple(item.id for item in reordered) == (RELATED_ID, created.post.id)
    assert tuple(item.id for item in replay) == (RELATED_ID, created.post.id)
    assert tuple(item.position for item in reordered) == (0, 1)


@pytest.mark.asyncio
async def test_taxonomy_update_reorder_and_unused_delete(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Taxonomy presentation, ordering, and unused soft deletion are independent."""
    service, uow = harness
    actor = ActorContext.administrator(ACTOR_ID)
    uow.blog.taxonomies[EXTRA_TAG_ID] = Taxonomy(
        id=EXTRA_TAG_ID,
        kind=TaxonomyKind.TAG,
        name="Operations",
        slug="operations",
        position=1,
        visible=True,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    updated = await service.update_taxonomy(
        UpdateTaxonomyCommand(
            actor,
            "req-update-tag",
            TAG_ID,
            '"v1"',
            "Platform Engineering",
            "Platform Engineering",
            visible=False,
        )
    )
    assert (updated.name, updated.slug, updated.visible) == (
        "Platform Engineering",
        "platform-engineering",
        False,
    )

    command = ReorderTaxonomiesCommand(
        actor,
        "req-reorder-tags",
        TaxonomyKind.TAG,
        '"v2"',
        "reorder-tags-001",
        b"reorder-tags",
        (EXTRA_TAG_ID, TAG_ID),
    )
    reordered = await service.reorder_taxonomies(command)
    assert await service.reorder_taxonomies(command) == reordered
    assert tuple(item.id for item in reordered) == (EXTRA_TAG_ID, TAG_ID)

    deleted = await service.delete_taxonomy(
        DeleteTaxonomyCommand(actor, "req-delete-unused-tag", EXTRA_TAG_ID, '"v2"')
    )
    assert deleted.deleted_at == NOW
    assert deleted.visible is False


@pytest.mark.asyncio
async def test_public_and_reference_lookups_fail_closed(
    harness: tuple[BlogService, _FakeUnitOfWork],
) -> None:
    """Malformed routes, duplicate IDs, and incomplete references reveal nothing."""
    service, _uow = harness
    await _create(service)
    with pytest.raises(BlogNotFoundError):
        await service.public_detail("Reliable Publication")
    with pytest.raises(BlogNotFoundError):
        await service.public_detail("missing")
    with pytest.raises(BlogNotFoundError):
        await service.reference_summaries((POST_ID, POST_ID))
    with pytest.raises(BlogNotFoundError):
        await service.reference_summaries((POST_ID, RELATED_ID))
    summaries = await service.reference_summaries((POST_ID,))
    assert summaries[0].id == POST_ID
