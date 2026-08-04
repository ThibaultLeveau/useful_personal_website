"""M8 page identity, lifecycle, ordering, and frozen-revision proofs."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.modules.pages.domain import (
    AdminPageView,
    BlockLayout,
    BlockTheme,
    FrozenPageRevisionError,
    Page,
    PageBlock,
    PageBlockValues,
    PageLifecycle,
    PageRevision,
    PageRevisionValues,
    PageRouteKind,
    PageSnapshot,
    PageValidationError,
    ResponsiveValues,
    derive_page_lifecycle,
    normalize_page_slug,
    page_canonical_path,
    require_mutable_page_revision,
    validate_block_order,
    validate_block_values,
    validate_revision_values,
    validate_route_identity,
)
from app.modules.pages.registry import BlockType

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)
PAGE_ID = UUID("0198a13d-8100-7000-8000-000000000001")
DRAFT_ID = UUID("0198a13d-8100-7000-8000-000000000002")
PUBLISHED_ID = UUID("0198a13d-8100-7000-8000-000000000003")
BLOCK_ID = UUID("0198a13d-8100-7000-8000-000000000004")
ACTOR_ID = UUID("0198a13d-8100-7000-8000-000000000005")


def _revision(identifier: UUID, *, frozen: bool, based_on: UUID | None = None) -> PageRevision:
    return PageRevision(
        id=identifier,
        page_id=PAGE_ID,
        revision_number=1 if frozen else 2,
        based_on_revision_id=based_on,
        values=PageRevisionValues("Work", "Selected evidence.", None, None, None),
        blocks=(),
        frozen=frozen,
        created_by=ACTOR_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _snapshot(*, published: bool = False, publish_at: datetime | None = None) -> PageSnapshot:
    return PageSnapshot(
        page=Page(
            id=PAGE_ID,
            route_kind=PageRouteKind.CUSTOM,
            slug="work",
            visible=True,
            navigation_visible=False,
            position=0,
            draft_revision_id=DRAFT_ID,
            published_revision_id=PUBLISHED_ID if published else None,
            publish_at=publish_at,
            unpublished_at=None,
            created_at=NOW,
            updated_at=NOW,
            version=1,
        ),
        draft=_revision(DRAFT_ID, frozen=False, based_on=PUBLISHED_ID if published else None),
        published=_revision(PUBLISHED_ID, frozen=True) if published else None,
    )


def test_home_and_custom_route_identity_are_unambiguous() -> None:
    """Home has no slug while custom routes normalize and reserve platform paths."""
    assert validate_route_identity(PageRouteKind.HOME, None) is None
    assert normalize_page_slug("Caf\u00e9 Work") == "cafe-work"
    assert validate_route_identity(PageRouteKind.CUSTOM, "Case Studies") == "case-studies"
    assert page_canonical_path(_snapshot().page) == "/work"
    with pytest.raises(PageValidationError) as reserved:
        normalize_page_slug("ADMIN")
    assert reserved.value.code == "reserved_slug"
    with pytest.raises(PageValidationError):
        validate_route_identity(PageRouteKind.HOME, "home")
    with pytest.raises(PageValidationError):
        validate_route_identity(PageRouteKind.CUSTOM, None)


def test_page_and_block_values_are_canonical_and_strict() -> None:
    """Common and type-specific fields are validated before persistence."""
    values = validate_revision_values(
        PageRevisionValues("Work", "A focused selection.", None, None, "https://example.test/work")
    )
    assert values.title == "Work"
    block_values, references = validate_block_values(
        PageBlockValues(
            block_type=BlockType.HERO,
            schema_version=1,
            visible=True,
            title=None,
            subtitle=None,
            description=None,
            theme=BlockTheme.DEFAULT,
            layout=BlockLayout.CONTAINED,
            responsive=ResponsiveValues(),
            config={"heading": "Selected work", "body": "Evidence over claims."},
        )
    )
    assert block_values.config["heading"] == "Selected work"
    assert references == ()


def test_complete_order_rejects_gaps_duplicates_and_foreign_children() -> None:
    """Only a contiguous complete block list belongs to one revision."""
    values, references = validate_block_values(
        PageBlockValues(
            block_type=BlockType.DIVIDER,
            schema_version=1,
            visible=True,
            title=None,
            subtitle=None,
            description=None,
            theme=BlockTheme.DEFAULT,
            layout=BlockLayout.CONTAINED,
            responsive=ResponsiveValues(),
            config={"style": "line"},
        )
    )
    block = PageBlock(BLOCK_ID, DRAFT_ID, 0, values, references, NOW, NOW)
    validate_block_order((block,), revision_id=DRAFT_ID)
    with pytest.raises(PageValidationError):
        validate_block_order((replace(block, position=1),), revision_id=DRAFT_ID)
    with pytest.raises(PageValidationError):
        validate_block_order((block, block), revision_id=DRAFT_ID)
    with pytest.raises(PageValidationError):
        validate_block_order((replace(block, revision_id=PUBLISHED_ID),), revision_id=DRAFT_ID)


def test_frozen_child_boundary_and_database_time_lifecycle() -> None:
    """Published children remain immutable and schedules derive from database time."""
    with pytest.raises(FrozenPageRevisionError):
        require_mutable_page_revision(_revision(PUBLISHED_ID, frozen=True))
    require_mutable_page_revision(_revision(DRAFT_ID, frozen=False))
    assert derive_page_lifecycle(_snapshot(), database_now=NOW) is PageLifecycle.DRAFT
    assert (
        derive_page_lifecycle(
            _snapshot(published=True, publish_at=NOW + timedelta(hours=1)), database_now=NOW
        )
        is PageLifecycle.SCHEDULED
    )
    live = _snapshot(published=True, publish_at=NOW)
    assert derive_page_lifecycle(live, database_now=NOW) is PageLifecycle.PUBLISHED
    pending = replace(live, draft=replace(live.draft, based_on_revision_id=None))
    assert (
        derive_page_lifecycle(pending, database_now=NOW) is PageLifecycle.PUBLISHED_CHANGES_PENDING
    )
    assert AdminPageView(live, PageLifecycle.PUBLISHED).snapshot is live
