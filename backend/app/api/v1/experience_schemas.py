"""Strict admin, preview, and public schemas for professional experiences."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003 - Pydantic resolves runtime annotations.
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.experiences.domain import (  # noqa: TC001 - Pydantic resolves enums.
    EmploymentType,
    ExperienceLifecycle,
    RemoteStatus,
)


class StrictModel(BaseModel):
    """Reject every undeclared mass-assignment field."""

    model_config = ConfigDict(extra="forbid")


CompanyName = Annotated[str, Field(min_length=1, max_length=160)]
CompanyUrl = Annotated[str, Field(min_length=1, max_length=2_048)]
RoleTitle = Annotated[str, Field(min_length=1, max_length=160)]
Location = Annotated[str, Field(min_length=1, max_length=160)]
Summary = Annotated[str, Field(min_length=1, max_length=500)]
Description = Annotated[str, Field(min_length=1, max_length=20_000)]
OrderedText = Annotated[list[str], Field(max_length=50)]
Technologies = Annotated[list[str], Field(max_length=80)]
SkillIds = Annotated[list[UUID], Field(max_length=100)]


class ExperienceInput(StrictModel):
    """Complete mutable revision values."""

    company_name: CompanyName
    company_url: CompanyUrl | None = None
    role_title: RoleTitle
    employment_type: EmploymentType
    location: Location | None = None
    remote_status: RemoteStatus
    start_date: date
    end_date: date | None = None
    current_position: bool
    short_summary: Summary
    detailed_description: Description | None = None
    responsibilities: OrderedText = Field(default_factory=list)
    achievements: OrderedText = Field(default_factory=list)
    technologies: Technologies = Field(default_factory=list)
    skill_ids: SkillIds = Field(default_factory=list)


class ExperienceCreateRequest(ExperienceInput):
    """Create values plus independent initial visibility."""

    visible: bool = True


class ExperienceRevisionData(ExperienceInput):
    """Administrator-visible revision metadata and complete values."""

    id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ExperienceData(StrictModel):
    """Complete administrator aggregate with draft and live snapshots."""

    id: UUID
    visible: bool
    position: int
    lifecycle: ExperienceLifecycle
    draft: ExperienceRevisionData
    published: ExperienceRevisionData | None
    publish_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None


class ExperiencePreviewData(StrictModel):
    """Private draft projection with persistent nonpublic semantics."""

    banner: Literal["Draft preview - not public"] = "Draft preview - not public"
    noindex: Literal[True] = True
    experience: ExperienceData


class PublishExperienceRequest(StrictModel):
    """Publish now when omitted or at one explicit UTC instant."""

    publish_at: datetime | None = None


class RescheduleExperienceRequest(StrictModel):
    """Replace only the UTC publication instant."""

    publish_at: datetime


class VisibilityRequest(StrictModel):
    """Set independent public visibility."""

    visible: bool


class ReorderExperiencesRequest(StrictModel):
    """Complete duplicate-free aggregate order."""

    ordered_ids: Annotated[list[UUID], Field(min_length=1, max_length=500)]


class ExperienceOrderData(StrictModel):
    """One aggregate's normalized order and version."""

    id: UUID
    position: int
    version: int


class ExperienceOrderListData(StrictModel):
    """Complete normalized aggregate order."""

    items: list[ExperienceOrderData]


class DeleteExperienceData(StrictModel):
    """Safe soft-delete acknowledgement."""

    deleted: Literal[True] = True


class PublicSkillReferenceData(StrictModel):
    """Visible public skill evidence without internal identifiers."""

    name: str
    slug: str


class PublicExperienceData(StrictModel):
    """Public allow-list with no revision, concurrency, creator, or audit fields."""

    id: UUID
    company_name: str
    company_url: str | None
    role_title: str
    employment_type: EmploymentType
    location: str | None
    remote_status: RemoteStatus
    start_date: date
    end_date: date | None
    current_position: bool
    short_summary: str
    detailed_description: str | None
    responsibilities: list[str]
    achievements: list[str]
    technologies: list[str]
    skills: list[PublicSkillReferenceData]
