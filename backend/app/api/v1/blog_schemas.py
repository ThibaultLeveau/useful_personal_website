"""Strict administrator, preview/export, taxonomy, and public blog schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.blog.domain import PostLifecycle, TaxonomyKind  # noqa: TC001


class StrictModel(BaseModel):
    """Reject every undeclared mass-assignment field."""

    model_config = ConfigDict(extra="forbid")


Slug = Annotated[str, Field(min_length=1, max_length=80)]
Title = Annotated[str, Field(min_length=1, max_length=180)]
Excerpt = Annotated[str, Field(min_length=1, max_length=500)]
Source = Annotated[str, Field(min_length=1, max_length=100_000)]
Author = Annotated[str, Field(min_length=1, max_length=180)]
RelationIds = Annotated[list[UUID], Field(max_length=30)]
RelatedPostIds = Annotated[list[UUID], Field(max_length=12)]
HttpsUrl = Annotated[str, Field(min_length=1, max_length=2_048)]


class PostInput(StrictModel):
    """Complete mutable post revision input; derivations are deliberately absent."""

    title: Title
    excerpt: Excerpt
    source: Source
    author_display: Author
    tag_ids: RelationIds = Field(default_factory=list)
    category_ids: RelationIds = Field(default_factory=list)
    related_post_ids: RelatedPostIds = Field(default_factory=list)
    seo_title: Annotated[str, Field(min_length=1, max_length=70)] | None = None
    seo_description: Annotated[str, Field(min_length=1, max_length=180)] | None = None
    canonical_url: HttpsUrl | None = None
    cover_media_id: UUID | None = None


class PostCreateRequest(PostInput):
    """Create content plus immutable route and independent visibility."""

    slug: Slug
    visible: bool = True


class PostRevisionData(PostInput):
    """Administrator-visible revision and server derivation metadata."""

    id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    reading_minutes: int
    content_checksum: str
    content_policy_name: str
    content_policy_version: str
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class PostData(StrictModel):
    """Complete administrator post aggregate."""

    id: UUID
    slug: str
    visible: bool
    position: int
    lifecycle: PostLifecycle
    draft: PostRevisionData
    published: PostRevisionData | None
    publish_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None


class SafeRenderedContentData(StrictModel):
    """Sanitized HTML with exact policy provenance."""

    html: str
    policy_name: str
    policy_version: str
    source_checksum: str


class PostPreviewData(StrictModel):
    """Private draft render with explicit indexing prohibition."""

    banner: Literal["Draft preview - not public"] = "Draft preview - not public"
    noindex: Literal[True] = True
    post_id: UUID
    title: str
    excerpt: str
    author_display: str
    cover_media_id: UUID | None
    content: SafeRenderedContentData
    reading_minutes: int


class PostSourceExportData(StrictModel):
    """Private exact normalized source export for generated clients."""

    post_id: UUID
    source: str
    checksum: str
    policy_name: str
    policy_version: str
    reading_minutes: int
    filename: str
    content_type: Literal["text/markdown; charset=utf-8"]


class PublishPostRequest(StrictModel):
    """Publish now when omitted or at one explicit UTC instant."""

    publish_at: datetime | None = None


class ReschedulePostRequest(StrictModel):
    """Replace only the UTC publication instant."""

    publish_at: datetime


class BlogVisibilityRequest(StrictModel):
    """Set independent public visibility."""

    visible: bool


class BlogReorderRequest(StrictModel):
    """Complete duplicate-free stable-ID order."""

    ordered_ids: Annotated[list[UUID], Field(min_length=1, max_length=500)]


class BlogOrderData(StrictModel):
    """One normalized resource order and version."""

    id: UUID
    position: int
    version: int


class BlogOrderListData(StrictModel):
    """Complete normalized resource order."""

    items: list[BlogOrderData]


class BlogDeleteData(StrictModel):
    """Safe soft-delete acknowledgement."""

    deleted: Literal[True] = True


class TaxonomyCreateRequest(StrictModel):
    """Create a stable tag/category identity."""

    kind: TaxonomyKind
    name: Annotated[str, Field(min_length=1, max_length=80)]
    slug: Slug
    visible: bool = True


class TaxonomyUpdateRequest(StrictModel):
    """Update taxonomy presentation without changing its kind."""

    name: Annotated[str, Field(min_length=1, max_length=80)]
    slug: Slug
    visible: bool


class TaxonomyData(StrictModel):
    """Administrator taxonomy projection."""

    id: UUID
    kind: TaxonomyKind
    name: str
    slug: str
    position: int
    visible: bool
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None


class TaxonomyListData(StrictModel):
    """One complete ordered taxonomy collection."""

    items: list[TaxonomyData]


class PublicTaxonomyData(StrictModel):
    """Visible public tag/category label."""

    id: UUID
    name: str
    slug: str


class PublicPostReferenceData(StrictModel):
    """Effective public related-post summary."""

    id: UUID
    slug: str
    title: str
    excerpt: str


class PublicPostData(StrictModel):
    """Public allow-list without source, pointers, creators, or hidden facts."""

    id: UUID
    slug: str
    title: str
    excerpt: str
    author_display: str
    content: SafeRenderedContentData
    reading_minutes: int
    published_at: datetime
    seo_title: str
    seo_description: str
    canonical_url: str | None
    cover_media_id: UUID | None
    tags: list[PublicTaxonomyData]
    categories: list[PublicTaxonomyData]
    related_posts: list[PublicPostReferenceData]
