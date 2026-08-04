"""M6 project content, relation, media, and lifecycle invariants."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import pytest

from app.modules.projects.domain import (
    FrozenProjectRevisionError,
    Project,
    ProjectLifecycle,
    ProjectRevision,
    ProjectSnapshot,
    ProjectStatus,
    ProjectValidationError,
    ProjectValues,
    derive_project_lifecycle,
    normalize_project_slug,
    project_seo,
    require_mutable_project_revision,
    validate_project_values,
)

PROJECT_ID = UUID("0198a13d-0000-7000-8000-000000000001")
DRAFT_ID = UUID("0198a13d-0000-7000-8000-000000000002")
PUBLISHED_ID = UUID("0198a13d-0000-7000-8000-000000000003")
ACTOR_ID = UUID("0198a13d-0000-7000-8000-000000000004")
SKILL_ID = UUID("0198a13d-0000-7000-8000-000000000005")
EXPERIENCE_ID = UUID("0198a13d-0000-7000-8000-000000000006")
RELATED_ID = UUID("0198a13d-0000-7000-8000-000000000007")
NOW = datetime(2026, 8, 4, 8, tzinfo=UTC)


def _values() -> ProjectValues:
    return ProjectValues(
        name="Release observability platform",
        short_description="Made delivery health understandable before a release reached users.",
        full_description="A **bounded** case study with [architecture notes](/about).",
        problem="Teams could not connect delivery changes to reliability outcomes.",
        solution="Built a typed event pipeline and a review-oriented interface.",
        impact="Reduced diagnosis time and made release risk visible.",
        owner_role="Technical lead and primary implementer",
        architecture="FastAPI services, PostgreSQL, and a server-rendered Next.js interface.",
        technologies=("Python", "PostgreSQL", "Next.js"),
        status=ProjectStatus.ACTIVE,
        start_date=date(2025, 1, 1),
        end_date=None,
        repository_url="https://github.com/example/release-observability",
        demo_url="https://projects.example.test/release-observability",
        skill_ids=(SKILL_ID,),
        experience_ids=(EXPERIENCE_ID,),
        related_project_ids=(RELATED_ID,),
        seo_title=None,
        seo_description=None,
        canonical_url=None,
    )


def _revision(identifier: UUID, *, frozen: bool) -> ProjectRevision:
    return ProjectRevision(
        id=identifier,
        project_id=PROJECT_ID,
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
    published: bool = False,
    publish_at: datetime | None = None,
    unpublished_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> ProjectSnapshot:
    return ProjectSnapshot(
        project=Project(
            id=PROJECT_ID,
            slug="release-observability",
            visible=True,
            featured=True,
            position=0,
            draft_revision_id=DRAFT_ID,
            published_revision_id=PUBLISHED_ID if published else None,
            publish_at=publish_at,
            unpublished_at=unpublished_at,
            created_at=NOW,
            updated_at=NOW,
            version=1,
            deleted_at=deleted_at,
        ),
        draft=_revision(DRAFT_ID, frozen=False),
        published=_revision(PUBLISHED_ID, frozen=True) if published else None,
    )


def test_normalizes_unicode_slug_to_stable_ascii_kebab_case() -> None:
    """Human slug input becomes one deterministic case-insensitive route key."""
    assert normalize_project_slug("Café Release  Observatory") == "cafe-release-observatory"
    with pytest.raises(ProjectValidationError) as caught:
        normalize_project_slug("---")
    assert (caught.value.path, caught.value.code) == ("slug", "invalid_slug")


def test_accepts_complete_controlled_case_study_and_metadata_fallback() -> None:
    """Ordered evidence and controlled Markdown survive without executable HTML."""
    accepted = validate_project_values(_values(), project_id=PROJECT_ID)
    assert accepted.technologies == ("Python", "PostgreSQL", "Next.js")
    assert project_seo(accepted) == (accepted.name, accepted.short_description)


@pytest.mark.parametrize(
    ("field", "value", "path", "code"),
    [
        ("name", "", "name", "invalid_text"),
        ("repository_url", "http://example.test/repo", "repository_url", "unsafe_url"),
        (
            "demo_url",
            "https://user:secret@example.test",
            "demo_url",
            "unsafe_url",
        ),
        ("canonical_url", "javascript:alert(1)", "canonical_url", "unsafe_url"),
        ("end_date", date(2024, 1, 1), "end_date", "before_start_date"),
        (
            "full_description",
            "Safe text <script>alert(1)</script>",
            "full_description",
            "raw_html",
        ),
        (
            "problem",
            "[unsafe](javascript:alert(1))",
            "problem",
            "unsafe_markdown_url",
        ),
    ],
)
def test_rejects_field_addressable_content_date_and_url_errors(
    field: str,
    value: object,
    path: str,
    code: str,
) -> None:
    """Rejected input exposes stable issue facts without echoing content."""
    changes = cast("dict[str, Any]", {field: value})
    with pytest.raises(ProjectValidationError) as caught:
        validate_project_values(replace(_values(), **changes), project_id=PROJECT_ID)
    assert (caught.value.path, caught.value.code) == (path, code)


@pytest.mark.parametrize("status", [ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED])
def test_terminal_status_requires_end_date(status: ProjectStatus) -> None:
    """Terminal project states cannot silently omit their end date."""
    with pytest.raises(ProjectValidationError) as caught:
        validate_project_values(replace(_values(), status=status), project_id=PROJECT_ID)
    assert caught.value.code == "status_requires_end_date"


def test_active_status_rejects_end_date_and_paused_status_permits_it() -> None:
    """Active work stays open while paused work may preserve a known interval."""
    ended = replace(_values(), end_date=date(2026, 1, 1))
    with pytest.raises(ProjectValidationError) as caught:
        validate_project_values(ended, project_id=PROJECT_ID)
    assert caught.value.code == "status_requires_open_end"
    assert validate_project_values(
        replace(ended, status=ProjectStatus.PAUSED),
        project_id=PROJECT_ID,
    ).end_date == date(2026, 1, 1)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("technologies", ("Python", "python"), "duplicate_value"),
        ("skill_ids", (SKILL_ID, SKILL_ID), "duplicate_id"),
        ("experience_ids", (EXPERIENCE_ID, EXPERIENCE_ID), "duplicate_id"),
        ("related_project_ids", (RELATED_ID, RELATED_ID), "duplicate_id"),
        ("related_project_ids", (PROJECT_ID,), "self_reference"),
    ],
)
def test_ordered_evidence_and_relations_reject_duplicates_or_self_edges(
    field: str,
    value: object,
    code: str,
) -> None:
    """Revision-owned ordered collections remain duplicate-free and graph-safe."""
    changes = cast("dict[str, Any]", {field: value})
    with pytest.raises(ProjectValidationError) as caught:
        validate_project_values(replace(_values(), **changes), project_id=PROJECT_ID)
    assert caught.value.code == code


def test_media_references_are_preserved_and_cover_cannot_repeat_in_gallery() -> None:
    """M9 accepts typed IDs while keeping the cover distinct from screenshots."""
    screenshot_id = UUID("0198a12c-7000-7000-8000-000000000009")
    accepted = validate_project_values(
        replace(
            _values(),
            cover_media_id=RELATED_ID,
            screenshot_media_ids=(screenshot_id,),
        ),
        project_id=PROJECT_ID,
    )
    assert accepted.cover_media_id == RELATED_ID
    assert accepted.screenshot_media_ids == (screenshot_id,)

    with pytest.raises(ProjectValidationError) as caught:
        validate_project_values(
            replace(
                _values(),
                cover_media_id=RELATED_ID,
                screenshot_media_ids=(RELATED_ID,),
            ),
            project_id=PROJECT_ID,
        )
    assert (caught.value.path, caught.value.code) == (
        "screenshot_media_ids",
        "duplicate_cover",
    )


def test_frozen_project_revision_cannot_be_mutated() -> None:
    """The domain guard rejects in-place writes to a publication."""
    with pytest.raises(FrozenProjectRevisionError):
        require_mutable_project_revision(_revision(PUBLISHED_ID, frozen=True))
    require_mutable_project_revision(_revision(DRAFT_ID, frozen=False))


@pytest.mark.parametrize(
    ("snapshot", "expected"),
    [
        (_snapshot(), ProjectLifecycle.DRAFT),
        (
            _snapshot(published=True, publish_at=NOW + timedelta(hours=1)),
            ProjectLifecycle.SCHEDULED,
        ),
        (_snapshot(published=True, publish_at=NOW), ProjectLifecycle.PUBLISHED),
        (_snapshot(unpublished_at=NOW), ProjectLifecycle.UNPUBLISHED),
        (_snapshot(deleted_at=NOW), ProjectLifecycle.DELETED),
    ],
)
def test_lifecycle_uses_pointers_and_database_time(
    snapshot: ProjectSnapshot,
    expected: ProjectLifecycle,
) -> None:
    """No worker or application-clock status mutation is required."""
    assert derive_project_lifecycle(snapshot, database_now=NOW) is expected


def test_changed_copy_on_write_draft_derives_pending_state() -> None:
    """Draft changes cannot mutate the frozen public case study."""
    snapshot = _snapshot(published=True, publish_at=NOW)
    changed = replace(
        snapshot.draft,
        based_on_revision_id=None,
        values=replace(snapshot.draft.values, impact="A newly measured outcome."),
    )
    assert (
        derive_project_lifecycle(replace(snapshot, draft=changed), database_now=NOW)
        is ProjectLifecycle.PUBLISHED_CHANGES_PENDING
    )
    assert snapshot.published is not None
    assert snapshot.published.values.impact == _values().impact
