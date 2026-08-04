"""Persistence-neutral page aggregates, immutable revisions, and lifecycle rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from app.modules.pages.registry import (
    BlockReference,
    BlockType,
    RegistryError,
    validate_and_serialize,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

MAXIMUM_PAGE_BLOCKS = 100
MAXIMUM_PAGE_TITLE_LENGTH = 180
MAXIMUM_DESCRIPTION_LENGTH = 500
MAXIMUM_SEO_TITLE_LENGTH = 70
MAXIMUM_SEO_DESCRIPTION_LENGTH = 180
MAXIMUM_SLUG_LENGTH = 80
MAXIMUM_URL_LENGTH = 2_048
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_SLUGS = frozenset(
    {
        "admin",
        "api",
        "_next",
        "about",
        "experience",
        "experiences",
        "skills",
        "projects",
        "blog",
        "contact",
        "privacy",
        "legal",
        "robots.txt",
        "sitemap.xml",
        "favicon.ico",
        "assets",
        "media",
        "health",
        "docs",
        "openapi.json",
    }
)


class PageRouteKind(StrEnum):
    """Stable route identity: singleton Home or one custom path segment."""

    HOME = "home"
    CUSTOM = "custom"


class PageLifecycle(StrEnum):
    """Derived page state from immutable pointers and PostgreSQL time."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PUBLISHED_CHANGES_PENDING = "published_changes_pending"
    UNPUBLISHED = "unpublished"
    DELETED = "deleted"


class BlockTheme(StrEnum):
    """Reviewed presentation variants only."""

    DEFAULT = "default"
    ACCENT = "accent"
    MUTED = "muted"
    CONTRAST = "contrast"


class BlockLayout(StrEnum):
    """Reviewed width variants that preserve DOM order."""

    CONTAINED = "contained"
    WIDE = "wide"
    FULL = "full"


class PageValidationError(ValueError):
    """Stable field-addressable page or block rejection."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only safe validation facts."""
        super().__init__("page input is invalid")
        self.path = path
        self.code = code


class FrozenPageRevisionError(Exception):
    """A frozen revision or one of its children was targeted for mutation."""


class PagePointerIntegrityError(Exception):
    """Stable aggregate pointers do not reference an internally consistent revision."""


class PagePersistenceError(Exception):
    """A page persistence invariant or required row was unavailable."""


@dataclass(frozen=True, slots=True)
class ResponsiveValues:
    """Bounded responsive visibility and density choices."""

    hide_on_small: bool = False
    hide_on_large: bool = False
    density: str = "comfortable"


@dataclass(frozen=True, slots=True)
class PageBlockValues:
    """Complete canonical mutable values for one revision-owned block."""

    block_type: BlockType
    schema_version: int
    visible: bool
    title: str | None
    subtitle: str | None
    description: str | None
    theme: BlockTheme
    layout: BlockLayout
    responsive: ResponsiveValues
    config: dict[str, object]


@dataclass(frozen=True, slots=True)
class PageBlock:
    """One ordered revision-owned block and its derived references."""

    id: UUID
    revision_id: UUID
    position: int
    values: PageBlockValues
    references: tuple[BlockReference, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PageRevisionValues:
    """Page-level authored and SEO fields."""

    title: str
    description: str
    seo_title: str | None
    seo_description: str | None
    canonical_url: str | None


@dataclass(frozen=True, slots=True)
class PageRevision:
    """One mutable draft or immutable published page snapshot."""

    id: UUID
    page_id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    values: PageRevisionValues
    blocks: tuple[PageBlock, ...]
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Page:
    """Stable page route, lifecycle pointers, and concurrency version."""

    id: UUID
    route_kind: PageRouteKind
    slug: str | None
    visible: bool
    navigation_visible: bool
    position: int
    draft_revision_id: UUID
    published_revision_id: UUID | None
    publish_at: datetime | None
    unpublished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PageSnapshot:
    """Stable aggregate with its draft and optional published revision."""

    page: Page
    draft: PageRevision
    published: PageRevision | None


@dataclass(frozen=True, slots=True)
class AdminPageView:
    """Administrator projection paired with database-time lifecycle."""

    snapshot: PageSnapshot
    lifecycle: PageLifecycle


@dataclass(frozen=True, slots=True)
class PageReferenceTarget:
    """Bounded internal-page facts used to validate and project page references."""

    id: UUID
    route_kind: PageRouteKind
    slug: str | None
    visible: bool
    deleted: bool
    publish_at: datetime | None
    title: str | None
    updated_at: datetime

    @property
    def canonical_path(self) -> str:
        """Return the stable public route without loading the full aggregate."""
        return "/" if self.route_kind is PageRouteKind.HOME else f"/{self.slug}"


@dataclass(frozen=True, slots=True)
class PublicPageRoute:
    """Privacy-safe effective route facts for public discovery metadata."""

    id: UUID
    canonical_path: str
    title: str
    published_at: datetime
    updated_at: datetime


def _safe_text(value: str | None, *, path: str, maximum: int, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise PageValidationError(path=path, code="invalid_text")
        return None
    if not value or value != value.strip() or len(value) > maximum:
        raise PageValidationError(path=path, code="invalid_text")
    if any(
        unicodedata.category(character) in {"Cf", "Cc", "Cs"}
        for character in value
        if character not in "\n\r\t"
    ):
        raise PageValidationError(path=path, code="unsafe_unicode")
    return unicodedata.normalize("NFC", value)


def normalize_page_slug(value: str) -> str:
    """Normalize one custom single-segment slug and reject reserved routes."""
    if not value or value != value.strip():
        raise PageValidationError(path="slug", code="invalid_slug")
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    if (
        not normalized
        or len(normalized) > MAXIMUM_SLUG_LENGTH
        or SLUG_PATTERN.fullmatch(normalized) is None
    ):
        raise PageValidationError(path="slug", code="invalid_slug")
    if normalized in RESERVED_SLUGS:
        raise PageValidationError(path="slug", code="reserved_slug")
    return normalized


def validate_route_identity(route_kind: PageRouteKind, slug: str | None) -> str | None:
    """Enforce the Home/custom identity and reserved-route contract."""
    if route_kind is PageRouteKind.HOME:
        if slug is not None:
            raise PageValidationError(path="slug", code="home_has_no_slug")
        return None
    if slug is None:
        raise PageValidationError(path="slug", code="slug_required")
    return normalize_page_slug(slug)


def _safe_canonical(value: str | None) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAXIMUM_URL_LENGTH:
        raise PageValidationError(path="canonical_url", code="unsafe_url")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise PageValidationError(path="canonical_url", code="unsafe_url")
    return value


def validate_revision_values(values: PageRevisionValues) -> PageRevisionValues:
    """Canonicalize bounded page metadata without reflective fields."""
    return replace(
        values,
        title=_safe_text(
            values.title, path="title", maximum=MAXIMUM_PAGE_TITLE_LENGTH, required=True
        )
        or "",
        description=_safe_text(
            values.description,
            path="description",
            maximum=MAXIMUM_DESCRIPTION_LENGTH,
            required=True,
        )
        or "",
        seo_title=_safe_text(values.seo_title, path="seo_title", maximum=MAXIMUM_SEO_TITLE_LENGTH),
        seo_description=_safe_text(
            values.seo_description, path="seo_description", maximum=MAXIMUM_SEO_DESCRIPTION_LENGTH
        ),
        canonical_url=_safe_canonical(values.canonical_url),
    )


def validate_block_values(
    values: PageBlockValues,
) -> tuple[PageBlockValues, tuple[BlockReference, ...]]:
    """Validate common fields plus the exact type/version config."""
    if values.schema_version < 1:
        raise PageValidationError(path="schema_version", code="invalid_schema_version")
    if values.responsive.density not in {"compact", "comfortable", "spacious"}:
        raise PageValidationError(path="responsive.density", code="invalid_token")
    try:
        config, references = validate_and_serialize(
            values.block_type, values.schema_version, values.config
        )
    except RegistryError as error:
        raise PageValidationError(path=error.path, code=error.code) from error
    return (
        replace(
            values,
            title=_safe_text(values.title, path="title", maximum=180),
            subtitle=_safe_text(values.subtitle, path="subtitle", maximum=240),
            description=_safe_text(values.description, path="description", maximum=500),
            config=config,
        ),
        references,
    )


def validate_block_order(blocks: tuple[PageBlock, ...], *, revision_id: UUID) -> None:
    """Require complete contiguous order and one revision owner."""
    if len(blocks) > MAXIMUM_PAGE_BLOCKS:
        raise PageValidationError(path="blocks", code="too_many_items")
    if tuple(block.position for block in blocks) != tuple(range(len(blocks))):
        raise PageValidationError(path="blocks", code="invalid_order")
    if len({block.id for block in blocks}) != len(blocks):
        raise PageValidationError(path="blocks", code="duplicate_id")
    if any(block.revision_id != revision_id for block in blocks):
        raise PageValidationError(path="blocks", code="foreign_block")


def require_mutable_page_revision(revision: PageRevision) -> None:
    """Reject mutation of a published revision and its owned children."""
    if revision.frozen:
        raise FrozenPageRevisionError


def derive_page_lifecycle(snapshot: PageSnapshot, *, database_now: datetime) -> PageLifecycle:
    """Derive lifecycle without a scheduler or mutable status row."""
    page = snapshot.page
    if page.deleted_at is not None:
        return PageLifecycle.DELETED
    if page.published_revision_id is None:
        return PageLifecycle.UNPUBLISHED if page.unpublished_at is not None else PageLifecycle.DRAFT
    if (
        snapshot.published is None
        or snapshot.published.id != page.published_revision_id
        or page.publish_at is None
    ):
        raise PagePointerIntegrityError
    if page.publish_at > database_now:
        return PageLifecycle.SCHEDULED
    if snapshot.draft.based_on_revision_id != snapshot.published.id:
        return PageLifecycle.PUBLISHED_CHANGES_PENDING
    return PageLifecycle.PUBLISHED


def page_canonical_path(page: Page) -> str:
    """Return the only canonical local route for a page identity."""
    return "/" if page.route_kind is PageRouteKind.HOME else f"/{page.slug}"
