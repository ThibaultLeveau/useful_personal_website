"""SQLAlchemy records for immutable revisioned blog articles and taxonomy."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BlogBase(DeclarativeBase):
    """SQLAlchemy registry for the M7 blog slice."""


class PostRecord(BlogBase):
    """Stable post route identity, publication pointers, and display state."""

    __tablename__ = "post"
    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="post_slug_format"),
        CheckConstraint("length(slug) BETWEEN 1 AND 80", name="post_slug_length"),
        CheckConstraint("position >= 0", name="post_nonnegative_position"),
        CheckConstraint("version > 0", name="post_positive_version"),
        CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="post_publication_pointer_schedule_pair",
        ),
        CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="post_distinct_draft_published_pointers",
        ),
        ForeignKeyConstraint(
            ["id", "draft_revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_post_draft_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["id", "published_revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_post_published_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index("uq_post_slug_ci", text("lower(slug)"), unique=True),
        Index("ix_post_admin_order", "position", "id", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_post_slug_lookup", "slug", postgresql_where=text("deleted_at IS NULL")),
        Index(
            "ix_post_effective_public",
            text("publish_at DESC"),
            "id",
            postgresql_where=text(
                "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    slug: Mapped[str] = mapped_column(String(80))
    visible: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int] = mapped_column(Integer)
    draft_revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    published_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PostRevisionRecord(BlogBase):
    """Revision-owned canonical article content and derivation provenance."""

    __tablename__ = "post_revision"
    __table_args__ = (
        CheckConstraint("revision_number > 0", name="post_revision_positive_number"),
        CheckConstraint(
            "length(title) BETWEEN 1 AND 180 AND title = btrim(title)",
            name="post_revision_title",
        ),
        CheckConstraint(
            "length(excerpt) BETWEEN 1 AND 500 AND excerpt = btrim(excerpt)",
            name="post_revision_excerpt",
        ),
        CheckConstraint(
            "length(source) BETWEEN 1 AND 100000",
            name="post_revision_source_length",
        ),
        CheckConstraint(
            "length(author_display) BETWEEN 1 AND 180 AND author_display = btrim(author_display)",
            name="post_revision_author_display",
        ),
        CheckConstraint(
            "reading_minutes BETWEEN 1 AND 240",
            name="post_revision_reading_minutes",
        ),
        CheckConstraint(
            "content_checksum ~ '^[0-9a-f]{64}$'",
            name="post_revision_content_checksum",
        ),
        CheckConstraint(
            "length(content_policy_name) BETWEEN 1 AND 80",
            name="post_revision_content_policy_name",
        ),
        CheckConstraint(
            "length(content_policy_version) BETWEEN 1 AND 32",
            name="post_revision_content_policy_version",
        ),
        CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="post_revision_seo_title",
        ),
        CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="post_revision_seo_description",
        ),
        CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) AND canonical_url LIKE 'https://%')",
            name="post_revision_https_canonical_url",
        ),
        UniqueConstraint("post_id", "revision_number", name="uq_post_revision_number"),
        UniqueConstraint("post_id", "id", name="uq_post_revision_owner_target"),
        ForeignKeyConstraint(
            ["post_id", "based_on_revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_post_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_post_revision_created_by_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["cover_media_id"],
            ["media_asset.id"],
            name="fk_post_revision_cover_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_post_revision_post_number", "post_id", "revision_number"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    post_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("post.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    based_on_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(180))
    excerpt: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(Text)
    author_display: Mapped[str] = mapped_column(String(180))
    reading_minutes: Mapped[int] = mapped_column(Integer)
    content_checksum: Mapped[str] = mapped_column(String(64))
    content_policy_name: Mapped[str] = mapped_column(String(80))
    content_policy_version: Mapped[str] = mapped_column(String(32))
    seo_title: Mapped[str | None] = mapped_column(String(70))
    seo_description: Mapped[str | None] = mapped_column(String(180))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    cover_media_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    frozen: Mapped[bool] = mapped_column(Boolean)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class _TaxonomyRecord:
    id: Mapped[UUID]
    name: Mapped[str]
    slug: Mapped[str]
    position: Mapped[int]
    visible: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int]
    deleted_at: Mapped[datetime | None]


def _taxonomy_constraints(prefix: str) -> tuple[object, ...]:
    return (
        CheckConstraint(
            "length(name) BETWEEN 1 AND 80 AND name = btrim(name)",
            name=f"{prefix}_name",
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' AND length(slug) BETWEEN 1 AND 80",
            name=f"{prefix}_slug",
        ),
        CheckConstraint("position >= 0", name=f"{prefix}_nonnegative_position"),
        CheckConstraint("version > 0", name=f"{prefix}_positive_version"),
        Index(f"uq_{prefix}_slug_ci", text("lower(slug)"), unique=True),
        Index(
            f"ix_{prefix}_public_order",
            "position",
            "id",
            postgresql_where=text("visible AND deleted_at IS NULL"),
        ),
    )


class TagRecord(_TaxonomyRecord, BlogBase):
    """Stable ordered blog tag."""

    __tablename__ = "tag"
    __table_args__ = _taxonomy_constraints("tag")

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    visible: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PostCategoryRecord(_TaxonomyRecord, BlogBase):
    """Stable ordered blog category."""

    __tablename__ = "post_category"
    __table_args__ = _taxonomy_constraints("post_category")

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    visible: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PostTagRecord(BlogBase):
    """One ordered revision-scoped tag reference."""

    __tablename__ = "post_tag"
    __table_args__ = (
        CheckConstraint("position >= 0", name="post_tag_nonnegative_position"),
        UniqueConstraint("revision_id", "tag_id", name="uq_post_tag_revision_tag"),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_post_tag_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index("ix_post_tag_revision_order", "revision_id", "position", "id"),
        Index("ix_post_tag_tag_revision", "tag_id", "revision_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("post_revision.id", ondelete="CASCADE")
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tag.id", ondelete="RESTRICT")
    )
    position: Mapped[int] = mapped_column(Integer)


class PostCategoryLinkRecord(BlogBase):
    """One ordered revision-scoped category reference."""

    __tablename__ = "post_category_link"
    __table_args__ = (
        CheckConstraint("position >= 0", name="post_category_link_nonnegative_position"),
        UniqueConstraint(
            "revision_id",
            "category_id",
            name="uq_post_category_link_revision_category",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_post_category_link_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index("ix_post_category_link_revision_order", "revision_id", "position", "id"),
        Index("ix_post_category_link_category_revision", "category_id", "revision_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("post_revision.id", ondelete="CASCADE")
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("post_category.id", ondelete="RESTRICT")
    )
    position: Mapped[int] = mapped_column(Integer)


class RelatedPostRecord(BlogBase):
    """One ordered stable-ID edge to another post."""

    __tablename__ = "related_post"
    __table_args__ = (
        CheckConstraint("position >= 0", name="related_post_nonnegative_position"),
        CheckConstraint("post_id <> related_post_id", name="related_post_not_self"),
        UniqueConstraint(
            "revision_id",
            "related_post_id",
            name="uq_related_post_revision_target",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_related_post_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["post_id", "revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_related_post_revision_owner",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["related_post_id"],
            ["post.id"],
            name="fk_related_post_target_post",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_related_post_revision_order", "revision_id", "position", "id"),
        Index("ix_related_post_target_revision", "related_post_id", "revision_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    post_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    related_post_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)
