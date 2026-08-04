"""Add revision-safe blog posts and taxonomy.

Revision ID: 20260802_0008
Revises: 20260802_0007
Create Date: 2026-08-04 15:00:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0008"
down_revision: str | None = "20260802_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_taxonomy(table_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 80 AND name = btrim(name)",
            name=f"{table_name}_name",
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' AND length(slug) BETWEEN 1 AND 80",
            name=f"{table_name}_slug",
        ),
        sa.CheckConstraint("position >= 0", name=f"{table_name}_nonnegative_position"),
        sa.CheckConstraint("version > 0", name=f"{table_name}_positive_version"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
    )
    op.create_index(
        f"uq_{table_name}_slug_ci",
        table_name,
        [sa.text("lower(slug)")],
        unique=True,
    )
    op.create_index(
        f"ix_{table_name}_public_order",
        table_name,
        ["position", "id"],
        postgresql_where=sa.text("visible AND deleted_at IS NULL"),
    )


def _create_revision_relation(
    *,
    table_name: str,
    target_column: str,
    target_table: str,
    target_label: str,
) -> None:
    op.create_table(
        table_name,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(target_column, postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name=f"{table_name}_nonnegative_position"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["post_revision.id"],
            name=f"fk_{table_name}_revision_id_post_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [target_column],
            [f"{target_table}.id"],
            name=f"fk_{table_name}_{target_column}_{target_table}",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
        sa.UniqueConstraint(
            "revision_id",
            target_column,
            name=f"uq_{table_name}_revision_{target_label}",
        ),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name=f"uq_{table_name}_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        f"ix_{table_name}_revision_order",
        table_name,
        ["revision_id", "position", "id"],
    )
    op.create_index(
        f"ix_{table_name}_{target_label}_revision",
        table_name,
        [target_column, "revision_id"],
    )


def upgrade() -> None:
    """Create the sole M7 blog aggregate, revision, taxonomy, and relation schema."""
    _create_taxonomy("tag")
    _create_taxonomy("post_category")
    op.create_table(
        "post",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("draft_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="post_slug_format"),
        sa.CheckConstraint("length(slug) BETWEEN 1 AND 80", name="post_slug_length"),
        sa.CheckConstraint("position >= 0", name="post_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="post_positive_version"),
        sa.CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="post_publication_pointer_schedule_pair",
        ),
        sa.CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="post_distinct_draft_published_pointers",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_post"),
    )
    op.create_index("uq_post_slug_ci", "post", [sa.text("lower(slug)")], unique=True)
    op.create_index(
        "ix_post_admin_order",
        "post",
        ["position", "id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_post_slug_lookup",
        "post",
        ["slug"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_post_effective_public",
        "post",
        [sa.text("publish_at DESC"), "id"],
        postgresql_where=sa.text(
            "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
        ),
    )
    op.create_table(
        "post_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("based_on_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("excerpt", sa.String(length=500), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("author_display", sa.String(length=180), nullable=False),
        sa.Column("reading_minutes", sa.Integer(), nullable=False),
        sa.Column("content_checksum", sa.String(length=64), nullable=False),
        sa.Column("content_policy_name", sa.String(length=80), nullable=False),
        sa.Column("content_policy_version", sa.String(length=32), nullable=False),
        sa.Column("seo_title", sa.String(length=70), nullable=True),
        sa.Column("seo_description", sa.String(length=180), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("frozen", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision_number > 0", name="post_revision_positive_number"),
        sa.CheckConstraint(
            "length(title) BETWEEN 1 AND 180 AND title = btrim(title)",
            name="post_revision_title",
        ),
        sa.CheckConstraint(
            "length(excerpt) BETWEEN 1 AND 500 AND excerpt = btrim(excerpt)",
            name="post_revision_excerpt",
        ),
        sa.CheckConstraint(
            "length(source) BETWEEN 1 AND 100000",
            name="post_revision_source_length",
        ),
        sa.CheckConstraint(
            "length(author_display) BETWEEN 1 AND 180 AND author_display = btrim(author_display)",
            name="post_revision_author_display",
        ),
        sa.CheckConstraint(
            "reading_minutes BETWEEN 1 AND 240",
            name="post_revision_reading_minutes",
        ),
        sa.CheckConstraint(
            "content_checksum ~ '^[0-9a-f]{64}$'",
            name="post_revision_content_checksum",
        ),
        sa.CheckConstraint(
            "length(content_policy_name) BETWEEN 1 AND 80",
            name="post_revision_content_policy_name",
        ),
        sa.CheckConstraint(
            "length(content_policy_version) BETWEEN 1 AND 32",
            name="post_revision_content_policy_version",
        ),
        sa.CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="post_revision_seo_title",
        ),
        sa.CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="post_revision_seo_description",
        ),
        sa.CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) AND canonical_url LIKE 'https://%')",
            name="post_revision_https_canonical_url",
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
            name="fk_post_revision_post_id_post",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["post_id", "based_on_revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_post_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_post_revision_created_by_administrator",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_post_revision"),
        sa.UniqueConstraint("post_id", "revision_number", name="uq_post_revision_number"),
        sa.UniqueConstraint("post_id", "id", name="uq_post_revision_owner_target"),
    )
    op.create_index(
        "ix_post_revision_post_number",
        "post_revision",
        ["post_id", "revision_number"],
    )
    op.create_foreign_key(
        "fk_post_draft_pointer",
        "post",
        "post_revision",
        ["id", "draft_revision_id"],
        ["post_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_post_published_pointer",
        "post",
        "post_revision",
        ["id", "published_revision_id"],
        ["post_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    _create_revision_relation(
        table_name="post_tag",
        target_column="tag_id",
        target_table="tag",
        target_label="tag",
    )
    _create_revision_relation(
        table_name="post_category_link",
        target_column="category_id",
        target_table="post_category",
        target_label="category",
    )
    op.create_table(
        "related_post",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="related_post_nonnegative_position"),
        sa.CheckConstraint("post_id <> related_post_id", name="related_post_not_self"),
        sa.ForeignKeyConstraint(
            ["post_id", "revision_id"],
            ["post_revision.post_id", "post_revision.id"],
            name="fk_related_post_revision_owner",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["related_post_id"],
            ["post.id"],
            name="fk_related_post_target_post",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_related_post"),
        sa.UniqueConstraint(
            "revision_id",
            "related_post_id",
            name="uq_related_post_revision_target",
        ),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name="uq_related_post_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        "ix_related_post_revision_order",
        "related_post",
        ["revision_id", "position", "id"],
    )
    op.create_index(
        "ix_related_post_target_revision",
        "related_post",
        ["related_post_id", "revision_id"],
    )
    _create_frozen_revision_guards()


def _create_frozen_revision_guards() -> None:
    op.execute(
        """
        CREATE FUNCTION reject_frozen_post_revision_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            target_revision uuid;
            target_frozen boolean;
        BEGIN
            IF TG_TABLE_NAME = 'post_revision' THEN
                target_frozen := OLD.frozen;
            ELSE
                target_revision := OLD.revision_id;
                SELECT frozen INTO target_frozen
                FROM post_revision WHERE id = target_revision;
            END IF;
            IF target_frozen THEN
                RAISE EXCEPTION 'frozen post revisions are immutable'
                    USING ERRCODE = '55000';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$
        """
    )
    for table_name in (
        "post_revision",
        "post_tag",
        "post_category_link",
        "related_post",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table_name}_reject_frozen_mutation "
            f"BEFORE UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION reject_frozen_post_revision_mutation()"
        )


def downgrade() -> None:
    """Remove the M7 blog slice in dependency-safe order."""
    for table_name in (
        "related_post",
        "post_category_link",
        "post_tag",
        "post_revision",
    ):
        op.execute(f"DROP TRIGGER trg_{table_name}_reject_frozen_mutation ON {table_name}")
    op.execute("DROP FUNCTION reject_frozen_post_revision_mutation()")
    op.drop_table("related_post")
    op.drop_table("post_category_link")
    op.drop_table("post_tag")
    op.drop_constraint("fk_post_published_pointer", "post", type_="foreignkey")
    op.drop_constraint("fk_post_draft_pointer", "post", type_="foreignkey")
    op.drop_table("post_revision")
    op.drop_table("post")
    op.drop_table("post_category")
    op.drop_table("tag")
