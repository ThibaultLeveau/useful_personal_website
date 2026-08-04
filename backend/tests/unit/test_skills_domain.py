"""Skills invariants and public projection tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from app.modules.skills.domain import (
    Skill,
    SkillCategory,
    SkillCategoryValues,
    SkillValidationError,
    SkillValues,
    normalize_slug,
    public_skill_groups,
    require_complete_order,
    validate_category_values,
    validate_skill_values,
)

NOW = datetime(2026, 8, 3, tzinfo=UTC)
CATEGORY_ID = UUID("00000000-0000-7000-8000-000000000101")
OTHER_CATEGORY_ID = UUID("00000000-0000-7000-8000-000000000102")
SKILL_ID = UUID("00000000-0000-7000-8000-000000000201")
OTHER_SKILL_ID = UUID("00000000-0000-7000-8000-000000000202")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("API Design", "api-design"), ("Déjà Vu", "deja-vu"), ("python", "python")],
)
def test_slug_normalization_is_deterministic(raw: str, expected: str) -> None:
    """Human slugs normalize once to stable ASCII kebab case."""
    assert normalize_slug(raw) == expected
    assert normalize_slug(expected) == expected


@pytest.mark.parametrize("raw", ["", " spaced", "spaced ", "a\u200bb", "skill\u00a0name", "питон"])
def test_slug_rejects_empty_invisible_or_unsafe_confusable_input(raw: str) -> None:
    """Invisible and non-transliterable confusable input is rejected."""
    with pytest.raises(SkillValidationError):
        normalize_slug(raw)


def _values(**changes: object) -> SkillValues:
    values: dict[str, object] = {
        "name": "Python",
        "slug": "Python",
        "category_id": CATEGORY_ID,
        "description": "Typed backend systems.",
        "proficiency_label": "Advanced",
        "proficiency_score": 90,
        "years_experience": Decimal("8.50"),
        "icon_key": "code",
        "featured": True,
        "visible": True,
    }
    values.update(changes)
    return SkillValues(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("score", [0, 100, None])
def test_score_boundaries_are_accepted(score: int | None) -> None:
    """Optional score accepts both inclusive boundaries."""
    assert validate_skill_values(_values(proficiency_score=score)).proficiency_score == score


@pytest.mark.parametrize("score", [-1, 101, True])
def test_score_outside_contract_is_rejected(score: int) -> None:
    """Score rejects bool and values outside zero through one hundred."""
    with pytest.raises(SkillValidationError) as captured:
        validate_skill_values(_values(proficiency_score=score))
    assert captured.value.path == "proficiency_score"


@pytest.mark.parametrize("years", [Decimal(0), Decimal("3.25"), Decimal("999.99")])
def test_year_boundaries_are_exact(years: Decimal) -> None:
    """Years retain exact two-decimal precision at accepted boundaries."""
    assert validate_skill_values(
        _values(years_experience=years)
    ).years_experience == years.quantize(Decimal("0.01"))


@pytest.mark.parametrize(
    "years",
    [Decimal("-0.01"), Decimal("1.001"), Decimal(1000), Decimal("NaN"), Decimal("Infinity")],
)
def test_invalid_or_silently_roundable_years_are_rejected(years: Decimal) -> None:
    """Negative, over-precise, nonfinite, and unstorable years fail."""
    with pytest.raises(SkillValidationError) as captured:
        validate_skill_values(_values(years_experience=years))
    assert captured.value.path == "years_experience"


def test_category_values_are_normalized_without_trimming_content() -> None:
    """Category slugs normalize while visible text remains exact."""
    values = validate_category_values(
        SkillCategoryValues(name="Backend", slug="Backend Engineering", description=None)
    )
    assert values.slug == "backend-engineering"


def test_order_requires_the_complete_unique_id_set() -> None:
    """Bulk order rejects duplicate or incomplete identifiers."""
    require_complete_order((SKILL_ID, OTHER_SKILL_ID), {OTHER_SKILL_ID, SKILL_ID})
    with pytest.raises(SkillValidationError, match="skill input is invalid"):
        require_complete_order((SKILL_ID, SKILL_ID), {SKILL_ID, OTHER_SKILL_ID})
    with pytest.raises(SkillValidationError, match="skill input is invalid"):
        require_complete_order((SKILL_ID,), {SKILL_ID, OTHER_SKILL_ID})


def _category(identifier: UUID, *, position: int) -> SkillCategory:
    return SkillCategory(
        id=identifier,
        name="Backend" if position == 0 else "Frontend",
        slug="backend" if position == 0 else "frontend",
        description=None,
        position=position,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


def _skill(
    identifier: UUID,
    *,
    category_id: UUID,
    position: int,
    visible: bool,
    featured: bool,
) -> Skill:
    return Skill(
        id=identifier,
        name="Python" if position == 0 else "TypeScript",
        slug="python" if position == 0 else "typescript",
        category_id=category_id,
        description=None,
        proficiency_label=None,
        proficiency_score=None,
        years_experience=Decimal("1.00"),
        icon_key=None,
        position=position,
        featured=featured,
        visible=visible,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


def test_public_groups_omit_hidden_skills_and_empty_categories() -> None:
    """Public projection excludes hidden rows and consequently empty groups."""
    groups = public_skill_groups(
        (_category(OTHER_CATEGORY_ID, position=1), _category(CATEGORY_ID, position=0)),
        (
            _skill(
                SKILL_ID,
                category_id=CATEGORY_ID,
                position=0,
                visible=True,
                featured=True,
            ),
            _skill(
                OTHER_SKILL_ID,
                category_id=OTHER_CATEGORY_ID,
                position=0,
                visible=False,
                featured=True,
            ),
        ),
    )
    assert [group.slug for group in groups] == ["backend"]
    assert [skill.slug for skill in groups[0].skills] == ["python"]
    assert groups[0].skills[0].featured is True
    assert not hasattr(groups[0].skills[0], "version")
