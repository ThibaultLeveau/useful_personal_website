"""Strict admin/public transport schemas for the skills capability."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves runtime annotations.
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID  # noqa: TC003 - Pydantic resolves runtime annotations.

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import WithJsonSchema


class StrictModel(BaseModel):
    """Reject every undeclared mass-assignment field."""

    model_config = ConfigDict(extra="forbid")


Name = Annotated[str, Field(min_length=1, max_length=120)]
Slug = Annotated[str, Field(min_length=1, max_length=80)]
Description = Annotated[str, Field(min_length=1, max_length=2_000)]
ProficiencyLabel = Annotated[str, Field(min_length=1, max_length=80)]
Score = Annotated[int, Field(ge=0, le=100)]
Years = Annotated[
    Decimal,
    Field(ge=0, le=Decimal("999.99"), max_digits=5, decimal_places=2),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?$",
            "examples": ["3.50"],
        }
    ),
]
IconKey = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=64)]


class SkillCategoryInput(StrictModel):
    """Complete create/update category values."""

    name: Name
    slug: Slug
    description: Description | None = None


class SkillCategoryData(SkillCategoryInput):
    """Administrator category with concurrency metadata."""

    id: UUID
    position: int
    created_at: datetime
    updated_at: datetime
    version: int


class SkillCategoryListData(StrictModel):
    """Complete ordered category collection."""

    items: list[SkillCategoryData]


class SkillInput(StrictModel):
    """Complete create/update skill values plus staged relation intent."""

    name: Name
    slug: Slug
    category_id: UUID
    description: Description | None = None
    proficiency_label: ProficiencyLabel | None = None
    proficiency_score: Score | None = None
    years_experience: Years
    icon_key: IconKey | None = None
    featured: bool = False
    visible: bool = True
    associated_project_ids: list[UUID] = Field(default_factory=list, max_length=100)
    associated_experience_ids: list[UUID] = Field(default_factory=list, max_length=100)


class SkillData(StrictModel):
    """Administrator skill with safe unavailable-relation state."""

    id: UUID
    name: str
    slug: str
    category_id: UUID
    description: str | None
    proficiency_label: str | None
    proficiency_score: int | None
    years_experience: Years
    icon_key: str | None
    position: int
    featured: bool
    visible: bool
    relation_provider: Literal["unavailable"] = "unavailable"
    created_at: datetime
    updated_at: datetime
    version: int


class SkillListData(StrictModel):
    """Complete category-scoped skill order."""

    items: list[SkillData]


class DeleteData(StrictModel):
    """Safe deletion acknowledgement."""

    deleted: Literal[True] = True


class ReorderRequest(StrictModel):
    """Complete duplicate-free order; domain validates authorized membership."""

    ordered_ids: Annotated[list[UUID], Field(min_length=1, max_length=500)]


class PublicSkillData(StrictModel):
    """Public-only skill projection with category context and no internal IDs."""

    name: str
    slug: str
    category_name: str
    category_slug: str
    category_description: str | None
    category_position: int
    description: str | None
    proficiency_label: str | None
    proficiency_score: int | None
    years_experience: Years
    icon_key: str | None
    position: int
    featured: bool
    related_projects: tuple[()] = ()
    related_experiences: tuple[()] = ()
