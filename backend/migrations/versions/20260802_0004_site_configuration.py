"""Add profile, website settings, navigation, and footer persistence.

Revision ID: 20260802_0004
Revises: 20260802_0003
Create Date: 2026-08-03 10:45:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0004"
down_revision: str | None = "20260802_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the sole M3 schema and content-free singleton shells."""
    op.create_table(
        "profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("singleton_key", sa.SmallInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=True),
        sa.Column("professional_title", sa.String(length=160), nullable=True),
        sa.Column("short_biography", sa.Text(), nullable=True),
        sa.Column("full_biography", sa.Text(), nullable=True),
        sa.Column("profile_image_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column("availability", sa.String(length=240), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("social_links", postgresql.JSONB(), nullable=False),
        sa.Column("github_url", sa.String(length=2048), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column("personal_values", postgresql.JSONB(), nullable=False),
        sa.Column("work_preferences", postgresql.JSONB(), nullable=False),
        sa.Column("resume_url", sa.String(length=2048), nullable=True),
        sa.Column("contact_preference", sa.String(length=24), nullable=False),
        sa.Column("public_fields", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("singleton_key = 1", name="profile_singleton_key"),
        sa.CheckConstraint("version > 0", name="profile_positive_version"),
        sa.PrimaryKeyConstraint("id", name="pk_profile"),
        sa.UniqueConstraint("singleton_key", name="uq_profile_singleton"),
    )
    op.create_table(
        "website_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("singleton_key", sa.SmallInteger(), nullable=False),
        sa.Column("website_name", sa.String(length=120), nullable=True),
        sa.Column("default_title", sa.String(length=160), nullable=True),
        sa.Column("default_description", sa.String(length=320), nullable=True),
        sa.Column("logo_media_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("favicon_media_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("social_image_media_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_locale", sa.String(length=35), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("theme_policy", sa.String(length=16), nullable=False),
        sa.Column("primary_color", sa.String(length=7), nullable=True),
        sa.Column("accent_color", sa.String(length=7), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("social_links", postgresql.JSONB(), nullable=False),
        sa.Column("seo_title_suffix", sa.String(length=80), nullable=True),
        sa.Column("seo_description", sa.String(length=320), nullable=True),
        sa.Column("analytics_provider", sa.String(length=32), nullable=False),
        sa.Column("analytics_public_id", sa.String(length=80), nullable=True),
        sa.Column("public_availability", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "singleton_key = 1",
            name="website_settings_singleton_key",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="website_settings_positive_version",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_website_settings"),
        sa.UniqueConstraint("singleton_key", name="uq_website_settings_singleton"),
    )
    op.create_table(
        "navigation_menu",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("singleton_key", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "singleton_key = 1",
            name="navigation_menu_singleton_key",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="navigation_menu_positive_version",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_navigation_menu"),
        sa.UniqueConstraint("singleton_key", name="uq_navigation_menu_singleton"),
    )
    op.create_table(
        "footer",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("singleton_key", sa.SmallInteger(), nullable=False),
        sa.Column("copyright_text", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("singleton_key = 1", name="footer_singleton_key"),
        sa.CheckConstraint("version > 0", name="footer_positive_version"),
        sa.PrimaryKeyConstraint("id", name="pk_footer"),
        sa.UniqueConstraint("singleton_key", name="uq_footer_singleton"),
    )
    op.create_table(
        "navigation_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("menu_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("link_kind", sa.String(length=16), nullable=False),
        sa.Column("href", sa.String(length=2048), nullable=False),
        sa.Column("target", sa.String(length=16), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "link_kind IN ('internal', 'external')",
            name="navigation_item_link_kind_catalog",
        ),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="navigation_item_not_self",
        ),
        sa.CheckConstraint(
            "position >= 0",
            name="navigation_item_nonnegative_position",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="navigation_item_positive_version",
        ),
        sa.CheckConstraint(
            "target IN ('same_window', 'new_window')",
            name="navigation_item_target_catalog",
        ),
        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["navigation_menu.id"],
            name="fk_navigation_item_menu_id_navigation_menu",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["navigation_item.id"],
            name="fk_navigation_item_parent_id_navigation_item",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_navigation_item"),
        sa.UniqueConstraint(
            "menu_id", "parent_id", "position", name="uq_navigation_item_child_position"
        ),
    )
    op.create_index(
        "ix_navigation_item_menu_parent",
        "navigation_item",
        ["menu_id", "parent_id", "position", "id"],
    )
    op.create_index(
        "uq_navigation_item_root_position",
        "navigation_item",
        ["menu_id", "position"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    op.create_table(
        "footer_column",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("footer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="footer_column_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="footer_column_positive_version"),
        sa.ForeignKeyConstraint(
            ["footer_id"],
            ["footer.id"],
            name="fk_footer_column_footer_id_footer",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_footer_column"),
        sa.UniqueConstraint("footer_id", "position", name="uq_footer_column_position"),
    )
    op.create_index(
        "ix_footer_column_footer_position",
        "footer_column",
        ["footer_id", "position", "id"],
    )
    op.create_table(
        "footer_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("link_kind", sa.String(length=16), nullable=False),
        sa.Column("item_kind", sa.String(length=16), nullable=False),
        sa.Column("href", sa.String(length=2048), nullable=False),
        sa.Column("target", sa.String(length=16), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "item_kind IN ('link', 'social', 'legal')",
            name="footer_item_kind_catalog",
        ),
        sa.CheckConstraint(
            "link_kind IN ('internal', 'external')",
            name="footer_item_link_kind_catalog",
        ),
        sa.CheckConstraint("position >= 0", name="footer_item_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="footer_item_positive_version"),
        sa.CheckConstraint(
            "target IN ('same_window', 'new_window')",
            name="footer_item_target_catalog",
        ),
        sa.ForeignKeyConstraint(
            ["column_id"],
            ["footer_column.id"],
            name="fk_footer_item_column_id_footer_column",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_footer_item"),
        sa.UniqueConstraint("column_id", "position", name="uq_footer_item_position"),
    )
    op.create_index(
        "ix_footer_item_column_position",
        "footer_item",
        ["column_id", "position", "id"],
    )

    op.execute(
        sa.text(
            "INSERT INTO profile "
            "(id, singleton_key, social_links, personal_values, work_preferences, "
            "contact_preference, public_fields, created_at, updated_at, version) VALUES "
            "('00000000-0000-7000-8000-000000000301', 1, '[]'::jsonb, '[]'::jsonb, "
            "'[]'::jsonb, 'none', '[]'::jsonb, '2026-08-03T10:45:00+00:00', "
            "'2026-08-03T10:45:00+00:00', 1)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO website_settings "
            "(id, singleton_key, default_locale, timezone, theme_policy, social_links, "
            "analytics_provider, created_at, updated_at, version) VALUES "
            "('00000000-0000-7000-8000-000000000302', 1, 'en', 'UTC', 'system', "
            "'[]'::jsonb, 'none', '2026-08-03T10:45:00+00:00', "
            "'2026-08-03T10:45:00+00:00', 1)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO navigation_menu "
            "(id, singleton_key, created_at, updated_at, version) VALUES "
            "('00000000-0000-7000-8000-000000000303', 1, "
            "'2026-08-03T10:45:00+00:00', '2026-08-03T10:45:00+00:00', 1)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO footer "
            "(id, singleton_key, created_at, updated_at, version) VALUES "
            "('00000000-0000-7000-8000-000000000304', 1, "
            "'2026-08-03T10:45:00+00:00', '2026-08-03T10:45:00+00:00', 1)"
        )
    )


def downgrade() -> None:
    """Remove only the M3 site-configuration slice."""
    op.drop_index("ix_footer_item_column_position", table_name="footer_item")
    op.drop_table("footer_item")
    op.drop_index("ix_footer_column_footer_position", table_name="footer_column")
    op.drop_table("footer_column")
    op.drop_index("uq_navigation_item_root_position", table_name="navigation_item")
    op.drop_index("ix_navigation_item_menu_parent", table_name="navigation_item")
    op.drop_table("navigation_item")
    op.drop_table("footer")
    op.drop_table("navigation_menu")
    op.drop_table("website_settings")
    op.drop_table("profile")
