"""PostgreSQL repository and unit of work for revisioned blog articles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import aliased

from app.common.domain.pagination import Page
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.blog import (
    PostCategoryLinkRecord,
    PostCategoryRecord,
    PostRecord,
    PostRevisionRecord,
    PostTagRecord,
    RelatedPostRecord,
    TagRecord,
)
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.media import MediaRepository
from app.infrastructure.database.pagination import fetch_page
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.blog.domain import (
    AdminPostQuery,
    FrozenPostRevisionError,
    Post,
    PostLifecycle,
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
)
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from types import TracebackType
    from typing import Any
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.elements import ColumnElement

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.blog.ports import BlogUnitOfWork


class BlogPersistenceError(Exception):
    """A locked blog aggregate could not be reloaded after mutation."""


class BlogRepository:
    """Bound-query, immutable-revision PostgreSQL blog adapter."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind one transaction-owned session and opaque child-ID seam."""
        self._session = session
        self._id_factory = id_factory

    async def database_now(self) -> datetime:
        """Read PostgreSQL transaction time."""
        return (await self._session.execute(select(func.now()))).scalar_one()

    async def post_slug_exists(self, slug: str) -> bool:
        """Check the stable identity including soft-deleted reservations."""
        return bool(
            (
                await self._session.execute(
                    select(exists().where(func.lower(PostRecord.slug) == slug.casefold()))
                )
            ).scalar_one()
        )

    async def taxonomy_slug_exists(
        self,
        kind: TaxonomyKind,
        slug: str,
        *,
        excluding_id: UUID | None = None,
    ) -> bool:
        """Check a stable tag/category identity including deleted rows."""
        record_type = self._taxonomy_record_type(kind)
        predicate = func.lower(record_type.slug) == slug.casefold()
        if excluding_id is not None:
            predicate &= record_type.id != excluding_id
        return bool((await self._session.execute(select(exists().where(predicate)))).scalar_one())

    async def list_admin_posts(self, query: AdminPostQuery) -> Page[PostSnapshot]:
        """Return one exact allow-listed administrator page."""
        draft = aliased(PostRevisionRecord, name="draft_revision")
        statement = select(PostRecord).join(draft, draft.id == PostRecord.draft_revision_id)
        count_statement = (
            select(func.count())
            .select_from(PostRecord)
            .join(draft, draft.id == PostRecord.draft_revision_id)
        )
        predicates = self._admin_predicates(query, draft)
        records = await fetch_page(
            self._session,
            ordered_statement=statement.where(*predicates).order_by(
                *self._admin_order(query.sort, draft)
            ),
            count_statement=count_statement.where(*predicates),
            request=query.page,
        )
        return Page(await self._snapshots(records.items), records.metadata)

    async def list_public_posts(self, query: PublicPostQuery) -> Page[PostSnapshot]:
        """Return only database-time-effective public snapshots."""
        published = aliased(PostRevisionRecord, name="published_revision")
        statement = select(PostRecord).join(
            published,
            published.id == PostRecord.published_revision_id,
        )
        count_statement = (
            select(func.count())
            .select_from(PostRecord)
            .join(published, published.id == PostRecord.published_revision_id)
        )
        predicates: list[ColumnElement[bool]] = [
            PostRecord.visible.is_(True),
            PostRecord.deleted_at.is_(None),
            PostRecord.published_revision_id.is_not(None),
            PostRecord.publish_at.is_not(None),
            PostRecord.publish_at <= func.now(),
        ]
        if query.tag_slug is not None:
            predicates.append(
                exists()
                .where(
                    PostTagRecord.revision_id == published.id,
                    PostTagRecord.tag_id == TagRecord.id,
                    TagRecord.slug == query.tag_slug,
                    TagRecord.visible.is_(True),
                    TagRecord.deleted_at.is_(None),
                )
                .correlate(published)
            )
        if query.category_slug is not None:
            predicates.append(
                exists()
                .where(
                    PostCategoryLinkRecord.revision_id == published.id,
                    PostCategoryLinkRecord.category_id == PostCategoryRecord.id,
                    PostCategoryRecord.slug == query.category_slug,
                    PostCategoryRecord.visible.is_(True),
                    PostCategoryRecord.deleted_at.is_(None),
                )
                .correlate(published)
            )
        if query.search is not None:
            pattern = f"%{query.search.casefold()}%"
            predicates.append(
                or_(
                    func.lower(published.title).like(pattern),
                    func.lower(published.excerpt).like(pattern),
                )
            )
        order = cast(
            "tuple[ColumnElement[Any], ...]",
            {
                "newest": (PostRecord.publish_at.desc(), PostRecord.id.asc()),
                "oldest": (PostRecord.publish_at.asc(), PostRecord.id.asc()),
                "title": (published.title.asc(), PostRecord.id.asc()),
                "id": (PostRecord.id.asc(),),
            }[query.sort],
        )
        records = await fetch_page(
            self._session,
            ordered_statement=statement.where(*predicates).order_by(*order),
            count_statement=count_statement.where(*predicates),
            request=query.page,
        )
        return Page(await self._snapshots(records.items), records.metadata)

    async def get_post(
        self,
        post_id: UUID,
        *,
        for_update: bool = False,
    ) -> PostSnapshot | None:
        """Load one aggregate and the exact pointed revisions."""
        statement = select(PostRecord).where(PostRecord.id == post_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        if row is None:
            return None
        return (await self._snapshots((row,)))[0]

    async def get_public_post_by_slug(self, slug: str) -> PostSnapshot | None:
        """Resolve an effective route without leaking excluded existence."""
        row = (
            await self._session.execute(
                select(PostRecord).where(
                    PostRecord.slug == slug,
                    PostRecord.visible.is_(True),
                    PostRecord.deleted_at.is_(None),
                    PostRecord.published_revision_id.is_not(None),
                    PostRecord.publish_at.is_not(None),
                    PostRecord.publish_at <= func.now(),
                )
            )
        ).scalar_one_or_none()
        return None if row is None else (await self._snapshots((row,)))[0]

    async def list_ordered_posts(self, *, for_update: bool = False) -> tuple[Post, ...]:
        """Return all nondeleted posts under deterministic order."""
        statement = (
            select(PostRecord)
            .where(PostRecord.deleted_at.is_(None))
            .order_by(PostRecord.position, PostRecord.id)
        )
        if for_update:
            statement = statement.with_for_update()
        return tuple(self._post(row) for row in (await self._session.execute(statement)).scalars())

    async def post_reference_summaries(
        self,
        post_ids: tuple[UUID, ...],
    ) -> tuple[PostReferenceSummary, ...]:
        """Resolve provider-owned labels and effective public summaries."""
        if not post_ids:
            return ()
        rows = tuple(
            (
                await self._session.execute(select(PostRecord).where(PostRecord.id.in_(post_ids)))
            ).scalars()
        )
        snapshots = await self._snapshots(rows)
        by_id = {item.post.id: item for item in snapshots}
        now = await self.database_now()
        result: list[PostReferenceSummary] = []
        for identifier in post_ids:
            snapshot = by_id.get(identifier)
            if snapshot is None:
                continue
            effective = (
                snapshot.post.visible
                and snapshot.post.deleted_at is None
                and snapshot.post.publish_at is not None
                and snapshot.post.publish_at <= now
                and snapshot.published is not None
            )
            result.append(
                PostReferenceSummary(
                    id=identifier,
                    slug=snapshot.post.slug,
                    title=snapshot.draft.values.title,
                    visible=snapshot.post.visible,
                    deleted=snapshot.post.deleted_at is not None,
                    public=(
                        PublicPostReference(
                            id=identifier,
                            slug=snapshot.post.slug,
                            title=snapshot.published.values.title,
                            excerpt=snapshot.published.values.excerpt,
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
        """Resolve both taxonomy kinds without exposing provider rows directly."""
        if not taxonomy_ids:
            return ()
        tags = tuple(
            (
                await self._session.execute(select(TagRecord).where(TagRecord.id.in_(taxonomy_ids)))
            ).scalars()
        )
        categories = tuple(
            (
                await self._session.execute(
                    select(PostCategoryRecord).where(PostCategoryRecord.id.in_(taxonomy_ids))
                )
            ).scalars()
        )
        values = {item.id: self._taxonomy_summary(item, TaxonomyKind.TAG) for item in tags} | {
            item.id: self._taxonomy_summary(item, TaxonomyKind.CATEGORY) for item in categories
        }
        return tuple(values[item] for item in taxonomy_ids if item in values)

    async def list_taxonomies(
        self,
        kind: TaxonomyKind,
        *,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> tuple[Taxonomy, ...]:
        """Return one taxonomy kind in curated deterministic order."""
        record_type = self._taxonomy_record_type(kind)
        statement = select(record_type).order_by(record_type.position, record_type.id)
        if not include_deleted:
            statement = statement.where(record_type.deleted_at.is_(None))
        if for_update:
            statement = statement.with_for_update()
        return tuple(
            self._taxonomy(row, kind) for row in (await self._session.execute(statement)).scalars()
        )

    async def get_taxonomy(
        self,
        taxonomy_id: UUID,
        *,
        for_update: bool = False,
    ) -> Taxonomy | None:
        """Load a tag or category by globally unique application ID."""
        for kind in TaxonomyKind:
            record_type = self._taxonomy_record_type(kind)
            statement = select(record_type).where(record_type.id == taxonomy_id)
            if for_update:
                statement = statement.with_for_update()
            row = (await self._session.execute(statement)).scalar_one_or_none()
            if row is not None:
                return self._taxonomy(row, kind)
        return None

    async def taxonomy_usage_count(self, taxonomy_id: UUID) -> int:
        """Count distinct retained revisions referencing the taxonomy."""
        tag_count = (
            await self._session.execute(
                select(func.count(func.distinct(PostTagRecord.revision_id))).where(
                    PostTagRecord.tag_id == taxonomy_id
                )
            )
        ).scalar_one()
        category_count = (
            await self._session.execute(
                select(func.count(func.distinct(PostCategoryLinkRecord.revision_id))).where(
                    PostCategoryLinkRecord.category_id == taxonomy_id
                )
            )
        ).scalar_one()
        return int(tag_count) + int(category_count)

    async def add_post(self, post: Post, revision: PostRevision) -> None:
        """Stage aggregate and revision one without committing."""
        self._session.add(self._post_record(post))
        await self._add_revision(revision)

    async def save_post_draft(
        self,
        snapshot: PostSnapshot,
        values: PostValues,
        *,
        now: datetime,
    ) -> PostSnapshot:
        """Replace only a mutable draft and its ordered relations."""
        aggregate = await self._locked_post(snapshot.post.id)
        revision = await self._locked_revision(aggregate.draft_revision_id)
        if revision.frozen:
            raise FrozenPostRevisionError
        self._set_revision_values(revision, values)
        revision.based_on_revision_id = (
            aggregate.published_revision_id
            if snapshot.published is not None and values == snapshot.published.values
            else None
        )
        revision.updated_at = now
        aggregate.updated_at = now
        aggregate.version += 1
        await self._replace_children(revision.id, aggregate.id, values)
        await self._session.flush()
        loaded = await self.get_post(aggregate.id)
        if loaded is None:
            raise BlogPersistenceError
        return loaded

    async def publish_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> PostSnapshot:
        """Freeze, point, and create one copy-on-write draft."""
        aggregate = await self._locked_post(snapshot.post.id)
        draft = await self._locked_revision(aggregate.draft_revision_id)
        if draft.frozen:
            raise FrozenPostRevisionError
        draft.frozen = True
        draft.updated_at = now
        copied = PostRevision(
            id=next_revision_id,
            post_id=aggregate.id,
            revision_number=draft.revision_number + 1,
            based_on_revision_id=draft.id,
            values=snapshot.draft.values,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        await self._add_revision(copied)
        aggregate.draft_revision_id = copied.id
        aggregate.published_revision_id = draft.id
        aggregate.publish_at = publish_at
        aggregate.unpublished_at = None
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        loaded = await self.get_post(aggregate.id)
        if loaded is None:
            raise BlogPersistenceError
        return loaded

    async def reschedule_post(
        self,
        snapshot: PostSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> PostSnapshot:
        """Change only publication time and aggregate version."""
        return await self._mutate_post(
            snapshot,
            {"publish_at": publish_at},
            now=now,
        )

    async def unpublish_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        """Clear eligibility pointers while retaining every revision."""
        return await self._mutate_post(
            snapshot,
            {
                "published_revision_id": None,
                "publish_at": None,
                "unpublished_at": now,
            },
            now=now,
        )

    async def set_post_visibility(
        self,
        snapshot: PostSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> PostSnapshot:
        """Set visibility independently from lifecycle."""
        return await self._mutate_post(snapshot, {"visible": visible}, now=now)

    async def reorder_posts(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Post, ...]:
        """Replace the full admin order after application validation."""
        for position, identifier in enumerate(ordered_ids):
            await self._session.execute(
                update(PostRecord)
                .where(PostRecord.id == identifier)
                .values(position=position, updated_at=now, version=PostRecord.version + 1)
            )
        await self._session.flush()
        return await self.list_ordered_posts()

    async def soft_delete_post(self, snapshot: PostSnapshot, *, now: datetime) -> PostSnapshot:
        """Remove eligibility but preserve the source/revision audit trail."""
        return await self._mutate_post(
            snapshot,
            {
                "published_revision_id": None,
                "publish_at": None,
                "deleted_at": now,
            },
            now=now,
        )

    async def add_taxonomy(self, taxonomy: Taxonomy) -> None:
        """Stage a tag/category without committing."""
        record_type = self._taxonomy_record_type(taxonomy.kind)
        self._session.add(
            record_type(
                id=taxonomy.id,
                name=taxonomy.name,
                slug=taxonomy.slug,
                position=taxonomy.position,
                visible=taxonomy.visible,
                created_at=taxonomy.created_at,
                updated_at=taxonomy.updated_at,
                version=taxonomy.version,
                deleted_at=taxonomy.deleted_at,
            )
        )
        await self._session.flush()

    async def update_taxonomy(
        self,
        taxonomy: Taxonomy,
        *,
        name: str,
        slug: str,
        visible: bool,
        now: datetime,
    ) -> Taxonomy:
        """Update mutable taxonomy presentation under its row lock."""
        record_type = self._taxonomy_record_type(taxonomy.kind)
        row = (
            await self._session.execute(
                select(record_type).where(record_type.id == taxonomy.id).with_for_update()
            )
        ).scalar_one()
        row.name = name
        row.slug = slug
        row.visible = visible
        row.updated_at = now
        row.version += 1
        await self._session.flush((row,))
        return self._taxonomy(row, taxonomy.kind)

    async def reorder_taxonomies(
        self,
        kind: TaxonomyKind,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Taxonomy, ...]:
        """Replace one complete curated taxonomy order."""
        record_type = self._taxonomy_record_type(kind)
        for position, identifier in enumerate(ordered_ids):
            await self._session.execute(
                update(record_type)
                .where(record_type.id == identifier)
                .values(position=position, updated_at=now, version=record_type.version + 1)
            )
        await self._session.flush()
        return await self.list_taxonomies(kind)

    async def soft_delete_taxonomy(self, taxonomy: Taxonomy, *, now: datetime) -> Taxonomy:
        """Soft-delete a taxonomy after the service proves zero use."""
        record_type = self._taxonomy_record_type(taxonomy.kind)
        row = (
            await self._session.execute(
                select(record_type).where(record_type.id == taxonomy.id).with_for_update()
            )
        ).scalar_one()
        row.visible = False
        row.deleted_at = now
        row.updated_at = now
        row.version += 1
        await self._session.flush((row,))
        return self._taxonomy(row, taxonomy.kind)

    async def _mutate_post(
        self,
        snapshot: PostSnapshot,
        values: dict[str, object],
        *,
        now: datetime,
    ) -> PostSnapshot:
        row = await self._locked_post(snapshot.post.id)
        for field, value in values.items():
            setattr(row, field, value)
        row.updated_at = now
        row.version += 1
        await self._session.flush((row,))
        loaded = await self.get_post(row.id)
        if loaded is None:
            raise BlogPersistenceError
        return loaded

    def _admin_predicates(
        self,
        query: AdminPostQuery,
        draft: type[PostRevisionRecord],
    ) -> list[ColumnElement[bool]]:
        predicates = self._lifecycle_predicates(query.lifecycle, draft)
        if query.visible is not None:
            predicates.append(PostRecord.visible.is_(query.visible))
        if query.tag_id is not None:
            predicates.append(
                exists().where(
                    PostTagRecord.revision_id == draft.id,
                    PostTagRecord.tag_id == query.tag_id,
                )
            )
        if query.category_id is not None:
            predicates.append(
                exists().where(
                    PostCategoryLinkRecord.revision_id == draft.id,
                    PostCategoryLinkRecord.category_id == query.category_id,
                )
            )
        if query.search is not None:
            pattern = f"%{query.search.casefold()}%"
            predicates.append(
                or_(
                    func.lower(draft.title).like(pattern),
                    func.lower(draft.excerpt).like(pattern),
                    func.lower(PostRecord.slug).like(pattern),
                )
            )
        return predicates

    @staticmethod
    def _lifecycle_predicates(
        lifecycle: PostLifecycle | None,
        draft: type[PostRevisionRecord],
    ) -> list[ColumnElement[bool]]:
        if lifecycle is PostLifecycle.DELETED:
            return [PostRecord.deleted_at.is_not(None)]
        values: list[ColumnElement[bool]] = [PostRecord.deleted_at.is_(None)]
        if lifecycle is PostLifecycle.DRAFT:
            values += [
                PostRecord.published_revision_id.is_(None),
                PostRecord.unpublished_at.is_(None),
            ]
        elif lifecycle is PostLifecycle.UNPUBLISHED:
            values += [
                PostRecord.published_revision_id.is_(None),
                PostRecord.unpublished_at.is_not(None),
            ]
        elif lifecycle is PostLifecycle.SCHEDULED:
            values += [
                PostRecord.published_revision_id.is_not(None),
                PostRecord.publish_at > func.now(),
            ]
        elif lifecycle is PostLifecycle.PUBLISHED:
            values += [
                PostRecord.published_revision_id.is_not(None),
                PostRecord.publish_at <= func.now(),
                draft.based_on_revision_id == PostRecord.published_revision_id,
            ]
        elif lifecycle is PostLifecycle.PUBLISHED_CHANGES_PENDING:
            values += [
                PostRecord.published_revision_id.is_not(None),
                PostRecord.publish_at <= func.now(),
                or_(
                    draft.based_on_revision_id.is_(None),
                    draft.based_on_revision_id != PostRecord.published_revision_id,
                ),
            ]
        return values

    @staticmethod
    def _admin_order(
        sort: str,
        draft: type[PostRevisionRecord],
    ) -> tuple[ColumnElement[Any], ...]:
        descending = sort.startswith("-")
        key = sort[1:] if descending else sort
        selected = {
            "position": PostRecord.position,
            "title": draft.title,
            "publish_at": PostRecord.publish_at,
            "updated_at": PostRecord.updated_at,
            "id": PostRecord.id,
        }[key]
        return (selected.desc() if descending else selected.asc(), PostRecord.id.asc())

    async def _snapshots(self, aggregates: Sequence[PostRecord]) -> tuple[PostSnapshot, ...]:
        if not aggregates:
            return ()
        revision_ids = {
            identifier
            for aggregate in aggregates
            for identifier in (aggregate.draft_revision_id, aggregate.published_revision_id)
            if identifier is not None
        }
        revisions = tuple(
            (
                await self._session.execute(
                    select(PostRevisionRecord).where(PostRevisionRecord.id.in_(revision_ids))
                )
            ).scalars()
        )
        tags = await self._ordered_ids(PostTagRecord, "tag_id", revision_ids)
        categories = await self._ordered_ids(
            PostCategoryLinkRecord,
            "category_id",
            revision_ids,
        )
        related = await self._ordered_ids(RelatedPostRecord, "related_post_id", revision_ids)
        by_id = {
            row.id: self._revision(
                row,
                tags.get(row.id, ()),
                categories.get(row.id, ()),
                related.get(row.id, ()),
            )
            for row in revisions
        }
        return tuple(
            PostSnapshot(
                post=self._post(row),
                draft=by_id[row.draft_revision_id],
                published=(
                    by_id[row.published_revision_id]
                    if row.published_revision_id is not None
                    else None
                ),
            )
            for row in aggregates
        )

    async def _ordered_ids(
        self,
        record_type: type[Any],
        attribute: str,
        revision_ids: set[UUID],
    ) -> dict[UUID, tuple[UUID, ...]]:
        statement = (
            select(record_type)
            .where(record_type.revision_id.in_(revision_ids))
            .order_by(record_type.revision_id, record_type.position, record_type.id)
        )
        grouped: dict[UUID, list[UUID]] = {}
        for row in (await self._session.execute(statement)).scalars():
            grouped.setdefault(row.revision_id, []).append(getattr(row, attribute))
        return {key: tuple(values) for key, values in grouped.items()}

    async def _replace_children(
        self,
        revision_id: UUID,
        post_id: UUID,
        values: PostValues,
    ) -> None:
        for record_type in (PostTagRecord, PostCategoryLinkRecord, RelatedPostRecord):
            await self._session.execute(
                delete(record_type).where(record_type.revision_id == revision_id)
            )
        self._add_children(revision_id, post_id, values)

    async def _add_revision(self, revision: PostRevision) -> None:
        row = PostRevisionRecord(
            id=revision.id,
            post_id=revision.post_id,
            revision_number=revision.revision_number,
            based_on_revision_id=revision.based_on_revision_id,
            title=revision.values.title,
            excerpt=revision.values.excerpt,
            source=revision.values.source,
            author_display=revision.values.author_display,
            reading_minutes=revision.values.reading_minutes,
            content_checksum=revision.values.content_checksum,
            content_policy_name=revision.values.content_policy_name,
            content_policy_version=revision.values.content_policy_version,
            seo_title=revision.values.seo_title,
            seo_description=revision.values.seo_description,
            canonical_url=revision.values.canonical_url,
            cover_media_id=revision.values.cover_media_id,
            frozen=revision.frozen,
            created_by=revision.created_by,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )
        self._session.add(row)
        await self._session.flush((row,))
        self._add_children(revision.id, revision.post_id, revision.values)

    def _add_children(self, revision_id: UUID, post_id: UUID, values: PostValues) -> None:
        for record_type, identifiers, attribute in (
            (PostTagRecord, values.tag_ids, "tag_id"),
            (PostCategoryLinkRecord, values.category_ids, "category_id"),
        ):
            for position, identifier in enumerate(identifiers):
                self._session.add(
                    record_type(
                        id=self._id_factory(),
                        revision_id=revision_id,
                        position=position,
                        **{attribute: identifier},
                    )
                )
        for position, identifier in enumerate(values.related_post_ids):
            self._session.add(
                RelatedPostRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    post_id=post_id,
                    related_post_id=identifier,
                    position=position,
                )
            )

    @staticmethod
    def _set_revision_values(row: PostRevisionRecord, values: PostValues) -> None:
        row.title = values.title
        row.excerpt = values.excerpt
        row.source = values.source
        row.author_display = values.author_display
        row.reading_minutes = values.reading_minutes
        row.content_checksum = values.content_checksum
        row.content_policy_name = values.content_policy_name
        row.content_policy_version = values.content_policy_version
        row.seo_title = values.seo_title
        row.seo_description = values.seo_description
        row.canonical_url = values.canonical_url
        row.cover_media_id = values.cover_media_id

    async def _locked_post(self, post_id: UUID) -> PostRecord:
        return (
            await self._session.execute(
                select(PostRecord).where(PostRecord.id == post_id).with_for_update()
            )
        ).scalar_one()

    async def _locked_revision(self, revision_id: UUID) -> PostRevisionRecord:
        return (
            await self._session.execute(
                select(PostRevisionRecord)
                .where(PostRevisionRecord.id == revision_id)
                .with_for_update()
            )
        ).scalar_one()

    @staticmethod
    def _post(row: PostRecord) -> Post:
        return Post(
            id=row.id,
            slug=row.slug,
            visible=row.visible,
            position=row.position,
            draft_revision_id=row.draft_revision_id,
            published_revision_id=row.published_revision_id,
            publish_at=row.publish_at,
            unpublished_at=row.unpublished_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def _post_record(value: Post) -> PostRecord:
        return PostRecord(
            id=value.id,
            slug=value.slug,
            visible=value.visible,
            position=value.position,
            draft_revision_id=value.draft_revision_id,
            published_revision_id=value.published_revision_id,
            publish_at=value.publish_at,
            unpublished_at=value.unpublished_at,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=value.version,
            deleted_at=value.deleted_at,
        )

    @staticmethod
    def _revision(
        row: PostRevisionRecord,
        tag_ids: tuple[UUID, ...],
        category_ids: tuple[UUID, ...],
        related_post_ids: tuple[UUID, ...],
    ) -> PostRevision:
        return PostRevision(
            id=row.id,
            post_id=row.post_id,
            revision_number=row.revision_number,
            based_on_revision_id=row.based_on_revision_id,
            values=PostValues(
                title=row.title,
                excerpt=row.excerpt,
                source=row.source,
                author_display=row.author_display,
                reading_minutes=row.reading_minutes,
                content_checksum=row.content_checksum,
                content_policy_name=row.content_policy_name,
                content_policy_version=row.content_policy_version,
                tag_ids=tag_ids,
                category_ids=category_ids,
                related_post_ids=related_post_ids,
                seo_title=row.seo_title,
                seo_description=row.seo_description,
                canonical_url=row.canonical_url,
                cover_media_id=row.cover_media_id,
            ),
            frozen=row.frozen,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _taxonomy_record_type(
        kind: TaxonomyKind,
    ) -> type[Any]:
        return TagRecord if kind is TaxonomyKind.TAG else PostCategoryRecord

    @staticmethod
    def _taxonomy(
        row: TagRecord | PostCategoryRecord,
        kind: TaxonomyKind,
    ) -> Taxonomy:
        return Taxonomy(
            id=row.id,
            kind=kind,
            name=row.name,
            slug=row.slug,
            position=row.position,
            visible=row.visible,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def _taxonomy_summary(
        row: TagRecord | PostCategoryRecord,
        kind: TaxonomyKind,
    ) -> TaxonomyReferenceSummary:
        return TaxonomyReferenceSummary(
            id=row.id,
            kind=kind,
            name=row.name,
            slug=row.slug,
            visible=row.visible,
            deleted=row.deleted_at is not None,
            public=(
                PublicTaxonomyReference(id=row.id, name=row.name, slug=row.slug)
                if row.visible and row.deleted_at is None
                else None
            ),
        )


class SqlAlchemyBlogUnitOfWork:
    """Bind M7 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.blog: BlogRepository
        self.media: MediaRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository

    async def __aenter__(self) -> Self:
        """Open the transaction and bind repositories."""
        await self._inner.__aenter__()
        self.blog = BlogRepository(self._inner.session)
        self.media = MediaRepository(self._inner.session, id_factory=uuid7)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        """Commit only at the application-service boundary."""
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Delegate rollback and resource cleanup."""
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemyBlogUnitOfWorkFactory:
    """Create structurally typed blog transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> BlogUnitOfWork:
        """Return a fresh unopened blog transaction."""
        return cast("BlogUnitOfWork", SqlAlchemyBlogUnitOfWork(self.session_factory))
