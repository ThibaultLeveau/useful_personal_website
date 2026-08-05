"""Add secure private image media, variants, usage, and accepted owner references.

Revision ID: 20260802_0010
Revises: 20260802_0009
Create Date: 2026-08-04 21:00:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0010"
down_revision: str | None = "20260802_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the sole M9 media schema and exact S1 owner reference shell."""
    _create_asset_table()
    _create_variant_table()
    _create_usage_table()
    _activate_owner_reference_shell()
    _create_ready_reference_guards()
    _create_usage_delete_guard()


def _create_asset_table() -> None:
    op.create_table(
        "media_asset",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("detected_format", sa.String(length=8), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("original_key", sa.String(length=200), nullable=True),
        sa.Column("quarantine_key", sa.String(length=200), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('quarantined','processing','ready','failed','deleting','deleted')",
            name="media_asset_status_catalog",
        ),
        sa.CheckConstraint(
            "detected_format IS NULL OR detected_format IN ('jpeg','png','webp')",
            name="media_asset_format_catalog",
        ),
        sa.CheckConstraint("version > 0", name="media_asset_positive_version"),
        sa.CheckConstraint(
            "length(display_name) BETWEEN 1 AND 180",
            name="media_asset_display_name_bounds",
        ),
        sa.CheckConstraint(
            "width IS NULL OR width BETWEEN 1 AND 6000",
            name="media_asset_width_bounds",
        ),
        sa.CheckConstraint(
            "height IS NULL OR height BETWEEN 1 AND 6000",
            name="media_asset_height_bounds",
        ),
        sa.CheckConstraint(
            "byte_size IS NULL OR byte_size BETWEEN 1 AND 10485760",
            name="media_asset_byte_size_bounds",
        ),
        sa.CheckConstraint(
            "checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="media_asset_checksum_shape",
        ),
        sa.CheckConstraint(
            "(status <> 'ready') OR "
            "(detected_format IS NOT NULL AND width IS NOT NULL AND height IS NOT NULL "
            "AND byte_size IS NOT NULL AND checksum_sha256 IS NOT NULL "
            "AND original_key IS NOT NULL AND quarantine_key IS NULL)",
            name="media_asset_ready_shape",
        ),
        sa.CheckConstraint(
            "(status IN ('deleting','deleted')) = (deleted_at IS NOT NULL)",
            name="media_asset_tombstone_shape",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_media_asset_created_by_administrator",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_asset"),
        sa.UniqueConstraint("original_key", name="uq_media_asset_original_key"),
        sa.UniqueConstraint("quarantine_key", name="uq_media_asset_quarantine_key"),
    )
    op.create_index("ix_media_asset_admin_order", "media_asset", ["created_at", "id"])
    op.create_index("ix_media_asset_status_updated", "media_asset", ["status", "updated_at", "id"])
    op.create_index("ix_media_asset_checksum", "media_asset", ["checksum_sha256"])


def _create_variant_table() -> None:
    op.create_table(
        "media_variant",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.String(length=24), nullable=False),
        sa.Column("format", sa.String(length=8), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('responsive_webp','responsive_fallback')",
            name="media_variant_purpose_catalog",
        ),
        sa.CheckConstraint("format IN ('jpeg','png','webp')", name="media_variant_format_catalog"),
        sa.CheckConstraint(
            "width BETWEEN 1 AND 6000 AND height BETWEEN 1 AND 6000",
            name="media_variant_dimension_bounds",
        ),
        sa.CheckConstraint(
            "byte_size BETWEEN 1 AND 10485760",
            name="media_variant_byte_size_bounds",
        ),
        sa.CheckConstraint(
            "checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="media_variant_checksum_shape",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["media_asset.id"],
            name="fk_media_variant_asset_id_media_asset",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_variant"),
        sa.UniqueConstraint("asset_id", "purpose", "width", name="uq_media_variant_catalog"),
        sa.UniqueConstraint("storage_key", name="uq_media_variant_storage_key"),
    )
    op.create_index(
        "ix_media_variant_asset_width", "media_variant", ["asset_id", "width", "purpose"]
    )


def _create_usage_table() -> None:
    op.create_table(
        "media_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=16), nullable=False),
        sa.Column("alt_text", sa.String(length=300), nullable=True),
        sa.Column("caption", sa.String(length=500), nullable=True),
        sa.Column("focal_x", sa.Integer(), nullable=False),
        sa.Column("focal_y", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("public", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "owner_type IN ('profile','website_settings','project_revision',"
            "'blog_post_revision','page_block')",
            name="media_usage_owner_catalog",
        ),
        sa.CheckConstraint(
            "role IN ('profile_image','site_logo','site_favicon','site_social_image',"
            "'project_cover','project_screenshot','blog_cover','page_primary')",
            name="media_usage_role_catalog",
        ),
        sa.CheckConstraint(
            "purpose IN ('meaningful','decorative')",
            name="media_usage_purpose_catalog",
        ),
        sa.CheckConstraint("position >= 0", name="media_usage_nonnegative_position"),
        sa.CheckConstraint(
            "focal_x BETWEEN 0 AND 100 AND focal_y BETWEEN 0 AND 100",
            name="media_usage_focal_bounds",
        ),
        sa.CheckConstraint(
            "alt_text IS NULL OR length(alt_text) <= 300",
            name="media_usage_alt_bounds",
        ),
        sa.CheckConstraint(
            "caption IS NULL OR length(caption) BETWEEN 1 AND 500",
            name="media_usage_caption_bounds",
        ),
        sa.CheckConstraint(
            "(purpose = 'decorative' AND alt_text = '') OR "
            "(purpose = 'meaningful' AND length(alt_text) > 0)",
            name="media_usage_accessibility_shape",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["media_asset.id"],
            name="fk_media_usage_asset_id_media_asset",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_usage"),
        sa.UniqueConstraint(
            "owner_type",
            "owner_id",
            "role",
            "position",
            name="uq_media_usage_owner_role_pos",
        ),
    )
    op.create_index("ix_media_usage_asset_active", "media_usage", ["asset_id", "active", "public"])
    op.create_index("ix_media_usage_owner", "media_usage", ["owner_type", "owner_id"])


def _activate_owner_reference_shell() -> None:
    for table_name, column_name, constraint_name in (
        ("profile", "profile_image_id", "fk_profile_image_media_asset"),
        ("website_settings", "logo_media_id", "fk_website_settings_logo_media_asset"),
        ("website_settings", "favicon_media_id", "fk_website_settings_favicon_media_asset"),
        (
            "website_settings",
            "social_image_media_id",
            "fk_website_settings_social_image_media_asset",
        ),
    ):
        op.create_foreign_key(
            constraint_name,
            table_name,
            "media_asset",
            [column_name],
            ["id"],
            ondelete="RESTRICT",
        )

    op.create_table(
        "project_revision_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "role IN ('project_cover','project_screenshot')",
            name="project_revision_media_role_catalog",
        ),
        sa.CheckConstraint(
            "position >= 0 AND (role <> 'project_cover' OR position = 0)",
            name="project_revision_media_position_shape",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["project_revision.id"],
            name="fk_project_revision_media_revision_id_project_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media_asset.id"],
            name="fk_project_revision_media_media_id_media_asset",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_revision_media"),
        sa.UniqueConstraint(
            "revision_id", "role", "position", name="uq_project_revision_media_role_position"
        ),
        sa.UniqueConstraint(
            "revision_id", "role", "media_id", name="uq_project_revision_media_role_asset"
        ),
    )
    op.create_index(
        "ix_project_revision_media_revision_order",
        "project_revision_media",
        ["revision_id", "role", "position", "id"],
    )
    op.create_index(
        "ix_project_revision_media_asset", "project_revision_media", ["media_id", "revision_id"]
    )
    op.execute(
        "CREATE TRIGGER trg_project_revision_media_reject_frozen_mutation "
        "BEFORE INSERT OR UPDATE OR DELETE ON project_revision_media "
        "FOR EACH ROW EXECUTE FUNCTION reject_frozen_project_revision_mutation()"
    )

    op.add_column(
        "post_revision",
        sa.Column("cover_media_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_post_revision_cover_media_asset",
        "post_revision",
        "media_asset",
        ["cover_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def _create_ready_reference_guards() -> None:
    op.execute(
        """
        CREATE FUNCTION require_ready_media_asset()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            media_target uuid;
            target_status text;
        BEGIN
            IF TG_TABLE_NAME = 'profile' THEN
                media_target := NEW.profile_image_id;
            ELSIF TG_TABLE_NAME = 'website_settings' THEN
                IF TG_ARGV[0] = 'logo' THEN media_target := NEW.logo_media_id;
                ELSIF TG_ARGV[0] = 'favicon' THEN media_target := NEW.favicon_media_id;
                ELSE media_target := NEW.social_image_media_id;
                END IF;
            ELSIF TG_TABLE_NAME = 'post_revision' THEN
                media_target := NEW.cover_media_id;
            ELSIF TG_TABLE_NAME = 'project_revision_media' THEN
                media_target := NEW.media_id;
            ELSIF TG_TABLE_NAME = 'page_block_reference' THEN
                IF NEW.reference_kind <> 'media' THEN RETURN NEW; END IF;
                media_target := NEW.target_id;
            ELSE
                media_target := NEW.asset_id;
            END IF;
            IF media_target IS NULL THEN RETURN NEW; END IF;
            SELECT status INTO target_status FROM media_asset WHERE id = media_target;
            IF target_status IS DISTINCT FROM 'ready' THEN
                RAISE EXCEPTION 'media reference requires a ready asset'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    trigger_specs = (
        ("profile", "profile_image", ""),
        ("website_settings", "settings_logo", "logo"),
        ("website_settings", "settings_favicon", "favicon"),
        ("website_settings", "settings_social", "social"),
        ("project_revision_media", "project_revision_media", ""),
        ("post_revision", "post_cover", ""),
        ("page_block_reference", "page_block_media", ""),
        ("media_usage", "media_usage", ""),
    )
    for table_name, trigger_label, argument in trigger_specs:
        suffix = f"('{argument}')" if argument else "()"
        op.execute(
            f"CREATE TRIGGER trg_{trigger_label}_require_ready "
            f"BEFORE INSERT OR UPDATE ON {table_name} "
            f"FOR EACH ROW EXECUTE FUNCTION require_ready_media_asset{suffix}"
        )


def _create_usage_delete_guard() -> None:
    op.execute(
        """
        CREATE FUNCTION reject_used_media_tombstone()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.status IN ('deleting','deleted')
               AND OLD.status NOT IN ('deleting','deleted')
               AND EXISTS (
                   SELECT 1 FROM media_usage
                   WHERE asset_id = NEW.id AND active
               ) THEN
                RAISE EXCEPTION 'active media usage blocks deletion'
                    USING ERRCODE = '55000';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_media_asset_reject_used_tombstone "
        "BEFORE UPDATE OF status ON media_asset "
        "FOR EACH ROW EXECUTE FUNCTION reject_used_media_tombstone()"
    )


def downgrade() -> None:
    """Remove M9 owner references and media tables in dependency-safe order."""
    op.execute("DROP TRIGGER trg_media_asset_reject_used_tombstone ON media_asset")
    op.execute("DROP FUNCTION reject_used_media_tombstone()")
    for table_name, trigger_label in (
        ("media_usage", "media_usage"),
        ("page_block_reference", "page_block_media"),
        ("post_revision", "post_cover"),
        ("project_revision_media", "project_revision_media"),
        ("website_settings", "settings_social"),
        ("website_settings", "settings_favicon"),
        ("website_settings", "settings_logo"),
        ("profile", "profile_image"),
    ):
        op.execute(f"DROP TRIGGER trg_{trigger_label}_require_ready ON {table_name}")
    op.execute("DROP FUNCTION require_ready_media_asset()")
    op.drop_constraint("fk_post_revision_cover_media_asset", "post_revision", type_="foreignkey")
    op.drop_column("post_revision", "cover_media_id")
    op.execute(
        "DROP TRIGGER trg_project_revision_media_reject_frozen_mutation ON project_revision_media"
    )
    op.drop_table("project_revision_media")
    for table_name, constraint_name in (
        ("website_settings", "fk_website_settings_social_image_media_asset"),
        ("website_settings", "fk_website_settings_favicon_media_asset"),
        ("website_settings", "fk_website_settings_logo_media_asset"),
        ("profile", "fk_profile_image_media_asset"),
    ):
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")
    op.drop_table("media_usage")
    op.drop_table("media_variant")
    op.drop_table("media_asset")
