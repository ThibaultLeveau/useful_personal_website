"""SQLAlchemy records for immutable revisioned professional experiences."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003 - SQLAlchemy resolves at runtime.
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves at runtime.

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


class ExperiencesBase(DeclarativeBase):
    """SQLAlchemy registry for the M5 experience slice."""


class ExperienceRecord(ExperiencesBase):
    """Stable aggregate and publication pointers."""

    __tablename__ = "experience"
    __table_args__ = (
        CheckConstraint("position >= 0", name="experience_nonnegative_position"),
        CheckConstraint("version > 0", name="experience_positive_version"),
        CheckConstraint(
            "(published_revision_id IS NULL) = (publish_at IS NULL)",
            name="experience_publication_pointer_schedule_pair",
        ),
        CheckConstraint(
            "published_revision_id IS NULL OR draft_revision_id <> published_revision_id",
            name="experience_distinct_draft_published_pointers",
        ),
        ForeignKeyConstraint(
            ["id", "draft_revision_id"],
            ["experience_revision.experience_id", "experience_revision.id"],
            name="fk_experience_draft_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["id", "published_revision_id"],
            ["experience_revision.experience_id", "experience_revision.id"],
            name="fk_experience_published_pointer",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
        ),
        Index(
            "ix_experience_admin_order",
            "position",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_experience_admin_lifecycle",
            "published_revision_id",
            "publish_at",
            "visible",
            "updated_at",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_experience_effective_public",
            "publish_at",
            "id",
            postgresql_where=text(
                "visible AND deleted_at IS NULL AND published_revision_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
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


class ExperienceRevisionRecord(ExperiencesBase):
    """Revision-owned scalar content and immutability state."""

    __tablename__ = "experience_revision"
    __table_args__ = (
        CheckConstraint(
            "revision_number > 0",
            name="experience_revision_positive_number",
        ),
        CheckConstraint(
            "length(company_name) BETWEEN 1 AND 160 AND company_name = btrim(company_name)",
            name="experience_revision_company_name",
        ),
        CheckConstraint(
            "company_url IS NULL OR (length(company_url) BETWEEN 1 AND 2048 "
            "AND company_url = btrim(company_url) AND company_url LIKE 'https://%')",
            name="experience_revision_https_company_url",
        ),
        CheckConstraint(
            "length(role_title) BETWEEN 1 AND 160 AND role_title = btrim(role_title)",
            name="experience_revision_role_title",
        ),
        CheckConstraint(
            "employment_type IN ('full_time', 'part_time', 'contract', 'freelance', "
            "'internship', 'apprenticeship', 'temporary', 'seasonal', 'volunteer')",
            name="experience_revision_employment_type_catalog",
        ),
        CheckConstraint(
            "location IS NULL OR (length(location) BETWEEN 1 AND 160 "
            "AND location = btrim(location))",
            name="experience_revision_location",
        ),
        CheckConstraint(
            "remote_status IN ('onsite', 'hybrid', 'remote')",
            name="experience_revision_remote_status_catalog",
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="experience_revision_date_order",
        ),
        CheckConstraint(
            "NOT current_position OR end_date IS NULL",
            name="experience_revision_current_without_end",
        ),
        CheckConstraint(
            "length(short_summary) BETWEEN 1 AND 500 AND short_summary = btrim(short_summary)",
            name="experience_revision_short_summary",
        ),
        CheckConstraint(
            "detailed_description IS NULL OR "
            "(length(detailed_description) BETWEEN 1 AND 20000 "
            "AND detailed_description = btrim(detailed_description))",
            name="experience_revision_detailed_description",
        ),
        UniqueConstraint(
            "experience_id",
            "revision_number",
            name="uq_experience_revision_number",
        ),
        UniqueConstraint(
            "experience_id",
            "id",
            name="uq_experience_revision_owner_target",
        ),
        ForeignKeyConstraint(
            ["experience_id", "based_on_revision_id"],
            ["experience_revision.experience_id", "experience_revision.id"],
            name="fk_experience_revision_based_on_owner",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_experience_revision_created_by_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index(
            "ix_experience_revision_chronology",
            text("current_position DESC"),
            text("start_date DESC"),
            text("end_date DESC NULLS LAST"),
            "experience_id",
            "id",
            postgresql_where=text("frozen"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    experience_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "experience.id",
            name="fk_experience_revision_experience_id_experience",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    based_on_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    company_name: Mapped[str] = mapped_column(String(160))
    company_url: Mapped[str | None] = mapped_column(String(2048))
    role_title: Mapped[str] = mapped_column(String(160))
    employment_type: Mapped[str] = mapped_column(String(24))
    location: Mapped[str | None] = mapped_column(String(160))
    remote_status: Mapped[str] = mapped_column(String(16))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    current_position: Mapped[bool] = mapped_column(Boolean)
    short_summary: Mapped[str] = mapped_column(String(500))
    detailed_description: Mapped[str | None] = mapped_column(Text)
    frozen: Mapped[bool] = mapped_column(Boolean)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class _OrderedExperienceText:
    """Shared annotations for revision-owned ordered text rows."""

    id: Mapped[UUID]
    revision_id: Mapped[UUID]
    position: Mapped[int]
    value: Mapped[str]


class ExperienceResponsibilityRecord(_OrderedExperienceText, ExperiencesBase):
    """One ordered responsibility."""

    __tablename__ = "experience_responsibility"
    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="experience_responsibility_nonnegative_position",
        ),
        CheckConstraint(
            "length(value) BETWEEN 1 AND 1000 AND value = btrim(value)",
            name="experience_responsibility_bounded_value",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_experience_responsibility_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "ix_experience_responsibility_revision_order",
            "revision_id",
            "position",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experience_revision.id", ondelete="CASCADE"),
    )
    position: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(Text)


class ExperienceAchievementRecord(_OrderedExperienceText, ExperiencesBase):
    """One ordered achievement."""

    __tablename__ = "experience_achievement"
    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="experience_achievement_nonnegative_position",
        ),
        CheckConstraint(
            "length(value) BETWEEN 1 AND 1000 AND value = btrim(value)",
            name="experience_achievement_bounded_value",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_experience_achievement_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "ix_experience_achievement_revision_order",
            "revision_id",
            "position",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experience_revision.id", ondelete="CASCADE"),
    )
    position: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(Text)


class ExperienceTechnologyRecord(_OrderedExperienceText, ExperiencesBase):
    """One ordered technology."""

    __tablename__ = "experience_technology"
    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="experience_technology_nonnegative_position",
        ),
        CheckConstraint(
            "length(value) BETWEEN 1 AND 1000 AND value = btrim(value)",
            name="experience_technology_bounded_value",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_experience_technology_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "ix_experience_technology_revision_order",
            "revision_id",
            "position",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experience_revision.id", ondelete="CASCADE"),
    )
    position: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(Text)


class ExperienceSkillRecord(ExperiencesBase):
    """One ordered revision-scoped skill reference."""

    __tablename__ = "experience_skill"
    __table_args__ = (
        CheckConstraint("position >= 0", name="experience_skill_nonnegative_position"),
        UniqueConstraint(
            "revision_id",
            "skill_id",
            name="uq_experience_skill_revision_skill",
        ),
        UniqueConstraint(
            "revision_id",
            "position",
            name="uq_experience_skill_revision_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["skill_id"],
            ["skill.id"],
            name="fk_experience_skill_skill_id_skill",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index(
            "ix_experience_skill_revision_order",
            "revision_id",
            "position",
            "id",
        ),
        Index(
            "ix_experience_skill_skill_revision",
            "skill_id",
            "revision_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experience_revision.id", ondelete="CASCADE"),
    )
    skill_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)
