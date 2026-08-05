"""Add immutable revisioned project case studies.

Revision ID: 20260802_0007
Revises: 20260802_0006
Create Date: 2026-08-04 12:00:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.schema import SchemaItem

revision: str = "20260802_0007"
down_revision: str | None = "20260802_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ordered_relation_constraints(
    *, table_name: str, target_column: str, target_table: str
) -> tuple[SchemaItem, ...]:
    prefix = table_name
    target_label = target_column.removesuffix("_id")
    return (
        sa.CheckConstraint("position >= 0", name=f"{prefix}_nonnegative_position"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["project_revision.id"],
            name=f"fk_{table_name}_revision_id_project_revision",
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
            "revision_id", target_column, name=f"uq_{prefix}_revision_{target_label}"
        ),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name=f"uq_{prefix}_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )


def _create_ordered_relation(*, table_name: str, target_column: str, target_table: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(target_column, postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *_ordered_relation_constraints(
            table_name=table_name,
            target_column=target_column,
            target_table=target_table,
        ),
    )
    op.create_index(
        f"ix_{table_name}_revision_order",
        table_name,
        ["revision_id", "position", "id"],
    )
    op.create_index(
        f"ix_{table_name}_{target_column.removesuffix('_id')}_revision",
        table_name,
        [target_column, "revision_id"],
    )


def upgrade() -> None:
    """Create the sole M6 project aggregate/revision schema."""
    op.create_table(
        "project",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("draft_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="project_slug_format"),
        sa.CheckConstraint("length(slug) BETWEEN 1 AND 80", name="project_slug_length"),
        sa.CheckConstraint("position >= 0", name="project_nonnegative_position"),
        sa.CheckConstraint("version > 0", name="project_positive_version"),
        sa.CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="project_publication_pointer_schedule_pair",
        ),
        sa.CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="project_distinct_draft_published_pointers",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project"),
        sa.UniqueConstraint("slug", name="uq_project_slug"),
    )
    op.create_table(
        "project_revision",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("based_on_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("owner_role", sa.String(length=180), nullable=False),
        sa.Column("architecture", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("repository_url", sa.String(length=2048), nullable=True),
        sa.Column("demo_url", sa.String(length=2048), nullable=True),
        sa.Column("seo_title", sa.String(length=70), nullable=True),
        sa.Column("seo_description", sa.String(length=180), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("frozen", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision_number > 0", name="project_revision_positive_number"),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 180 AND name = btrim(name)",
            name="project_revision_name",
        ),
        sa.CheckConstraint(
            "length(short_description) BETWEEN 1 AND 500 "
            "AND short_description = btrim(short_description)",
            name="project_revision_short_description",
        ),
        sa.CheckConstraint(
            "length(full_description) BETWEEN 1 AND 30000 "
            "AND full_description = btrim(full_description)",
            name="project_revision_full_description",
        ),
        sa.CheckConstraint(
            "length(problem) BETWEEN 1 AND 30000 AND problem = btrim(problem)",
            name="project_revision_problem",
        ),
        sa.CheckConstraint(
            "length(solution) BETWEEN 1 AND 30000 AND solution = btrim(solution)",
            name="project_revision_solution",
        ),
        sa.CheckConstraint(
            "length(impact) BETWEEN 1 AND 30000 AND impact = btrim(impact)",
            name="project_revision_impact",
        ),
        sa.CheckConstraint(
            "length(owner_role) BETWEEN 1 AND 180 AND owner_role = btrim(owner_role)",
            name="project_revision_owner_role",
        ),
        sa.CheckConstraint(
            "length(architecture) BETWEEN 1 AND 30000 AND architecture = btrim(architecture)",
            name="project_revision_architecture",
        ),
        sa.CheckConstraint(
            "status IN ('planned','active','paused','completed','maintenance','archived')",
            name="project_revision_status_catalog",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="project_revision_date_order"
        ),
        sa.CheckConstraint(
            "status NOT IN ('planned','active','maintenance') OR end_date IS NULL",
            name="project_revision_open_status_date",
        ),
        sa.CheckConstraint(
            "status NOT IN ('completed','archived') OR end_date IS NOT NULL",
            name="project_revision_closed_status_date",
        ),
        sa.CheckConstraint(
            "repository_url IS NULL OR (length(repository_url) BETWEEN 1 AND 2048 "
            "AND repository_url = btrim(repository_url) "
            "AND repository_url LIKE 'https://%')",
            name="project_revision_https_repository_url",
        ),
        sa.CheckConstraint(
            "demo_url IS NULL OR (length(demo_url) BETWEEN 1 AND 2048 "
            "AND demo_url = btrim(demo_url) AND demo_url LIKE 'https://%')",
            name="project_revision_https_demo_url",
        ),
        sa.CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="project_revision_seo_title",
        ),
        sa.CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="project_revision_seo_description",
        ),
        sa.CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) "
            "AND canonical_url LIKE 'https://%')",
            name="project_revision_https_canonical_url",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name="fk_project_revision_project_id_project",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_project_revision_created_by_administrator",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "based_on_revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_project_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_revision"),
        sa.UniqueConstraint("project_id", "revision_number", name="uq_project_revision_number"),
        sa.UniqueConstraint("project_id", "id", name="uq_project_revision_owner_target"),
    )
    op.create_foreign_key(
        "fk_project_draft_pointer",
        "project",
        "project_revision",
        ["id", "draft_revision_id"],
        ["project_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_project_published_pointer",
        "project",
        "project_revision",
        ["id", "published_revision_id"],
        ["project_id", "id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_table(
        "project_technology",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(length=120), nullable=False),
        sa.CheckConstraint("position >= 0", name="project_technology_nonnegative_position"),
        sa.CheckConstraint(
            "length(value) BETWEEN 1 AND 120 AND value = btrim(value)",
            name="project_technology_bounded_value",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["project_revision.id"],
            name="fk_project_technology_revision_id_project_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_technology"),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name="uq_project_technology_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.UniqueConstraint("revision_id", "value", name="uq_project_technology_revision_value"),
    )
    _create_ordered_relation(
        table_name="project_skill", target_column="skill_id", target_table="skill"
    )
    _create_ordered_relation(
        table_name="project_experience",
        target_column="experience_id",
        target_table="experience",
    )
    op.create_table(
        "related_project",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="related_project_nonnegative_position"),
        sa.CheckConstraint("project_id <> related_project_id", name="related_project_not_self"),
        sa.ForeignKeyConstraint(
            ["project_id", "revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_related_project_revision_owner",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["related_project_id"],
            ["project.id"],
            name="fk_related_project_target_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_related_project"),
        sa.UniqueConstraint(
            "revision_id", "related_project_id", name="uq_related_project_revision_target"
        ),
        sa.UniqueConstraint(
            "revision_id",
            "position",
            name="uq_related_project_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    for name, table_name, columns in (
        ("ix_project_admin_order", "project", ["position", "id"]),
        ("ix_project_slug_lookup", "project", ["slug"]),
        (
            "ix_project_effective_public",
            "project",
            ["featured", "position", "id"],
        ),
        (
            "ix_project_technology_revision_order",
            "project_technology",
            ["revision_id", "position", "id"],
        ),
        (
            "ix_related_project_revision_order",
            "related_project",
            ["revision_id", "position", "id"],
        ),
        (
            "ix_related_project_target_revision",
            "related_project",
            ["related_project_id", "revision_id"],
        ),
    ):
        where = None
        if name in {"ix_project_admin_order", "ix_project_slug_lookup"}:
            where = sa.text("deleted_at IS NULL")
        elif name == "ix_project_effective_public":
            where = sa.text("visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL")
        op.create_index(name, table_name, columns, postgresql_where=where)
    op.create_index(
        "ix_project_technology_value_revision",
        "project_technology",
        [sa.text("lower(value)"), "revision_id"],
    )

    op.execute(
        """
        CREATE FUNCTION reject_frozen_project_revision_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            target_revision_id uuid;
            target_frozen boolean;
        BEGIN
            IF TG_TABLE_NAME = 'project_revision' THEN
                target_frozen := OLD.frozen;
            ELSE
                target_revision_id := OLD.revision_id;
                SELECT frozen INTO target_frozen
                FROM project_revision
                WHERE id = target_revision_id;
            END IF;
            IF target_frozen THEN
                RAISE EXCEPTION 'frozen project revisions are immutable'
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
        "project_revision",
        "project_technology",
        "project_skill",
        "project_experience",
        "related_project",
    ):
        op.execute(
            sa.text(
                f"CREATE TRIGGER trg_{table_name}_reject_frozen_mutation "
                f"BEFORE UPDATE OR DELETE ON {table_name} "
                "FOR EACH ROW EXECUTE FUNCTION reject_frozen_project_revision_mutation()"
            )
        )


def downgrade() -> None:
    """Remove only the M6 project schema."""
    op.drop_table("related_project")
    op.drop_table("project_experience")
    op.drop_table("project_skill")
    op.drop_table("project_technology")
    op.drop_constraint("fk_project_published_pointer", "project", type_="foreignkey")
    op.drop_constraint("fk_project_draft_pointer", "project", type_="foreignkey")
    op.drop_table("project_revision")
    op.drop_table("project")
    op.execute("DROP FUNCTION reject_frozen_project_revision_mutation()")
