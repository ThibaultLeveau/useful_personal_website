"""PostgreSQL-backed M6 project admin, preview, and public contracts."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient, Response
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
EMAIL = "project-owner@example.test"
INITIAL_PASSWORD = "M6!Initial-9Forest"
REPLACEMENT_PASSWORD = "M6!Replacement-7Harbor"


@dataclass(frozen=True, slots=True)
class _ProjectHarness:
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
        f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {quoted_user}",
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
def migrated_project_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the sole M6 head."""
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
async def project_harness(
    migrated_project_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_ProjectHarness]:
    """Yield one full-session administrator against migrated PostgreSQL."""
    del migrated_project_database
    application = create_app(settings=_settings(test_database_url))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(
        email=EMAIL,
        display_name="Project Owner",
        password=INITIAL_PASSWORD,
    )
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url=ORIGIN,
    ) as client:
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
        yield _ProjectHarness(application, client)
    await runtime.dispose()


def _unsafe_headers(harness: _ProjectHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


def _payload(*, name: str = "API Platform", status: str = "active") -> dict[str, object]:
    return {
        "name": name,
        "short_description": "A secure API-first publishing platform.",
        "full_description": "## Overview\n\nA complete, controlled-Markdown case study.",
        "problem": "Teams needed reliable delivery and a clear ownership model.",
        "solution": "Built bounded services, immutable revisions, and typed contracts.",
        "impact": "Reduced lead time while improving operational confidence.",
        "owner_role": "Technical lead",
        "architecture": "FastAPI, PostgreSQL, and a generated TypeScript client.",
        "technologies": ["Python", "PostgreSQL"],
        "status": status,
        "start_date": "2025-01-01",
        "end_date": None,
        "repository_url": "https://example.test/repository",
        "demo_url": "https://example.test/demo",
        "skill_ids": [],
        "experience_ids": [],
        "related_project_ids": [],
        "seo_title": "API Platform case study",
        "seo_description": "How a secure API-first publishing platform was designed.",
        "canonical_url": "https://portfolio.example.test/projects/api-platform",
        "cover_media_id": None,
        "screenshot_media_ids": [],
    }


async def _create(
    harness: _ProjectHarness,
    *,
    slug: str,
    name: str,
    idempotency_key: str,
    featured: bool = False,
) -> Response:
    response = await harness.client.post(
        "/api/v1/admin/projects",
        headers=_unsafe_headers(harness, **{"Idempotency-Key": idempotency_key}),
        json={**_payload(name=name), "slug": slug, "visible": True, "featured": featured},
    )
    assert response.status_code == 201, response.text
    return response


async def test_complete_revision_publication_privacy_lifecycle(  # noqa: PLR0915
    project_harness: _ProjectHarness,
) -> None:
    """Create, preview, publish, edit-live, republish, hide, and retire a project."""
    create_headers = _unsafe_headers(
        project_harness,
        **{"Idempotency-Key": "project-create-lifecycle-0001"},
    )
    create_payload = {
        **_payload(),
        "slug": "api-platform",
        "visible": True,
        "featured": False,
    }
    created = await project_harness.client.post(
        "/api/v1/admin/projects", headers=create_headers, json=create_payload
    )
    assert created.status_code == 201
    assert created.headers["cache-control"] == "private, no-store"
    assert created.headers["etag"] == '"v1"'
    project_id = created.json()["data"]["id"]

    replay = await project_harness.client.post(
        "/api/v1/admin/projects", headers=create_headers, json=create_payload
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == project_id
    conflict = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers=create_headers,
        json={**create_payload, "name": "Different request"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    preview = await project_harness.client.get(f"/api/v1/admin/projects/{project_id}/preview")
    assert preview.status_code == 200
    assert preview.headers["x-robots-tag"] == "noindex, nofollow"
    assert preview.json()["data"]["banner"] == "Draft preview - not public"
    assert (await project_harness.client.get("/api/v1/public/projects")).json()["data"] == []
    missing_detail = await project_harness.client.get("/api/v1/public/projects/api-platform")
    assert missing_detail.status_code == 404

    published = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/actions/publish",
        headers=_unsafe_headers(
            project_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "project-publish-now-0001"},
        ),
        json={},
    )
    assert published.status_code == 200
    assert published.headers["etag"] == '"v2"'
    assert published.json()["data"]["lifecycle"] == "published"

    public = await project_harness.client.get("/api/v1/public/projects")
    assert public.status_code == 200
    assert public.headers["cache-control"] == "public, max-age=0, s-maxage=0, must-revalidate"
    assert public.json()["data"][0]["slug"] == "api-platform"
    assert public.json()["data"][0]["cover_media_id"] is None
    assert public.json()["data"][0]["screenshot_media_ids"] == []
    assert "gallery_available" not in public.text
    assert "published_revision_id" not in public.text
    assert "created_by" not in public.text
    detail = await project_harness.client.get("/api/v1/public/projects/api-platform")
    assert detail.status_code == 200
    assert detail.json()["data"]["full_description"].startswith("## Overview")

    changed_payload = _payload(name="API Platform, evolved")
    changed_payload["impact"] = "## Results\n\nCut deployment time by **40%**."
    changed = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v2"'}),
        json=changed_payload,
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["lifecycle"] == "published_changes_pending"
    assert changed.json()["data"]["published"]["name"] == "API Platform"
    unchanged = await project_harness.client.get("/api/v1/public/projects/api-platform")
    assert unchanged.json()["data"]["name"] == "API Platform"

    republished = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/actions/publish",
        headers=_unsafe_headers(
            project_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "project-republish-00001"},
        ),
        json={},
    )
    assert republished.status_code == 200
    assert republished.json()["data"]["lifecycle"] == "published"
    updated_public = await project_harness.client.get("/api/v1/public/projects/api-platform")
    assert updated_public.json()["data"]["name"] == "API Platform, evolved"

    featured = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/featured",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v4"'}),
        json={"featured": True},
    )
    assert featured.status_code == 200
    hidden = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/visibility",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v5"'}),
        json={"visible": False},
    )
    assert hidden.status_code == 200
    assert (await project_harness.client.get("/api/v1/public/projects")).json()["data"] == []
    shown = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/visibility",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v6"'}),
        json={"visible": True},
    )
    assert shown.status_code == 200
    unpublished = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}/actions/unpublish",
        headers=_unsafe_headers(
            project_harness,
            **{"If-Match": '"v7"', "Idempotency-Key": "project-unpublish-0001"},
        ),
    )
    assert unpublished.status_code == 200
    assert unpublished.json()["data"]["lifecycle"] == "unpublished"
    deleted = await project_harness.client.delete(
        f"/api/v1/admin/projects/{project_id}",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v8"'}),
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"deleted": True}


async def test_schedule_reorder_filters_and_query_allow_lists(
    project_harness: _ProjectHarness,
) -> None:
    """Exercise curated order, database-time scheduling, and all public filter families."""
    first = await _create(
        project_harness,
        slug="platform-one",
        name="Platform One",
        idempotency_key="project-breadth-create-0001",
    )
    second = await _create(
        project_harness,
        slug="platform-two",
        name="Platform Two",
        idempotency_key="project-breadth-create-0002",
    )
    first_id = first.json()["data"]["id"]
    second_id = second.json()["data"]["id"]

    filtered = await project_harness.client.get(
        "/api/v1/admin/projects",
        params={
            "lifecycle": "draft",
            "visible": "true",
            "featured": "false",
            "status": "active",
            "search": "One",
            "sort": "-updated_at",
            "page": "1",
            "page_size": "1",
        },
    )
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["data"]] == [first_id]
    fetched = await project_harness.client.get(f"/api/v1/admin/projects/{first_id}")
    assert fetched.status_code == 200
    assert fetched.headers["etag"] == '"v1"'

    reorder_headers = _unsafe_headers(
        project_harness,
        **{"If-Match": '"v1"', "Idempotency-Key": "project-reorder-all-0001"},
    )
    reordered = await project_harness.client.put(
        "/api/v1/admin/projects/actions/reorder",
        headers=reorder_headers,
        json={"ordered_ids": [second_id, first_id]},
    )
    assert reordered.status_code == 200
    assert [item["id"] for item in reordered.json()["data"]["items"]] == [
        second_id,
        first_id,
    ]
    replay = await project_harness.client.put(
        "/api/v1/admin/projects/actions/reorder",
        headers=reorder_headers,
        json={"ordered_ids": [second_id, first_id]},
    )
    assert replay.status_code == 200

    future = datetime.now(UTC) + timedelta(days=1)
    scheduled = await project_harness.client.put(
        f"/api/v1/admin/projects/{first_id}/actions/publish",
        headers=_unsafe_headers(
            project_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "project-schedule-000001"},
        ),
        json={"publish_at": future.isoformat().replace("+00:00", "Z")},
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["data"]["lifecycle"] == "scheduled"
    assert (await project_harness.client.get("/api/v1/public/projects")).json()["data"] == []

    effective = datetime.now(UTC) - timedelta(minutes=1)
    rescheduled = await project_harness.client.put(
        f"/api/v1/admin/projects/{first_id}/actions/reschedule",
        headers=_unsafe_headers(
            project_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "project-reschedule-0001"},
        ),
        json={"publish_at": effective.isoformat().replace("+00:00", "Z")},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["data"]["lifecycle"] == "published"

    public = await project_harness.client.get(
        "/api/v1/public/projects",
        params={
            "status": "active",
            "technology": "Python",
            "featured": "false",
            "search": "Platform",
            "sort": "-start_date",
        },
    )
    assert public.status_code == 200
    assert [item["id"] for item in public.json()["data"]] == [first_id]

    invalid_queries = (
        "/api/v1/admin/projects?visible=perhaps",
        "/api/v1/admin/projects?featured=perhaps",
        "/api/v1/admin/projects?status=unknown",
        "/api/v1/admin/projects?skill_id=not-a-uuid",
        "/api/v1/admin/projects?experience_id=not-a-uuid",
        "/api/v1/admin/projects?search=%20Platform",
        "/api/v1/admin/projects?sort=updated_at;DROP%20TABLE%20project",
        "/api/v1/admin/projects?visible=true&visible=false",
        "/api/v1/public/projects?featured=perhaps",
        "/api/v1/public/projects?status=unknown",
        "/api/v1/public/projects?experience_id=not-a-uuid",
        f"/api/v1/public/projects?skill={'x' * 81}",
        f"/api/v1/public/projects?technology={'x' * 121}",
    )
    for path in invalid_queries:
        response = await project_harness.client.get(path)
        assert response.status_code == 422, path


async def test_security_validation_concurrency_and_media_staging(
    project_harness: _ProjectHarness,
) -> None:
    """Forged, stale, unsafe Markdown, mass-assignment, and unavailable media fail safely."""
    valid = {**_payload(), "slug": "secure-project", "visible": True, "featured": False}
    mass_assignment = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers=_unsafe_headers(
            project_harness,
            **{"Idempotency-Key": "project-mass-assignment-01"},
        ),
        json={**valid, "version": 999},
    )
    assert mass_assignment.status_code == 422
    assert "version" in mass_assignment.text

    missing_csrf = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers={"Origin": ORIGIN, "Idempotency-Key": "project-forged-request-01"},
        json=valid,
    )
    assert missing_csrf.status_code == 422
    untrusted = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers={
            "Origin": "https://evil.example",
            "X-CSRF-Token": project_harness.client.cookies["__Host-admin_csrf"],
            "Idempotency-Key": "project-forged-request-02",
        },
        json=valid,
    )
    assert untrusted.status_code == 403

    unsafe_markdown = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers=_unsafe_headers(
            project_harness,
            **{"Idempotency-Key": "project-unsafe-markdown-01"},
        ),
        json={**valid, "slug": "unsafe-markdown", "full_description": "<script>x</script>"},
    )
    assert unsafe_markdown.status_code == 422
    assert unsafe_markdown.json()["error"]["code"] == "VALIDATION_FAILED"

    media = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers=_unsafe_headers(
            project_harness,
            **{"Idempotency-Key": "project-media-staging-001"},
        ),
        json={
            **valid,
            "slug": "media-staging",
            "cover_media_id": "0198a12c-ffff-7000-8000-000000000001",
        },
    )
    assert media.status_code == 409
    assert media.json()["error"]["code"] == "RESOURCE_CONFLICT"

    created = await project_harness.client.post(
        "/api/v1/admin/projects",
        headers=_unsafe_headers(
            project_harness,
            **{"Idempotency-Key": "project-security-valid-001"},
        ),
        json=valid,
    )
    assert created.status_code == 201
    project_id = created.json()["data"]["id"]
    missing_match = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}",
        headers=_unsafe_headers(project_harness),
        json=_payload(),
    )
    assert missing_match.status_code == 428
    stale = await project_harness.client.put(
        f"/api/v1/admin/projects/{project_id}",
        headers=_unsafe_headers(project_harness, **{"If-Match": '"v99"'}),
        json=_payload(),
    )
    assert stale.status_code == 409

    anonymous = AsyncClient(
        transport=ASGITransport(app=project_harness.application),
        base_url=ORIGIN,
    )
    async with anonymous:
        guessed = await anonymous.get(f"/api/v1/admin/projects/{project_id}/preview")
    assert guessed.status_code == 401
    assert "API Platform" not in guessed.text


def test_projects_openapi_documents_security_queries_and_public_projection() -> None:
    """The generated-client contract documents controls and keeps public data narrow."""
    schema = create_app(settings=Settings(environment=Environment.TEST)).openapi()
    paths = schema["paths"]
    admin_list = paths["/api/v1/admin/projects"]["get"]
    public_list = paths["/api/v1/public/projects"]["get"]
    create = paths["/api/v1/admin/projects"]["post"]
    publish = paths["/api/v1/admin/projects/{project_id}/actions/publish"]["put"]

    assert admin_list["security"] == [{"AdminSessionCookie": []}]
    assert "security" not in public_list
    assert create["security"] == [{"AdminSessionCookie": []}]
    create_parameters = {(item["name"], item["in"]): item for item in create["parameters"]}
    publish_parameters = {(item["name"], item["in"]): item for item in publish["parameters"]}
    assert create_parameters[("Origin", "header")]["required"] is True
    assert create_parameters[("X-CSRF-Token", "header")]["required"] is True
    assert create_parameters[("Idempotency-Key", "header")]["required"] is True
    assert publish_parameters[("If-Match", "header")]["required"] is True

    admin_queries = {item["name"] for item in admin_list["parameters"]}
    public_queries = {item["name"] for item in public_list["parameters"]}
    assert admin_queries == {
        "experience_id",
        "featured",
        "lifecycle",
        "page",
        "page_size",
        "search",
        "skill_id",
        "sort",
        "status",
        "visible",
    }
    assert public_queries == {
        "experience_id",
        "featured",
        "page",
        "page_size",
        "search",
        "skill",
        "sort",
        "status",
        "technology",
    }

    components = schema["components"]["schemas"]
    public = components["PublicProjectData"]["properties"]
    admin = components["ProjectData"]["properties"]
    assert {"published", "publish_at", "version", "visible"}.isdisjoint(public)
    assert {"published", "publish_at", "version", "visible"}.issubset(admin)
