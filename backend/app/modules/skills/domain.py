"""Persistence-neutral skills values, invariants, and public projections."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from uuid import UUID

    from app.common.domain.pagination import PageRequest

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ICON_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAXIMUM_SLUG_LENGTH = 80
MAXIMUM_NAME_LENGTH = 120
MAXIMUM_DESCRIPTION_LENGTH = 2_000
MAXIMUM_PROFICIENCY_LABEL_LENGTH = 80
MAXIMUM_ICON_KEY_LENGTH = 64
MAXIMUM_YEARS_EXPERIENCE = Decimal("999.99")
YEARS_QUANTUM = Decimal("0.01")
MAXIMUM_PROFICIENCY_SCORE = 100
MINIMUM_YEARS_EXPONENT = -2


class SkillValidationError(ValueError):
    """A skill/category value violates a stable field-addressable rule."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain only a safe field path and stable validation code."""
        super().__init__("skill input is invalid")
        self.path = path
        self.code = code


class CategoryInUseError(Exception):
    """A category with skills cannot be deleted."""


class RelationProviderUnavailableError(Exception):
    """A future experience/project relation provider is not installed."""


class SkillsSlugConflictError(Exception):
    """A normalized skill/category slug is already used."""

    def __init__(self, path: str) -> None:
        """Retain only the stable conflicting field path."""
        super().__init__("normalized slug is already used")
        self.path = path


@dataclass(frozen=True, slots=True)
class SkillCategoryValues:
    """Validated category write values."""

    name: str
    slug: str
    description: str | None


@dataclass(frozen=True, slots=True)
class SkillCategory:
    """One flat globally ordered skill category."""

    id: UUID
    name: str
    slug: str
    description: str | None
    position: int
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class SkillValues:
    """Validated skill write values; relation writes are deliberately absent."""

    name: str
    slug: str
    category_id: UUID
    description: str | None
    proficiency_label: str | None
    proficiency_score: int | None
    years_experience: Decimal
    icon_key: str | None
    featured: bool
    visible: bool


@dataclass(frozen=True, slots=True)
class Skill:
    """One administrator-managed skill."""

    id: UUID
    name: str
    slug: str
    category_id: UUID
    description: str | None
    proficiency_label: str | None
    proficiency_score: int | None
    years_experience: Decimal
    icon_key: str | None
    position: int
    featured: bool
    visible: bool
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class SkillReferenceSummary:
    """Safe inward-facing reference used by later content modules."""

    id: UUID
    name: str
    slug: str
    visible: bool


@dataclass(frozen=True, slots=True)
class PublicSkill:
    """Public-only skill shape with no version, timestamps, or relation IDs."""

    name: str
    slug: str
    description: str | None
    proficiency_label: str | None
    proficiency_score: int | None
    years_experience: Decimal
    icon_key: str | None
    featured: bool
    position: int


@dataclass(frozen=True, slots=True)
class PublicSkillGroup:
    """One non-empty category and its visible skills."""

    name: str
    slug: str
    description: str | None
    position: int
    skills: tuple[PublicSkill, ...]


@dataclass(frozen=True, slots=True)
class AdminSkillQuery:
    """Allow-listed administrator collection inputs."""

    page: PageRequest
    category_id: UUID | None = None
    visible: bool | None = None
    featured: bool | None = None
    search: str | None = None
    sort: str = "position"


@dataclass(frozen=True, slots=True)
class PublicSkillQuery:
    """Allow-listed public collection inputs."""

    page: PageRequest
    category_slug: str | None = None
    featured: bool | None = None
    search: str | None = None
    sort: str = "position"


def _reject_unsafe_unicode(value: str, *, path: str) -> None:
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cf", "Cc", "Cs"}:
            raise SkillValidationError(path=path, code="unsafe_unicode")
        if character.isspace() and character != " ":
            raise SkillValidationError(path=path, code="unsafe_whitespace")
        if character.isalnum() and not character.isascii():
            ascii_form = unicodedata.normalize("NFKD", character).encode("ascii", "ignore")
            if not any(chr(byte).isalnum() for byte in ascii_form):
                raise SkillValidationError(path=path, code="unsafe_confusable")


def normalize_slug(value: str, *, path: str = "slug") -> str:
    """Normalize a human slug to ASCII kebab case without silent confusables."""
    if value != value.strip() or not value:
        raise SkillValidationError(path=path, code="invalid_slug")
    _reject_unsafe_unicode(value, path=path)
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    if (
        not normalized
        or len(normalized) > MAXIMUM_SLUG_LENGTH
        or _SLUG_PATTERN.fullmatch(normalized) is None
    ):
        raise SkillValidationError(path=path, code="invalid_slug")
    return normalized


def _required_text(value: str, *, path: str, maximum: int) -> str:
    if value != value.strip() or not value or len(value) > maximum:
        raise SkillValidationError(path=path, code="invalid_text")
    _reject_unsafe_unicode(value, path=path)
    return value


def _optional_text(value: str | None, *, path: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _required_text(value, path=path, maximum=maximum)


def validate_category_values(values: SkillCategoryValues) -> SkillCategoryValues:
    """Normalize and validate one complete category input."""
    return SkillCategoryValues(
        name=_required_text(values.name, path="name", maximum=MAXIMUM_NAME_LENGTH),
        slug=normalize_slug(values.slug),
        description=_optional_text(
            values.description,
            path="description",
            maximum=MAXIMUM_DESCRIPTION_LENGTH,
        ),
    )


def validate_skill_values(values: SkillValues) -> SkillValues:
    """Normalize one skill without rounding/coercing numeric values."""
    score = values.proficiency_score
    if score is not None and (
        isinstance(score, bool) or score < 0 or score > MAXIMUM_PROFICIENCY_SCORE
    ):
        raise SkillValidationError(path="proficiency_score", code="out_of_range")
    years = values.years_experience
    years_exponent = years.as_tuple().exponent
    if (
        not years.is_finite()
        or years < 0
        or years > MAXIMUM_YEARS_EXPERIENCE
        or not isinstance(years_exponent, int)
        or years_exponent < MINIMUM_YEARS_EXPONENT
    ):
        raise SkillValidationError(path="years_experience", code="out_of_range")
    icon = values.icon_key
    if icon is not None and (
        len(icon) > MAXIMUM_ICON_KEY_LENGTH or _ICON_PATTERN.fullmatch(icon) is None
    ):
        raise SkillValidationError(path="icon_key", code="invalid_icon")
    return SkillValues(
        name=_required_text(values.name, path="name", maximum=MAXIMUM_NAME_LENGTH),
        slug=normalize_slug(values.slug),
        category_id=values.category_id,
        description=_optional_text(
            values.description,
            path="description",
            maximum=MAXIMUM_DESCRIPTION_LENGTH,
        ),
        proficiency_label=_optional_text(
            values.proficiency_label,
            path="proficiency_label",
            maximum=MAXIMUM_PROFICIENCY_LABEL_LENGTH,
        ),
        proficiency_score=score,
        years_experience=years.quantize(YEARS_QUANTUM),
        icon_key=icon,
        featured=values.featured,
        visible=values.visible,
    )


def require_complete_order(
    submitted_ids: tuple[UUID, ...],
    expected_ids: Iterable[UUID],
    *,
    path: str = "items",
) -> None:
    """Require one complete duplicate-free authorized reorder set."""
    expected = set(expected_ids)
    if len(submitted_ids) != len(set(submitted_ids)):
        raise SkillValidationError(path=path, code="duplicate_id")
    if set(submitted_ids) != expected:
        raise SkillValidationError(path=path, code="incomplete_order")


def public_skill_groups(
    categories: Iterable[SkillCategory],
    skills: Iterable[Skill],
) -> tuple[PublicSkillGroup, ...]:
    """Group only visible skills and omit categories with no public rows."""
    visible_by_category: dict[UUID, list[Skill]] = {}
    for skill in skills:
        if skill.visible:
            visible_by_category.setdefault(skill.category_id, []).append(skill)
    groups: list[PublicSkillGroup] = []
    for category in sorted(categories, key=lambda item: (item.position, item.id)):
        visible = visible_by_category.get(category.id, [])
        if not visible:
            continue
        ordered = sorted(visible, key=lambda item: (item.position, item.id))
        groups.append(
            PublicSkillGroup(
                name=category.name,
                slug=category.slug,
                description=category.description,
                position=category.position,
                skills=tuple(
                    PublicSkill(
                        name=skill.name,
                        slug=skill.slug,
                        description=skill.description,
                        proficiency_label=skill.proficiency_label,
                        proficiency_score=skill.proficiency_score,
                        years_experience=skill.years_experience,
                        icon_key=skill.icon_key,
                        featured=skill.featured,
                        position=skill.position,
                    )
                    for skill in ordered
                ),
            )
        )
    return tuple(groups)
