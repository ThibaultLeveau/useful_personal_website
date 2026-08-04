"""PostgreSQL-backed secure media ingestion, library, delivery, and deletion tests."""

# ruff: noqa: D103, PLR0915

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text

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
EMAIL = "media-owner@example.test"
INITIAL_PASSWORD = "M9!Initial-4Meadow"
REPLACEMENT_PASSWORD = "M9!Replacement-8Harbor"


@dataclass(frozen=True, slots=True)
class _MediaHarness:
    application: FastAPI
    client: AsyncClient


@pytest.fixture
def migrated_media_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
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
async def media_harness(
    migrated_media_database: None,
    test_database_url: SecretStr,
    tmp_path: Path,
) -> AsyncIterator[_MediaHarness]:
    del migrated_media_database
    application = create_app(settings=_settings(test_database_url, tmp_path / "private-media"))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(email=EMAIL, display_name="Media Owner", password=INITIAL_PASSWORD)
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
        yield _MediaHarness(application, client)
    await runtime.dispose()


def _unsafe_headers(harness: _MediaHarness, *, key: str | None = None) -> dict[str, str]:
    result = {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
    }
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def _png_bytes(*, color: tuple[int, int, int] = (25, 82, 110)) -> bytes:
    target = BytesIO()
    Image.new("RGB", (800, 400), color).save(target, format="PNG")
    return target.getvalue()


def _profile_payload(data: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in data.items()
        if key not in {"id", "created_at", "updated_at", "version"}
    }


async def test_upload_replay_library_delivery_and_tombstone(media_harness: _MediaHarness) -> None:
    client = media_harness.client
    content = _png_bytes()
    headers = _unsafe_headers(media_harness, key="media-upload-portrait-0001")
    upload = await client.post(
        "/api/v1/admin/media",
        headers=headers,
        files={"file": ("../../private/portrait.png", content, "image/png")},
    )
    assert upload.status_code == 201, upload.text
    data = upload.json()["data"]
    asset_id = data["id"]
    assert data["status"] == "ready"
    assert data["display_name"] == "portrait.png"
    assert len(data["variants"]) == 4
    assert "storage_key" not in upload.text
    assert "checksum" not in upload.text
    assert upload.headers["cache-control"] == "private, no-store"

    replay = await client.post(
        "/api/v1/admin/media",
        headers=headers,
        files={"file": ("../../private/portrait.png", content, "image/png")},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["data"]["id"] == asset_id

    conflict = await client.post(
        "/api/v1/admin/media",
        headers=headers,
        files={"file": ("portrait.png", _png_bytes(color=(90, 30, 20)), "image/png")},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    listing = await client.get("/api/v1/admin/media")
    assert listing.status_code == 200
    assert listing.json()["meta"]["pagination"]["total_items"] == 1

    rendition = await client.get(
        f"/api/v1/admin/media/{asset_id}/content?width=500&representation=webp"
    )
    assert rendition.status_code == 200
    assert rendition.headers["content-type"] == "image/webp"
    assert rendition.headers["cache-control"] == "private, no-store"
    with Image.open(BytesIO(rendition.content)) as decoded:
        assert decoded.size == (640, 320)
        assert not decoded.getexif()

    public = await client.get(f"/api/v1/media/{asset_id}/640")
    assert public.status_code == 404

    profile = await client.get("/api/v1/admin/profile")
    assert profile.status_code == 200
    profile_payload = _profile_payload(profile.json()["data"])
    profile_payload.update({"full_name": "Media Owner", "profile_image_id": asset_id})
    assigned = await client.put(
        "/api/v1/admin/profile",
        headers={**_unsafe_headers(media_harness), "If-Match": profile.headers["etag"]},
        json=profile_payload,
    )
    assert assigned.status_code == 200, assigned.text
    usage = await client.get(f"/api/v1/admin/media/{asset_id}/usage")
    assert usage.status_code == 200
    assert usage.json()["data"]["items"] == [
        {
            "owner_type": "profile",
            "owner_id": assigned.json()["data"]["id"],
            "role": "profile_image",
            "position": 0,
            "active": True,
            "public": True,
        }
    ]
    public = await client.get(f"/api/v1/media/{asset_id}/640")
    assert public.status_code == 200
    assert public.headers["cache-control"] == "public, max-age=300, s-maxage=300"

    in_use = await client.delete(
        f"/api/v1/admin/media/{asset_id}",
        headers={**_unsafe_headers(media_harness), "If-Match": upload.headers["etag"]},
    )
    assert in_use.status_code == 409

    cleared_payload = _profile_payload(assigned.json()["data"])
    cleared_payload["profile_image_id"] = None
    cleared = await client.put(
        "/api/v1/admin/profile",
        headers={**_unsafe_headers(media_harness), "If-Match": assigned.headers["etag"]},
        json=cleared_payload,
    )
    assert cleared.status_code == 200, cleared.text
    assert (await client.get(f"/api/v1/media/{asset_id}/640")).status_code == 404

    missing_precondition = await client.patch(
        f"/api/v1/admin/media/{asset_id}",
        headers=_unsafe_headers(media_harness),
        json={"display_name": "Updated portrait"},
    )
    assert missing_precondition.status_code == 428

    deleted = await client.delete(
        f"/api/v1/admin/media/{asset_id}",
        headers={**_unsafe_headers(media_harness), "If-Match": upload.headers["etag"]},
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["data"]["status"] == "deleted"
    assert (await client.get(f"/api/v1/admin/media/{asset_id}")).status_code == 404
    runtime = media_harness.application.state.database_runtime
    async with runtime.engine.connect() as connection:
        audit_rows = (
            await connection.execute(
                text(
                    "SELECT event_type,metadata FROM audit_entry "
                    "WHERE resource_type='media_asset' ORDER BY occurred_at,id"
                )
            )
        ).all()
    assert [row.event_type for row in audit_rows] == [
        "media.upload.accepted",
        "media.upload.ready",
        "media.delete.requested",
        "media.delete.completed",
    ]
    serialized_audit = str(audit_rows).casefold()
    assert "portrait" not in serialized_audit
    assert "storage_key" not in serialized_audit
    assert "checksum" not in serialized_audit


async def test_hostile_and_oversized_uploads_fail_without_reflection(
    media_harness: _MediaHarness,
) -> None:
    client = media_harness.client
    svg = b"<svg><script>alert(document.cookie)</script></svg>"
    rejected = await client.post(
        "/api/v1/admin/media",
        headers=_unsafe_headers(media_harness, key="media-upload-hostile-0001"),
        files={"file": ("attack.svg", svg, "image/svg+xml")},
    )
    assert rejected.status_code == 415
    assert "script" not in rejected.text
    assert "attack.svg" not in rejected.text

    oversized = await client.post(
        "/api/v1/admin/media",
        headers=_unsafe_headers(media_harness, key="media-upload-oversize-0001"),
        files={"file": ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
    )
    assert oversized.status_code == 413
    assert "large.png" not in oversized.text
