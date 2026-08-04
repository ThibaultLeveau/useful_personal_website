"""Persistence-neutral project values, relations, and lifecycle rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date, datetime
    from uuid import UUID

    from app.common.domain.pagination import PageRequest

MAXIMUM_SLUG_LENGTH = 80
MAXIMUM_NAME_LENGTH = 180
MAXIMUM_SHORT_DESCRIPTION_LENGTH = 500
MAXIMUM_CASE_STUDY_LENGTH = 30_000
MAXIMUM_ROLE_LENGTH = 180
MAXIMUM_TECHNOLOGY_LENGTH = 120
MAXIMUM_TECHNOLOGIES = 80
MAXIMUM_RELATIONS = 50
MAXIMUM_SEO_TITLE_LENGTH = 70
MAXIMUM_SEO_DESCRIPTION_LENGTH = 180
MAXIMUM_URL_LENGTH = 2_048
MAXIMUM_TCP_PORT = 65_535
MAXIMUM_GRAPH_NODES = 256
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RAW_HTML_PATTERN = re.compile(r"<\s*/?\s*(?!https?://)[a-z][^>]*>", re.IGNORECASE)
_MARKDOWN_DESTINATION_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
_UNSAFE_MARKDOWN_SCHEME_PATTERN = re.compile(
    r"(?:\]\(|<)\s*(?:javascript|data|file|mailto):",
    re.IGNORECASE,
)


class ProjectStatus(StrEnum):
    """Closed public project-status catalog."""

    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"


class ProjectLifecycle(StrEnum):
    """Derived administrator lifecycle; never persisted as mutable state."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PUBLISHED_CHANGES_PENDING = "published_changes_pending"
    UNPUBLISHED = "unpublished"
    DELETED = "deleted"


class ProjectValidationError(ValueError):
    """Stable field-addressable project validation failure."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only safe catalog information, never rejected content."""
        super().__init__("project input is invalid")
        self.path = path
        self.code = code


class FrozenProjectRevisionError(Exception):
    """A caller attempted to mutate immutable published project content."""


class ProjectPointerIntegrityError(Exception):
    """Aggregate pointers violate revision ownership or publication rules."""


@dataclass(frozen=True, slots=True)
class ProjectValues:
    """Complete values and revision-scoped relations for one project revision."""

    name: str
    short_description: str
    full_description: str
    problem: str
    solution: str
    impact: str
    owner_role: str
    architecture: str
    technologies: tuple[str, ...]
    status: ProjectStatus
    start_date: date
    end_date: date | None
    repository_url: str | None
    demo_url: str | None
    skill_ids: tuple[UUID, ...]
    experience_ids: tuple[UUID, ...]
    related_project_ids: tuple[UUID, ...]
    seo_title: str | None
    seo_description: str | None
    canonical_url: str | None
    cover_media_id: UUID | None = None
    screenshot_media_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectRevision:
    """One mutable draft or immutable project publication snapshot."""

    id: UUID
    project_id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    values: ProjectValues
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Project:
    """Stable project route identity, lifecycle pointers, and concurrency state."""

    id: UUID
    slug: str
    visible: bool
    featured: bool
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
class ProjectSnapshot:
    """Stable aggregate plus the draft and optional publication."""

    project: Project
    draft: ProjectRevision
    published: ProjectRevision | None


@dataclass(frozen=True, slots=True)
class AdminProjectView:
    """Administrator project state paired with database-time lifecycle."""

    snapshot: ProjectSnapshot
    lifecycle: ProjectLifecycle


@dataclass(frozen=True, slots=True)
class PublicProjectReference:
    """Minimal public-safe related-project link."""

    id: UUID
    slug: str
    name: str


@dataclass(frozen=True, slots=True)
class ProjectReferenceSummary:
    """Admin label and optional effective public projection for consumers."""

    id: UUID
    slug: str
    name: str
    visible: bool
    deleted: bool
    public: PublicProjectReference | None


@dataclass(frozen=True, slots=True)
class PublicProjectSkillReference:
    """Allow-listed skill evidence shown on a public case study."""

    name: str
    slug: str


@dataclass(frozen=True, slots=True)
class PublicProjectExperienceReference:
    """Allow-listed experience evidence shown on a public case study."""

    id: UUID
    company_name: str
    role_title: str


@dataclass(frozen=True, slots=True)
class PublicProject:
    """Complete public case-study projection with no internal lifecycle data."""

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
    technologies: tuple[str, ...]
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
    screenshot_media_ids: tuple[UUID, ...]
    skills: tuple[PublicProjectSkillReference, ...]
    experiences: tuple[PublicProjectExperienceReference, ...]
    related_projects: tuple[PublicProjectReference, ...]


@dataclass(frozen=True, slots=True)
class AdminProjectQuery:
    """Allow-listed administrator project collection inputs."""

    page: PageRequest
    lifecycle: ProjectLifecycle | None = None
    visible: bool | None = None
    featured: bool | None = None
    status: ProjectStatus | None = None
    skill_id: UUID | None = None
    experience_id: UUID | None = None
    search: str | None = None
    sort: str = "position"


@dataclass(frozen=True, slots=True)
class PublicProjectQuery:
    """Allow-listed public case-study collection inputs."""

    page: PageRequest
    status: ProjectStatus | None = None
    technology: str | None = None
    skill_slug: str | None = None
    experience_id: UUID | None = None
    featured: bool | None = None
    search: str | None = None
    sort: str = "default"


def normalize_project_slug(value: str) -> str:
    """Normalize human input to the immutable ASCII route identity."""
    if not value or value != value.strip():
        raise ProjectValidationError(path="slug", code="invalid_slug")
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    if (
        not normalized
        or len(normalized) > MAXIMUM_SLUG_LENGTH
        or SLUG_PATTERN.fullmatch(normalized) is None
    ):
        raise ProjectValidationError(path="slug", code="invalid_slug")
    return normalized


def _reject_unsafe_text(value: str, *, path: str) -> None:
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cf", "Cc", "Cs"} and character not in {"\n", "\r", "\t"}:
            raise ProjectValidationError(path=path, code="unsafe_unicode")


def _required_text(value: str, *, path: str, maximum: int) -> str:
    if not value or value != value.strip() or len(value) > maximum:
        raise ProjectValidationError(path=path, code="invalid_text")
    _reject_unsafe_text(value, path=path)
    return value


def _optional_text(value: str | None, *, path: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, path=path, maximum=maximum)


def _safe_https_url(value: str | None, *, path: str) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAXIMUM_URL_LENGTH:
        raise ProjectValidationError(path=path, code="unsafe_url")
    _reject_unsafe_text(value, path=path)
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise ProjectValidationError(path=path, code="unsafe_url") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or value.startswith("//")
        or "\\" in value
        or (port is not None and not 1 <= port <= MAXIMUM_TCP_PORT)
    ):
        raise ProjectValidationError(path=path, code="unsafe_url")
    return value


def _controlled_markdown(value: str, *, path: str) -> str:
    accepted = _required_text(value, path=path, maximum=MAXIMUM_CASE_STUDY_LENGTH)
    if "<!--" in accepted or _RAW_HTML_PATTERN.search(accepted):
        raise ProjectValidationError(path=path, code="raw_html")
    if _UNSAFE_MARKDOWN_SCHEME_PATTERN.search(accepted):
        raise ProjectValidationError(path=path, code="unsafe_markdown_url")
    for destination in _MARKDOWN_DESTINATION_PATTERN.findall(accepted):
        if not destination.startswith(("https://", "http://", "/", "#")):
            raise ProjectValidationError(path=path, code="unsafe_markdown_url")
    return accepted


def _ordered_technologies(values: Iterable[str]) -> tuple[str, ...]:
    items = tuple(values)
    if not items or len(items) > MAXIMUM_TECHNOLOGIES:
        raise ProjectValidationError(path="technologies", code="invalid_count")
    accepted: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(items):
        item = _required_text(
            value,
            path=f"technologies.{index}",
            maximum=MAXIMUM_TECHNOLOGY_LENGTH,
        )
        key = unicodedata.normalize("NFKC", item).casefold()
        if key in seen:
            raise ProjectValidationError(path=f"technologies.{index}", code="duplicate_value")
        seen.add(key)
        accepted.append(item)
    return tuple(accepted)


def _relation_ids(values: tuple[UUID, ...], *, path: str) -> tuple[UUID, ...]:
    if len(values) > MAXIMUM_RELATIONS:
        raise ProjectValidationError(path=path, code="too_many_items")
    if len(values) != len(set(values)):
        raise ProjectValidationError(path=path, code="duplicate_id")
    return values


def validate_project_values(
    values: ProjectValues, *, project_id: UUID | None = None
) -> ProjectValues:
    """Validate complete project content without coercing enums, dates, or order."""
    if not isinstance(values.status, ProjectStatus):
        raise ProjectValidationError(path="status", code="unsupported_value")
    if values.end_date is not None and values.end_date < values.start_date:
        raise ProjectValidationError(path="end_date", code="before_start_date")
    if (
        values.status in {ProjectStatus.ACTIVE, ProjectStatus.MAINTENANCE, ProjectStatus.PLANNED}
        and values.end_date is not None
    ):
        raise ProjectValidationError(path="end_date", code="status_requires_open_end")
    if (
        values.status in {ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED}
        and values.end_date is None
    ):
        raise ProjectValidationError(path="end_date", code="status_requires_end_date")
    related_project_ids = _relation_ids(
        values.related_project_ids,
        path="related_project_ids",
    )
    if project_id is not None and project_id in related_project_ids:
        raise ProjectValidationError(path="related_project_ids", code="self_reference")
    screenshot_media_ids = _relation_ids(
        values.screenshot_media_ids,
        path="screenshot_media_ids",
    )
    if values.cover_media_id is not None and values.cover_media_id in screenshot_media_ids:
        raise ProjectValidationError(path="screenshot_media_ids", code="duplicate_cover")
    return ProjectValues(
        name=_required_text(values.name, path="name", maximum=MAXIMUM_NAME_LENGTH),
        short_description=_required_text(
            values.short_description,
            path="short_description",
            maximum=MAXIMUM_SHORT_DESCRIPTION_LENGTH,
        ),
        full_description=_controlled_markdown(values.full_description, path="full_description"),
        problem=_controlled_markdown(values.problem, path="problem"),
        solution=_controlled_markdown(values.solution, path="solution"),
        impact=_controlled_markdown(values.impact, path="impact"),
        owner_role=_required_text(
            values.owner_role,
            path="owner_role",
            maximum=MAXIMUM_ROLE_LENGTH,
        ),
        architecture=_controlled_markdown(values.architecture, path="architecture"),
        technologies=_ordered_technologies(values.technologies),
        status=values.status,
        start_date=values.start_date,
        end_date=values.end_date,
        repository_url=_safe_https_url(values.repository_url, path="repository_url"),
        demo_url=_safe_https_url(values.demo_url, path="demo_url"),
        skill_ids=_relation_ids(values.skill_ids, path="skill_ids"),
        experience_ids=_relation_ids(values.experience_ids, path="experience_ids"),
        related_project_ids=related_project_ids,
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
        cover_media_id=values.cover_media_id,
        screenshot_media_ids=screenshot_media_ids,
    )


def require_mutable_project_revision(revision: ProjectRevision) -> None:
    """Reject application-layer writes to a frozen project revision."""
    if revision.frozen:
        raise FrozenProjectRevisionError


def derive_project_lifecycle(
    snapshot: ProjectSnapshot,
    *,
    database_now: datetime,
) -> ProjectLifecycle:
    """Derive publication state from pointers and database-sourced time."""
    aggregate = snapshot.project
    if aggregate.deleted_at is not None:
        return ProjectLifecycle.DELETED
    if aggregate.published_revision_id is None:
        return (
            ProjectLifecycle.UNPUBLISHED
            if aggregate.unpublished_at is not None
            else ProjectLifecycle.DRAFT
        )
    if aggregate.publish_at is None:
        raise ProjectPointerIntegrityError
    if aggregate.publish_at > database_now:
        return ProjectLifecycle.SCHEDULED
    if snapshot.published is None or snapshot.published.id != aggregate.published_revision_id:
        raise ProjectPointerIntegrityError
    if snapshot.draft.project_id != aggregate.id or snapshot.published.project_id != aggregate.id:
        raise ProjectPointerIntegrityError
    if snapshot.draft.based_on_revision_id != snapshot.published.id:
        return ProjectLifecycle.PUBLISHED_CHANGES_PENDING
    return ProjectLifecycle.PUBLISHED


def project_seo(values: ProjectValues) -> tuple[str, str]:
    """Apply safe deterministic metadata fallbacks from public case-study values."""
    return (
        values.seo_title or values.name,
        values.seo_description or values.short_description,
    )
