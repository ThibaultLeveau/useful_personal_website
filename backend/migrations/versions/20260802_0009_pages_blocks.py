"""Add immutable configurable pages, blocks, and normalized references.

Revision ID: 20260802_0009
Revises: 20260802_0008
Create Date: 2026-08-04 18:00:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0009"
down_revision: str | None = "20260802_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RESERVED = (
    "admin",
    "api",
    "_next",
    "about",
    "experience",
    "experiences",
    "skills",
    "projects",
    "blog",
    "contact",
    "privacy",
    "legal",
    "robots.txt",
    "sitemap.xml",
    "favicon.ico",
    "assets",
    "media",
    "health",
    "docs",
    "openapi.json",
)


def upgrade() -> None:
    """Create the accepted M8 relational shell and immutable child guards."""
    op.create_table(
        "page",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("route_kind", sa.String(length=16), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=True),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("navigation_visible", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("draft_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("route_kind IN ('home','custom')", name="page_route_kind_catalog"),
        sa.CheckConstraint(
            "(route_kind = 'home' AND slug IS NULL) OR "
            "(route_kind = 'custom' AND slug IS NOT NULL)",
            name="page_route_slug_shape",
        ),
        sa.CheckConstraint(
            "slug IS NULL OR (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' AND length(slug) BETWEEN 1 AND 80)",
            name="page_slug_format",
        ),
        sa.CheckConstraint(
            "slug IS NULL OR lower(slug) NOT IN ("
            + ",".join(f"'{item}'" for item in _RESERVED)
            + ")",
            name="page_slug_not_reserved",
        ),
        sa.CheckConstraint("position >= 0", name="page_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="page_positive_version"),
        sa.CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="page_publication_pointer_schedule_pair",
        ),
        sa.CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="page_distinct_revision_pointers",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page"),
    )
    op.create_index(
        "uq_page_home_singleton",
        "page",
        ["route_kind"],
        unique=True,
        postgresql_where=sa.text("route_kind = 'home'"),
    )
    op.create_index(
        "uq_page_custom_slug_ci",
        "page",
        [sa.text("lower(slug)")],
        unique=True,
        postgresql_where=sa.text("route_kind = 'custom'"),
    )
    op.create_index("ix_page_admin_order", "page", ["position", "id"])
    op.create_index(
        "ix_page_effective_public",
        "page",
        ["route_kind", "slug"],
        postgresql_where=sa.text(
            "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
        ),
    )

    op.create_table(
        "page_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("based_on_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("seo_title", sa.String(length=70), nullable=True),
        sa.Column("seo_description", sa.String(length=180), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("frozen", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision_number > 0", name="page_revision_positive_number"),
        sa.CheckConstraint(
            "length(title) BETWEEN 1 AND 180 AND title = btrim(title)",
            name="page_revision_title",
        ),
        sa.CheckConstraint(
            "length(description) BETWEEN 1 AND 500 AND description = btrim(description)",
            name="page_revision_description",
        ),
        sa.CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="page_revision_seo_title",
        ),
        sa.CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="page_revision_seo_description",
        ),
        sa.CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) AND canonical_url LIKE 'https://%')",
            name="page_revision_https_canonical_url",
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["page.id"],
            name="fk_page_revision_page_id_page",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["page_id", "based_on_revision_id"],
            ["page_revision.page_id", "page_revision.id"],
            name="fk_page_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_page_revision_created_by_administrator",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page_revision"),
        sa.UniqueConstraint("page_id", "revision_number", name="uq_page_revision_number"),
        sa.UniqueConstraint("page_id", "id", name="uq_page_revision_owner_target"),
    )
    op.create_index("ix_page_revision_page_number", "page_revision", ["page_id", "revision_number"])
    op.create_foreign_key(
        "fk_page_draft_pointer",
        "page",
        "page_revision",
        ["id", "draft_revision_id"],
        ["page_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_page_published_pointer",
        "page",
        "page_revision",
        ["id", "published_revision_id"],
        ["page_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )

    op.create_table(
        "page_block",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_type", sa.String(length=40), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=True),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("theme", sa.String(length=20), nullable=False),
        sa.Column("layout", sa.String(length=20), nullable=False),
        sa.Column("responsive", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position >= 0", name="page_block_nonnegative_position"),
        sa.CheckConstraint("schema_version > 0", name="page_block_positive_schema_version"),
        sa.CheckConstraint(
            "block_type IN ('hero','profile_summary','call_to_action','statistics',"
            "'skills_grid','featured_skills','experience_summary','experience_list',"
            "'project_grid','featured_projects','latest_posts','rich_text','image',"
            "'image_with_text','links_collection','contact_callout','testimonial',"
            "'divider','spacer')",
            name="page_block_type_catalog",
        ),
        sa.CheckConstraint(
            "theme IN ('default','accent','muted','contrast')",
            name="page_block_theme_catalog",
        ),
        sa.CheckConstraint(
            "layout IN ('contained','wide','full')", name="page_block_layout_catalog"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(config) = 'object' AND pg_column_size(config) <= 32768",
            name="page_block_config_bounds",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(responsive) = 'object' AND pg_column_size(responsive) <= 1024",
            name="page_block_responsive_bounds",
        ),
        sa.CheckConstraint(
            "title IS NULL OR (length(title) BETWEEN 1 AND 180 AND title = btrim(title))",
            name="page_block_title",
        ),
        sa.CheckConstraint(
            "subtitle IS NULL OR (length(subtitle) BETWEEN 1 AND 240 "
            "AND subtitle = btrim(subtitle))",
            name="page_block_subtitle",
        ),
        sa.CheckConstraint(
            "description IS NULL OR (length(description) BETWEEN 1 AND 500 "
            "AND description = btrim(description))",
            name="page_block_description",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["page_revision.id"],
            name="fk_page_block_revision_id_page_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page_block"),
        sa.UniqueConstraint("revision_id", "position", name="uq_page_block_revision_position"),
        sa.UniqueConstraint("revision_id", "id", name="uq_page_block_revision_owner_target"),
    )
    op.create_index("ix_page_block_revision_order", "page_block", ["revision_id", "position", "id"])

    op.create_table(
        "page_block_reference",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_kind", sa.String(length=32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.CheckConstraint("position >= 0", name="page_block_reference_nonnegative_position"),
        sa.CheckConstraint(
            "reference_kind IN ('profile','skill','experience','project','post','page','media')",
            name="page_block_reference_kind_catalog",
        ),
        sa.CheckConstraint(
            "role IN ('profile_evidence','skill_item','experience_item','project_item',"
            "'post_item','internal_destination','media_primary')",
            name="page_block_reference_role_catalog",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "block_id"],
            ["page_block.revision_id", "page_block.id"],
            name="fk_page_block_reference_block_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page_block_reference"),
        sa.UniqueConstraint(
            "block_id",
            "role",
            "position",
            name="uq_page_block_reference_role_position",
        ),
        sa.UniqueConstraint(
            "block_id",
            "reference_kind",
            "role",
            "target_id",
            name="uq_page_block_reference_target",
        ),
    )
    op.create_index(
        "ix_page_block_reference_revision_kind",
        "page_block_reference",
        ["revision_id", "reference_kind", "position"],
    )
    op.create_index(
        "ix_page_block_reference_target",
        "page_block_reference",
        ["reference_kind", "target_id"],
    )
    _create_frozen_revision_guards()


def _create_frozen_revision_guards() -> None:
    op.execute(
        """
        CREATE FUNCTION reject_frozen_page_revision_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            old_revision uuid;
            new_revision uuid;
            old_frozen boolean := false;
            new_frozen boolean := false;
        BEGIN
            IF TG_TABLE_NAME = 'page_revision' THEN
                old_frozen := OLD.frozen;
            ELSE
                IF TG_OP <> 'INSERT' THEN
                    old_revision := OLD.revision_id;
                    SELECT frozen INTO old_frozen FROM page_revision WHERE id = old_revision;
                END IF;
                IF TG_OP <> 'DELETE' THEN
                    new_revision := NEW.revision_id;
                    SELECT frozen INTO new_frozen FROM page_revision WHERE id = new_revision;
                END IF;
            END IF;
            IF old_frozen OR new_frozen THEN
                RAISE EXCEPTION 'frozen page revisions are immutable'
                    USING ERRCODE = '55000';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_page_revision_reject_frozen_mutation "
        "BEFORE UPDATE OR DELETE ON page_revision "
        "FOR EACH ROW EXECUTE FUNCTION reject_frozen_page_revision_mutation()"
    )
    for table_name in ("page_block", "page_block_reference"):
        op.execute(
            f"CREATE TRIGGER trg_{table_name}_reject_frozen_mutation "
            f"BEFORE INSERT OR UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION reject_frozen_page_revision_mutation()"
        )


def downgrade() -> None:
    """Remove the M8 page slice in dependency-safe order."""
    for table_name in ("page_block_reference", "page_block"):
        op.execute(f"DROP TRIGGER trg_{table_name}_reject_frozen_mutation ON {table_name}")
    op.execute("DROP TRIGGER trg_page_revision_reject_frozen_mutation ON page_revision")
    op.execute("DROP FUNCTION reject_frozen_page_revision_mutation()")
    op.drop_table("page_block_reference")
    op.drop_table("page_block")
    op.drop_constraint("fk_page_published_pointer", "page", type_="foreignkey")
    op.drop_constraint("fk_page_draft_pointer", "page", type_="foreignkey")
    op.drop_table("page_revision")
    op.drop_table("page")
