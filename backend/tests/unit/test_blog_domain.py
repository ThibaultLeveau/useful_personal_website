"""M7 blog domain, taxonomy, controlled-content, and lifecycle proofs."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import pytest

from app.common.content_policy import POLICY_NAME, POLICY_VERSION, parse_content
from app.common.domain.pagination import PageRequest
from app.modules.blog.domain import (
    AdminPostQuery,
    BlogValidationError,
    FrozenPostRevisionError,
    Post,
    PostLifecycle,
    PostRevision,
    PostSnapshot,
    PostValues,
    TaxonomyKind,
    derive_post_lifecycle,
    normalize_blog_slug,
    post_seo,
    require_mutable_post_revision,
    validate_post_values,
    validate_taxonomy,
)

POST_ID = UUID("0198a13d-2000-7000-8000-000000000001")
DRAFT_ID = UUID("0198a13d-2000-7000-8000-000000000002")
PUBLISHED_ID = UUID("0198a13d-2000-7000-8000-000000000003")
ACTOR_ID = UUID("0198a13d-2000-7000-8000-000000000004")
TAG_ID = UUID("0198a13d-2000-7000-8000-000000000005")
CATEGORY_ID = UUID("0198a13d-2000-7000-8000-000000000006")
RELATED_ID = UUID("0198a13d-2000-7000-8000-000000000007")
NOW = datetime(2026, 8, 4, 10, tzinfo=UTC)


def _values(*, source: str = "## A safe article\n\nBuilt with **care**.") -> PostValues:
    return PostValues(
        title="Designing a reliable release path",
        excerpt="How bounded contracts keep a release understandable and reversible.",
        source=source,
        author_display="Site owner",
        reading_minutes=999,
        content_checksum="attacker-controlled",
        content_policy_name="attacker-controlled",
        content_policy_version="999",
        tag_ids=(TAG_ID,),
        category_ids=(CATEGORY_ID,),
        related_post_ids=(RELATED_ID,),
        seo_title=None,
        seo_description=None,
        canonical_url="https://example.test/blog/reliable-release-path",
    )


def _revision(identifier: UUID, *, frozen: bool, values: PostValues | None = None) -> PostRevision:
    return PostRevision(
        id=identifier,
        post_id=POST_ID,
        revision_number=1 if frozen else 2,
        based_on_revision_id=PUBLISHED_ID if not frozen else None,
        values=values or validate_post_values(_values(), post_id=POST_ID),
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
) -> PostSnapshot:
    return PostSnapshot(
        post=Post(
            id=POST_ID,
            slug="reliable-release-path",
            visible=True,
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


def test_normalizes_post_and_taxonomy_slugs() -> None:
    """Unicode human input becomes deterministic case-insensitive route keys."""
    assert normalize_blog_slug("Café Release Notes") == "cafe-release-notes"
    assert validate_taxonomy(kind=TaxonomyKind.TAG, name="API Design", slug="API Design") == (
        "API Design",
        "api-design",
    )
    with pytest.raises(BlogValidationError) as captured:
        normalize_blog_slug("---")
    assert (captured.value.path, captured.value.code) == ("slug", "invalid_slug")


def test_content_derivations_are_server_owned_and_deterministic() -> None:
    """Canonical source, reading time, checksum, and policy cannot be mass assigned."""
    source = "# Café\r\n\r\n" + "word " * 226
    accepted = validate_post_values(_values(source=source), post_id=POST_ID)
    expected = parse_content(source)
    assert accepted.source == expected.source
    assert accepted.reading_minutes == 2
    assert accepted.content_checksum == expected.rendered.source_checksum
    assert (accepted.content_policy_name, accepted.content_policy_version) == (
        POLICY_NAME,
        POLICY_VERSION,
    )
    assert validate_post_values(accepted, post_id=POST_ID) == accepted


@pytest.mark.parametrize(
    ("field", "value", "path", "code"),
    [
        ("title", "", "title", "invalid_text"),
        ("canonical_url", "http://example.test", "canonical_url", "unsafe_url"),
        ("canonical_url", "https://user:secret@example.test", "canonical_url", "unsafe_url"),
        ("source", "<script>alert(1)</script>", "source", "raw_html"),
        ("source", "![remote](https://example.test/a.png)", "source", "media_unavailable"),
        ("source", "[bad](javascript:alert(1))", "source", "unsafe_url"),
    ],
)
def test_rejects_field_addressable_content_and_metadata_errors(
    field: str,
    value: object,
    path: str,
    code: str,
) -> None:
    """Invalid input reports stable facts without echoing rejected content."""
    changes = cast("dict[str, Any]", {field: value})
    with pytest.raises(BlogValidationError) as captured:
        validate_post_values(replace(_values(), **changes), post_id=POST_ID)
    assert (captured.value.path, captured.value.code) == (path, code)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("tag_ids", (TAG_ID, TAG_ID), "duplicate_id"),
        ("category_ids", (CATEGORY_ID, CATEGORY_ID), "duplicate_id"),
        ("related_post_ids", (RELATED_ID, RELATED_ID), "duplicate_id"),
        ("related_post_ids", (POST_ID,), "self_reference"),
    ],
)
def test_revision_relations_reject_duplicates_and_self_edges(
    field: str,
    value: object,
    code: str,
) -> None:
    """Revision-owned ordered relations stay unambiguous and bounded."""
    changes = cast("dict[str, Any]", {field: value})
    with pytest.raises(BlogValidationError) as captured:
        validate_post_values(replace(_values(), **changes), post_id=POST_ID)
    assert captured.value.code == code


def test_cover_media_id_is_preserved_for_transactional_m9_validation() -> None:
    """The domain carries the logical ID while the media repository verifies readiness."""
    accepted = validate_post_values(
        replace(_values(), cover_media_id=RELATED_ID),
        post_id=POST_ID,
    )
    assert accepted.cover_media_id == RELATED_ID


def test_frozen_revision_cannot_be_changed() -> None:
    """Published content is immutable while the copy-on-write draft remains mutable."""
    with pytest.raises(FrozenPostRevisionError):
        require_mutable_post_revision(_revision(PUBLISHED_ID, frozen=True))
    require_mutable_post_revision(_revision(DRAFT_ID, frozen=False))


@pytest.mark.parametrize(
    ("snapshot", "expected"),
    [
        (_snapshot(), PostLifecycle.DRAFT),
        (_snapshot(published=True, publish_at=NOW + timedelta(hours=1)), PostLifecycle.SCHEDULED),
        (_snapshot(published=True, publish_at=NOW), PostLifecycle.PUBLISHED),
        (_snapshot(unpublished_at=NOW), PostLifecycle.UNPUBLISHED),
        (_snapshot(deleted_at=NOW), PostLifecycle.DELETED),
    ],
)
def test_lifecycle_uses_database_time(snapshot: PostSnapshot, expected: PostLifecycle) -> None:
    """Scheduling needs neither a worker nor application-clock state transitions."""
    assert derive_post_lifecycle(snapshot, database_now=NOW) is expected


def test_draft_content_taxonomy_and_seo_changes_do_not_mutate_live_revision() -> None:
    """Any copy-on-write difference becomes a pending draft without changing public values."""
    snapshot = _snapshot(published=True, publish_at=NOW)
    assert snapshot.published is not None
    changed_values = replace(
        snapshot.draft.values,
        source="## Revised draft\n\nPrivate until republished.",
        tag_ids=(),
        seo_title="A draft-only title",
    )
    changed = replace(
        snapshot.draft,
        based_on_revision_id=None,
        values=validate_post_values(changed_values, post_id=POST_ID),
    )
    assert (
        derive_post_lifecycle(replace(snapshot, draft=changed), database_now=NOW)
        is PostLifecycle.PUBLISHED_CHANGES_PENDING
    )
    assert snapshot.published.values.source != changed.values.source
    assert post_seo(snapshot.published.values)[0] == snapshot.published.values.title


def test_admin_query_contract_uses_closed_defaults() -> None:
    """The domain exposes explicit page and sort inputs for transport allow-lists."""
    query = AdminPostQuery(PageRequest())
    assert query.sort == "position"
    assert query.search is None
