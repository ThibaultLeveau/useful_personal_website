"""SQLAlchemy records for ordered skill categories and skills."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves runtime annotations.
from decimal import Decimal  # noqa: TC003 - SQLAlchemy resolves runtime annotations.
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves runtime annotations.

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SkillsBase(DeclarativeBase):
    """SQLAlchemy registry for the M4 skills slice."""


class SkillCategoryRecord(SkillsBase):
    """One flat globally ordered category."""

    __tablename__ = "skill_category"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="skill_category_lower_slug"),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="skill_category_slug_format",
        ),
        CheckConstraint("position >= 0", name="skill_category_nonnegative_position"),
        CheckConstraint("version > 0", name="skill_category_positive_version"),
        UniqueConstraint("slug", name="uq_skill_category_slug"),
        UniqueConstraint(
            "position",
            name="uq_skill_category_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index("ix_skill_category_order", "position", "id"),
        Index("uq_skill_category_slug_lower", func.lower(text("slug")), unique=True),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class SkillRecord(SkillsBase):
    """One category-scoped ordered skill."""

    __tablename__ = "skill"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="skill_lower_slug"),
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="skill_slug_format"),
        CheckConstraint("position >= 0", name="skill_nonnegative_position"),
        CheckConstraint("version > 0", name="skill_positive_version"),
        CheckConstraint(
            "proficiency_score IS NULL OR proficiency_score BETWEEN 0 AND 100",
            name="skill_score_range",
        ),
        CheckConstraint(
            "years_experience >= 0 AND years_experience <= 999.99",
            name="skill_years_range",
        ),
        CheckConstraint(
            "icon_key IS NULL OR icon_key ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="skill_icon_key_format",
        ),
        UniqueConstraint("slug", name="uq_skill_slug"),
        UniqueConstraint(
            "category_id",
            "position",
            name="uq_skill_category_skill_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index("uq_skill_slug_lower", func.lower(text("slug")), unique=True),
        Index("ix_skill_category_skill_order", "category_id", "position", "id"),
        Index(
            "ix_skill_public_category_order",
            "category_id",
            "position",
            "id",
            postgresql_where=text("visible"),
        ),
        Index(
            "ix_skill_public_featured_order",
            "featured",
            "position",
            "id",
            postgresql_where=text("visible"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80))
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_category.id", ondelete="RESTRICT"),
    )
    description: Mapped[str | None] = mapped_column(Text)
    proficiency_label: Mapped[str | None] = mapped_column(String(80))
    proficiency_score: Mapped[int | None] = mapped_column(SmallInteger)
    years_experience: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    icon_key: Mapped[str | None] = mapped_column(String(64))
    position: Mapped[int] = mapped_column(Integer)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
