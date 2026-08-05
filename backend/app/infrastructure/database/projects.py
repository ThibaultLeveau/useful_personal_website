"""SQLAlchemy records for immutable revisioned project case studies."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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


class ProjectsBase(DeclarativeBase):
    """SQLAlchemy registry for the M6 project slice."""


class ProjectRecord(ProjectsBase):
    """Stable route identity, publication pointers, and display state."""

    __tablename__ = "project"
    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="project_slug_format"),
        CheckConstraint("length(slug) BETWEEN 1 AND 80", name="project_slug_length"),
        CheckConstraint("position >= 0", name="project_nonnegative_position"),
        CheckConstraint("version > 0", name="project_positive_version"),
        CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="project_publication_pointer_schedule_pair",
        ),
        CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="project_distinct_draft_published_pointers",
        ),
        UniqueConstraint("slug", name="uq_project_slug"),
        ForeignKeyConstraint(
            ["id", "draft_revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_project_draft_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["id", "published_revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_project_published_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index(
            "ix_project_admin_order", "position", "id", postgresql_where=text("deleted_at IS NULL")
        ),
        Index("ix_project_slug_lookup", "slug", postgresql_where=text("deleted_at IS NULL")),
        Index(
            "ix_project_effective_public",
            "featured",
            "position",
            "id",
            postgresql_where=text(
                "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    slug: Mapped[str] = mapped_column(String(80))
    visible: Mapped[bool] = mapped_column(Boolean)
    featured: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int] = mapped_column(Integer)
    draft_revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    published_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unpublished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectRevisionRecord(ProjectsBase):
    """Revision-owned scalar project case-study content."""

    __tablename__ = "project_revision"
    __table_args__ = (
        CheckConstraint("revision_number > 0", name="project_revision_positive_number"),
        CheckConstraint(
            "length(name) BETWEEN 1 AND 180 AND name = btrim(name)", name="project_revision_name"
        ),
        CheckConstraint(
            "length(short_description) BETWEEN 1 AND 500 "
            "AND short_description = btrim(short_description)",
            name="project_revision_short_description",
        ),
        CheckConstraint(
            "length(full_description) BETWEEN 1 AND 30000 "
            "AND full_description = btrim(full_description)",
            name="project_revision_full_description",
        ),
        CheckConstraint(
            "length(problem) BETWEEN 1 AND 30000 AND problem = btrim(problem)",
            name="project_revision_problem",
        ),
        CheckConstraint(
            "length(solution) BETWEEN 1 AND 30000 AND solution = btrim(solution)",
            name="project_revision_solution",
        ),
        CheckConstraint(
            "length(impact) BETWEEN 1 AND 30000 AND impact = btrim(impact)",
            name="project_revision_impact",
        ),
        CheckConstraint(
            "length(owner_role) BETWEEN 1 AND 180 AND owner_role = btrim(owner_role)",
            name="project_revision_owner_role",
        ),
        CheckConstraint(
            "length(architecture) BETWEEN 1 AND 30000 AND architecture = btrim(architecture)",
            name="project_revision_architecture",
        ),
        CheckConstraint(
            "status IN ('planned','active','paused','completed','maintenance','archived')",
            name="project_revision_status_catalog",
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="project_revision_date_order"
        ),
        CheckConstraint(
            "status NOT IN ('planned','active','maintenance') OR end_date IS NULL",
            name="project_revision_open_status_date",
        ),
        CheckConstraint(
            "status NOT IN ('completed','archived') OR end_date IS NOT NULL",
            name="project_revision_closed_status_date",
        ),
        CheckConstraint(
            "repository_url IS NULL OR (length(repository_url) BETWEEN 1 AND 2048 "
            "AND repository_url = btrim(repository_url) "
            "AND repository_url LIKE 'https://%')",
            name="project_revision_https_repository_url",
        ),
        CheckConstraint(
            "demo_url IS NULL OR (length(demo_url) BETWEEN 1 AND 2048 "
            "AND demo_url = btrim(demo_url) AND demo_url LIKE 'https://%')",
            name="project_revision_https_demo_url",
        ),
        CheckConstraint(
            "seo_title IS NULL OR (length(seo_title) BETWEEN 1 AND 70 "
            "AND seo_title = btrim(seo_title))",
            name="project_revision_seo_title",
        ),
        CheckConstraint(
            "seo_description IS NULL OR (length(seo_description) BETWEEN 1 AND 180 "
            "AND seo_description = btrim(seo_description))",
            name="project_revision_seo_description",
        ),
        CheckConstraint(
            "canonical_url IS NULL OR (length(canonical_url) BETWEEN 1 AND 2048 "
            "AND canonical_url = btrim(canonical_url) "
            "AND canonical_url LIKE 'https://%')",
            name="project_revision_https_canonical_url",
        ),
        UniqueConstraint("project_id", "revision_number", name="uq_project_revision_number"),
        UniqueConstraint("project_id", "id", name="uq_project_revision_owner_target"),
        ForeignKeyConstraint(
            ["project_id", "based_on_revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_project_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_project_revision_created_by_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE", deferrable=True, initially="DEFERRED"),
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    based_on_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(180))
    short_description: Mapped[str] = mapped_column(String(500))
    full_description: Mapped[str] = mapped_column(Text)
    problem: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    owner_role: Mapped[str] = mapped_column(String(180))
    architecture: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    repository_url: Mapped[str | None] = mapped_column(String(2048))
    demo_url: Mapped[str | None] = mapped_column(String(2048))
    seo_title: Mapped[str | None] = mapped_column(String(70))
    seo_description: Mapped[str | None] = mapped_column(String(180))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    frozen: Mapped[bool] = mapped_column(Boolean)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectTechnologyRecord(ProjectsBase):
    """One ordered revision-owned technology label."""

    __tablename__ = "project_technology"
    __table_args__ = (
        CheckConstraint("position >= 0", name="project_technology_nonnegative_position"),
        CheckConstraint(
            "length(value) BETWEEN 1 AND 120 AND value = btrim(value)",
            name="project_technology_bounded_value",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_project_technology_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint("revision_id", "value", name="uq_project_technology_revision_value"),
        Index("ix_project_technology_revision_order", "revision_id", "position", "id"),
        Index(
            "ix_project_technology_value_revision",
            text("lower(value)"),
            "revision_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_revision.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(String(120))


class ProjectRevisionMediaRecord(ProjectsBase):
    """One ready cover or ordered screenshot selected by a project revision."""

    __tablename__ = "project_revision_media"
    __table_args__ = (
        CheckConstraint(
            "role IN ('project_cover','project_screenshot')",
            name="project_revision_media_role_catalog",
        ),
        CheckConstraint(
            "position >= 0 AND (role <> 'project_cover' OR position = 0)",
            name="project_revision_media_position_shape",
        ),
        ForeignKeyConstraint(
            ["media_id"],
            ["media_asset.id"],
            name="fk_project_revision_media_media_id_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        UniqueConstraint(
            "revision_id", "role", "position", name="uq_project_revision_media_role_position"
        ),
        UniqueConstraint(
            "revision_id", "role", "media_id", name="uq_project_revision_media_role_asset"
        ),
        Index(
            "ix_project_revision_media_revision_order",
            "revision_id",
            "role",
            "position",
            "id",
        ),
        Index("ix_project_revision_media_asset", "media_id", "revision_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_revision.id", ondelete="CASCADE")
    )
    media_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    role: Mapped[str] = mapped_column(String(24))
    position: Mapped[int] = mapped_column(Integer)


class _OrderedProjectRelation:
    id: Mapped[UUID]
    revision_id: Mapped[UUID]
    position: Mapped[int]


class ProjectSkillRecord(_OrderedProjectRelation, ProjectsBase):
    """One ordered revision-scoped skill reference."""

    __tablename__ = "project_skill"
    __table_args__ = (
        CheckConstraint("position >= 0", name="project_skill_nonnegative_position"),
        UniqueConstraint("revision_id", "skill_id", name="uq_project_skill_revision_skill"),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_project_skill_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["skill_id"],
            ["skill.id"],
            name="fk_project_skill_skill_id_skill",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_project_skill_revision_order", "revision_id", "position", "id"),
        Index("ix_project_skill_skill_revision", "skill_id", "revision_id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_revision.id", ondelete="CASCADE")
    )
    skill_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)


class ProjectExperienceRecord(_OrderedProjectRelation, ProjectsBase):
    """One ordered revision-scoped experience reference."""

    __tablename__ = "project_experience"
    __table_args__ = (
        CheckConstraint("position >= 0", name="project_experience_nonnegative_position"),
        UniqueConstraint(
            "revision_id", "experience_id", name="uq_project_experience_revision_experience"
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_project_experience_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["experience_id"],
            ["experience.id"],
            name="fk_project_experience_experience_id_experience",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_project_experience_revision_order", "revision_id", "position", "id"),
        Index("ix_project_experience_experience_revision", "experience_id", "revision_id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_revision.id", ondelete="CASCADE")
    )
    experience_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)


class RelatedProjectRecord(_OrderedProjectRelation, ProjectsBase):
    """One ordered stable-ID edge to another project."""

    __tablename__ = "related_project"
    __table_args__ = (
        CheckConstraint("position >= 0", name="related_project_nonnegative_position"),
        CheckConstraint("project_id <> related_project_id", name="related_project_not_self"),
        UniqueConstraint(
            "revision_id", "related_project_id", name="uq_related_project_revision_target"
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_related_project_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["project_id", "revision_id"],
            ["project_revision.project_id", "project_revision.id"],
            name="fk_related_project_revision_owner",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["related_project_id"],
            ["project.id"],
            name="fk_related_project_target_project",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_related_project_revision_order", "revision_id", "position", "id"),
        Index("ix_related_project_target_revision", "related_project_id", "revision_id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    related_project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)
