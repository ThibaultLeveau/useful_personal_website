"""Focused M7 blog transport, safe-render, and OpenAPI privacy proofs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.v1.admin_blog import _map_error, _values
from app.api.v1.blog_schemas import PostInput, PublicPostData
from app.api.v1.public_blog import _data
from app.common.content_policy import parse_content
from app.main import create_app
from app.modules.blog.domain import (
    BlogValidationError,
    PublicPost,
    PublicPostReference,
    PublicTaxonomyReference,
)
from app.modules.blog.service import BlogRelationError

POST_ID = UUID("0198a12c-8000-7000-8000-000000000001")


def _input(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "title": "Safe publication",
        "excerpt": "A revision-safe controlled-content article.",
        "source": "## Overview\n\nA **controlled** article.",
        "author_display": "Site owner",
        "tag_ids": [],
        "category_ids": [],
        "related_post_ids": [],
    }
    values.update(overrides)
    return values


def test_post_input_rejects_mass_assignment_and_has_no_derivation_override() -> None:
    """Transport cannot accept client reading time, checksum, policy, or internal state."""
    for field, value in (
        ("reading_minutes", 99),
        ("content_checksum", "attacker"),
        ("content_policy_version", "999"),
        ("version", 99),
    ):
        with pytest.raises(ValidationError):
            PostInput.model_validate(_input(**{field: value}))
    values = _values(PostInput.model_validate(_input()))
    assert values.reading_minutes == 0
    assert values.content_checksum == ""


def test_transport_maps_content_and_relation_errors_without_rejected_values() -> None:
    """Stable field facts never echo hostile source or unavailable identifiers."""
    field = _map_error(BlogValidationError(path="source", code="raw_html"))
    relation = _map_error(BlogRelationError("taxonomy_kind_mismatch"))
    assert field.code == "VALIDATION_FAILED"
    field_items = field.details["fields"]
    relation_items = relation.details["fields"]
    assert isinstance(field_items, list)
    assert isinstance(field_items[0], dict)
    assert isinstance(relation_items, list)
    assert isinstance(relation_items[0], dict)
    assert field_items[0]["path"] == "body.source"
    assert relation_items[0]["code"] == "taxonomy_kind_mismatch"


def test_public_projection_contains_only_safe_render_and_public_summaries() -> None:
    """Public JSON omits source, revisions, creator, pointers, and sanitizer internals."""
    rendered = parse_content("## Public\n\nSafe **content**.").rendered
    item = PublicPost(
        id=POST_ID,
        slug="safe-publication",
        title="Safe publication",
        excerpt="A safe article.",
        author_display="Site owner",
        rendered=rendered,
        reading_minutes=1,
        published_at=datetime(2026, 8, 4, 16, tzinfo=UTC),
        seo_title="Safe publication",
        seo_description="A safe article.",
        canonical_url=None,
        cover_media_id=POST_ID,
        tags=(PublicTaxonomyReference(POST_ID, "Engineering", "engineering"),),
        categories=(),
        related_posts=(PublicPostReference(POST_ID, "related", "Related", "Related article."),),
    )
    document = _data(item).model_dump(mode="json")
    assert document["content"]["html"].startswith('<h3 id="public">')
    assert document["cover_media_id"] == str(POST_ID)
    assert "cover_media_available" not in document
    for forbidden in (
        "source",
        "draft_revision_id",
        "published_revision_id",
        "created_by",
        "version",
        "content_policy_name",
    ):
        assert forbidden not in document


def test_openapi_has_unique_blog_operations_and_private_export_contract() -> None:
    """The generated transport surface is closed, unique, and explicit about Markdown export."""
    document = create_app().openapi()
    operations = [
        operation["operationId"]
        for path in document["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    blog_operations = {item for item in operations if "blog" in item}
    assert len(operations) == len(set(operations))
    assert len(blog_operations) == 19
    export = document["paths"]["/api/v1/admin/blog/posts/{post_id}/source"]["get"]
    assert "text/markdown" in export["responses"]["200"]["content"]
    public_schema = document["components"]["schemas"]["PublicPostData"]
    assert "source" not in public_schema["properties"]
    assert "content" in public_schema["properties"]


def test_public_schema_rejects_internal_mass_assignment() -> None:
    """Direct construction cannot smuggle internal state through extra properties."""
    rendered = parse_content("Safe content.").rendered
    base = _data(
        PublicPost(
            id=POST_ID,
            slug="safe-publication",
            title="Safe publication",
            excerpt="A safe article.",
            author_display="Site owner",
            rendered=rendered,
            reading_minutes=1,
            published_at=datetime(2026, 8, 4, 16, tzinfo=UTC),
            seo_title="Safe publication",
            seo_description="A safe article.",
            canonical_url=None,
            cover_media_id=None,
            tags=(),
            categories=(),
            related_posts=(),
        )
    ).model_dump(mode="json")
    with pytest.raises(ValidationError):
        PublicPostData.model_validate({**base, "source": "private"})
