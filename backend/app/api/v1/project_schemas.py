"""Strict administrator, preview, and public schemas for projects."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.domain import (  # noqa: TC001
    ProjectLifecycle,
    ProjectStatus,
)


class StrictModel(BaseModel):
    """Reject every undeclared mass-assignment field."""

    model_config = ConfigDict(extra="forbid")


Name = Annotated[str, Field(min_length=1, max_length=180)]
Slug = Annotated[str, Field(min_length=1, max_length=80)]
Summary = Annotated[str, Field(min_length=1, max_length=500)]
CaseStudy = Annotated[str, Field(min_length=1, max_length=30_000)]
Role = Annotated[str, Field(min_length=1, max_length=180)]
Technologies = Annotated[list[str], Field(min_length=1, max_length=80)]
RelationIds = Annotated[list[UUID], Field(max_length=50)]
HttpsUrl = Annotated[str, Field(min_length=1, max_length=2_048)]


class ProjectInput(StrictModel):
    """Complete mutable project revision values."""

    name: Name
    short_description: Summary
    full_description: CaseStudy
    problem: CaseStudy
    solution: CaseStudy
    impact: CaseStudy
    owner_role: Role
    architecture: CaseStudy
    technologies: Technologies
    status: ProjectStatus
    start_date: date
    end_date: date | None = None
    repository_url: HttpsUrl | None = None
    demo_url: HttpsUrl | None = None
    skill_ids: RelationIds = Field(default_factory=list)
    experience_ids: RelationIds = Field(default_factory=list)
    related_project_ids: RelationIds = Field(default_factory=list)
    seo_title: Annotated[str, Field(min_length=1, max_length=70)] | None = None
    seo_description: Annotated[str, Field(min_length=1, max_length=180)] | None = None
    canonical_url: HttpsUrl | None = None
    cover_media_id: UUID | None = None
    screenshot_media_ids: RelationIds = Field(default_factory=list)


class ProjectCreateRequest(ProjectInput):
    """Create content plus immutable slug and independent display flags."""

    slug: Slug
    visible: bool = True
    featured: bool = False


class ProjectRevisionData(ProjectInput):
    """Administrator-visible revision metadata and values."""

    id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ProjectData(StrictModel):
    """Complete administrator project aggregate."""

    id: UUID
    slug: str
    visible: bool
    featured: bool
    position: int
    lifecycle: ProjectLifecycle
    draft: ProjectRevisionData
    published: ProjectRevisionData | None
    publish_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None


class ProjectPreviewData(StrictModel):
    """Private draft projection with explicit indexing prohibition."""

    banner: Literal["Draft preview - not public"] = "Draft preview - not public"
    noindex: Literal[True] = True
    project: ProjectData


class PublishProjectRequest(StrictModel):
    """Publish now when omitted or at an explicit UTC instant."""

    publish_at: datetime | None = None


class RescheduleProjectRequest(StrictModel):
    """Replace only the UTC publication instant."""

    publish_at: datetime


class VisibilityRequest(StrictModel):
    """Set independent public visibility."""

    visible: bool


class FeaturedRequest(StrictModel):
    """Set independent featured state."""

    featured: bool


class ReorderProjectsRequest(StrictModel):
    """Complete duplicate-free aggregate order."""

    ordered_ids: Annotated[list[UUID], Field(min_length=1, max_length=500)]


class ProjectOrderData(StrictModel):
    """One aggregate's normalized order and version."""

    id: UUID
    position: int
    version: int


class ProjectOrderListData(StrictModel):
    """Complete normalized aggregate order."""

    items: list[ProjectOrderData]


class DeleteProjectData(StrictModel):
    """Safe soft-delete acknowledgement."""

    deleted: Literal[True] = True


class PublicSkillReferenceData(StrictModel):
    """Visible public skill evidence."""

    name: str
    slug: str


class PublicExperienceReferenceData(StrictModel):
    """Effective public professional-experience evidence."""

    id: UUID
    company_name: str
    role_title: str


class PublicProjectReferenceData(StrictModel):
    """Effective public related-project link."""

    id: UUID
    slug: str
    name: str


class PublicProjectData(StrictModel):
    """Public allow-list without revisions, creator, or storage identifiers."""

    id: UUID
    slug: str
    name: str
    short_description: str
    full_description: str
    problem: str
    solution: str
    impact: str
    owner_role: str
    architecture: str
    technologies: list[str]
    status: ProjectStatus
    start_date: date
    end_date: date | None
    repository_url: str | None
    demo_url: str | None
    featured: bool
    seo_title: str
    seo_description: str
    canonical_url: str | None
    cover_media_id: UUID | None
    screenshot_media_ids: list[UUID]
    skills: list[PublicSkillReferenceData]
    experiences: list[PublicExperienceReferenceData]
    related_projects: list[PublicProjectReferenceData]
