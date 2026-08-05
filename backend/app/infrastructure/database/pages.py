"""SQLAlchemy records and PostgreSQL repository for configurable pages."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves this type at runtime.
from typing import TYPE_CHECKING, cast
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves this type at runtime.

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.pages.domain import (
    BlockLayout,
    BlockTheme,
    FrozenPageRevisionError,
    Page,
    PageBlock,
    PageBlockValues,
    PagePersistenceError,
    PageReferenceTarget,
    PageRevision,
    PageRevisionValues,
    PageRouteKind,
    PageSnapshot,
    ResponsiveValues,
)
from app.modules.pages.registry import BlockReference, BlockType, ReferenceKind, ReferenceRole

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

MAXIMUM_PAGE_QUERY_ITEMS = 100


class PagesBase(DeclarativeBase):
    """SQLAlchemy registry owned only by the M8 page slice."""


class PageRecord(PagesBase):
    """Stable route identity, lifecycle pointers, visibility, and concurrency."""

    __tablename__ = "page"
    __table_args__ = (
        CheckConstraint("route_kind IN ('home','custom')", name="page_route_kind_catalog"),
        CheckConstraint(
            "(route_kind = 'home' AND slug IS NULL) OR "
            "(route_kind = 'custom' AND slug IS NOT NULL)",
            name="page_route_slug_shape",
        ),
        CheckConstraint(
            "slug IS NULL OR (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' AND length(slug) BETWEEN 1 AND 80)",
            name="page_slug_format",
        ),
        CheckConstraint(
            "slug IS NULL OR lower(slug) NOT IN ('admin','api','_next','about',"
            "'experience','experiences','skills','projects','blog','contact','privacy',"
            "'legal','robots.txt','sitemap.xml','favicon.ico','assets','media','health',"
            "'docs','openapi.json')",
            name="page_slug_not_reserved",
        ),
        CheckConstraint("position >= 0", name="page_nonnegative_position"),
        CheckConstraint("version > 0", name="page_positive_version"),
        CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="page_publication_pointer_schedule_pair",
        ),
        CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="page_distinct_revision_pointers",
        ),
        ForeignKeyConstraint(
            ["id", "draft_revision_id"],
            ["page_revision.page_id", "page_revision.id"],
            name="fk_page_draft_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["id", "published_revision_id"],
            ["page_revision.page_id", "page_revision.id"],
            name="fk_page_published_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index(
            "uq_page_home_singleton",
            "route_kind",
            unique=True,
            postgresql_where=text("route_kind = 'home'"),
        ),
        Index(
            "uq_page_custom_slug_ci",
            text("lower(slug)"),
            unique=True,
            postgresql_where=text("route_kind = 'custom'"),
        ),
        Index("ix_page_admin_order", "position", "id"),
        Index(
            "ix_page_effective_public",
            "route_kind",
            "slug",
            postgresql_where=text(
                "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    route_kind: Mapped[str] = mapped_column(String(16))
    slug: Mapped[str | None] = mapped_column(String(80))
    visible: Mapped[bool] = mapped_column(Boolean)
    navigation_visible: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int] = mapped_column(Integer)
    draft_revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    published_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PageRevisionRecord(PagesBase):
    """Page metadata snapshot owning one ordered immutable-capable block tree."""

    __tablename__ = "page_revision"
    __table_args__ = (
        CheckConstraint("revision_number > 0", name="page_revision_positive_number"),
        CheckConstraint(
            "length(title) BETWEEN 1 AND 180 AND title = btrim(title)",
            name="page_revision_title",
        ),
        CheckConstraint(
            "length(description) BETWEEN 1 AND 500 AND description = btrim(description)",
            name="page_revision_description",
        ),
        CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="page_revision_seo_title",
        ),
        CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="page_revision_seo_description",
        ),
        CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) AND canonical_url LIKE 'https://%')",
            name="page_revision_https_canonical_url",
        ),
        UniqueConstraint("page_id", "revision_number", name="uq_page_revision_number"),
        UniqueConstraint("page_id", "id", name="uq_page_revision_owner_target"),
        ForeignKeyConstraint(
            ["page_id", "based_on_revision_id"],
            ["page_revision.page_id", "page_revision.id"],
            name="fk_page_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_page_revision_created_by_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_page_revision_page_number", "page_id", "revision_number"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("page.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    based_on_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(String(500))
    seo_title: Mapped[str | None] = mapped_column(String(70))
    seo_description: Mapped[str | None] = mapped_column(String(180))
    canonical_url: Mapped[str | None] = mapped_column(String(2_048))
    frozen: Mapped[bool] = mapped_column(Boolean)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PageBlockRecord(PagesBase):
    """Relational block shell with bounded canonical type-specific JSON."""

    __tablename__ = "page_block"
    __table_args__ = (
        CheckConstraint("position >= 0", name="page_block_nonnegative_position"),
        CheckConstraint("schema_version > 0", name="page_block_positive_schema_version"),
        CheckConstraint(
            "block_type IN ('hero','profile_summary','call_to_action','statistics',"
            "'skills_grid','featured_skills','experience_summary','experience_list',"
            "'project_grid','featured_projects','latest_posts','rich_text','image',"
            "'image_with_text','links_collection','contact_callout','testimonial',"
            "'divider','spacer')",
            name="page_block_type_catalog",
        ),
        CheckConstraint(
            "theme IN ('default','accent','muted','contrast')",
            name="page_block_theme_catalog",
        ),
        CheckConstraint(
            "layout IN ('contained','wide','full')",
            name="page_block_layout_catalog",
        ),
        CheckConstraint(
            "jsonb_typeof(config) = 'object' AND pg_column_size(config) <= 32768",
            name="page_block_config_bounds",
        ),
        CheckConstraint(
            "jsonb_typeof(responsive) = 'object' AND pg_column_size(responsive) <= 1024",
            name="page_block_responsive_bounds",
        ),
        CheckConstraint(
            "title IS NULL OR (length(title) BETWEEN 1 AND 180 AND title = btrim(title))",
            name="page_block_title",
        ),
        CheckConstraint(
            "subtitle IS NULL OR (length(subtitle) BETWEEN 1 AND 240 "
            "AND subtitle = btrim(subtitle))",
            name="page_block_subtitle",
        ),
        CheckConstraint(
            "description IS NULL OR (length(description) BETWEEN 1 AND 500 "
            "AND description = btrim(description))",
            name="page_block_description",
        ),
        UniqueConstraint("revision_id", "position", name="uq_page_block_revision_position"),
        UniqueConstraint("revision_id", "id", name="uq_page_block_revision_owner_target"),
        Index("ix_page_block_revision_order", "revision_id", "position", "id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("page_revision.id", ondelete="CASCADE")
    )
    block_type: Mapped[str] = mapped_column(String(40))
    schema_version: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    visible: Mapped[bool] = mapped_column(Boolean)
    title: Mapped[str | None] = mapped_column(String(180))
    subtitle: Mapped[str | None] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(String(500))
    theme: Mapped[str] = mapped_column(String(20))
    layout: Mapped[str] = mapped_column(String(20))
    responsive: Mapped[dict[str, object]] = mapped_column(JSONB)
    config: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PageBlockReferenceRecord(PagesBase):
    """Normalized typed target derived from one trusted block config."""

    __tablename__ = "page_block_reference"
    __table_args__ = (
        CheckConstraint("position >= 0", name="page_block_reference_nonnegative_position"),
        CheckConstraint(
            "reference_kind IN ('profile','skill','experience','project','post','page','media')",
            name="page_block_reference_kind_catalog",
        ),
        CheckConstraint(
            "role IN ('profile_evidence','skill_item','experience_item','project_item',"
            "'post_item','internal_destination','media_primary')",
            name="page_block_reference_role_catalog",
        ),
        ForeignKeyConstraint(
            ["revision_id", "block_id"],
            ["page_block.revision_id", "page_block.id"],
            name="fk_page_block_reference_block_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "block_id", "role", "position", name="uq_page_block_reference_role_position"
        ),
        UniqueConstraint(
            "block_id",
            "reference_kind",
            "role",
            "target_id",
            name="uq_page_block_reference_target",
        ),
        Index(
            "ix_page_block_reference_revision_kind",
            "revision_id",
            "reference_kind",
            "position",
        ),
        Index("ix_page_block_reference_target", "reference_kind", "target_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    block_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    reference_kind: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    role: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean)


class PageRepository:
    """Bound-query, immutable-revision PostgreSQL page adapter."""

    def __init__(self, session: AsyncSession, *, id_factory: Callable[[], UUID]) -> None:
        """Bind the caller-owned transaction and opaque child-ID factory."""
        self._session = session
        self._id_factory = id_factory

    async def database_now(self) -> datetime:
        """Return PostgreSQL transaction time in UTC."""
        return (await self._session.execute(select(func.now()))).scalar_one()

    async def route_exists(
        self,
        route_kind: PageRouteKind,
        slug: str | None,
        *,
        excluding_id: UUID | None = None,
    ) -> bool:
        """Check stable route reservations including soft-deleted identities."""
        predicate = PageRecord.route_kind == route_kind.value
        if route_kind is PageRouteKind.CUSTOM:
            predicate &= func.lower(PageRecord.slug) == cast("str", slug).casefold()
        if excluding_id is not None:
            predicate &= PageRecord.id != excluding_id
        return bool(
            (await self._session.execute(select(func.count()).where(predicate))).scalar_one()
        )

    async def next_position(self) -> int:
        """Return the next deterministic administrator position."""
        current = (await self._session.execute(select(func.max(PageRecord.position)))).scalar_one()
        return 0 if current is None else int(current) + 1

    async def add_page(self, page: Page, revision: PageRevision) -> None:
        """Stage a stable route and revision-one draft."""
        self._session.add(self._page_record(page))
        self._session.add(self._revision_record(revision))
        await self._session.flush()
        await self._add_blocks(revision)

    async def get_page(self, page_id: UUID, *, for_update: bool = False) -> PageSnapshot | None:
        """Load one aggregate plus draft and optional published revision."""
        statement = select(PageRecord).where(PageRecord.id == page_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else await self._snapshot(row)

    async def get_public_home(self) -> PageSnapshot | None:
        """Resolve only the effective singleton Home snapshot."""
        return await self._get_public(route_kind=PageRouteKind.HOME, slug=None)

    async def get_public_custom(self, slug: str) -> PageSnapshot | None:
        """Resolve only an effective custom page without widening by credentials."""
        return await self._get_public(route_kind=PageRouteKind.CUSTOM, slug=slug)

    async def list_pages(self, *, offset: int, limit: int) -> tuple[tuple[PageSnapshot, ...], int]:
        """Return one bounded administrator page and its exact retained total."""
        if offset < 0 or limit < 1 or limit > MAXIMUM_PAGE_QUERY_ITEMS:
            raise PagePersistenceError
        predicate = PageRecord.deleted_at.is_(None)
        total = int(
            (
                await self._session.execute(select(func.count(PageRecord.id)).where(predicate))
            ).scalar_one()
        )
        rows = (
            await self._session.execute(
                select(PageRecord)
                .where(predicate)
                .order_by(PageRecord.position, PageRecord.id)
                .offset(offset)
                .limit(limit)
            )
        ).scalars()
        return tuple([await self._snapshot(row) for row in rows]), total

    async def reference_targets(self, ids: tuple[UUID, ...]) -> tuple[PageReferenceTarget, ...]:
        """Resolve bounded internal-page facts in one set query."""
        if len(ids) > MAXIMUM_PAGE_QUERY_ITEMS:
            raise PagePersistenceError
        if not ids:
            return ()
        statement = (
            select(PageRecord, PageRevisionRecord.title)
            .outerjoin(
                PageRevisionRecord,
                PageRevisionRecord.id == PageRecord.published_revision_id,
            )
            .where(PageRecord.id.in_(ids))
            .order_by(PageRecord.id)
        )
        return tuple(
            PageReferenceTarget(
                id=row.id,
                route_kind=PageRouteKind(row.route_kind),
                slug=row.slug,
                visible=row.visible,
                deleted=row.deleted_at is not None,
                publish_at=row.publish_at,
                title=title,
                updated_at=row.updated_at,
            )
            for row, title in (await self._session.execute(statement)).all()
        )

    async def list_public_routes(
        self, *, offset: int, limit: int
    ) -> tuple[tuple[PageReferenceTarget, ...], int]:
        """Return one bounded effective route page without loading block trees."""
        if offset < 0 or limit < 1 or limit > MAXIMUM_PAGE_QUERY_ITEMS:
            raise PagePersistenceError
        predicate = (
            PageRecord.visible.is_(True)
            & PageRecord.deleted_at.is_(None)
            & PageRecord.published_revision_id.is_not(None)
            & PageRecord.publish_at.is_not(None)
            & (PageRecord.publish_at <= func.now())
        )
        total = int(
            (
                await self._session.execute(select(func.count(PageRecord.id)).where(predicate))
            ).scalar_one()
        )
        statement = (
            select(PageRecord, PageRevisionRecord.title)
            .join(PageRevisionRecord, PageRevisionRecord.id == PageRecord.published_revision_id)
            .where(predicate)
            .order_by(PageRecord.position, PageRecord.id)
            .offset(offset)
            .limit(limit)
        )
        return (
            tuple(
                PageReferenceTarget(
                    id=row.id,
                    route_kind=PageRouteKind(row.route_kind),
                    slug=row.slug,
                    visible=True,
                    deleted=False,
                    publish_at=row.publish_at,
                    title=title,
                    updated_at=row.updated_at,
                )
                for row, title in (await self._session.execute(statement)).all()
            ),
            total,
        )

    async def save_draft(  # noqa: PLR0913 - complete atomic aggregate mutation.
        self,
        snapshot: PageSnapshot,
        *,
        values: PageRevisionValues,
        route_kind: PageRouteKind,
        slug: str | None,
        visible: bool,
        navigation_visible: bool,
        now: datetime,
    ) -> PageSnapshot:
        """Replace mutable metadata and route presentation under one lock."""
        if snapshot.draft.frozen:
            raise FrozenPageRevisionError
        page_row = await self._page_row(snapshot.page.id)
        revision_row = await self._revision_row(snapshot.draft.id)
        page_row.route_kind = route_kind.value
        page_row.slug = slug
        page_row.visible = visible
        page_row.navigation_visible = navigation_visible
        page_row.version += 1
        page_row.updated_at = now
        revision_row.title = values.title
        revision_row.description = values.description
        revision_row.seo_title = values.seo_title
        revision_row.seo_description = values.seo_description
        revision_row.canonical_url = values.canonical_url
        revision_row.based_on_revision_id = None
        revision_row.updated_at = now
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def add_block(
        self,
        snapshot: PageSnapshot,
        block: PageBlock,
        *,
        position: int,
        now: datetime,
    ) -> PageSnapshot:
        """Insert one validated block and atomically normalize order."""
        self._require_mutable(snapshot)
        rows = await self._block_rows(snapshot.draft.id, for_update=True)
        if position < 0 or position > len(rows):
            raise PagePersistenceError
        await self._set_temporary_positions(rows)
        rows.insert(position, self._block_record(block))
        self._session.add(rows[position])
        self._session.add_all(self._reference_records(block))
        self._set_positions(rows, now=now)
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def update_block(
        self,
        snapshot: PageSnapshot,
        block_id: UUID,
        values: PageBlockValues,
        references: tuple[BlockReference, ...],
        *,
        now: datetime,
    ) -> PageSnapshot:
        """Replace one mutable block and its config-derived reference rows."""
        self._require_mutable(snapshot)
        row = await self._owned_block_row(snapshot.draft.id, block_id)
        self._apply_block_values(row, values, now=now)
        existing = await self._session.execute(
            select(PageBlockReferenceRecord).where(PageBlockReferenceRecord.block_id == block_id)
        )
        for stored_reference in existing.scalars():
            await self._session.delete(stored_reference)
        # Execute removals before inserting replacement rows. PostgreSQL otherwise
        # sees the old role/position key until the unit-of-work flushes and rejects
        # an in-place media metadata edit as a duplicate reference.
        await self._session.flush()
        for reference in references:
            self._session.add(self._reference_record(snapshot.draft.id, block_id, reference))
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def duplicate_block(
        self, snapshot: PageSnapshot, block_id: UUID, *, now: datetime
    ) -> PageSnapshot:
        """Deep-copy one mutable block next to its source with new child IDs."""
        self._require_mutable(snapshot)
        rows = await self._block_rows(snapshot.draft.id, for_update=True)
        source = next((row for row in rows if row.id == block_id), None)
        if source is None:
            raise PagePersistenceError
        references = await self._reference_rows(source.id)
        copy_id = self._id_factory()
        copy = PageBlockRecord(
            id=copy_id,
            revision_id=source.revision_id,
            block_type=source.block_type,
            schema_version=source.schema_version,
            position=source.position + 1,
            visible=source.visible,
            title=source.title,
            subtitle=source.subtitle,
            description=source.description,
            theme=source.theme,
            layout=source.layout,
            responsive=dict(source.responsive),
            config=dict(source.config),
            created_at=now,
            updated_at=now,
        )
        await self._set_temporary_positions(rows)
        rows.insert(source.position + 1, copy)
        self._session.add(copy)
        for reference in references:
            self._session.add(
                PageBlockReferenceRecord(
                    id=self._id_factory(),
                    revision_id=source.revision_id,
                    block_id=copy_id,
                    reference_kind=reference.reference_kind,
                    target_id=reference.target_id,
                    role=reference.role,
                    position=reference.position,
                    required=reference.required,
                )
            )
        self._set_positions(rows, now=now)
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def set_block_visibility(
        self, snapshot: PageSnapshot, block_id: UUID, *, visible: bool, now: datetime
    ) -> PageSnapshot:
        """Set one mutable block's independent public visibility."""
        self._require_mutable(snapshot)
        row = await self._owned_block_row(snapshot.draft.id, block_id)
        row.visible = visible
        row.updated_at = now
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def delete_block(
        self, snapshot: PageSnapshot, block_id: UUID, *, now: datetime
    ) -> PageSnapshot:
        """Delete one mutable block and restore contiguous order."""
        self._require_mutable(snapshot)
        rows = await self._block_rows(snapshot.draft.id, for_update=True)
        target = next((row for row in rows if row.id == block_id), None)
        if target is None:
            raise PagePersistenceError
        await self._session.delete(target)
        await self._session.flush()
        remaining = [row for row in rows if row.id != block_id]
        await self._set_temporary_positions(remaining)
        self._set_positions(remaining, now=now)
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def reorder_blocks(
        self, snapshot: PageSnapshot, ordered_ids: tuple[UUID, ...], *, now: datetime
    ) -> PageSnapshot:
        """Replace the complete draft block order after exact-set validation."""
        self._require_mutable(snapshot)
        rows = await self._block_rows(snapshot.draft.id, for_update=True)
        if len(ordered_ids) != len(set(ordered_ids)) or set(ordered_ids) != {
            row.id for row in rows
        }:
            raise PagePersistenceError
        by_id = {row.id: row for row in rows}
        await self._set_temporary_positions(rows)
        self._set_positions([by_id[item] for item in ordered_ids], now=now)
        await self._touch_page(snapshot.page.id, now=now)
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def publish(
        self,
        snapshot: PageSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> PageSnapshot:
        """Freeze the draft, point public state, and deep-copy one next draft."""
        self._require_mutable(snapshot)
        draft_row = await self._revision_row(snapshot.draft.id)
        draft_row.frozen = True
        draft_row.updated_at = now
        next_revision = PageRevisionRecord(
            id=next_revision_id,
            page_id=snapshot.page.id,
            revision_number=snapshot.draft.revision_number + 1,
            based_on_revision_id=snapshot.draft.id,
            title=draft_row.title,
            description=draft_row.description,
            seo_title=draft_row.seo_title,
            seo_description=draft_row.seo_description,
            canonical_url=draft_row.canonical_url,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(next_revision)
        await self._session.flush()
        for block in snapshot.draft.blocks:
            copy_id = self._id_factory()
            copy = PageBlockRecord(
                id=copy_id,
                revision_id=next_revision_id,
                block_type=block.values.block_type.value,
                schema_version=block.values.schema_version,
                position=block.position,
                visible=block.values.visible,
                title=block.values.title,
                subtitle=block.values.subtitle,
                description=block.values.description,
                theme=block.values.theme.value,
                layout=block.values.layout.value,
                responsive=self._responsive_json(block.values.responsive),
                config=dict(block.values.config),
                created_at=now,
                updated_at=now,
            )
            self._session.add(copy)
            for reference in block.references:
                self._session.add(self._reference_record(next_revision_id, copy_id, reference))
        page_row = await self._page_row(snapshot.page.id)
        page_row.published_revision_id = snapshot.draft.id
        page_row.draft_revision_id = next_revision_id
        page_row.publish_at = publish_at
        page_row.unpublished_at = None
        page_row.version += 1
        page_row.updated_at = now
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def reschedule(
        self, snapshot: PageSnapshot, *, publish_at: datetime, now: datetime
    ) -> PageSnapshot:
        """Change schedule metadata without touching frozen content."""
        if snapshot.page.published_revision_id is None:
            raise PagePersistenceError
        row = await self._page_row(snapshot.page.id)
        row.publish_at = publish_at
        row.version += 1
        row.updated_at = now
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def unpublish(self, snapshot: PageSnapshot, *, now: datetime) -> PageSnapshot:
        """Remove public eligibility while retaining all revision history."""
        row = await self._page_row(snapshot.page.id)
        row.published_revision_id = None
        row.publish_at = None
        row.unpublished_at = now
        row.version += 1
        row.updated_at = now
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def soft_delete(self, snapshot: PageSnapshot, *, now: datetime) -> PageSnapshot:
        """Soft-delete a custom page without releasing its reserved slug."""
        row = await self._page_row(snapshot.page.id)
        row.visible = False
        row.navigation_visible = False
        row.published_revision_id = None
        row.publish_at = None
        row.deleted_at = now
        row.version += 1
        row.updated_at = now
        await self._session.flush()
        return await self._required_snapshot(snapshot.page.id)

    async def _get_public(
        self, *, route_kind: PageRouteKind, slug: str | None
    ) -> PageSnapshot | None:
        predicate = PageRecord.route_kind == route_kind.value
        if route_kind is PageRouteKind.CUSTOM:
            predicate &= func.lower(PageRecord.slug) == cast("str", slug).casefold()
        row = (
            await self._session.execute(
                select(PageRecord).where(
                    predicate,
                    PageRecord.visible.is_(True),
                    PageRecord.deleted_at.is_(None),
                    PageRecord.published_revision_id.is_not(None),
                    PageRecord.publish_at.is_not(None),
                    PageRecord.publish_at <= func.now(),
                )
            )
        ).scalar_one_or_none()
        return None if row is None else await self._snapshot(row)

    async def _snapshot(self, row: PageRecord) -> PageSnapshot:
        draft = await self._revision(row.draft_revision_id)
        published = (
            None
            if row.published_revision_id is None
            else await self._revision(row.published_revision_id)
        )
        return PageSnapshot(self._page(row), draft, published)

    async def _revision(self, revision_id: UUID) -> PageRevision:
        row = await self._revision_row(revision_id)
        blocks = await self._block_rows(revision_id)
        values: list[PageBlock] = []
        for block in blocks:
            references = await self._reference_rows(block.id)
            values.append(self._block(block, references))
        return PageRevision(
            id=row.id,
            page_id=row.page_id,
            revision_number=row.revision_number,
            based_on_revision_id=row.based_on_revision_id,
            values=PageRevisionValues(
                row.title, row.description, row.seo_title, row.seo_description, row.canonical_url
            ),
            blocks=tuple(values),
            frozen=row.frozen,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def _page_row(self, page_id: UUID) -> PageRecord:
        row = await self._session.get(PageRecord, page_id)
        if row is None:
            raise PagePersistenceError
        return row

    async def _revision_row(self, revision_id: UUID) -> PageRevisionRecord:
        row = await self._session.get(PageRevisionRecord, revision_id)
        if row is None:
            raise PagePersistenceError
        return row

    async def _owned_block_row(self, revision_id: UUID, block_id: UUID) -> PageBlockRecord:
        row = (
            await self._session.execute(
                select(PageBlockRecord)
                .where(PageBlockRecord.id == block_id, PageBlockRecord.revision_id == revision_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise PagePersistenceError
        return row

    async def _block_rows(
        self, revision_id: UUID, *, for_update: bool = False
    ) -> list[PageBlockRecord]:
        statement = (
            select(PageBlockRecord)
            .where(PageBlockRecord.revision_id == revision_id)
            .order_by(PageBlockRecord.position, PageBlockRecord.id)
        )
        if for_update:
            statement = statement.with_for_update()
        return list((await self._session.execute(statement)).scalars())

    async def _reference_rows(self, block_id: UUID) -> list[PageBlockReferenceRecord]:
        return list(
            (
                await self._session.execute(
                    select(PageBlockReferenceRecord)
                    .where(PageBlockReferenceRecord.block_id == block_id)
                    .order_by(
                        PageBlockReferenceRecord.role,
                        PageBlockReferenceRecord.position,
                        PageBlockReferenceRecord.id,
                    )
                )
            ).scalars()
        )

    async def _required_snapshot(self, page_id: UUID) -> PageSnapshot:
        snapshot = await self.get_page(page_id)
        if snapshot is None:
            raise PagePersistenceError
        return snapshot

    async def _touch_page(self, page_id: UUID, *, now: datetime) -> None:
        row = await self._page_row(page_id)
        row.version += 1
        row.updated_at = now
        revision = await self._revision_row(row.draft_revision_id)
        revision.based_on_revision_id = None
        revision.updated_at = now

    async def _set_temporary_positions(self, rows: Sequence[PageBlockRecord]) -> None:
        offset = max((row.position for row in rows), default=-1) + 1
        for index, row in enumerate(rows):
            row.position = offset + index
        await self._session.flush()

    @staticmethod
    def _set_positions(rows: Sequence[PageBlockRecord], *, now: datetime) -> None:
        for position, row in enumerate(rows):
            row.position = position
            row.updated_at = now

    @staticmethod
    def _require_mutable(snapshot: PageSnapshot) -> None:
        if snapshot.draft.frozen:
            raise FrozenPageRevisionError

    async def _add_blocks(self, revision: PageRevision) -> None:
        for block in revision.blocks:
            self._session.add(self._block_record(block))
            self._session.add_all(self._reference_records(block))

    def _reference_records(self, block: PageBlock) -> list[PageBlockReferenceRecord]:
        return [
            self._reference_record(block.revision_id, block.id, item) for item in block.references
        ]

    def _reference_record(
        self, revision_id: UUID, block_id: UUID, item: BlockReference
    ) -> PageBlockReferenceRecord:
        return PageBlockReferenceRecord(
            id=self._id_factory(),
            revision_id=revision_id,
            block_id=block_id,
            reference_kind=item.kind.value,
            target_id=item.target_id,
            role=item.role.value,
            position=item.position,
            required=item.required,
        )

    @staticmethod
    def _responsive_json(value: ResponsiveValues) -> dict[str, object]:
        return {
            "hide_on_small": value.hide_on_small,
            "hide_on_large": value.hide_on_large,
            "density": value.density,
        }

    @classmethod
    def _page_record(cls, value: Page) -> PageRecord:
        return PageRecord(
            id=value.id,
            route_kind=value.route_kind.value,
            slug=value.slug,
            visible=value.visible,
            navigation_visible=value.navigation_visible,
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
    def _revision_record(value: PageRevision) -> PageRevisionRecord:
        return PageRevisionRecord(
            id=value.id,
            page_id=value.page_id,
            revision_number=value.revision_number,
            based_on_revision_id=value.based_on_revision_id,
            title=value.values.title,
            description=value.values.description,
            seo_title=value.values.seo_title,
            seo_description=value.values.seo_description,
            canonical_url=value.values.canonical_url,
            frozen=value.frozen,
            created_by=value.created_by,
            created_at=value.created_at,
            updated_at=value.updated_at,
        )

    @classmethod
    def _block_record(cls, value: PageBlock) -> PageBlockRecord:
        return PageBlockRecord(
            id=value.id,
            revision_id=value.revision_id,
            block_type=value.values.block_type.value,
            schema_version=value.values.schema_version,
            position=value.position,
            visible=value.values.visible,
            title=value.values.title,
            subtitle=value.values.subtitle,
            description=value.values.description,
            theme=value.values.theme.value,
            layout=value.values.layout.value,
            responsive=cls._responsive_json(value.values.responsive),
            config=dict(value.values.config),
            created_at=value.created_at,
            updated_at=value.updated_at,
        )

    @staticmethod
    def _apply_block_values(row: PageBlockRecord, value: PageBlockValues, *, now: datetime) -> None:
        row.block_type = value.block_type.value
        row.schema_version = value.schema_version
        row.visible = value.visible
        row.title = value.title
        row.subtitle = value.subtitle
        row.description = value.description
        row.theme = value.theme.value
        row.layout = value.layout.value
        row.responsive = PageRepository._responsive_json(value.responsive)
        row.config = dict(value.config)
        row.updated_at = now

    @staticmethod
    def _page(row: PageRecord) -> Page:
        return Page(
            id=row.id,
            route_kind=PageRouteKind(row.route_kind),
            slug=row.slug,
            visible=row.visible,
            navigation_visible=row.navigation_visible,
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
    def _block(row: PageBlockRecord, references: Sequence[PageBlockReferenceRecord]) -> PageBlock:
        responsive = row.responsive
        return PageBlock(
            id=row.id,
            revision_id=row.revision_id,
            position=row.position,
            values=PageBlockValues(
                block_type=BlockType(row.block_type),
                schema_version=row.schema_version,
                visible=row.visible,
                title=row.title,
                subtitle=row.subtitle,
                description=row.description,
                theme=BlockTheme(row.theme),
                layout=BlockLayout(row.layout),
                responsive=ResponsiveValues(
                    hide_on_small=bool(responsive.get("hide_on_small", False)),
                    hide_on_large=bool(responsive.get("hide_on_large", False)),
                    density=str(responsive.get("density", "comfortable")),
                ),
                config=dict(row.config),
            ),
            references=tuple(
                BlockReference(
                    kind=ReferenceKind(item.reference_kind),
                    target_id=item.target_id,
                    role=ReferenceRole(item.role),
                    position=item.position,
                    required=item.required,
                )
                for item in references
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
