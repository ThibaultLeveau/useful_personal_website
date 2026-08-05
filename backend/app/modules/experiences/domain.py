"""Persistence-neutral professional experience values and lifecycle rules."""

from __future__ import annotations

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

MAXIMUM_COMPANY_LENGTH = 160
MAXIMUM_ROLE_LENGTH = 160
MAXIMUM_LOCATION_LENGTH = 160
MAXIMUM_SUMMARY_LENGTH = 500
MAXIMUM_DESCRIPTION_LENGTH = 20_000
MAXIMUM_ORDERED_ITEM_LENGTH = 1_000
MAXIMUM_ORDERED_ITEMS = 50
MAXIMUM_TECHNOLOGIES = 80
MAXIMUM_URL_LENGTH = 2_048
MAXIMUM_TCP_PORT = 65_535


class EmploymentType(StrEnum):
    """Closed employment-type catalog frozen for the M5 contract."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    APPRENTICESHIP = "apprenticeship"
    TEMPORARY = "temporary"
    SEASONAL = "seasonal"
    VOLUNTEER = "volunteer"


class RemoteStatus(StrEnum):
    """Closed work-location arrangement catalog."""

    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class ExperienceLifecycle(StrEnum):
    """Derived administrator lifecycle labels; never persisted as mutable state."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PUBLISHED_CHANGES_PENDING = "published_changes_pending"
    UNPUBLISHED = "unpublished"
    DELETED = "deleted"


class ExperienceValidationError(ValueError):
    """One stable, field-addressable experience validation failure."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only safe catalog values, never rejected user input."""
        super().__init__("experience input is invalid")
        self.path = path
        self.code = code


class FrozenRevisionError(Exception):
    """A caller attempted to mutate an immutable published revision."""


class PointerIntegrityError(Exception):
    """Aggregate revision pointers do not satisfy the frozen ownership contract."""


@dataclass(frozen=True, slots=True)
class ExperienceValues:
    """Complete validated values owned by one experience revision."""

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
    responsibilities: tuple[str, ...]
    achievements: tuple[str, ...]
    technologies: tuple[str, ...]
    skill_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class ExperienceRevision:
    """One mutable draft or immutable publication snapshot."""

    id: UUID
    experience_id: UUID
    revision_number: int
    based_on_revision_id: UUID | None
    values: ExperienceValues
    frozen: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Experience:
    """Stable aggregate carrying publication pointers and concurrency state."""

    id: UUID
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
class ExperienceSnapshot:
    """Aggregate plus the revisions required by admin lifecycle decisions."""

    experience: Experience
    draft: ExperienceRevision
    published: ExperienceRevision | None


@dataclass(frozen=True, slots=True)
class AdminExperienceView:
    """Administrator snapshot paired with its database-time lifecycle label."""

    snapshot: ExperienceSnapshot
    lifecycle: ExperienceLifecycle


@dataclass(frozen=True, slots=True)
class PublicSkillReference:
    """Public allow-listed skill evidence linked from an experience."""

    name: str
    slug: str


@dataclass(frozen=True, slots=True)
class PublicExperience:
    """Public experience projection with no internal revision or audit data."""

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
    responsibilities: tuple[str, ...]
    achievements: tuple[str, ...]
    technologies: tuple[str, ...]
    skills: tuple[PublicSkillReference, ...]


@dataclass(frozen=True, slots=True)
class PublicExperienceReference:
    """Minimal public-safe experience evidence for downstream content."""

    id: UUID
    company_name: str
    role_title: str


@dataclass(frozen=True, slots=True)
class ExperienceReferenceSummary:
    """Provider-owned admin label and optional effective public projection."""

    id: UUID
    company_name: str
    role_title: str
    visible: bool
    deleted: bool
    public: PublicExperienceReference | None


@dataclass(frozen=True, slots=True)
class AdminExperienceQuery:
    """Allow-listed administrator experience collection inputs."""

    page: PageRequest
    lifecycle: ExperienceLifecycle | None = None
    visible: bool | None = None
    current: bool | None = None
    employment_type: EmploymentType | None = None
    remote_status: RemoteStatus | None = None
    skill_id: UUID | None = None
    search: str | None = None
    sort: str = "position"


@dataclass(frozen=True, slots=True)
class PublicExperienceQuery:
    """Allow-listed public timeline traversal inputs."""

    page: PageRequest
    current: bool | None = None
    employment_type: EmploymentType | None = None
    remote_status: RemoteStatus | None = None
    skill_slug: str | None = None
    sort: str = "chronology"


def _reject_unsafe_text(value: str, *, path: str) -> None:
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cf", "Cc", "Cs"} and character not in {"\n", "\r"}:
            raise ExperienceValidationError(path=path, code="unsafe_unicode")


def _required_text(value: str, *, path: str, maximum: int) -> str:
    if not value or value != value.strip() or len(value) > maximum:
        raise ExperienceValidationError(path=path, code="invalid_text")
    _reject_unsafe_text(value, path=path)
    return value


def _optional_text(value: str | None, *, path: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, path=path, maximum=maximum)


def _safe_https_url(value: str | None) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > MAXIMUM_URL_LENGTH:
        raise ExperienceValidationError(path="company_url", code="unsafe_url")
    _reject_unsafe_text(value, path="company_url")
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise ExperienceValidationError(path="company_url", code="unsafe_url") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or value.startswith("//")
        or "\\" in value
        or (port is not None and not 1 <= port <= MAXIMUM_TCP_PORT)
    ):
        raise ExperienceValidationError(path="company_url", code="unsafe_url")
    return value


def _ordered_text(
    values: Iterable[str],
    *,
    path: str,
    maximum_items: int = MAXIMUM_ORDERED_ITEMS,
) -> tuple[str, ...]:
    items = tuple(values)
    if len(items) > maximum_items:
        raise ExperienceValidationError(path=path, code="too_many_items")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(items):
        item_path = f"{path}.{index}"
        accepted = _required_text(
            value,
            path=item_path,
            maximum=MAXIMUM_ORDERED_ITEM_LENGTH,
        )
        duplicate_key = unicodedata.normalize("NFKC", accepted).casefold()
        if duplicate_key in seen:
            raise ExperienceValidationError(path=item_path, code="duplicate_value")
        seen.add(duplicate_key)
        normalized.append(accepted)
    return tuple(normalized)


def validate_experience_values(values: ExperienceValues) -> ExperienceValues:
    """Validate a complete draft without coercing dates, enums, or ordering."""
    if not isinstance(values.employment_type, EmploymentType):
        raise ExperienceValidationError(path="employment_type", code="unsupported_value")
    if not isinstance(values.remote_status, RemoteStatus):
        raise ExperienceValidationError(path="remote_status", code="unsupported_value")
    if values.end_date is not None and values.end_date < values.start_date:
        raise ExperienceValidationError(path="end_date", code="before_start_date")
    if values.current_position and values.end_date is not None:
        raise ExperienceValidationError(path="end_date", code="current_position_has_end_date")
    if len(values.skill_ids) != len(set(values.skill_ids)):
        raise ExperienceValidationError(path="skill_ids", code="duplicate_id")
    return ExperienceValues(
        company_name=_required_text(
            values.company_name,
            path="company_name",
            maximum=MAXIMUM_COMPANY_LENGTH,
        ),
        company_url=_safe_https_url(values.company_url),
        role_title=_required_text(
            values.role_title,
            path="role_title",
            maximum=MAXIMUM_ROLE_LENGTH,
        ),
        employment_type=values.employment_type,
        location=_optional_text(
            values.location,
            path="location",
            maximum=MAXIMUM_LOCATION_LENGTH,
        ),
        remote_status=values.remote_status,
        start_date=values.start_date,
        end_date=values.end_date,
        current_position=values.current_position,
        short_summary=_required_text(
            values.short_summary,
            path="short_summary",
            maximum=MAXIMUM_SUMMARY_LENGTH,
        ),
        detailed_description=_optional_text(
            values.detailed_description,
            path="detailed_description",
            maximum=MAXIMUM_DESCRIPTION_LENGTH,
        ),
        responsibilities=_ordered_text(values.responsibilities, path="responsibilities"),
        achievements=_ordered_text(values.achievements, path="achievements"),
        technologies=_ordered_text(
            values.technologies,
            path="technologies",
            maximum_items=MAXIMUM_TECHNOLOGIES,
        ),
        skill_ids=values.skill_ids,
    )


def require_mutable_revision(revision: ExperienceRevision) -> None:
    """Reject application-layer writes to a frozen publication snapshot."""
    if revision.frozen:
        raise FrozenRevisionError


def derive_lifecycle(
    snapshot: ExperienceSnapshot, *, database_now: datetime
) -> ExperienceLifecycle:
    """Derive lifecycle from pointers and database-sourced effective time."""
    aggregate = snapshot.experience
    if aggregate.deleted_at is not None:
        return ExperienceLifecycle.DELETED
    if aggregate.published_revision_id is None:
        if aggregate.unpublished_at is not None:
            return ExperienceLifecycle.UNPUBLISHED
        return ExperienceLifecycle.DRAFT
    if aggregate.publish_at is None:
        raise PointerIntegrityError
    if aggregate.publish_at > database_now:
        return ExperienceLifecycle.SCHEDULED
    if snapshot.published is None or snapshot.published.id != aggregate.published_revision_id:
        raise PointerIntegrityError
    if (
        snapshot.draft.experience_id != aggregate.id
        or snapshot.published.experience_id != aggregate.id
    ):
        raise PointerIntegrityError
    if snapshot.draft.based_on_revision_id != snapshot.published.id:
        return ExperienceLifecycle.PUBLISHED_CHANGES_PENDING
    return ExperienceLifecycle.PUBLISHED


def public_chronology_key(item: PublicExperience) -> tuple[object, ...]:
    """Return the documented current-first, newest-start deterministic key."""
    ordinal_end = item.end_date.toordinal() if item.end_date is not None else -1
    return (
        not item.current_position,
        -item.start_date.toordinal(),
        -ordinal_end,
        str(item.id),
    )
