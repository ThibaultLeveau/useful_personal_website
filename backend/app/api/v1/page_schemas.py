"""Strict administrator, preview/export, and public configurable-page schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves this type at runtime.
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID  # noqa: TC003 - Pydantic resolves this type at runtime.

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from app.api.v1.blog_schemas import SafeRenderedContentData  # noqa: TC001
from app.api.v1.site_configuration_schemas import PublicProfileData, SocialLinkInput
from app.modules.pages.domain import (
    BlockLayout,
    BlockTheme,
    PageLifecycle,
    PageRouteKind,
)
from app.modules.pages.registry import (  # noqa: TC001 - Pydantic runtime schema.
    BlockType,
    CallToActionConfig,
    ContactCalloutConfig,
    DividerConfig,
    ExperienceCollectionConfig,
    HeroConfig,
    ImageConfig,
    ImageWithTextConfig,
    LatestPostsConfig,
    LinksCollectionConfig,
    ProfileSummaryConfig,
    ProjectCollectionConfig,
    RichTextConfig,
    SkillCollectionConfig,
    SpacerConfig,
    StatisticsConfig,
    TestimonialConfig,
)

if TYPE_CHECKING:
    from app.modules.profile.domain import PublicProfile


class StrictModel(BaseModel):
    """Reject every undeclared mass-assignment field."""

    model_config = ConfigDict(extra="forbid")


class ResponsiveData(StrictModel):
    """Bounded responsive presentation choices."""

    hide_on_small: bool = False
    hide_on_large: bool = False
    density: Literal["compact", "comfortable", "spacious"] = "comfortable"


class BlockCommon(StrictModel):
    """Shared explicit block fields; arbitrary styling is absent."""

    schema_version: Literal[1] = 1
    visible: bool = True
    title: Annotated[str, Field(min_length=1, max_length=180)] | None = None
    subtitle: Annotated[str, Field(min_length=1, max_length=240)] | None = None
    description: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    theme: BlockTheme = BlockTheme.DEFAULT
    layout: BlockLayout = BlockLayout.CONTAINED
    responsive: ResponsiveData = Field(default_factory=ResponsiveData)


class HeroBlock(BlockCommon):
    """Hero definition."""

    block_type: Literal[BlockType.HERO]
    config: HeroConfig


class ProfileSummaryBlock(BlockCommon):
    """Profile summary definition."""

    block_type: Literal[BlockType.PROFILE_SUMMARY]
    config: ProfileSummaryConfig


class CallToActionBlock(BlockCommon):
    """Call-to-action definition."""

    block_type: Literal[BlockType.CALL_TO_ACTION]
    config: CallToActionConfig


class StatisticsBlock(BlockCommon):
    """Statistics definition."""

    block_type: Literal[BlockType.STATISTICS]
    config: StatisticsConfig


class SkillsGridBlock(BlockCommon):
    """Skills grid definition."""

    block_type: Literal[BlockType.SKILLS_GRID]
    config: SkillCollectionConfig


class FeaturedSkillsBlock(BlockCommon):
    """Featured skills definition."""

    block_type: Literal[BlockType.FEATURED_SKILLS]
    config: SkillCollectionConfig


class ExperienceSummaryBlock(BlockCommon):
    """Experience summary definition."""

    block_type: Literal[BlockType.EXPERIENCE_SUMMARY]
    config: ExperienceCollectionConfig


class ExperienceListBlock(BlockCommon):
    """Experience list definition."""

    block_type: Literal[BlockType.EXPERIENCE_LIST]
    config: ExperienceCollectionConfig


class ProjectGridBlock(BlockCommon):
    """Project grid definition."""

    block_type: Literal[BlockType.PROJECT_GRID]
    config: ProjectCollectionConfig


class FeaturedProjectsBlock(BlockCommon):
    """Featured projects definition."""

    block_type: Literal[BlockType.FEATURED_PROJECTS]
    config: ProjectCollectionConfig


class LatestPostsBlock(BlockCommon):
    """Latest posts definition."""

    block_type: Literal[BlockType.LATEST_POSTS]
    config: LatestPostsConfig


class RichTextBlock(BlockCommon):
    """Controlled rich-text definition."""

    block_type: Literal[BlockType.RICH_TEXT]
    config: RichTextConfig


class ImageBlock(BlockCommon):
    """Responsive image definition backed by a verified media asset."""

    block_type: Literal[BlockType.IMAGE]
    config: ImageConfig


class ImageWithTextBlock(BlockCommon):
    """Responsive image and authored-text definition."""

    block_type: Literal[BlockType.IMAGE_WITH_TEXT]
    config: ImageWithTextConfig


class LinksCollectionBlock(BlockCommon):
    """Links collection definition."""

    block_type: Literal[BlockType.LINKS_COLLECTION]
    config: LinksCollectionConfig


class ContactCalloutBlock(BlockCommon):
    """Contact callout definition."""

    block_type: Literal[BlockType.CONTACT_CALLOUT]
    config: ContactCalloutConfig


class TestimonialBlock(BlockCommon):
    """Testimonial definition."""

    block_type: Literal[BlockType.TESTIMONIAL]
    config: TestimonialConfig


class DividerBlock(BlockCommon):
    """Decorative divider definition."""

    block_type: Literal[BlockType.DIVIDER]
    config: DividerConfig


class SpacerBlock(BlockCommon):
    """Responsive spacer definition."""

    block_type: Literal[BlockType.SPACER]
    config: SpacerConfig


BlockDefinition = Annotated[
    HeroBlock
    | ProfileSummaryBlock
    | CallToActionBlock
    | StatisticsBlock
    | SkillsGridBlock
    | FeaturedSkillsBlock
    | ExperienceSummaryBlock
    | ExperienceListBlock
    | ProjectGridBlock
    | FeaturedProjectsBlock
    | LatestPostsBlock
    | RichTextBlock
    | ImageBlock
    | ImageWithTextBlock
    | LinksCollectionBlock
    | ContactCalloutBlock
    | TestimonialBlock
    | DividerBlock
    | SpacerBlock,
    Field(discriminator="block_type"),
]
BLOCK_DEFINITION_ADAPTER: TypeAdapter[BlockDefinition] = TypeAdapter(BlockDefinition)


class PublicRichTextConfig(StrictModel):
    """Sanitized public render with policy provenance and no authored source."""

    content: SafeRenderedContentData


class PublicRichTextBlock(BlockCommon):
    """Public controlled-rich-text definition without CommonMark source."""

    block_type: Literal[BlockType.RICH_TEXT]
    config: PublicRichTextConfig


PublicBlockDefinition = Annotated[
    HeroBlock
    | ProfileSummaryBlock
    | CallToActionBlock
    | StatisticsBlock
    | SkillsGridBlock
    | FeaturedSkillsBlock
    | ExperienceSummaryBlock
    | ExperienceListBlock
    | ProjectGridBlock
    | FeaturedProjectsBlock
    | LatestPostsBlock
    | PublicRichTextBlock
    | ImageBlock
    | ImageWithTextBlock
    | LinksCollectionBlock
    | ContactCalloutBlock
    | TestimonialBlock
    | DividerBlock
    | SpacerBlock,
    Field(discriminator="block_type"),
]
PUBLIC_BLOCK_DEFINITION_ADAPTER: TypeAdapter[PublicBlockDefinition] = TypeAdapter(
    PublicBlockDefinition
)


class AddBlockRequest(StrictModel):
    """Insert one discriminated current-version block."""

    block: BlockDefinition
    position: Annotated[int, Field(ge=0, le=100)] | None = None


class UpdateBlockRequest(StrictModel):
    """Complete replacement of one discriminated draft block."""

    block: BlockDefinition


class BlockData(StrictModel):
    """Administrator block identity/order plus its exact definition."""

    id: UUID
    position: int
    definition: BlockDefinition


class PageValuesInput(StrictModel):
    """Complete mutable page-level route, metadata, and visibility fields."""

    route_kind: PageRouteKind
    slug: Annotated[str, Field(min_length=1, max_length=80)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=180)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    seo_title: Annotated[str, Field(min_length=1, max_length=70)] | None = None
    seo_description: Annotated[str, Field(min_length=1, max_length=180)] | None = None
    canonical_url: Annotated[str, Field(min_length=1, max_length=2_048)] | None = None
    visible: bool = True
    navigation_visible: bool = False


class PageCreateRequest(PageValuesInput):
    """Create one stable page and empty initial draft."""


class PageUpdateRequest(PageValuesInput):
    """Complete optimistic replacement of mutable page metadata."""


class PageDuplicateRequest(StrictModel):
    """Duplicate a custom page to one administrator-reviewed slug."""

    slug: Annotated[str, Field(min_length=1, max_length=80)]
    title: Annotated[str, Field(min_length=1, max_length=180)] | None = None


class PageRevisionData(StrictModel):
    """Administrator revision snapshot and its ordered block tree."""

    id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    title: str
    description: str
    seo_title: str | None
    seo_description: str | None
    canonical_url: str | None
    blocks: list[BlockData]
    frozen: bool
    created_at: datetime
    updated_at: datetime


class PageData(StrictModel):
    """Complete administrator page aggregate without raw JSON or pointers."""

    id: UUID
    route_kind: PageRouteKind
    slug: str | None
    visible: bool
    navigation_visible: bool
    position: int
    lifecycle: PageLifecycle
    draft: PageRevisionData
    published: PageRevisionData | None
    publish_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None


class PublishPageRequest(StrictModel):
    """Publish now when omitted or at one explicit UTC instant."""

    publish_at: datetime | None = None


class ReschedulePageRequest(StrictModel):
    """Replace only the UTC publication instant."""

    publish_at: datetime


class BlockVisibilityRequest(StrictModel):
    """Set one draft block's independent visibility."""

    visible: bool


class BlockReorderRequest(StrictModel):
    """Complete duplicate-free draft block order."""

    ordered_ids: Annotated[list[UUID], Field(max_length=100)]


class PublicationIssueData(StrictModel):
    """Safe linked preview/publication issue."""

    block_id: UUID
    path: str
    code: str


class ResolvedReferenceData(StrictModel):
    """Public-safe normalized target projection."""

    kind: str
    target_id: UUID
    label: str
    href: str | None
    description: str | None


class PreviewBlockData(BlockData):
    """Preview block plus only public-safe resolved references."""

    references: list[ResolvedReferenceData]
    profile: PublicProfileData | None = None


class PagePreviewData(StrictModel):
    """Private noindex draft projection with linked issue states."""

    banner: Literal["Draft preview - not public"]
    noindex: Literal[True]
    page: PageData
    blocks: list[PreviewBlockData]
    issues: list[PublicationIssueData]


class PageExportData(StrictModel):
    """Canonical private page export with integrity checksum."""

    page_id: UUID
    manifest: dict[str, JsonValue]
    checksum: str
    filename: str
    content_type: Literal["application/json"] = "application/json"


class PublicPageBlockData(StrictModel):
    """Renderer-ready visible block with exact config and safe target data."""

    id: UUID
    position: int
    definition: PublicBlockDefinition
    references: list[ResolvedReferenceData]
    profile: PublicProfileData | None = None


def public_profile_data(profile: PublicProfile | None) -> PublicProfileData | None:
    """Map an approved profile projection without reviving private fields."""
    if profile is None:
        return None
    values = (
        profile.full_name,
        profile.professional_title,
        profile.short_biography,
        profile.full_biography,
        profile.location,
        profile.availability,
        profile.email,
        profile.social_links,
        profile.github_url,
        profile.linkedin_url,
        profile.personal_values,
        profile.work_preferences,
        profile.resume_url,
        profile.contact_preference,
    )
    return PublicProfileData(
        configured=any(value is not None for value in values),
        full_name=profile.full_name,
        professional_title=profile.professional_title,
        short_biography=profile.short_biography,
        full_biography=profile.full_biography,
        location=profile.location,
        availability=profile.availability,
        email=profile.email,
        social_links=(
            [SocialLinkInput(label=item.label, url=item.url) for item in profile.social_links]
            if profile.social_links is not None
            else None
        ),
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        personal_values=(
            list(profile.personal_values) if profile.personal_values is not None else None
        ),
        work_preferences=(
            list(profile.work_preferences) if profile.work_preferences is not None else None
        ),
        resume_url=profile.resume_url,
        contact_preference=profile.contact_preference,
    )


class PublicPageData(StrictModel):
    """Effective public page without draft, pointer, config-shell, or audit fields."""

    id: UUID
    route_kind: PageRouteKind
    slug: str | None
    title: str
    description: str
    seo_title: str
    seo_description: str
    canonical_path: str
    canonical_url: str | None
    published_at: datetime
    blocks: list[PublicPageBlockData]


class PublicPageRouteData(StrictModel):
    """Effective public route facts for discovery and sitemap generation."""

    id: UUID
    canonical_path: str
    title: str
    published_at: datetime
    updated_at: datetime


class PageDeleteData(StrictModel):
    """Safe soft-delete acknowledgement."""

    deleted: Literal[True] = True


class RegistryEntryData(StrictModel):
    """Public administrator-facing palette facts without executable names."""

    block_type: BlockType
    schema_version: int
    renderer_key: str
    group: Literal["narrative", "evidence", "media", "conversion"]
    media_required: bool


class RegistryData(StrictModel):
    """Exact frozen palette manifest."""

    entries: list[RegistryEntryData]
