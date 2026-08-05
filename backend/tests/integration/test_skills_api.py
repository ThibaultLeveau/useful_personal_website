"""PostgreSQL-backed M4 skills admin-to-public contracts."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from app.config import Environment, Settings
from app.infrastructure.database.audit import AuditEntryRecord
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.infrastructure.database.session import create_database_engine
from app.main import create_app
from app.modules.identity.service import BootstrapService
from app.modules.skills.service import SkillReferenceFacade, SkillsNotFoundError, SkillsService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI

pytestmark = pytest.mark.postgresql

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://testserver"
EMAIL = "skills-owner@example.test"
INITIAL_PASSWORD = "M4!Initial-9Forest"
REPLACEMENT_PASSWORD = "M4!Replacement-7Harbor"


@dataclass(frozen=True, slots=True)
class _SkillsHarness:
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
def migrated_skills_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the sole M4 head."""
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
async def skills_harness(
    migrated_skills_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_SkillsHarness]:
    """Yield one full-session administrator against migrated PostgreSQL."""
    del migrated_skills_database
    application = create_app(settings=_settings(test_database_url))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(
        email=EMAIL,
        display_name="Skills Owner",
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
        yield _SkillsHarness(application=application, client=client)
    await runtime.dispose()


def _unsafe_headers(harness: _SkillsHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


async def _create_category(harness: _SkillsHarness) -> dict[str, object]:
    payload = {
        "name": "Backend Engineering",
        "slug": "Backend Engineering",
        "description": "Server-side systems.",
    }
    headers = _unsafe_headers(harness, **{"Idempotency-Key": "category-create-00001"})
    created = await harness.client.post(
        "/api/v1/admin/skill-categories",
        headers=headers,
        json=payload,
    )
    assert created.status_code == 201
    replay = await harness.client.post(
        "/api/v1/admin/skill-categories",
        headers=headers,
        json=payload,
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == created.json()["data"]["id"]
    return cast("dict[str, object]", created.json()["data"])


async def _create_skill(
    harness: _SkillsHarness,
    category_id: str,
    *,
    name: str,
    visible: bool,
    key: str,
) -> dict[str, object]:
    payload = {
        "name": name,
        "slug": name,
        "category_id": category_id,
        "description": f"Fictional {name} capability.",
        "proficiency_label": "Advanced",
        "proficiency_score": 90,
        "years_experience": "8.50",
        "icon_key": "code",
        "featured": True,
        "visible": visible,
    }
    response = await harness.client.post(
        "/api/v1/admin/skills",
        headers=_unsafe_headers(harness, **{"Idempotency-Key": key}),
        json=payload,
    )
    assert response.status_code == 201
    replay = await harness.client.post(
        "/api/v1/admin/skills",
        headers=_unsafe_headers(harness, **{"Idempotency-Key": key}),
        json=payload,
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == response.json()["data"]["id"]
    return cast("dict[str, object]", response.json()["data"])


async def _assert_public_and_filtered_lists(
    harness: _SkillsHarness,
    category_id: str,
) -> None:
    """Verify public privacy and allow-listed administrator filtering."""
    public = await harness.client.get(
        "/api/v1/public/skills?featured=true",
        headers={"Authorization": "Bearer ignored-public-credential"},
    )
    assert public.status_code == 200
    assert public.headers["cache-control"].startswith("public")
    assert [item["slug"] for item in public.json()["data"]] == ["python"]
    assert "private-tooling" not in public.text
    assert '"id"' not in public.text
    assert '"version"' not in public.text
    assert public.json()["data"][0]["category_slug"] == "backend-engineering"
    assert public.json()["data"][0]["related_projects"] == []

    listing = await harness.client.get(
        f"/api/v1/admin/skills?category_id={category_id}&visible=true&sort=name"
    )
    assert listing.status_code == 200
    assert listing.headers["cache-control"] == "private, no-store"
    assert listing.json()["meta"]["pagination"]["total_items"] == 1

    invalid_query = await harness.client.get("/api/v1/admin/skills?filter[name]=sql")
    assert invalid_query.status_code == 422
    assert invalid_query.json()["error"]["code"] == "VALIDATION_FAILED"


async def _exercise_remaining_crud(
    harness: _SkillsHarness,
    *,
    category_id: str,
    hidden_id: str,
    skill_id: str,
    skill_payload: dict[str, object],
) -> None:
    """Cover remaining category CRUD, reassignment, deletion, and public filters."""
    client = harness.client
    second = await client.post(
        "/api/v1/admin/skill-categories",
        headers=_unsafe_headers(harness, **{"Idempotency-Key": "category-create-00002"}),
        json={"name": "Platform", "slug": "platform", "description": None},
    )
    assert second.status_code == 201
    second_id = second.json()["data"]["id"]

    duplicate = await client.post(
        "/api/v1/admin/skill-categories",
        headers=_unsafe_headers(harness, **{"Idempotency-Key": "category-create-00003"}),
        json={"name": "Duplicate", "slug": "Backend Engineering"},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["details"]["fields"][0]["code"] == "duplicate"

    categories = await client.get("/api/v1/admin/skill-categories")
    assert categories.status_code == 200
    assert len(categories.json()["data"]["items"]) == 2
    assert (await client.get(f"/api/v1/admin/skill-categories/{category_id}")).status_code == 200

    stale = await client.put(
        f"/api/v1/admin/skill-categories/{second_id}",
        headers=_unsafe_headers(harness, **{"If-Match": '"v99"'}),
        json={"name": "Platform", "slug": "platform", "description": "Operations."},
    )
    assert stale.status_code == 409
    updated_second = await client.put(
        f"/api/v1/admin/skill-categories/{second_id}",
        headers=_unsafe_headers(harness, **{"If-Match": '"v1"'}),
        json={"name": "Platform", "slug": "platform", "description": "Operations."},
    )
    assert updated_second.status_code == 200

    category_order = await client.put(
        "/api/v1/admin/skill-categories/actions/reorder",
        headers=_unsafe_headers(
            harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "category-reorder-0001"},
        ),
        json={"ordered_ids": [second_id, category_id]},
    )
    assert category_order.status_code == 200
    assert [item["id"] for item in category_order.json()["data"]["items"]] == [
        second_id,
        category_id,
    ]
    category_replay = await client.put(
        "/api/v1/admin/skill-categories/actions/reorder",
        headers=_unsafe_headers(
            harness,
            **{"If-Match": '"v1"', "Idempotency-Key": "category-reorder-0001"},
        ),
        json={"ordered_ids": [second_id, category_id]},
    )
    assert category_replay.status_code == 200

    assert (await client.get(f"/api/v1/admin/skills/{skill_id}")).status_code == 200
    reassigned = await client.put(
        f"/api/v1/admin/skills/{skill_id}",
        headers=_unsafe_headers(harness, **{"If-Match": '"v3"'}),
        json={**skill_payload, "category_id": second_id},
    )
    assert reassigned.status_code == 200
    assert reassigned.json()["data"]["category_id"] == second_id

    service = cast("SkillsService", harness.application.state.skills_service)
    references = await SkillReferenceFacade(service).resolve((UUID(skill_id), UUID(hidden_id)))
    assert {item.slug for item in references} == {"python", "private-tooling"}
    with pytest.raises(SkillsNotFoundError):
        await service.reference_summaries((UUID(skill_id), UUID(skill_id)))
    service.reject_unavailable_relations(())

    platform_public = await client.get("/api/v1/public/skills?category=platform&search=Python")
    assert platform_public.status_code == 200
    assert [item["slug"] for item in platform_public.json()["data"]] == ["python"]
    assert (await client.get("/api/v1/public/skills?featured=TRUE")).status_code == 422

    hidden = await client.get(f"/api/v1/admin/skills/{hidden_id}")
    assert hidden.status_code == 200
    for target_id, version in (
        (hidden_id, hidden.json()["data"]["version"]),
        (skill_id, reassigned.json()["data"]["version"]),
    ):
        deleted = await client.delete(
            f"/api/v1/admin/skills/{target_id}",
            headers=_unsafe_headers(harness, **{"If-Match": f'"v{version}"'}),
        )
        assert deleted.status_code == 200

    assert (await client.get(f"/api/v1/admin/skills/{skill_id}")).status_code == 404

    for target_id in (category_id, second_id):
        current = await client.get(f"/api/v1/admin/skill-categories/{target_id}")
        assert current.status_code == 200
        version = current.json()["data"]["version"]
        deleted = await client.delete(
            f"/api/v1/admin/skill-categories/{target_id}",
            headers=_unsafe_headers(harness, **{"If-Match": f'"v{version}"'}),
        )
        assert deleted.status_code == 200

    assert (await client.get(f"/api/v1/admin/skill-categories/{category_id}")).status_code == 404

    empty = await client.get("/api/v1/public/skills")
    assert empty.status_code == 200
    assert empty.json()["data"] == []


async def test_skills_crud_privacy_filters_concurrency_and_order(
    skills_harness: _SkillsHarness,
) -> None:
    """Built API enforces public visibility, ordering, conflicts, and safe relations."""
    client = skills_harness.client
    category = await _create_category(skills_harness)
    category_id = str(category["id"])
    visible = await _create_skill(
        skills_harness,
        category_id,
        name="Python",
        visible=True,
        key="skill-create-python-0001",
    )
    hidden = await _create_skill(
        skills_harness,
        category_id,
        name="Private Tooling",
        visible=False,
        key="skill-create-hidden-0001",
    )

    await _assert_public_and_filtered_lists(skills_harness, category_id)

    skill_id = str(visible["id"])
    payload = {
        "name": "Python",
        "slug": "python",
        "category_id": category_id,
        "description": "Updated without exposing hidden content.",
        "proficiency_label": "Advanced",
        "proficiency_score": 100,
        "years_experience": "9.00",
        "featured": False,
        "visible": True,
    }
    stale = await client.put(
        f"/api/v1/admin/skills/{skill_id}",
        headers=_unsafe_headers(skills_harness, **{"If-Match": '"v99"'}),
        json=payload,
    )
    assert stale.status_code == 409

    updated = await client.put(
        f"/api/v1/admin/skills/{skill_id}",
        headers=_unsafe_headers(skills_harness, **{"If-Match": '"v1"'}),
        json=payload,
    )
    assert updated.status_code == 200
    assert updated.headers["etag"] == '"v2"'

    ids = [str(hidden["id"]), skill_id]
    reordered = await client.put(
        f"/api/v1/admin/skill-categories/{category_id}/skills/reorder",
        headers=_unsafe_headers(
            skills_harness,
            **{
                "If-Match": '"v2"',
                "Idempotency-Key": "skill-reorder-backend-001",
            },
        ),
        json={"ordered_ids": ids},
    )
    assert reordered.status_code == 200
    assert [item["id"] for item in reordered.json()["data"]["items"]] == ids
    replayed_order = await client.put(
        f"/api/v1/admin/skill-categories/{category_id}/skills/reorder",
        headers=_unsafe_headers(
            skills_harness,
            **{
                "If-Match": '"v2"',
                "Idempotency-Key": "skill-reorder-backend-001",
            },
        ),
        json={"ordered_ids": ids},
    )
    assert replayed_order.status_code == 200

    mismatch = await client.put(
        f"/api/v1/admin/skill-categories/{category_id}/skills/reorder",
        headers=_unsafe_headers(
            skills_harness,
            **{
                "If-Match": '"v1"',
                "Idempotency-Key": "skill-reorder-backend-001",
            },
        ),
        json={"ordered_ids": list(reversed(ids))},
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    in_use = await client.delete(
        f"/api/v1/admin/skill-categories/{category_id}",
        headers=_unsafe_headers(skills_harness, **{"If-Match": '"v1"'}),
    )
    assert in_use.status_code == 409
    assert in_use.json()["error"]["details"]["reason"] == "category_in_use"

    relation = await client.put(
        f"/api/v1/admin/skills/{skill_id}",
        headers=_unsafe_headers(skills_harness, **{"If-Match": '"v3"'}),
        json={**payload, "associated_project_ids": [skill_id]},
    )
    assert relation.status_code == 422
    assert relation.json()["error"]["details"]["fields"][0]["code"] == ("capability_unavailable")

    mass_assignment = await client.put(
        f"/api/v1/admin/skills/{skill_id}",
        headers=_unsafe_headers(skills_harness, **{"If-Match": '"v3"'}),
        json={**payload, "actor_id": "must-not-cross"},
    )
    assert mass_assignment.status_code == 422
    assert "must-not-cross" not in mass_assignment.text

    await _exercise_remaining_crud(
        skills_harness,
        category_id=category_id,
        hidden_id=str(hidden["id"]),
        skill_id=skill_id,
        skill_payload=payload,
    )

    runtime = skills_harness.application.state.database_runtime
    async with runtime.session_factory() as session:
        audits = list((await session.execute(select(AuditEntryRecord))).scalars())
    skill_audits = [entry for entry in audits if entry.event_type.startswith("skill")]
    assert {entry.event_type for entry in skill_audits} >= {
        "skill_category.created",
        "skill.created",
        "skill.updated",
        "skill.reordered",
        "skill.deleted",
        "skill_category.updated",
        "skill_category.reordered",
        "skill_category.deleted",
    }
    assert all(set(entry.metadata_json) == {"version", "fields"} for entry in skill_audits)
    assert "Fictional" not in str([entry.metadata_json for entry in skill_audits])


def test_skills_openapi_has_distinct_security_and_projection_shapes() -> None:
    """OpenAPI declares protected mutations and a no-auth public projection."""
    schema = create_app(settings=Settings(environment=Environment.TEST)).openapi()
    paths = schema["paths"]
    assert "security" not in paths["/api/v1/public/skills"]["get"]
    create = paths["/api/v1/admin/skills"]["post"]
    parameters = {(item["name"], item["in"]): item for item in create["parameters"]}
    assert create["security"] == [{"AdminSessionCookie": []}]
    assert parameters[("Origin", "header")]["required"] is True
    assert parameters[("X-CSRF-Token", "header")]["required"] is True
    assert parameters[("Idempotency-Key", "header")]["required"] is True

    components = schema["components"]["schemas"]
    public = components["PublicSkillData"]["properties"]
    admin = components["SkillData"]["properties"]
    assert "id" not in public
    assert "version" not in public
    assert "visible" not in public
    assert "id" in admin
    assert "version" in admin
