"""Add ordered skill categories and skills.

Revision ID: 20260802_0005
Revises: 20260802_0004
Create Date: 2026-08-03 18:30:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0005"
down_revision: str | None = "20260802_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the sole M4 skills schema without content or target relations."""
    op.create_table(
        "skill_category",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("slug = lower(slug)", name="skill_category_lower_slug"),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="skill_category_slug_format",
        ),
        sa.CheckConstraint(
            "position >= 0",
            name="skill_category_nonnegative_position",
        ),
        sa.CheckConstraint("version > 0", name="skill_category_positive_version"),
        sa.PrimaryKeyConstraint("id", name="pk_skill_category"),
        sa.UniqueConstraint("slug", name="uq_skill_category_slug"),
        sa.UniqueConstraint(
            "position",
            name="uq_skill_category_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        "ix_skill_category_order",
        "skill_category",
        ["position", "id"],
    )
    op.create_index(
        "uq_skill_category_slug_lower",
        "skill_category",
        [sa.text("lower(slug)")],
        unique=True,
    )
    op.create_table(
        "skill",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("proficiency_label", sa.String(length=80), nullable=True),
        sa.Column("proficiency_score", sa.SmallInteger(), nullable=True),
        sa.Column("years_experience", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("icon_key", sa.String(length=64), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("slug = lower(slug)", name="skill_lower_slug"),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="skill_slug_format",
        ),
        sa.CheckConstraint("position >= 0", name="skill_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="skill_positive_version"),
        sa.CheckConstraint(
            "proficiency_score IS NULL OR proficiency_score BETWEEN 0 AND 100",
            name="skill_score_range",
        ),
        sa.CheckConstraint(
            "years_experience >= 0 AND years_experience <= 999.99",
            name="skill_years_range",
        ),
        sa.CheckConstraint(
            "icon_key IS NULL OR icon_key ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="skill_icon_key_format",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["skill_category.id"],
            name="fk_skill_category_id_skill_category",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_skill"),
        sa.UniqueConstraint("slug", name="uq_skill_slug"),
        sa.UniqueConstraint(
            "category_id",
            "position",
            name="uq_skill_category_skill_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index("uq_skill_slug_lower", "skill", [sa.text("lower(slug)")], unique=True)
    op.create_index(
        "ix_skill_category_skill_order",
        "skill",
        ["category_id", "position", "id"],
    )
    op.create_index(
        "ix_skill_public_category_order",
        "skill",
        ["category_id", "position", "id"],
        postgresql_where=sa.text("visible"),
    )
    op.create_index(
        "ix_skill_public_featured_order",
        "skill",
        ["featured", "position", "id"],
        postgresql_where=sa.text("visible"),
    )


def downgrade() -> None:
    """Remove only the M4 skills slice."""
    op.drop_index("ix_skill_public_featured_order", table_name="skill")
    op.drop_index("ix_skill_public_category_order", table_name="skill")
    op.drop_index("ix_skill_category_skill_order", table_name="skill")
    op.drop_index("uq_skill_slug_lower", table_name="skill")
    op.drop_table("skill")
    op.drop_index("uq_skill_category_slug_lower", table_name="skill_category")
    op.drop_index("ix_skill_category_order", table_name="skill_category")
    op.drop_table("skill_category")
