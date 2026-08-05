"""Focused M5 experience invariant and lifecycle tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import pytest

from app.modules.experiences.domain import (
    EmploymentType,
    Experience,
    ExperienceLifecycle,
    ExperienceRevision,
    ExperienceSnapshot,
    ExperienceValidationError,
    ExperienceValues,
    FrozenRevisionError,
    PublicExperience,
    RemoteStatus,
    derive_lifecycle,
    public_chronology_key,
    require_mutable_revision,
    validate_experience_values,
)

EXPERIENCE_ID = UUID("0198a12c-0000-7000-8000-000000000001")
DRAFT_ID = UUID("0198a12c-0000-7000-8000-000000000002")
PUBLISHED_ID = UUID("0198a12c-0000-7000-8000-000000000003")
ACTOR_ID = UUID("0198a12c-0000-7000-8000-000000000004")
NOW = datetime(2026, 8, 3, 10, tzinfo=UTC)


def _values() -> ExperienceValues:
    return ExperienceValues(
        company_name="Example Studio",
        company_url="https://example.test/careers",
        role_title="Staff Engineer",
        employment_type=EmploymentType.FULL_TIME,
        location="Paris, France",
        remote_status=RemoteStatus.HYBRID,
        start_date=date(2024, 1, 1),
        end_date=None,
        current_position=True,
        short_summary="Led the platform team.",
        detailed_description="A bounded plain-text description. <script> remains text.",
        responsibilities=("Designed service boundaries", "Mentored engineers"),
        achievements=("Reduced deployment time",),
        technologies=("Python", "PostgreSQL"),
        skill_ids=(UUID("0198a12c-0000-7000-8000-000000000010"),),
    )


def _revision(identifier: UUID, *, frozen: bool) -> ExperienceRevision:
    return ExperienceRevision(
        id=identifier,
        experience_id=EXPERIENCE_ID,
        revision_number=1 if frozen else 2,
        based_on_revision_id=None if frozen else PUBLISHED_ID,
        values=_values(),
        frozen=frozen,
        created_by=ACTOR_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _snapshot(
    *,
    published_id: UUID | None = None,
    publish_at: datetime | None = None,
    unpublished_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> ExperienceSnapshot:
    draft = _revision(DRAFT_ID, frozen=False)
    published = _revision(PUBLISHED_ID, frozen=True) if published_id is not None else None
    return ExperienceSnapshot(
        experience=Experience(
            id=EXPERIENCE_ID,
            visible=True,
            position=0,
            draft_revision_id=DRAFT_ID,
            published_revision_id=published_id,
            publish_at=publish_at,
            unpublished_at=unpublished_at,
            created_at=NOW,
            updated_at=NOW,
            version=1,
            deleted_at=deleted_at,
        ),
        draft=draft,
        published=published,
    )


def test_accepts_complete_ordered_plain_text_values() -> None:
    """Ordered fields survive validation and plain text stays non-executable data."""
    accepted = validate_experience_values(_values())

    assert accepted.responsibilities == ("Designed service boundaries", "Mentored engineers")
    assert (
        accepted.detailed_description == "A bounded plain-text description. <script> remains text."
    )


@pytest.mark.parametrize(
    ("field", "value", "path", "code"),
    [
        ("company_name", "", "company_name", "invalid_text"),
        ("role_title", " Staff Engineer", "role_title", "invalid_text"),
        ("company_url", "http://example.test", "company_url", "unsafe_url"),
        ("company_url", "https://user:secret@example.test", "company_url", "unsafe_url"),
        ("company_url", "javascript:alert(1)", "company_url", "unsafe_url"),
        ("end_date", date(2023, 12, 31), "end_date", "before_start_date"),
    ],
)
def test_rejects_field_addressable_invalid_values(
    field: str,
    value: object,
    path: str,
    code: str,
) -> None:
    """Invalid scalar/date inputs expose only stable field and code values."""
    changes = cast("dict[str, Any]", {field: value})
    with pytest.raises(ExperienceValidationError) as caught:
        validate_experience_values(replace(_values(), **changes))

    assert (caught.value.path, caught.value.code) == (path, code)


def test_current_position_rejects_an_end_date() -> None:
    """A current role cannot also declare an end date."""
    with pytest.raises(ExperienceValidationError) as caught:
        validate_experience_values(replace(_values(), end_date=date(2026, 1, 1)))

    assert (caught.value.path, caught.value.code) == (
        "end_date",
        "current_position_has_end_date",
    )


def test_noncurrent_position_may_have_an_unknown_end_date() -> None:
    """An ended/unknown role does not receive an invented end date."""
    assert validate_experience_values(replace(_values(), current_position=False)).end_date is None


@pytest.mark.parametrize("field", ["responsibilities", "achievements", "technologies"])
def test_ordered_content_rejects_normalized_duplicates(field: str) -> None:
    """Case-normalized duplicate ordered items fail at their exact index."""
    changes = cast("dict[str, Any]", {field: ("Python", "python")})
    with pytest.raises(ExperienceValidationError) as caught:
        validate_experience_values(replace(_values(), **changes))

    assert caught.value.code == "duplicate_value"
    assert caught.value.path == f"{field}.1"


def test_skill_relations_are_duplicate_free() -> None:
    """One revision cannot carry the same skill relation twice."""
    skill_id = _values().skill_ids[0]
    with pytest.raises(ExperienceValidationError) as caught:
        validate_experience_values(replace(_values(), skill_ids=(skill_id, skill_id)))

    assert (caught.value.path, caught.value.code) == ("skill_ids", "duplicate_id")


def test_frozen_revision_cannot_be_mutated() -> None:
    """The domain write guard rejects a published revision."""
    with pytest.raises(FrozenRevisionError):
        require_mutable_revision(_revision(PUBLISHED_ID, frozen=True))

    require_mutable_revision(_revision(DRAFT_ID, frozen=False))


@pytest.mark.parametrize(
    ("snapshot", "expected"),
    [
        (_snapshot(), ExperienceLifecycle.DRAFT),
        (
            _snapshot(published_id=PUBLISHED_ID, publish_at=NOW + timedelta(hours=1)),
            ExperienceLifecycle.SCHEDULED,
        ),
        (
            _snapshot(published_id=PUBLISHED_ID, publish_at=NOW),
            ExperienceLifecycle.PUBLISHED,
        ),
        (
            _snapshot(unpublished_at=NOW),
            ExperienceLifecycle.UNPUBLISHED,
        ),
        (
            _snapshot(deleted_at=NOW),
            ExperienceLifecycle.DELETED,
        ),
    ],
)
def test_lifecycle_is_derived_from_pointers_and_database_time(
    snapshot: ExperienceSnapshot,
    expected: ExperienceLifecycle,
) -> None:
    """Lifecycle is derived without any background status mutation."""
    assert derive_lifecycle(snapshot, database_now=NOW) is expected


def test_changed_copy_on_write_draft_is_pending_without_changing_live_revision() -> None:
    """A changed draft derives pending state while the frozen snapshot stays intact."""
    snapshot = _snapshot(published_id=PUBLISHED_ID, publish_at=NOW)
    changed_draft = replace(
        snapshot.draft,
        based_on_revision_id=None,
        values=replace(snapshot.draft.values, role_title="Principal Engineer"),
    )

    assert (
        derive_lifecycle(replace(snapshot, draft=changed_draft), database_now=NOW)
        is ExperienceLifecycle.PUBLISHED_CHANGES_PENDING
    )
    assert snapshot.published is not None
    assert snapshot.published.values.role_title == "Staff Engineer"


def test_public_chronology_is_current_then_start_then_end_then_id() -> None:
    """Public chronology places current roles first and applies stable tie-breakers."""

    def item(
        identifier: str,
        start: date,
        end: date | None,
        *,
        current: bool,
    ) -> PublicExperience:
        values = _values()
        return PublicExperience(
            id=UUID(identifier),
            company_name=values.company_name,
            company_url=values.company_url,
            role_title=values.role_title,
            employment_type=values.employment_type,
            location=values.location,
            remote_status=values.remote_status,
            start_date=start,
            end_date=end,
            current_position=current,
            short_summary=values.short_summary,
            detailed_description=values.detailed_description,
            responsibilities=values.responsibilities,
            achievements=values.achievements,
            technologies=values.technologies,
            skills=(),
        )

    rows = (
        item(
            "0198a12c-0000-7000-8000-000000000023",
            date(2025, 1, 1),
            None,
            current=False,
        ),
        item(
            "0198a12c-0000-7000-8000-000000000021",
            date(2024, 1, 1),
            None,
            current=True,
        ),
        item(
            "0198a12c-0000-7000-8000-000000000022",
            date(2026, 1, 1),
            None,
            current=False,
        ),
    )

    assert [row.id for row in sorted(rows, key=public_chronology_key)] == [
        UUID("0198a12c-0000-7000-8000-000000000021"),
        UUID("0198a12c-0000-7000-8000-000000000022"),
        UUID("0198a12c-0000-7000-8000-000000000023"),
    ]
