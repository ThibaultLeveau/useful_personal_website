"""Closed, versioned page-block schemas and deterministic reference extraction."""

from __future__ import annotations

import json
import math
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Literal, cast
from urllib.parse import urlsplit
from uuid import UUID  # noqa: TC003 - Pydantic resolves this type at runtime.

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.common.content_policy import ContentPolicyError, parse_content

MAXIMUM_CONFIG_BYTES = 32_768
MAXIMUM_CONFIG_DEPTH = 8
MAXIMUM_STRING_LENGTH = 4_000
MAXIMUM_COLLECTION_ITEMS = 24
MAXIMUM_URL_LENGTH = 2_048
MAXIMUM_TCP_PORT = 65_535
EXPECTED_BLOCK_COUNT = 19
_UNSAFE_DESTINATION = "unsafe destination"


class BlockType(StrEnum):
    """The exact nineteen block kinds accepted by SPEC section 5.2."""

    HERO = "hero"
    PROFILE_SUMMARY = "profile_summary"
    CALL_TO_ACTION = "call_to_action"
    STATISTICS = "statistics"
    SKILLS_GRID = "skills_grid"
    FEATURED_SKILLS = "featured_skills"
    EXPERIENCE_SUMMARY = "experience_summary"
    EXPERIENCE_LIST = "experience_list"
    PROJECT_GRID = "project_grid"
    FEATURED_PROJECTS = "featured_projects"
    LATEST_POSTS = "latest_posts"
    RICH_TEXT = "rich_text"
    IMAGE = "image"
    IMAGE_WITH_TEXT = "image_with_text"
    LINKS_COLLECTION = "links_collection"
    CONTACT_CALLOUT = "contact_callout"
    TESTIMONIAL = "testimonial"
    DIVIDER = "divider"
    SPACER = "spacer"


class ReferenceKind(StrEnum):
    """Closed provider/reference destinations."""

    PROFILE = "profile"
    SKILL = "skill"
    EXPERIENCE = "experience"
    PROJECT = "project"
    POST = "post"
    PAGE = "page"
    MEDIA = "media"


class ReferenceRole(StrEnum):
    """Closed semantic roles for normalized references."""

    PROFILE_EVIDENCE = "profile_evidence"
    SKILL_ITEM = "skill_item"
    EXPERIENCE_ITEM = "experience_item"
    PROJECT_ITEM = "project_item"
    POST_ITEM = "post_item"
    INTERNAL_DESTINATION = "internal_destination"
    MEDIA_PRIMARY = "media_primary"


class RegistryError(ValueError):
    """The registry or a payload violates the frozen catalog contract."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only a safe field path and stable catalog code."""
        super().__init__("page block registry validation failed")
        self.path = path
        self.code = code


class StrictConfig(BaseModel):
    """Base for every block config; unknown fields are never persisted."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


ShortText = Annotated[str, Field(min_length=1, max_length=180)]
BodyText = Annotated[str, Field(min_length=1, max_length=1_200)]
BoundedCount = Annotated[int, Field(ge=1, le=24)]


def _safe_destination(value: str | None) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAXIMUM_URL_LENGTH:
        raise ValueError(_UNSAFE_DESTINATION)
    parsed = urlsplit(value)
    if value.startswith("/") and not value.startswith("//") and not parsed.netloc:
        return value
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError(_UNSAFE_DESTINATION)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(_UNSAFE_DESTINATION) from error
    if port is not None and not 1 <= port <= MAXIMUM_TCP_PORT:
        raise ValueError(_UNSAFE_DESTINATION)
    return value


class ActionConfig(StrictConfig):
    """One named internal or HTTPS action."""

    label: Annotated[str, Field(min_length=1, max_length=80)]
    destination: Annotated[str, Field(min_length=1, max_length=2_048)] | None = None
    page_id: UUID | None = None
    new_window: bool = False

    _destination_policy = field_validator("destination")(_safe_destination)

    @model_validator(mode="after")
    def validate_target(self) -> ActionConfig:
        """Require exactly one direct destination or normalized custom-page target."""
        if (self.destination is None) == (self.page_id is None):
            message = "exactly one action target is required"
            raise ValueError(message)
        if self.page_id is not None and self.new_window:
            message = "internal page targets cannot open a new window"
            raise ValueError(message)
        return self


class HeroConfig(StrictConfig):
    """Primary page introduction with bounded actions and optional profile evidence."""

    eyebrow: Annotated[str, Field(min_length=1, max_length=80)] | None = None
    heading: ShortText
    body: BodyText
    actions: Annotated[tuple[ActionConfig, ...], Field(max_length=2)] = ()
    include_profile_evidence: bool = False


class ProfileSummaryConfig(StrictConfig):
    """Public-approved profile projection options."""

    show_biography: bool = True
    show_location: bool = True
    about_destination: str = "/about"

    _destination_policy = field_validator("about_destination")(_safe_destination)


class CallToActionConfig(StrictConfig):
    """Conversion copy with one to three safe actions."""

    heading: ShortText
    body: BodyText
    actions: Annotated[tuple[ActionConfig, ...], Field(min_length=1, max_length=3)]


class StatisticItem(StrictConfig):
    """One authored, non-executable evidence value."""

    value: Annotated[str, Field(min_length=1, max_length=40)]
    label: Annotated[str, Field(min_length=1, max_length=80)]
    context: Annotated[str, Field(min_length=1, max_length=160)] | None = None


class StatisticsConfig(StrictConfig):
    """Bounded ordered evidence items."""

    items: Annotated[tuple[StatisticItem, ...], Field(min_length=1, max_length=12)]


class SkillCollectionConfig(StrictConfig):
    """Explicit or bounded public skill selection."""

    skill_ids: Annotated[tuple[UUID, ...], Field(max_length=24)] = ()
    maximum_items: BoundedCount = 12


class ExperienceCollectionConfig(StrictConfig):
    """Explicit or bounded public experience selection."""

    experience_ids: Annotated[tuple[UUID, ...], Field(max_length=24)] = ()
    maximum_items: BoundedCount = 8


class ProjectCollectionConfig(StrictConfig):
    """Explicit or bounded public project selection."""

    project_ids: Annotated[tuple[UUID, ...], Field(max_length=24)] = ()
    maximum_items: BoundedCount = 12


class LatestPostsConfig(StrictConfig):
    """Explicit or recent public article selection."""

    post_ids: Annotated[tuple[UUID, ...], Field(max_length=12)] = ()
    maximum_items: Annotated[int, Field(ge=1, le=12)] = 3


class RichTextConfig(StrictConfig):
    """M7-policy-controlled CommonMark source."""

    source: Annotated[str, Field(min_length=1, max_length=100_000)]

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """Reuse the M7 CommonMark policy and retain canonical source only."""
        try:
            return parse_content(value).source
        except ContentPolicyError as error:
            raise ValueError(error.code) from error


class ImageConfig(StrictConfig):
    """Validated primary media reference and authored use metadata."""

    media_id: UUID
    purpose: Literal["content", "portrait", "illustration"] = "content"
    alt: Annotated[str, Field(min_length=1, max_length=300)]
    caption: Annotated[str, Field(min_length=1, max_length=300)] | None = None
    focal_point: Literal["center", "top", "bottom", "left", "right"] = "center"


class ImageWithTextConfig(ImageConfig):
    """Validated media use paired with safe authored copy."""

    heading: ShortText
    body: BodyText
    image_position: Literal["start", "end"] = "start"
    action: ActionConfig | None = None


class LinkItem(ActionConfig):
    """One descriptive link in a bounded collection."""

    description: Annotated[str, Field(min_length=1, max_length=240)] | None = None


class LinksCollectionConfig(StrictConfig):
    """Bounded ordered named destinations."""

    links: Annotated[tuple[LinkItem, ...], Field(min_length=1, max_length=16)]


class ContactCalloutConfig(CallToActionConfig):
    """Contact-oriented copy without form submission behavior."""


class TestimonialConfig(StrictConfig):
    """Administrator-authored quote with attribution."""

    quote: Annotated[str, Field(min_length=1, max_length=1_000)]
    attribution: Annotated[str, Field(min_length=1, max_length=120)]
    context: Annotated[str, Field(min_length=1, max_length=180)] | None = None


class DividerConfig(StrictConfig):
    """Decorative divider style token."""

    style: Literal["line", "dots", "subtle"] = "line"


class SpacerConfig(StrictConfig):
    """Bounded responsive spacing tokens."""

    size: Literal["small", "medium", "large"] = "medium"
    narrow_size: Literal["small", "medium", "large"] = "small"


@dataclass(frozen=True, slots=True)
class BlockReference:
    """One reference derived by trusted registry code, never client-assigned."""

    kind: ReferenceKind
    target_id: UUID
    role: ReferenceRole
    position: int
    required: bool


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """One complete canonical kind/version contract."""

    block_type: BlockType
    schema_version: int
    config_model: type[StrictConfig]
    renderer_key: str
    group: Literal["narrative", "evidence", "media", "conversion"]
    media_required: bool = False


_ENTRIES = (
    RegistryEntry(BlockType.HERO, 1, HeroConfig, "hero", "narrative"),
    RegistryEntry(
        BlockType.PROFILE_SUMMARY, 1, ProfileSummaryConfig, "profile_summary", "evidence"
    ),
    RegistryEntry(BlockType.CALL_TO_ACTION, 1, CallToActionConfig, "call_to_action", "conversion"),
    RegistryEntry(BlockType.STATISTICS, 1, StatisticsConfig, "statistics", "evidence"),
    RegistryEntry(BlockType.SKILLS_GRID, 1, SkillCollectionConfig, "skills_grid", "evidence"),
    RegistryEntry(
        BlockType.FEATURED_SKILLS, 1, SkillCollectionConfig, "featured_skills", "evidence"
    ),
    RegistryEntry(
        BlockType.EXPERIENCE_SUMMARY,
        1,
        ExperienceCollectionConfig,
        "experience_summary",
        "evidence",
    ),
    RegistryEntry(
        BlockType.EXPERIENCE_LIST, 1, ExperienceCollectionConfig, "experience_list", "evidence"
    ),
    RegistryEntry(BlockType.PROJECT_GRID, 1, ProjectCollectionConfig, "project_grid", "evidence"),
    RegistryEntry(
        BlockType.FEATURED_PROJECTS, 1, ProjectCollectionConfig, "featured_projects", "evidence"
    ),
    RegistryEntry(BlockType.LATEST_POSTS, 1, LatestPostsConfig, "latest_posts", "evidence"),
    RegistryEntry(BlockType.RICH_TEXT, 1, RichTextConfig, "rich_text", "narrative"),
    RegistryEntry(BlockType.IMAGE, 1, ImageConfig, "image", "media", media_required=True),
    RegistryEntry(
        BlockType.IMAGE_WITH_TEXT,
        1,
        ImageWithTextConfig,
        "image_with_text",
        "media",
        media_required=True,
    ),
    RegistryEntry(
        BlockType.LINKS_COLLECTION, 1, LinksCollectionConfig, "links_collection", "conversion"
    ),
    RegistryEntry(
        BlockType.CONTACT_CALLOUT, 1, ContactCalloutConfig, "contact_callout", "conversion"
    ),
    RegistryEntry(BlockType.TESTIMONIAL, 1, TestimonialConfig, "testimonial", "narrative"),
    RegistryEntry(BlockType.DIVIDER, 1, DividerConfig, "divider", "narrative"),
    RegistryEntry(BlockType.SPACER, 1, SpacerConfig, "spacer", "narrative"),
)

BLOCK_REGISTRY: dict[BlockType, RegistryEntry] = {entry.block_type: entry for entry in _ENTRIES}


def _validate_registry() -> None:
    expected = set(BlockType)
    if len(_ENTRIES) != EXPECTED_BLOCK_COUNT or set(BLOCK_REGISTRY) != expected:
        message = "page block registry must contain the exact nineteen SPEC kinds"
        raise RuntimeError(message)
    renderers = [entry.renderer_key for entry in _ENTRIES]
    if len(renderers) != len(set(renderers)):
        message = "page block renderer keys must be unique"
        raise RuntimeError(message)
    if any(entry.schema_version < 1 for entry in _ENTRIES):
        message = "page block schema versions must be positive"
        raise RuntimeError(message)


_validate_registry()


def _validate_json_shape(  # noqa: C901, PLR0912 - explicit fail-closed JSON walker.
    value: object, *, path: str = "config", depth: int = 0
) -> None:
    if depth > MAXIMUM_CONFIG_DEPTH:
        raise RegistryError(path=path, code="config_too_deep")
    if isinstance(value, dict):
        if len(value) > MAXIMUM_COLLECTION_ITEMS:
            raise RegistryError(path=path, code="too_many_items")
        for key, child in value.items():
            if not isinstance(key, str):
                raise RegistryError(path=path, code="non_string_key")
            if key in {"__proto__", "prototype", "constructor"}:
                raise RegistryError(path=f"{path}.{key}", code="unsafe_key")
            _validate_json_shape(child, path=f"{path}.{key}", depth=depth + 1)
    elif isinstance(value, (list, tuple)):
        if len(value) > MAXIMUM_COLLECTION_ITEMS:
            raise RegistryError(path=path, code="too_many_items")
        for index, child in enumerate(value):
            _validate_json_shape(child, path=f"{path}.{index}", depth=depth + 1)
    elif isinstance(value, str):
        if len(value) > MAXIMUM_STRING_LENGTH and path != "config.source":
            raise RegistryError(path=path, code="string_too_long")
        if any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"} and character not in "\n\r\t"
            for character in value
        ):
            raise RegistryError(path=path, code="unsafe_unicode")
    elif isinstance(value, float) and not math.isfinite(value):
        raise RegistryError(path=path, code="nonfinite_number")
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise RegistryError(path=path, code="invalid_json_type")


def deserialize_config(block_type: BlockType, schema_version: int, raw: object) -> StrictConfig:
    """Validate one exact kind/version payload and reject compatibility guesses."""
    entry = BLOCK_REGISTRY.get(block_type)
    if entry is None:
        raise RegistryError(path="block_type", code="unknown_block_type")
    if schema_version != entry.schema_version:
        raise RegistryError(path="schema_version", code="unsupported_schema_version")
    _validate_json_shape(raw)
    try:
        return entry.config_model.model_validate(raw)
    except ValidationError as error:
        first = error.errors(include_input=False)[0]
        suffix = ".".join(str(item) for item in first["loc"])
        raise RegistryError(
            path=f"config.{suffix}" if suffix else "config",
            code="invalid_config",
        ) from error


def canonical_config(config: StrictConfig) -> dict[str, object]:
    """Return stable JSON primitives for storage and checksums."""
    value = cast("dict[str, object]", config.model_dump(mode="json", exclude_none=True))
    encoded = json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    if len(encoded.encode()) > MAXIMUM_CONFIG_BYTES:
        raise RegistryError(path="config", code="config_too_large")
    return value


def canonical_config_bytes(config: StrictConfig) -> bytes:
    """Serialize canonically without platform-dependent whitespace."""
    return json.dumps(
        canonical_config(config),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def config_checksum(config: StrictConfig) -> str:
    """Return the portable SHA-256 checksum used by exports and fixtures."""
    return sha256(canonical_config_bytes(config)).hexdigest()


def _references(
    kind: ReferenceKind, role: ReferenceRole, ids: tuple[UUID, ...], *, required: bool
) -> tuple[BlockReference, ...]:
    if len(ids) != len(set(ids)):
        raise RegistryError(path="config", code="duplicate_reference")
    return tuple(
        BlockReference(kind, item, role, position, required) for position, item in enumerate(ids)
    )


def _action_references(actions: tuple[ActionConfig, ...]) -> tuple[BlockReference, ...]:
    page_ids = tuple(action.page_id for action in actions if action.page_id is not None)
    return _references(
        ReferenceKind.PAGE,
        ReferenceRole.INTERNAL_DESTINATION,
        page_ids,
        required=True,
    )


def extract_references(  # noqa: C901, PLR0911 - closed kinds are deliberately explicit.
    block_type: BlockType, config: StrictConfig
) -> tuple[BlockReference, ...]:
    """Derive ordered normalized references from validated config only."""
    if block_type is BlockType.HERO:
        return _action_references(cast("HeroConfig", config).actions)
    if block_type is BlockType.PROFILE_SUMMARY:
        return ()
    if block_type in {BlockType.CALL_TO_ACTION, BlockType.CONTACT_CALLOUT}:
        return _action_references(cast("CallToActionConfig", config).actions)
    if block_type in {BlockType.SKILLS_GRID, BlockType.FEATURED_SKILLS}:
        skills = cast("SkillCollectionConfig", config)
        return _references(
            ReferenceKind.SKILL, ReferenceRole.SKILL_ITEM, skills.skill_ids, required=False
        )
    if block_type in {BlockType.EXPERIENCE_SUMMARY, BlockType.EXPERIENCE_LIST}:
        experiences = cast("ExperienceCollectionConfig", config)
        return _references(
            ReferenceKind.EXPERIENCE,
            ReferenceRole.EXPERIENCE_ITEM,
            experiences.experience_ids,
            required=False,
        )
    if block_type in {BlockType.PROJECT_GRID, BlockType.FEATURED_PROJECTS}:
        projects = cast("ProjectCollectionConfig", config)
        return _references(
            ReferenceKind.PROJECT,
            ReferenceRole.PROJECT_ITEM,
            projects.project_ids,
            required=False,
        )
    if block_type is BlockType.LATEST_POSTS:
        posts = cast("LatestPostsConfig", config)
        return _references(
            ReferenceKind.POST, ReferenceRole.POST_ITEM, posts.post_ids, required=False
        )
    if block_type in {BlockType.IMAGE, BlockType.IMAGE_WITH_TEXT}:
        image = cast("ImageConfig", config)
        media = _references(
            ReferenceKind.MEDIA,
            ReferenceRole.MEDIA_PRIMARY,
            (image.media_id,),
            required=True,
        )
        if block_type is BlockType.IMAGE_WITH_TEXT:
            action = cast("ImageWithTextConfig", config).action
            return media + (() if action is None else _action_references((action,)))
        return media
    if block_type is BlockType.LINKS_COLLECTION:
        return _action_references(cast("LinksCollectionConfig", config).links)
    return ()


def validate_and_serialize(
    block_type: BlockType, schema_version: int, raw: object
) -> tuple[dict[str, object], tuple[BlockReference, ...]]:
    """Canonicalize config and extract the only accepted reference rows."""
    config = deserialize_config(block_type, schema_version, raw)
    return canonical_config(config), extract_references(block_type, config)


def upgrade_config(
    block_type: BlockType, from_version: int, raw: object
) -> tuple[int, dict[str, object]]:
    """Validate current data; version one has no legacy write-time adapter."""
    entry = BLOCK_REGISTRY[block_type]
    if from_version != entry.schema_version:
        raise RegistryError(path="schema_version", code="unsupported_schema_version")
    return entry.schema_version, canonical_config(deserialize_config(block_type, from_version, raw))


REGISTRY_MANIFEST: tuple[dict[str, Any], ...] = tuple(
    {
        "block_type": entry.block_type.value,
        "schema_version": entry.schema_version,
        "renderer_key": entry.renderer_key,
        "group": entry.group,
        "media_required": entry.media_required,
    }
    for entry in _ENTRIES
)
