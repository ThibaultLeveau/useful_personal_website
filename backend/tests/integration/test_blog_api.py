"""PostgreSQL-backed M7 blog admin, preview/export, taxonomy, and public contracts."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import Environment, Settings
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.infrastructure.database.session import create_database_engine
from app.main import create_app
from app.modules.identity.service import BootstrapService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://testserver"
EMAIL = "blog-owner@example.test"
INITIAL_PASSWORD = "M7!Initial-9Forest"
REPLACEMENT_PASSWORD = "M7!Replacement-7Harbor"


@dataclass(frozen=True, slots=True)
class _BlogHarness:
    application: FastAPI
    client: AsyncClient


async def _reconcile_permissions(owner_url: SecretStr, runtime_url: SecretStr) -> None:
    runtime_user = make_url(runtime_url.get_secret_value()).username
    if runtime_user is None or re.fullmatch(r"[a-z_][a-z0-9_]*", runtime_user) is None:
        message = "TEST_DATABASE_URL requires a conservative runtime role"
        raise ValueError(message)
    quoted_user = f'"{runtime_user}"'
    engine = create_database_engine(DatabaseConfig(url=owner_url))
    statements = (
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM {quoted_user}",
        f"GRANT SELECT ON TABLE public.alembic_version TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.audit_entry FROM {quoted_user}",
        f"GRANT SELECT, INSERT ON TABLE public.audit_entry TO {quoted_user}",
    )
    try:
        async with engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


@pytest.fixture
def migrated_blog_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the sole M7 head."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(_reconcile_permissions(test_database_owner_url, test_database_url))
    try:
        yield
    finally:
        command.downgrade(config, "base")


def _settings(database_url: SecretStr) -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_url=database_url,
        trusted_origins=(ORIGIN,),
        csrf_signing_key=SecretStr("c" * 32),
        token_digest_pepper=SecretStr("t" * 32),
        privacy_hmac_key=SecretStr("p" * 32),
    )


@pytest.fixture
async def blog_harness(
    migrated_blog_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_BlogHarness]:
    """Yield one full-session administrator against migrated PostgreSQL."""
    del migrated_blog_database
    application = create_app(settings=_settings(test_database_url))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(email=EMAIL, display_name="Blog Owner", password=INITIAL_PASSWORD)
    async with AsyncClient(transport=ASGITransport(app=application), base_url=ORIGIN) as client:
        login = await client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": EMAIL, "password": INITIAL_PASSWORD},
        )
        assert login.status_code == 200
        changed = await client.post(
            "/api/v1/auth/password/change",
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": client.cookies["__Host-admin_csrf"],
            },
            json={
                "current_password": INITIAL_PASSWORD,
                "new_password": REPLACEMENT_PASSWORD,
            },
        )
        assert changed.status_code == 200
        yield _BlogHarness(application, client)
    await runtime.dispose()


def _unsafe_headers(harness: _BlogHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


def _payload(*, title: str = "Safe publication", source: str | None = None) -> dict[str, object]:
    return {
        "title": title,
        "excerpt": "A practical guide to revision-safe publishing.",
        "source": source
        or (
            "# Overview\n\nA **controlled** article with [internal notes](/about).\n\n"
            "- [x] validated\n\n| Gate | Result |\n| - | - |\n| Policy | Pass |\n\n"
            "```python\nprint('<safe>')\n```"
        ),
        "author_display": "Blog Owner",
        "tag_ids": [],
        "category_ids": [],
        "related_post_ids": [],
        "seo_title": "Safe publication",
        "seo_description": "A practical guide to revision-safe publishing.",
        "canonical_url": "https://portfolio.example.test/blog/safe-publication",
        "cover_media_id": None,
    }


async def test_complete_blog_revision_preview_export_publication_and_privacy(  # noqa: PLR0915
    blog_harness: _BlogHarness,
) -> None:
    """Create taxonomy/article, reject HTML, preview/export, publish, edit-live, and hide."""
    tag = await blog_harness.client.post(
        "/api/v1/admin/blog/taxonomies",
        headers=_unsafe_headers(
            blog_harness,
            **{"Idempotency-Key": "blog-taxonomy-tag-0001"},
        ),
        json={"kind": "tag", "name": "Engineering", "slug": "engineering"},
    )
    assert tag.status_code == 201, tag.text
    category = await blog_harness.client.post(
        "/api/v1/admin/blog/taxonomies",
        headers=_unsafe_headers(
            blog_harness,
            **{"Idempotency-Key": "blog-taxonomy-category-0001"},
        ),
        json={"kind": "category", "name": "Delivery", "slug": "delivery"},
    )
    assert category.status_code == 201, category.text
    tag_id = tag.json()["data"]["id"]
    category_id = category.json()["data"]["id"]

    hostile = await blog_harness.client.post(
        "/api/v1/admin/blog/posts",
        headers=_unsafe_headers(
            blog_harness,
            **{"Idempotency-Key": "blog-hostile-create-0001"},
        ),
        json={
            **_payload(source="<script>alert(1)</script>"),
            "slug": "hostile",
            "visible": True,
        },
    )
    assert hostile.status_code == 422
    assert hostile.json()["error"]["details"]["fields"][0]["code"] == "raw_html"
    assert "alert(1)" not in hostile.text

    create_payload = {
        **_payload(),
        "slug": "Safe Publication",
        "visible": True,
        "tag_ids": [tag_id],
        "category_ids": [category_id],
    }
    create_headers = _unsafe_headers(
        blog_harness,
        **{"Idempotency-Key": "blog-post-create-0001"},
    )
    created = await blog_harness.client.post(
        "/api/v1/admin/blog/posts",
        headers=create_headers,
        json=create_payload,
    )
    assert created.status_code == 201, created.text
    assert created.headers["etag"] == '"v1"'
    post_id = created.json()["data"]["id"]
    assert created.json()["data"]["draft"]["reading_minutes"] == 1
    replay = await blog_harness.client.post(
        "/api/v1/admin/blog/posts",
        headers=create_headers,
        json=create_payload,
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == post_id

    preview = await blog_harness.client.get(f"/api/v1/admin/blog/posts/{post_id}/preview")
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "private, no-store"
    assert preview.headers["x-robots-tag"] == "noindex, nofollow"
    preview_html = preview.json()["data"]["content"]["html"]
    assert '<h2 id="overview">' in preview_html
    assert "&lt;safe&gt;" in preview_html
    exported = await blog_harness.client.get(f"/api/v1/admin/blog/posts/{post_id}/source")
    assert exported.status_code == 200
    assert exported.headers["cache-control"] == "private, no-store"
    assert exported.headers["content-type"].startswith("text/markdown")
    assert exported.text == str(create_payload["source"]).replace("\r\n", "\n")
    assert (
        exported.headers["x-content-checksum"]
        == preview.json()["data"]["content"]["source_checksum"]
    )

    assert (await blog_harness.client.get("/api/v1/public/blog/posts")).json()["data"] == []
    published = await blog_harness.client.put(
        f"/api/v1/admin/blog/posts/{post_id}/actions/publish",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "blog-post-publish-0001"},
        ),
        json={},
    )
    assert published.status_code == 200, published.text
    assert published.headers["etag"] == '"v2"'
    assert published.json()["data"]["lifecycle"] == "published"

    public = await blog_harness.client.get("/api/v1/public/blog/posts?tag=engineering")
    assert public.status_code == 200
    assert public.json()["meta"]["pagination"]["total_items"] == 1
    detail = await blog_harness.client.get("/api/v1/public/blog/posts/safe-publication")
    assert detail.status_code == 200
    public_data = detail.json()["data"]
    assert public_data["title"] == "Safe publication"
    assert public_data["tags"][0]["slug"] == "engineering"
    for secret_field in (
        '"source":',
        '"created_by":',
        '"draft_revision_id":',
        '"published_revision_id":',
    ):
        assert secret_field not in detail.text

    revised_payload = {
        **_payload(title="Private draft title", source="## Private draft\n\nNot public yet."),
        "tag_ids": [],
        "category_ids": [category_id],
    }
    revised = await blog_harness.client.put(
        f"/api/v1/admin/blog/posts/{post_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v2"'}),
        json=revised_payload,
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["data"]["lifecycle"] == "published_changes_pending"
    unchanged = await blog_harness.client.get("/api/v1/public/blog/posts/safe-publication")
    assert unchanged.json()["data"] == public_data

    hidden = await blog_harness.client.put(
        f"/api/v1/admin/blog/posts/{post_id}/visibility",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v3"'}),
        json={"visible": False},
    )
    assert hidden.status_code == 200
    assert (
        await blog_harness.client.get("/api/v1/public/blog/posts/safe-publication")
    ).status_code == 404


async def test_admin_blog_maintenance_lifecycle_and_errors(  # noqa: PLR0915
    blog_harness: _BlogHarness,
) -> None:
    """Exercise ordered maintenance, lifecycle separation, and stable error mapping."""
    client = blog_harness.client
    first_tag = await client.post(
        "/api/v1/admin/blog/taxonomies",
        headers=_unsafe_headers(blog_harness, **{"Idempotency-Key": "tag-create-first-0001"}),
        json={"kind": "tag", "name": "Engineering", "slug": "engineering"},
    )
    second_tag = await client.post(
        "/api/v1/admin/blog/taxonomies",
        headers=_unsafe_headers(blog_harness, **{"Idempotency-Key": "tag-create-second-0001"}),
        json={"kind": "tag", "name": "Operations", "slug": "operations"},
    )
    assert first_tag.status_code == second_tag.status_code == 201
    first_tag_id = first_tag.json()["data"]["id"]
    second_tag_id = second_tag.json()["data"]["id"]

    conflict = await client.put(
        f"/api/v1/admin/blog/taxonomies/{first_tag_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v1"'}),
        json={"name": "Duplicate", "slug": "operations", "visible": True},
    )
    assert conflict.status_code == 422
    assert conflict.json()["error"]["details"]["fields"][0]["code"] == "duplicate_slug"
    updated_tag = await client.put(
        f"/api/v1/admin/blog/taxonomies/{first_tag_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v1"'}),
        json={"name": "Platform Engineering", "slug": "platform-engineering", "visible": True},
    )
    assert updated_tag.status_code == 200
    assert updated_tag.headers["etag"] == '"v2"'
    listed_tags = await client.get("/api/v1/admin/blog/taxonomies/tag")
    assert [item["id"] for item in listed_tags.json()["data"]["items"]] == [
        first_tag_id,
        second_tag_id,
    ]

    incomplete_order = await client.put(
        "/api/v1/admin/blog/taxonomies/tag/actions/reorder",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "tag-reorder-incomplete-0001"},
        ),
        json={"ordered_ids": [first_tag_id]},
    )
    assert incomplete_order.status_code == 422
    reordered_tags = await client.put(
        "/api/v1/admin/blog/taxonomies/tag/actions/reorder",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "tag-reorder-complete-0001"},
        ),
        json={"ordered_ids": [second_tag_id, first_tag_id]},
    )
    assert reordered_tags.status_code == 200
    assert [item["id"] for item in reordered_tags.json()["data"]["items"]] == [
        second_tag_id,
        first_tag_id,
    ]

    first_post = await client.post(
        "/api/v1/admin/blog/posts",
        headers=_unsafe_headers(blog_harness, **{"Idempotency-Key": "post-create-first-0001"}),
        json={
            **_payload(title="First ordered post"),
            "slug": "first-ordered-post",
            "visible": True,
            "tag_ids": [first_tag_id],
        },
    )
    second_post = await client.post(
        "/api/v1/admin/blog/posts",
        headers=_unsafe_headers(blog_harness, **{"Idempotency-Key": "post-create-second-0001"}),
        json={
            **_payload(title="Second ordered post"),
            "slug": "second-ordered-post",
            "visible": True,
        },
    )
    assert first_post.status_code == second_post.status_code == 201
    first_post_id = first_post.json()["data"]["id"]
    second_post_id = second_post.json()["data"]["id"]

    duplicate_post = await client.post(
        "/api/v1/admin/blog/posts",
        headers=_unsafe_headers(blog_harness, **{"Idempotency-Key": "post-create-duplicate-0001"}),
        json={**_payload(), "slug": "first-ordered-post", "visible": True},
    )
    assert duplicate_post.status_code == 422
    invalid_query = await client.get("/api/v1/admin/blog/posts?visible=maybe")
    assert invalid_query.status_code == 422
    filtered = await client.get(
        f"/api/v1/admin/blog/posts?visible=true&lifecycle=draft&tag_id={first_tag_id}"
        "&search=First&sort=title"
    )
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["data"]] == [first_post_id]
    fetched = await client.get(f"/api/v1/admin/blog/posts/{second_post_id}")
    assert fetched.status_code == 200
    assert fetched.headers["etag"] == '"v1"'

    stale = await client.put(
        f"/api/v1/admin/blog/posts/{second_post_id}/visibility",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v99"'}),
        json={"visible": False},
    )
    assert stale.status_code == 409
    premature = await client.put(
        f"/api/v1/admin/blog/posts/{second_post_id}/actions/reschedule",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "post-reschedule-premature-0001"},
        ),
        json={"publish_at": "2099-01-01T00:00:00Z"},
    )
    assert premature.status_code == 409
    assert premature.json()["error"]["details"]["reason"] == "not_published"

    reordered_posts = await client.put(
        "/api/v1/admin/blog/posts/actions/reorder",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "post-reorder-complete-0001"},
        ),
        json={"ordered_ids": [second_post_id, first_post_id]},
    )
    assert reordered_posts.status_code == 200
    assert [item["id"] for item in reordered_posts.json()["data"]["items"]] == [
        second_post_id,
        first_post_id,
    ]

    scheduled = await client.put(
        f"/api/v1/admin/blog/posts/{first_post_id}/actions/publish",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "post-publish-scheduled-0001"},
        ),
        json={"publish_at": "2099-01-01T00:00:00Z"},
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["data"]["lifecycle"] == "scheduled"
    rescheduled = await client.put(
        f"/api/v1/admin/blog/posts/{first_post_id}/actions/reschedule",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "post-reschedule-valid-0001"},
        ),
        json={"publish_at": "2099-02-01T00:00:00Z"},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.headers["etag"] == '"v4"'
    unpublished = await client.put(
        f"/api/v1/admin/blog/posts/{first_post_id}/actions/unpublish",
        headers=_unsafe_headers(
            blog_harness,
            **{"If-Match": '"v4"', "Idempotency-Key": "post-unpublish-valid-0001"},
        ),
    )
    assert unpublished.status_code == 200
    assert unpublished.json()["data"]["lifecycle"] == "unpublished"

    taxonomy_in_use = await client.delete(
        f"/api/v1/admin/blog/taxonomies/{first_tag_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v3"'}),
    )
    assert taxonomy_in_use.status_code == 409
    assert taxonomy_in_use.json()["error"]["details"]["reason"] == "taxonomy_in_use"
    deleted_post = await client.delete(
        f"/api/v1/admin/blog/posts/{second_post_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v2"'}),
    )
    assert deleted_post.status_code == 200
    deleted_tag = await client.delete(
        f"/api/v1/admin/blog/taxonomies/{second_tag_id}",
        headers=_unsafe_headers(blog_harness, **{"If-Match": '"v2"'}),
    )
    assert deleted_tag.status_code == 200
    assert (await client.get("/api/v1/public/blog/posts/First-Ordered-Post")).status_code == 404
