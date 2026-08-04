"""Persistence-neutral blog values, taxonomy, projections, and lifecycle rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from app.common.content_policy import (
    POLICY_NAME,
    POLICY_VERSION,
    ContentPolicyError,
    SafeRenderedContent,
    parse_content,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from app.common.domain.pagination import PageRequest

MAXIMUM_SLUG_LENGTH = 80
MAXIMUM_TITLE_LENGTH = 180
MAXIMUM_EXCERPT_LENGTH = 500
MAXIMUM_AUTHOR_LENGTH = 180
MAXIMUM_TAXONOMY_NAME_LENGTH = 80
MAXIMUM_TAXONOMY_RELATIONS = 30
MAXIMUM_RELATED_POSTS = 12
MAXIMUM_SEO_TITLE_LENGTH = 70
MAXIMUM_SEO_DESCRIPTION_LENGTH = 180
MAXIMUM_URL_LENGTH = 2_048
MAXIMUM_TCP_PORT = 65_535
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TaxonomyKind(StrEnum):
    """Closed blog taxonomy catalog."""

    TAG = "tag"
    CATEGORY = "category"


class PostLifecycle(StrEnum):
    """Derived administrator lifecycle; never mutable persisted state."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PUBLISHED_CHANGES_PENDING = "published_changes_pending"
    UNPUBLISHED = "unpublished"
    DELETED = "deleted"


class BlogValidationError(ValueError):
    """Stable field-addressable blog input rejection."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only catalog facts and never rejected content."""
        super().__init__("blog input is invalid")
        self.path = path
        self.code = code


class FrozenPostRevisionError(Exception):
    """A caller attempted to mutate immutable published content."""


class PostPointerIntegrityError(Exception):
    """Aggregate pointers violate revision ownership or publication rules."""


@dataclass(frozen=True, slots=True)
class PostValues:
    """Complete canonical values and relations for one post revision."""

    title: str
    excerpt: str
    source: str
    author_display: str
    reading_minutes: int
    content_checksum: str
    content_policy_name: str
    content_policy_version: str
    tag_ids: tuple[UUID, ...]
    category_ids: tuple[UUID, ...]
    related_post_ids: tuple[UUID, ...]
    seo_title: str | None
    seo_description: str | None
    canonical_url: str | None
    cover_media_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PostRevision:
    """One mutable draft or immutable publication snapshot."""

    id: UUID
    post_id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    values: PostValues
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Post:
    """Stable route identity, lifecycle pointers, and concurrency state."""

    id: UUID
    slug: str
    visible: bool
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
class PostSnapshot:
    """Stable post aggregate with its draft and optional publication."""

    post: Post
    draft: PostRevision
    published: PostRevision | None


@dataclass(frozen=True, slots=True)
class AdminPostView:
    """Administrator post state paired with database-time lifecycle."""

    snapshot: PostSnapshot
    lifecycle: PostLifecycle


@dataclass(frozen=True, slots=True)
class Taxonomy:
    """Stable ordered tag or category identity."""

    id: UUID
    kind: TaxonomyKind
    name: str
    slug: str
    position: int
    visible: bool
    created_at: datetime
    updated_at: datetime
    version: int
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PublicTaxonomyReference:
    """Allow-listed public taxonomy label."""

    id: UUID
    name: str
    slug: str


@dataclass(frozen=True, slots=True)
class TaxonomyReferenceSummary:
    """Admin taxonomy facts plus an optional public-safe projection."""

    id: UUID
    kind: TaxonomyKind
    name: str
    slug: str
    visible: bool
    deleted: bool
    public: PublicTaxonomyReference | None


@dataclass(frozen=True, slots=True)
class PublicPostReference:
    """Minimal effective related-post link."""

    id: UUID
    slug: str
    title: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class PostReferenceSummary:
    """Admin post label and optional effective public projection."""

    id: UUID
    slug: str
    title: str
    visible: bool
    deleted: bool
    public: PublicPostReference | None


@dataclass(frozen=True, slots=True)
class PublicPost:
    """Complete public article projection without source or internal state."""

    id: UUID
    slug: str
    title: str
    excerpt: str
    author_display: str
    rendered: SafeRenderedContent
    reading_minutes: int
    published_at: datetime
    seo_title: str
    seo_description: str
    canonical_url: str | None
    cover_media_id: UUID | None
    tags: tuple[PublicTaxonomyReference, ...]
    categories: tuple[PublicTaxonomyReference, ...]
    related_posts: tuple[PublicPostReference, ...]


@dataclass(frozen=True, slots=True)
class AdminPostQuery:
    """Allow-listed administrator collection inputs."""

    page: PageRequest
    lifecycle: PostLifecycle | None = None
    visible: bool | None = None
    tag_id: UUID | None = None
    category_id: UUID | None = None
    search: str | None = None
    sort: str = "position"


@dataclass(frozen=True, slots=True)
class PublicPostQuery:
    """Allow-listed public collection inputs."""

    page: PageRequest
    tag_slug: str | None = None
    category_slug: str | None = None
    search: str | None = None
    sort: str = "newest"


def normalize_blog_slug(value: str, *, path: str = "slug") -> str:
    """Normalize a human label to one immutable ASCII route key."""
    if not value or value != value.strip():
        raise BlogValidationError(path=path, code="invalid_slug")
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    if (
        not normalized
        or len(normalized) > MAXIMUM_SLUG_LENGTH
        or SLUG_PATTERN.fullmatch(normalized) is None
    ):
        raise BlogValidationError(path=path, code="invalid_slug")
    return normalized


def _reject_unsafe_text(value: str, *, path: str) -> None:
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cf", "Cc", "Cs"} and character not in {"\n", "\r", "\t"}:
            raise BlogValidationError(path=path, code="unsafe_unicode")


def _required_text(value: str, *, path: str, maximum: int) -> str:
    if not value or value != value.strip() or len(value) > maximum:
        raise BlogValidationError(path=path, code="invalid_text")
    _reject_unsafe_text(value, path=path)
    return unicodedata.normalize("NFC", value)


def _optional_text(value: str | None, *, path: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, path=path, maximum=maximum)


def _safe_https_url(value: str | None, *, path: str) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAXIMUM_URL_LENGTH:
        raise BlogValidationError(path=path, code="unsafe_url")
    _reject_unsafe_text(value, path=path)
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise BlogValidationError(path=path, code="unsafe_url") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or (port is not None and not 1 <= port <= MAXIMUM_TCP_PORT)
    ):
        raise BlogValidationError(path=path, code="unsafe_url")
    return value


def _ordered_ids(
    values: tuple[UUID, ...],
    *,
    path: str,
    maximum: int,
    post_id: UUID | None = None,
) -> tuple[UUID, ...]:
    if len(values) > maximum:
        raise BlogValidationError(path=path, code="too_many_items")
    if len(values) != len(set(values)):
        raise BlogValidationError(path=path, code="duplicate_id")
    if post_id is not None and post_id in values:
        raise BlogValidationError(path=path, code="self_reference")
    return values


def validate_post_values(values: PostValues, *, post_id: UUID | None = None) -> PostValues:
    """Canonicalize post content and replace all server-owned derivations."""
    try:
        document = parse_content(values.source)
    except ContentPolicyError as error:
        raise BlogValidationError(path="source", code=error.code) from error
    return replace(
        values,
        title=_required_text(values.title, path="title", maximum=MAXIMUM_TITLE_LENGTH),
        excerpt=_required_text(values.excerpt, path="excerpt", maximum=MAXIMUM_EXCERPT_LENGTH),
        source=document.source,
        author_display=_required_text(
            values.author_display,
            path="author_display",
            maximum=MAXIMUM_AUTHOR_LENGTH,
        ),
        reading_minutes=document.reading_minutes,
        content_checksum=document.rendered.source_checksum,
        content_policy_name=POLICY_NAME,
        content_policy_version=POLICY_VERSION,
        tag_ids=_ordered_ids(
            values.tag_ids,
            path="tag_ids",
            maximum=MAXIMUM_TAXONOMY_RELATIONS,
        ),
        category_ids=_ordered_ids(
            values.category_ids,
            path="category_ids",
            maximum=MAXIMUM_TAXONOMY_RELATIONS,
        ),
        related_post_ids=_ordered_ids(
            values.related_post_ids,
            path="related_post_ids",
            maximum=MAXIMUM_RELATED_POSTS,
            post_id=post_id,
        ),
        seo_title=_optional_text(
            values.seo_title,
            path="seo_title",
            maximum=MAXIMUM_SEO_TITLE_LENGTH,
        ),
        seo_description=_optional_text(
            values.seo_description,
            path="seo_description",
            maximum=MAXIMUM_SEO_DESCRIPTION_LENGTH,
        ),
        canonical_url=_safe_https_url(values.canonical_url, path="canonical_url"),
    )


def validate_taxonomy(*, kind: TaxonomyKind, name: str, slug: str) -> tuple[str, str]:
    """Validate one stable tag/category identity and return canonical values."""
    canonical_name = _required_text(
        name,
        path=f"{kind.value}.name",
        maximum=MAXIMUM_TAXONOMY_NAME_LENGTH,
    )
    return canonical_name, normalize_blog_slug(slug, path=f"{kind.value}.slug")


def require_mutable_post_revision(revision: PostRevision) -> None:
    """Reject in-place updates to a publication snapshot."""
    if revision.frozen:
        raise FrozenPostRevisionError


def post_seo(values: PostValues) -> tuple[str, str]:
    """Return explicit SEO values or deterministic public fallbacks."""
    return values.seo_title or values.title, values.seo_description or values.excerpt


def derive_post_lifecycle(snapshot: PostSnapshot, *, database_now: datetime) -> PostLifecycle:
    """Derive lifecycle exclusively from pointers, timestamps, and database time."""
    post = snapshot.post
    if post.deleted_at is not None:
        return PostLifecycle.DELETED
    if post.published_revision_id is None:
        return PostLifecycle.UNPUBLISHED if post.unpublished_at is not None else PostLifecycle.DRAFT
    if snapshot.published is None or snapshot.published.id != post.published_revision_id:
        raise PostPointerIntegrityError
    if post.publish_at is None:
        raise PostPointerIntegrityError
    if post.publish_at > database_now:
        return PostLifecycle.SCHEDULED
    if snapshot.draft.based_on_revision_id != snapshot.published.id:
        return PostLifecycle.PUBLISHED_CHANGES_PENDING
    return PostLifecycle.PUBLISHED
