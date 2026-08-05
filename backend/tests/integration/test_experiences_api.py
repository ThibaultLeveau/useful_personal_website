"""PostgreSQL-backed M5 experience admin, preview, and public contracts."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, cast

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
EMAIL = "experience-owner@example.test"
INITIAL_PASSWORD = "M5!Initial-9Forest"
REPLACEMENT_PASSWORD = "M5!Replacement-7Harbor"


@dataclass(frozen=True, slots=True)
class _ExperienceHarness:
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
def migrated_experience_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the sole M5 head."""
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
async def experience_harness(
    migrated_experience_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_ExperienceHarness]:
    """Yield one full-session administrator against migrated PostgreSQL."""
    del migrated_experience_database
    application = create_app(settings=_settings(test_database_url))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(
        email=EMAIL,
        display_name="Experience Owner",
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
        yield _ExperienceHarness(application, client)
    await runtime.dispose()


def _unsafe_headers(harness: _ExperienceHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


async def _create_skill(harness: _ExperienceHarness, *, visible: bool) -> str:
    category = await harness.client.post(
        "/api/v1/admin/skill-categories",
        headers=_unsafe_headers(
            harness,
            **{"Idempotency-Key": f"category-{str(visible).lower()}-00001"},
        ),
        json={
            "name": "Visible" if visible else "Internal",
            "slug": "visible" if visible else "internal",
            "description": "Synthetic category.",
        },
    )
    assert category.status_code == 201
    category_id = category.json()["data"]["id"]
    skill = await harness.client.post(
        "/api/v1/admin/skills",
        headers=_unsafe_headers(
            harness,
            **{"Idempotency-Key": f"skill-{str(visible).lower()}-0000001"},
        ),
        json={
            "name": "Python" if visible else "Private systems",
            "slug": "python" if visible else "private-systems",
            "category_id": category_id,
            "years_experience": "8.00",
            "featured": True,
            "visible": visible,
        },
    )
    assert skill.status_code == 201
    return cast("str", skill.json()["data"]["id"])


def _payload(skill_ids: list[str], *, role: str = "Staff Engineer") -> dict[str, object]:
    return {
        "company_name": "Example Studio",
        "company_url": "https://example.test/careers",
        "role_title": role,
        "employment_type": "full_time",
        "location": "Paris, France",
        "remote_status": "hybrid",
        "start_date": "2024-01-01",
        "end_date": None,
        "current_position": True,
        "short_summary": "Led the platform team.",
        "detailed_description": "A safe plain-text description.",
        "responsibilities": ["Designed service boundaries", "Mentored engineers"],
        "achievements": ["Reduced deployment time"],
        "technologies": ["Python", "PostgreSQL"],
        "skill_ids": skill_ids,
    }


async def _assert_public_role(
    harness: _ExperienceHarness,
    *,
    role: str,
    hidden_skill_id: str | None = None,
) -> None:
    response = await harness.client.get(
        "/api/v1/public/experiences",
        headers={"Authorization": "Bearer ignored-public-credential"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == ("public, max-age=0, s-maxage=0, must-revalidate")
    assert response.json()["data"][0]["role_title"] == role
    if hidden_skill_id is not None:
        assert response.json()["data"][0]["skills"] == [{"name": "Python", "slug": "python"}]
        assert hidden_skill_id not in response.text
        assert "published_revision_id" not in response.text
        assert "created_by" not in response.text


async def _assert_create_idempotency(
    harness: _ExperienceHarness,
    *,
    headers: dict[str, str],
    payload: dict[str, object],
    experience_id: str,
) -> None:
    replay = await harness.client.post(
        "/api/v1/admin/experiences",
        headers=headers,
        json=payload,
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == experience_id
    conflict = await harness.client.post(
        "/api/v1/admin/experiences",
        headers=headers,
        json={**payload, "role_title": "Different request"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


async def test_complete_revision_publication_privacy_lifecycle(
    experience_harness: _ExperienceHarness,
) -> None:
    """Create, preview, publish, edit-live, republish, hide, unpublish, and delete."""
    visible_skill = await _create_skill(experience_harness, visible=True)
    hidden_skill = await _create_skill(experience_harness, visible=False)
    payload = {**_payload([visible_skill, hidden_skill]), "visible": True}
    create_headers = _unsafe_headers(
        experience_harness,
        **{"Idempotency-Key": "experience-create-00001"},
    )
    created = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=create_headers,
        json=payload,
    )
    assert created.status_code == 201
    assert created.headers["cache-control"] == "private, no-store"
    assert created.headers["etag"] == '"v1"'
    experience_id = created.json()["data"]["id"]
    await _assert_create_idempotency(
        experience_harness,
        headers=create_headers,
        payload=payload,
        experience_id=experience_id,
    )

    preview = await experience_harness.client.get(
        f"/api/v1/admin/experiences/{experience_id}/preview"
    )
    assert preview.status_code == 200
    assert preview.headers["x-robots-tag"] == "noindex, nofollow"
    assert preview.json()["data"]["banner"] == "Draft preview - not public"
    assert preview.json()["data"]["noindex"] is True
    assert (await experience_harness.client.get("/api/v1/public/experiences")).json()["data"] == []

    published = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/actions/publish",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "experience-publish-0001"},
        ),
        json={},
    )
    assert published.status_code == 200
    assert published.headers["etag"] == '"v2"'
    assert published.json()["data"]["lifecycle"] == "published"

    await _assert_public_role(
        experience_harness,
        role="Staff Engineer",
        hidden_skill_id=hidden_skill,
    )

    changed = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}",
        headers=_unsafe_headers(experience_harness, **{"If-Match": '"v2"'}),
        json=_payload([visible_skill], role="Principal Engineer"),
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["lifecycle"] == "published_changes_pending"
    assert changed.json()["data"]["published"]["role_title"] == "Staff Engineer"
    public_unchanged = await experience_harness.client.get("/api/v1/public/experiences")
    assert public_unchanged.json()["data"][0]["role_title"] == "Staff Engineer"
    draft_preview = await experience_harness.client.get(
        f"/api/v1/admin/experiences/{experience_id}/preview"
    )
    assert draft_preview.json()["data"]["experience"]["draft"]["role_title"] == (
        "Principal Engineer"
    )

    republished = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/actions/publish",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "experience-publish-0002"},
        ),
        json={},
    )
    assert republished.status_code == 200
    assert republished.json()["data"]["lifecycle"] == "published"
    await _assert_public_role(experience_harness, role="Principal Engineer")

    hidden = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/visibility",
        headers=_unsafe_headers(experience_harness, **{"If-Match": '"v4"'}),
        json={"visible": False},
    )
    assert hidden.status_code == 200
    assert (await experience_harness.client.get("/api/v1/public/experiences")).json()["data"] == []
    shown = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/visibility",
        headers=_unsafe_headers(experience_harness, **{"If-Match": '"v5"'}),
        json={"visible": True},
    )
    assert shown.status_code == 200
    unpublished = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/actions/unpublish",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v6"', "Idempotency-Key": "experience-unpublish-01"},
        ),
    )
    assert unpublished.status_code == 200
    assert unpublished.json()["data"]["lifecycle"] == "unpublished"
    assert (await experience_harness.client.get("/api/v1/public/experiences")).json()["data"] == []
    deleted = await experience_harness.client.delete(
        f"/api/v1/admin/experiences/{experience_id}",
        headers=_unsafe_headers(experience_harness, **{"If-Match": '"v7"'}),
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"deleted": True}


async def test_validation_concurrency_filters_and_preview_isolation(
    experience_harness: _ExperienceHarness,
) -> None:
    """Invalid, stale, forged, guessed, mass-assignment, and query inputs fail safely."""
    skill_id = await _create_skill(experience_harness, visible=True)
    invalid = _payload([skill_id])
    invalid.update(
        {
            "current_position": True,
            "end_date": "2023-12-31",
            "version": 999,
            "visible": True,
        }
    )
    mass_assignment = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-invalid-0001"},
        ),
        json=invalid,
    )
    assert mass_assignment.status_code == 422
    assert "version" in mass_assignment.text

    invalid.pop("version")
    date_error = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-invalid-0002"},
        ),
        json=invalid,
    )
    assert date_error.status_code == 422
    assert date_error.json()["error"]["details"]["fields"][0]["path"] == "body.end_date"

    payload = {**_payload([skill_id]), "visible": True}
    missing_csrf = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers={"Origin": ORIGIN, "Idempotency-Key": "experience-forged-0001"},
        json=payload,
    )
    assert missing_csrf.status_code == 422
    assert missing_csrf.json()["error"]["code"] == "VALIDATION_FAILED"
    untrusted = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers={
            "Origin": "https://evil.example",
            "X-CSRF-Token": experience_harness.client.cookies["__Host-admin_csrf"],
            "Idempotency-Key": "experience-forged-0002",
        },
        json=payload,
    )
    assert untrusted.status_code == 403

    created = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-valid-00001"},
        ),
        json=payload,
    )
    experience_id = created.json()["data"]["id"]
    missing_match = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}",
        headers=_unsafe_headers(experience_harness),
        json=_payload([skill_id]),
    )
    assert missing_match.status_code == 428
    stale = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}",
        headers=_unsafe_headers(experience_harness, **{"If-Match": '"v99"'}),
        json=_payload([skill_id]),
    )
    assert stale.status_code == 409
    query_attack = await experience_harness.client.get(
        "/api/v1/admin/experiences?sort=updated_at;DROP%20TABLE%20experience"
    )
    assert query_attack.status_code == 422
    duplicate_query = await experience_harness.client.get(
        "/api/v1/admin/experiences?visible=true&visible=false"
    )
    assert duplicate_query.status_code == 422

    anonymous = AsyncClient(
        transport=ASGITransport(app=experience_harness.application),
        base_url=ORIGIN,
    )
    async with anonymous:
        guessed = await anonymous.get(f"/api/v1/admin/experiences/{experience_id}/preview")
    assert guessed.status_code == 401
    assert "Example Studio" not in guessed.text


async def test_future_schedule_is_absent_and_requires_no_worker(
    experience_harness: _ExperienceHarness,
) -> None:
    """A future UTC schedule stays absent through database-time eligibility."""
    skill_id = await _create_skill(experience_harness, visible=True)
    created = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-scheduled-01"},
        ),
        json={**_payload([skill_id]), "visible": True},
    )
    experience_id = created.json()["data"]["id"]
    future = datetime.now(UTC) + timedelta(days=1)
    scheduled = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{experience_id}/actions/publish",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "experience-schedule-0001"},
        ),
        json={"publish_at": future.isoformat().replace("+00:00", "Z")},
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["data"]["lifecycle"] == "scheduled"
    public = await experience_harness.client.get("/api/v1/public/experiences")
    assert public.json()["data"] == []


async def test_list_reorder_reschedule_and_allow_list_filter_contracts(
    experience_harness: _ExperienceHarness,
) -> None:
    """Exercise the remaining curated-order, lifecycle, and query branches end to end."""
    skill_id = await _create_skill(experience_harness, visible=True)
    first = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-breadth-0001"},
        ),
        json={**_payload([skill_id]), "visible": True},
    )
    second_payload = {
        **_payload([skill_id], role="Consulting Engineer"),
        "employment_type": "contract",
        "remote_status": "remote",
        "start_date": "2022-01-01",
        "end_date": "2023-12-31",
        "current_position": False,
        "visible": True,
    }
    second = await experience_harness.client.post(
        "/api/v1/admin/experiences",
        headers=_unsafe_headers(
            experience_harness,
            **{"Idempotency-Key": "experience-breadth-0002"},
        ),
        json=second_payload,
    )
    assert first.status_code == second.status_code == 201
    first_id = first.json()["data"]["id"]
    second_id = second.json()["data"]["id"]

    filtered = await experience_harness.client.get(
        "/api/v1/admin/experiences",
        params={
            "current": "true",
            "employment_type": "full_time",
            "lifecycle": "draft",
            "page": "1",
            "page_size": "1",
            "remote_status": "hybrid",
            "search": "Staff",
            "skill_id": skill_id,
            "sort": "-start_date",
            "visible": "true",
        },
    )
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["data"]] == [first_id]
    assert filtered.json()["meta"]["pagination"]["total_items"] == 1
    fetched = await experience_harness.client.get(f"/api/v1/admin/experiences/{first_id}")
    assert fetched.status_code == 200
    assert fetched.headers["etag"] == '"v1"'

    reorder_headers = _unsafe_headers(
        experience_harness,
        **{"If-Match": '"v1"', "Idempotency-Key": "experience-reorder-001"},
    )
    reordered = await experience_harness.client.put(
        "/api/v1/admin/experiences/actions/reorder",
        headers=reorder_headers,
        json={"ordered_ids": [second_id, first_id]},
    )
    assert reordered.status_code == 200
    assert [item["id"] for item in reordered.json()["data"]["items"]] == [second_id, first_id]
    replay = await experience_harness.client.put(
        "/api/v1/admin/experiences/actions/reorder",
        headers=reorder_headers,
        json={"ordered_ids": [second_id, first_id]},
    )
    assert replay.status_code == 200
    duplicate = await experience_harness.client.put(
        "/api/v1/admin/experiences/actions/reorder",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "experience-reorder-002"},
        ),
        json={"ordered_ids": [second_id, second_id]},
    )
    assert duplicate.status_code == 422

    future = datetime.now(UTC) + timedelta(days=1)
    scheduled = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{first_id}/actions/publish",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "experience-breadth-publish"},
        ),
        json={"publish_at": future.isoformat().replace("+00:00", "Z")},
    )
    assert scheduled.status_code == 200
    effective = datetime.now(UTC) - timedelta(minutes=1)
    rescheduled = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{first_id}/actions/reschedule",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v3"', "Idempotency-Key": "experience-reschedule-01"},
        ),
        json={"publish_at": effective.isoformat().replace("+00:00", "Z")},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["data"]["lifecycle"] == "published"
    public = await experience_harness.client.get(
        "/api/v1/public/experiences",
        params={
            "current": "true",
            "employment_type": "full_time",
            "remote_status": "hybrid",
            "skill": "python",
            "sort": "chronology",
        },
    )
    assert public.status_code == 200
    assert [item["id"] for item in public.json()["data"]] == [first_id]

    invalid_queries = (
        "/api/v1/admin/experiences?visible=perhaps",
        "/api/v1/admin/experiences?current=perhaps",
        "/api/v1/admin/experiences?employment_type=unknown",
        "/api/v1/admin/experiences?remote_status=unknown",
        "/api/v1/admin/experiences?skill_id=not-a-uuid",
        "/api/v1/admin/experiences?search=%20Staff",
        "/api/v1/public/experiences?current=perhaps",
        "/api/v1/public/experiences?employment_type=unknown",
        "/api/v1/public/experiences?remote_status=unknown",
        f"/api/v1/public/experiences?skill={'x' * 81}",
    )
    for path in invalid_queries:
        response = await experience_harness.client.get(path)
        assert response.status_code == 422, path

    missing = await experience_harness.client.get(
        "/api/v1/admin/experiences/0198a12c-ffff-7000-8000-000000000001"
    )
    assert missing.status_code == 404
    cannot_reschedule_draft = await experience_harness.client.put(
        f"/api/v1/admin/experiences/{second_id}/actions/reschedule",
        headers=_unsafe_headers(
            experience_harness,
            **{"If-Match": '"v2"', "Idempotency-Key": "experience-reschedule-02"},
        ),
        json={"publish_at": effective.isoformat().replace("+00:00", "Z")},
    )
    assert cannot_reschedule_draft.status_code == 409


def test_experiences_openapi_documents_security_queries_and_projections() -> None:
    """The generated-client contract exposes filters and keeps public data narrow."""
    schema = create_app(settings=Settings(environment=Environment.TEST)).openapi()
    paths = schema["paths"]
    admin_list = paths["/api/v1/admin/experiences"]["get"]
    public_list = paths["/api/v1/public/experiences"]["get"]
    create = paths["/api/v1/admin/experiences"]["post"]
    publish = paths["/api/v1/admin/experiences/{experience_id}/actions/publish"]["put"]

    assert admin_list["security"] == [{"AdminSessionCookie": []}]
    assert "security" not in public_list
    assert create["security"] == [{"AdminSessionCookie": []}]
    assert publish["security"] == [{"AdminSessionCookie": []}]
    create_parameters = {(item["name"], item["in"]): item for item in create["parameters"]}
    publish_parameters = {(item["name"], item["in"]): item for item in publish["parameters"]}
    assert create_parameters[("Origin", "header")]["required"] is True
    assert create_parameters[("X-CSRF-Token", "header")]["required"] is True
    assert create_parameters[("Idempotency-Key", "header")]["required"] is True
    assert publish_parameters[("If-Match", "header")]["required"] is True

    admin_queries = {item["name"] for item in admin_list["parameters"]}
    public_queries = {item["name"] for item in public_list["parameters"]}
    assert admin_queries == {
        "current",
        "employment_type",
        "lifecycle",
        "page",
        "page_size",
        "remote_status",
        "search",
        "skill_id",
        "sort",
        "visible",
    }
    assert public_queries == {
        "current",
        "employment_type",
        "page",
        "page_size",
        "remote_status",
        "skill",
        "sort",
    }

    components = schema["components"]["schemas"]
    public = components["PublicExperienceData"]["properties"]
    admin = components["ExperienceData"]["properties"]
    assert {"published", "publish_at", "version", "visible"}.isdisjoint(public)
    assert {"published", "publish_at", "version", "visible"}.issubset(admin)
