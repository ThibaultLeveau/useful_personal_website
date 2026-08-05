"""PostgreSQL-backed M8 builder, preview/export, lifecycle, and public contracts."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from PIL import Image
from pydantic import SecretStr

from app.config import Environment, MediaStorageKind, Settings
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.main import create_app
from app.modules.identity.service import BootstrapService
from tests.database.runtime_permissions import reconcile_runtime_permissions

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://testserver"
EMAIL = "page-owner@example.test"
INITIAL_PASSWORD = "M8!Initial-4Meadow"
REPLACEMENT_PASSWORD = "M8!Replacement-8Harbor"


@dataclass(frozen=True, slots=True)
class _PageHarness:
    application: FastAPI
    client: AsyncClient


@pytest.fixture
def migrated_pages_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset PostgreSQL, migrate through sole head, and restore runtime grants."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(reconcile_runtime_permissions(test_database_owner_url, test_database_url))
    try:
        yield
    finally:
        command.downgrade(config, "base")


def _settings(database_url: SecretStr, media_root: Path) -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_url=database_url,
        trusted_origins=(ORIGIN,),
        csrf_signing_key=SecretStr("c" * 32),
        token_digest_pepper=SecretStr("t" * 32),
        privacy_hmac_key=SecretStr("p" * 32),
        media_storage_kind=MediaStorageKind.LOCAL,
        media_local_root=media_root.resolve(),
    )


@pytest.fixture
async def page_harness(
    migrated_pages_database: None,
    test_database_url: SecretStr,
    tmp_path: Path,
) -> AsyncIterator[_PageHarness]:
    """Yield one full administrator session against migrated PostgreSQL."""
    del migrated_pages_database
    application = create_app(settings=_settings(test_database_url, tmp_path / "private-media"))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(email=EMAIL, display_name="Page Owner", password=INITIAL_PASSWORD)
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
        yield _PageHarness(application, client)
    await runtime.dispose()


def _unsafe_headers(harness: _PageHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


def _page_payload(*, title: str = "Selected work") -> dict[str, object]:
    return {
        "route_kind": "custom",
        "slug": "selected-work",
        "title": title,
        "description": "A focused collection of useful outcomes.",
        "seo_title": "Selected engineering work",
        "seo_description": "Selected product and engineering outcomes.",
        "canonical_url": "https://portfolio.example.test/selected-work",
        "visible": True,
        "navigation_visible": True,
    }


def _png_bytes() -> bytes:
    target = BytesIO()
    Image.new("RGB", (800, 400), (25, 82, 110)).save(target, format="PNG")
    return target.getvalue()


async def test_complete_page_builder_preview_export_publication_and_privacy(  # noqa: PLR0915
    page_harness: _PageHarness,
) -> None:
    """Exercise strict blocks, staging, ordering, COW publication, and public privacy."""
    client = page_harness.client
    registry = await client.get("/api/v1/admin/pages/registry")
    assert registry.status_code == 200
    assert len(registry.json()["data"]["entries"]) == 19

    reserved = await client.post(
        "/api/v1/admin/pages",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-reserved-create-0001"}),
        json={**_page_payload(), "slug": "admin"},
    )
    assert reserved.status_code == 422
    assert reserved.json()["error"]["details"]["fields"][0]["code"] == "reserved_slug"

    create_headers = _unsafe_headers(page_harness, **{"Idempotency-Key": "page-custom-create-0001"})
    created = await client.post("/api/v1/admin/pages", headers=create_headers, json=_page_payload())
    assert created.status_code == 201, created.text
    assert created.headers["etag"] == '"v1"'
    page_id = created.json()["data"]["id"]
    replay = await client.post("/api/v1/admin/pages", headers=create_headers, json=_page_payload())
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == page_id

    hero = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "page-block-hero-add-0001"},
        ),
        json={
            "block": {
                "block_type": "hero",
                "theme": "accent",
                "config": {
                    "eyebrow": "Independent engineer",
                    "heading": "Systems that earn trust",
                    "body": "A clear path from hard problem to useful outcome.",
                    "actions": [{"label": "About this portfolio", "destination": "/about"}],
                },
            }
        },
    )
    assert hero.status_code == 201, hero.text
    hero_id = hero.json()["data"]["draft"]["blocks"][0]["id"]

    rich_text = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "page-block-rich-add-0001"},
        ),
        json={
            "block": {
                "block_type": "rich_text",
                "config": {"source": "## Deliberate work\n\nSafe **CommonMark** only."},
            }
        },
    )
    assert rich_text.status_code == 201, rich_text.text
    rich_id = rich_text.json()["data"]["draft"]["blocks"][1]["id"]

    unavailable_media = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "page-block-image-add-0001"},
        ),
        json={
            "block": {
                "block_type": "image",
                "config": {
                    "media_id": "0198a13d-8300-7000-8000-000000000001",
                    "alt": "Staged architecture diagram",
                },
            }
        },
    )
    assert unavailable_media.status_code == 409, unavailable_media.text

    upload = await client.post(
        "/api/v1/admin/media",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-image-upload-0001"}),
        files={"file": ("architecture.png", _png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    asset_id = upload.json()["data"]["id"]
    image = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "page-block-image-ready-0001"},
        ),
        json={
            "block": {
                "block_type": "image",
                "config": {
                    "media_id": asset_id,
                    "alt": "Architecture diagram",
                    "caption": "A bounded service architecture.",
                    "focal_point": "center",
                },
            }
        },
    )
    assert image.status_code == 201, image.text
    image_id = image.json()["data"]["draft"]["blocks"][2]["id"]

    preview = await client.get(f"/api/v1/admin/pages/{page_id}/preview")
    assert preview.status_code == 200, preview.text
    assert preview.headers["cache-control"] == "private, no-store"
    assert preview.headers["x-robots-tag"] == "noindex, nofollow"
    assert preview.json()["data"]["banner"] == "Draft preview - not public"
    assert preview.json()["data"]["issues"] == []
    assert (await client.get(f"/api/v1/media/{asset_id}/640")).status_code == 404

    reordered = await client.put(
        f"/api/v1/admin/pages/{page_id}/blocks/actions/reorder",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v4"', "Idempotency-Key": "page-reorder-complete-0001"},
        ),
        json={"ordered_ids": [rich_id, image_id, hero_id]},
    )
    assert reordered.status_code == 200, reordered.text
    assert [item["id"] for item in reordered.json()["data"]["draft"]["blocks"]] == [
        rich_id,
        image_id,
        hero_id,
    ]

    exported = await client.get(f"/api/v1/admin/pages/{page_id}/export")
    assert exported.status_code == 200
    assert exported.headers["cache-control"] == "private, no-store"
    assert exported.json()["data"]["manifest"]["format"] == "upw-page-export"
    assert len(exported.json()["data"]["checksum"]) == 64

    assert (await client.get("/api/v1/public/pages/selected-work")).status_code == 404
    published = await client.put(
        f"/api/v1/admin/pages/{page_id}/publish",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v5"', "Idempotency-Key": "page-publish-now-0001"},
        ),
        json={},
    )
    assert published.status_code == 200, published.text
    assert published.json()["data"]["lifecycle"] == "published"
    assert published.headers["etag"] == '"v6"'

    public = await client.get("/api/v1/public/pages/selected-work")
    assert public.status_code == 200, public.text
    public_rendition = await client.get(f"/api/v1/media/{asset_id}/640")
    assert public_rendition.status_code == 200
    assert public_rendition.headers["cache-control"] == "public, max-age=300, s-maxage=300"
    routes = await client.get("/api/v1/public/pages?page=1&page_size=100")
    assert routes.status_code == 200
    assert routes.json()["data"] == [
        {
            "id": page_id,
            "canonical_path": "/selected-work",
            "title": "Selected work",
            "published_at": public.json()["data"]["published_at"],
            "updated_at": published.json()["data"]["updated_at"],
        }
    ]
    public_data = public.json()["data"]
    assert [item["definition"]["block_type"] for item in public_data["blocks"]] == [
        "rich_text",
        "image",
        "hero",
    ]
    rich_content = public_data["blocks"][0]["definition"]["config"]["content"]
    assert (
        rich_content["html"] == '<h3 id="deliberate-work">Deliberate work</h3>\n'
        "<p>Safe <strong>CommonMark</strong> only.</p>\n"
    )
    assert '"source"' not in public.text
    for private_field in (
        '"draft"',
        '"published_revision_id"',
        '"created_by"',
        '"version"',
    ):
        assert private_field not in public.text

    draft_update = await client.put(
        f"/api/v1/admin/pages/{page_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v6"'}),
        json={**_page_payload(title="Private pending title")},
    )
    assert draft_update.status_code == 200, draft_update.text
    assert draft_update.json()["data"]["lifecycle"] == "published_changes_pending"
    unchanged = await client.get("/api/v1/public/pages/selected-work")
    assert unchanged.json()["data"] == public_data

    unpublish = await client.put(
        f"/api/v1/admin/pages/{page_id}/unpublish",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v7"', "Idempotency-Key": "page-unpublish-now-0001"},
        ),
    )
    assert unpublish.status_code == 200, unpublish.text
    assert (await client.get("/api/v1/public/pages/selected-work")).status_code == 404
    assert (await client.get(f"/api/v1/media/{asset_id}/640")).status_code == 404
    unpublish_replay = await client.put(
        f"/api/v1/admin/pages/{page_id}/unpublish",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v7"', "Idempotency-Key": "page-unpublish-now-0001"},
        ),
    )
    assert unpublish_replay.status_code == 200
    assert unpublish_replay.headers["etag"] == '"v8"'


async def test_image_block_usage_metadata_can_be_replaced_in_place(
    page_harness: _PageHarness,
) -> None:
    """Updating an existing media reference replaces its unique role-position row."""
    client = page_harness.client
    created = await client.post(
        "/api/v1/admin/pages",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-media-edit-0001"}),
        json={**_page_payload(), "slug": "media-edit"},
    )
    assert created.status_code == 201, created.text
    page_id = created.json()["data"]["id"]
    upload = await client.post(
        "/api/v1/admin/media",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-media-edit-0002"}),
        files={"file": ("editable.png", _png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    asset_id = upload.json()["data"]["id"]
    added = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "page-media-edit-0003"},
        ),
        json={
            "block": {
                "block_type": "image",
                "config": {"media_id": asset_id, "alt": "Initial architecture diagram"},
            }
        },
    )
    assert added.status_code == 201, added.text
    image_id = added.json()["data"]["draft"]["blocks"][0]["id"]

    updated = await client.put(
        f"/api/v1/admin/pages/{page_id}/blocks/{image_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v2"'}),
        json={
            "block": {
                "block_type": "image",
                "config": {
                    "media_id": asset_id,
                    "alt": "Updated architecture diagram",
                    "caption": "The same asset with revised usage metadata.",
                    "focal_point": "right",
                },
            }
        },
    )
    assert updated.status_code == 200, updated.text
    updated_image = updated.json()["data"]["draft"]["blocks"][0]
    assert updated_image["id"] == image_id
    assert updated_image["definition"]["config"]["alt"] == "Updated architecture diagram"


async def test_page_security_concurrency_and_deep_duplicate(page_harness: _PageHarness) -> None:
    """Reject forged writes/stale versions and deep-copy a custom draft safely."""
    client = page_harness.client
    async with AsyncClient(
        transport=ASGITransport(app=page_harness.application), base_url=ORIGIN
    ) as anonymous:
        unauthenticated = await anonymous.post(
            "/api/v1/admin/pages",
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": "not-a-session-token",
                "Idempotency-Key": "page-unauthorized-0001",
            },
            json=_page_payload(),
        )
    assert unauthenticated.status_code == 401

    created = await client.post(
        "/api/v1/admin/pages",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-security-create-0001"}),
        json=_page_payload(),
    )
    assert created.status_code == 201
    page_id = created.json()["data"]["id"]

    missing_precondition = await client.put(
        f"/api/v1/admin/pages/{page_id}",
        headers=_unsafe_headers(page_harness),
        json=_page_payload(),
    )
    assert missing_precondition.status_code == 428
    stale = await client.put(
        f"/api/v1/admin/pages/{page_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v99"'}),
        json=_page_payload(),
    )
    assert stale.status_code == 409

    added = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "page-security-block-0001"},
        ),
        json={"block": {"block_type": "divider", "config": {"style": "line"}}},
    )
    assert added.status_code == 201, added.text
    source_block_id = added.json()["data"]["draft"]["blocks"][0]["id"]

    duplicated = await client.post(
        f"/api/v1/admin/pages/{page_id}/duplicate",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "page-deep-duplicate-0001"},
        ),
        json={"slug": "selected-work-copy", "title": "Selected work copy"},
    )
    assert duplicated.status_code == 201, duplicated.text
    duplicate_data = duplicated.json()["data"]
    assert duplicate_data["slug"] == "selected-work-copy"
    assert duplicate_data["visible"] is False
    assert duplicate_data["id"] != page_id
    assert duplicate_data["draft"]["blocks"][0]["id"] != source_block_id
    assert duplicate_data["draft"]["blocks"][0]["definition"]["config"] == {"style": "line"}

    block_duplicate_headers = _unsafe_headers(
        page_harness,
        **{"If-Match": '"v2"', "Idempotency-Key": "page-block-duplicate-0001"},
    )
    block_copy = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks/{source_block_id}/duplicate",
        headers=block_duplicate_headers,
    )
    assert block_copy.status_code == 200, block_copy.text
    copied_blocks = block_copy.json()["data"]["draft"]["blocks"]
    assert len(copied_blocks) == 2
    assert copied_blocks[0]["id"] == source_block_id
    assert copied_blocks[1]["id"] != source_block_id
    block_copy_replay = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks/{source_block_id}/duplicate",
        headers=block_duplicate_headers,
    )
    assert block_copy_replay.status_code == 200
    assert block_copy_replay.json()["data"]["draft"]["blocks"] == copied_blocks


async def test_page_block_and_scheduled_deletion_lifecycle(page_harness: _PageHarness) -> None:
    """Cover visibility, block deletion, scheduling, rescheduling, and page deletion."""
    client = page_harness.client
    created = await client.post(
        "/api/v1/admin/pages",
        headers=_unsafe_headers(page_harness, **{"Idempotency-Key": "page-lifecycle-create-0001"}),
        json={**_page_payload(), "slug": "lifecycle", "title": "Lifecycle"},
    )
    assert created.status_code == 201
    page_id = created.json()["data"]["id"]
    assert (await client.get("/api/v1/admin/pages?page=1&page_size=5")).status_code == 200
    assert (await client.get(f"/api/v1/admin/pages/{page_id}")).status_code == 200

    added = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "page-lifecycle-block-0001"},
        ),
        json={"block": {"block_type": "divider", "config": {"style": "line"}}},
    )
    assert added.status_code == 201
    block_id = added.json()["data"]["draft"]["blocks"][0]["id"]

    hidden = await client.put(
        f"/api/v1/admin/pages/{page_id}/blocks/{block_id}/visibility",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v2"'}),
        json={"visible": False},
    )
    assert hidden.status_code == 200
    assert hidden.json()["data"]["draft"]["blocks"][0]["definition"]["visible"] is False

    updated = await client.put(
        f"/api/v1/admin/pages/{page_id}/blocks/{block_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v3"'}),
        json={"block": {"block_type": "divider", "visible": True, "config": {"style": "dots"}}},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["draft"]["blocks"][0]["definition"]["config"] == {"style": "dots"}

    copied = await client.post(
        f"/api/v1/admin/pages/{page_id}/blocks/{block_id}/duplicate",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v4"', "Idempotency-Key": "page-lifecycle-copy-0001"},
        ),
    )
    assert copied.status_code == 200
    copied_id = copied.json()["data"]["draft"]["blocks"][1]["id"]

    deleted_block = await client.delete(
        f"/api/v1/admin/pages/{page_id}/blocks/{block_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v5"'}),
    )
    assert deleted_block.status_code == 200
    assert [item["id"] for item in deleted_block.json()["data"]["draft"]["blocks"]] == [copied_id]

    reordered = await client.put(
        f"/api/v1/admin/pages/{page_id}/blocks/actions/reorder",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v6"', "Idempotency-Key": "page-lifecycle-order-0001"},
        ),
        json={"ordered_ids": [copied_id]},
    )
    assert reordered.status_code == 200

    first_time = datetime.now(UTC) + timedelta(days=2)
    published = await client.put(
        f"/api/v1/admin/pages/{page_id}/publish",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v7"', "Idempotency-Key": "page-lifecycle-publish-0001"},
        ),
        json={"publish_at": first_time.isoformat()},
    )
    assert published.status_code == 200
    assert published.json()["data"]["lifecycle"] == "scheduled"

    second_time = first_time + timedelta(days=1)
    rescheduled = await client.put(
        f"/api/v1/admin/pages/{page_id}/reschedule",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v8"', "Idempotency-Key": "page-lifecycle-reschedule-0001"},
        ),
        json={"publish_at": second_time.isoformat()},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["data"]["lifecycle"] == "scheduled"

    unpublished = await client.put(
        f"/api/v1/admin/pages/{page_id}/unpublish",
        headers=_unsafe_headers(
            page_harness,
            **{"If-Match": '"v9"', "Idempotency-Key": "page-lifecycle-unpublish-0001"},
        ),
    )
    assert unpublished.status_code == 200

    deleted_page = await client.delete(
        f"/api/v1/admin/pages/{page_id}",
        headers=_unsafe_headers(page_harness, **{"If-Match": '"v10"'}),
    )
    assert deleted_page.status_code == 200
    assert deleted_page.json()["data"] == {"deleted": True}
    assert (await client.get(f"/api/v1/admin/pages/{page_id}")).status_code == 404
