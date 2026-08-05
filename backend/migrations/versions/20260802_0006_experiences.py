"""Add immutable revisioned professional experiences.

Revision ID: 20260802_0006
Revises: 20260802_0005
Create Date: 2026-08-03 20:30:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0006"
down_revision: str | None = "20260802_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMPLOYMENT_TYPES = (
    "full_time",
    "part_time",
    "contract",
    "freelance",
    "internship",
    "apprenticeship",
    "temporary",
    "seasonal",
    "volunteer",
)
REMOTE_STATUSES = ("onsite", "hybrid", "remote")


def _catalog(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def _create_ordered_text_table(table_name: str, constraint_prefix: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.CheckConstraint("position >= 0", name=f"{constraint_prefix}_nonnegative_position"),
        sa.CheckConstraint(
            "length(value) BETWEEN 1 AND 1000 AND value = btrim(value)",
            name=f"{constraint_prefix}_bounded_value",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["experience_revision.id"],
            name=f"fk_{table_name}_revision_id_experience_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name=f"uq_{constraint_prefix}_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        f"ix_{constraint_prefix}_revision_order",
        table_name,
        ["revision_id", "position", "id"],
    )


def upgrade() -> None:
    """Create the sole M5 aggregate/revision schema and immutability triggers."""
    op.create_table(
        "experience",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.CheckConstraint("position >= 0", name="experience_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="experience_positive_version"),
        sa.CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="experience_publication_pointer_schedule_pair",
        ),
        sa.CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="experience_distinct_draft_published_pointers",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_experience"),
    )
    op.create_table(
        "experience_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("experience_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("based_on_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(length=160), nullable=False),
        sa.Column("company_url", sa.String(length=2048), nullable=True),
        sa.Column("role_title", sa.String(length=160), nullable=False),
        sa.Column("employment_type", sa.String(length=24), nullable=False),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column("remote_status", sa.String(length=16), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("current_position", sa.Boolean(), nullable=False),
        sa.Column("short_summary", sa.String(length=500), nullable=False),
        sa.Column("detailed_description", sa.Text(), nullable=True),
        sa.Column("frozen", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision_number > 0", name="experience_revision_positive_number"),
        sa.CheckConstraint(
            "length(company_name) BETWEEN 1 AND 160 AND company_name = btrim(company_name)",
            name="experience_revision_company_name",
        ),
        sa.CheckConstraint(
            "company_url IS NULL OR (length(company_url) BETWEEN 1 AND 2048 "
            "AND company_url = btrim(company_url) AND company_url LIKE 'https://%')",
            name="experience_revision_https_company_url",
        ),
        sa.CheckConstraint(
            "length(role_title) BETWEEN 1 AND 160 AND role_title = btrim(role_title)",
            name="experience_revision_role_title",
        ),
        sa.CheckConstraint(
            f"employment_type IN ({_catalog(EMPLOYMENT_TYPES)})",
            name="experience_revision_employment_type_catalog",
        ),
        sa.CheckConstraint(
            "location IS NULL OR (length(location) BETWEEN 1 AND 160 "
            "AND location = btrim(location))",
            name="experience_revision_location",
        ),
        sa.CheckConstraint(
            f"remote_status IN ({_catalog(REMOTE_STATUSES)})",
            name="experience_revision_remote_status_catalog",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="experience_revision_date_order",
        ),
        sa.CheckConstraint(
            "NOT current_position OR end_date IS NULL",
            name="experience_revision_current_without_end",
        ),
        sa.CheckConstraint(
            "length(short_summary) BETWEEN 1 AND 500 AND short_summary = btrim(short_summary)",
            name="experience_revision_short_summary",
        ),
        sa.CheckConstraint(
            "detailed_description IS NULL OR "
            "(length(detailed_description) BETWEEN 1 AND 20000 "
            "AND detailed_description = btrim(detailed_description))",
            name="experience_revision_detailed_description",
        ),
        sa.ForeignKeyConstraint(
            ["experience_id"],
            ["experience.id"],
            name="fk_experience_revision_experience_id_experience",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_experience_revision_created_by_administrator",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["experience_id", "based_on_revision_id"],
            ["experience_revision.experience_id", "experience_revision.id"],
            name="fk_experience_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_experience_revision"),
        sa.UniqueConstraint(
            "experience_id",
            "revision_number",
            name="uq_experience_revision_number",
        ),
        sa.UniqueConstraint(
            "experience_id",
            "id",
            name="uq_experience_revision_owner_target",
        ),
    )
    op.create_foreign_key(
        "fk_experience_draft_pointer",
        "experience",
        "experience_revision",
        ["id", "draft_revision_id"],
        ["experience_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_experience_published_pointer",
        "experience",
        "experience_revision",
        ["id", "published_revision_id"],
        ["experience_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    _create_ordered_text_table("experience_responsibility", "experience_responsibility")
    _create_ordered_text_table("experience_achievement", "experience_achievement")
    _create_ordered_text_table("experience_technology", "experience_technology")
    op.create_table(
        "experience_skill",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="experience_skill_nonnegative_position"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["experience_revision.id"],
            name="fk_experience_skill_revision_id_experience_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skill.id"],
            name="fk_experience_skill_skill_id_skill",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_experience_skill"),
        sa.UniqueConstraint(
            "revision_id",
            "skill_id",
            name="uq_experience_skill_revision_skill",
        ),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name="uq_experience_skill_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_index(
        "ix_experience_admin_order",
        "experience",
        ["position", "id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_experience_admin_lifecycle",
        "experience",
        ["published_revision_id", "publish_at", "visible", "updated_at", "id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_experience_effective_public",
        "experience",
        ["publish_at", "id"],
        postgresql_where=sa.text(
            "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_experience_revision_chronology",
        "experience_revision",
        [
            sa.text("current_position DESC"),
            sa.text("start_date DESC"),
            sa.text("end_date DESC NULLS LAST"),
            "experience_id",
            "id",
        ],
        postgresql_where=sa.text("frozen"),
    )
    op.create_index(
        "ix_experience_skill_revision_order",
        "experience_skill",
        ["revision_id", "position", "id"],
    )
    op.create_index(
        "ix_experience_skill_skill_revision",
        "experience_skill",
        ["skill_id", "revision_id"],
    )

    op.execute(
        """
        CREATE FUNCTION reject_frozen_experience_revision_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            target_revision_id uuid;
            target_frozen boolean;
        BEGIN
            IF TG_TABLE_NAME = 'experience_revision' THEN
                target_frozen := OLD.frozen;
            ELSE
                target_revision_id := OLD.revision_id;
                SELECT frozen INTO target_frozen
                FROM experience_revision
                WHERE id = target_revision_id;
            END IF;
            IF target_frozen THEN
                RAISE EXCEPTION 'frozen experience revisions are immutable'
                    USING ERRCODE = '55000';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    for table_name in (
        "experience_revision",
        "experience_responsibility",
        "experience_achievement",
        "experience_technology",
        "experience_skill",
    ):
        op.execute(
            sa.text(
                f"CREATE TRIGGER trg_{table_name}_reject_frozen_mutation "
                f"BEFORE UPDATE OR DELETE ON {table_name} "
                "FOR EACH ROW EXECUTE FUNCTION reject_frozen_experience_revision_mutation()"
            )
        )


def downgrade() -> None:
    """Remove only the M5 experience schema."""
    op.drop_index("ix_experience_skill_skill_revision", table_name="experience_skill")
    op.drop_index("ix_experience_skill_revision_order", table_name="experience_skill")
    op.drop_index("ix_experience_revision_chronology", table_name="experience_revision")
    op.drop_index("ix_experience_effective_public", table_name="experience")
    op.drop_index("ix_experience_admin_lifecycle", table_name="experience")
    op.drop_index("ix_experience_admin_order", table_name="experience")
    op.drop_table("experience_skill")
    op.drop_index("ix_experience_technology_revision_order", table_name="experience_technology")
    op.drop_table("experience_technology")
    op.drop_index("ix_experience_achievement_revision_order", table_name="experience_achievement")
    op.drop_table("experience_achievement")
    op.drop_index(
        "ix_experience_responsibility_revision_order",
        table_name="experience_responsibility",
    )
    op.drop_table("experience_responsibility")
    op.drop_constraint("fk_experience_published_pointer", "experience", type_="foreignkey")
    op.drop_constraint("fk_experience_draft_pointer", "experience", type_="foreignkey")
    op.drop_table("experience_revision")
    op.drop_table("experience")
    op.execute("DROP FUNCTION reject_frozen_experience_revision_mutation()")
