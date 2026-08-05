"""PostgreSQL-backed M3 admin-to-public site configuration contracts."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from app.commands.seed_demo import EXIT_PRODUCTION_REFUSED, seed_demo
from app.commands.seed_demo import main as seed_demo_main
from app.config import Environment, Settings
from app.infrastructure.database.audit import AuditEntryRecord
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.database.site_configuration_uow import FooterRepository
from app.main import create_app
from app.modules.identity.service import BootstrapService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI

pytestmark = pytest.mark.postgresql

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://testserver"
EMAIL = "site-owner@example.test"
INITIAL_PASSWORD = "M3!Initial-9Frost"
REPLACEMENT_PASSWORD = "M3!Replacement-7River"
ROOT_ID = UUID("00000000-0000-7000-8000-000000000321")
HIDDEN_ID = UUID("00000000-0000-7000-8000-000000000322")
COLUMN_ID = UUID("00000000-0000-7000-8000-000000000323")
FOOTER_ITEM_ID = UUID("00000000-0000-7000-8000-000000000324")


@dataclass(frozen=True, slots=True)
class _SiteHarness:
    application: FastAPI
    client: AsyncClient


async def _reconcile_runtime_permissions(
    owner_url: SecretStr,
    runtime_url: SecretStr,
) -> None:
    runtime_user = make_url(runtime_url.get_secret_value()).username
    if runtime_user is None or re.fullmatch(r"[a-z_][a-z0-9_]*", runtime_user) is None:
        msg = "TEST_DATABASE_URL must contain a conservative runtime role name"
        raise ValueError(msg)
    quoted_user = f'"{runtime_user}"'
    engine = create_database_engine(DatabaseConfig(url=owner_url))
    statements = (
        f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {quoted_user}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM {quoted_user}",
        f"GRANT SELECT ON TABLE public.alembic_version TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.audit_entry FROM {quoted_user}",
        f"GRANT SELECT, INSERT ON TABLE public.audit_entry TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {quoted_user}",
    )
    try:
        async with engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


@pytest.fixture
def migrated_site_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the sole M3 head."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(_reconcile_runtime_permissions(test_database_owner_url, test_database_url))
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
async def site_harness(
    migrated_site_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_SiteHarness]:
    """Yield a full-session administrator against migrated PostgreSQL."""
    del migrated_site_database
    application = create_app(settings=_settings(test_database_url))
    runtime = application.state.database_runtime
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    await bootstrap.bootstrap(
        email=EMAIL,
        display_name="Site Owner",
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
        yield _SiteHarness(application=application, client=client)
    await runtime.dispose()


def _unsafe_headers(harness: _SiteHarness, **extra: str) -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": harness.client.cookies["__Host-admin_csrf"],
        **extra,
    }


async def test_profile_privacy_concurrency_csrf_and_safe_errors(
    site_harness: _SiteHarness,
) -> None:
    """Admin state remains private while explicit public fields are cacheable."""
    client = site_harness.client
    initial = await client.get("/api/v1/admin/profile")
    assert initial.status_code == 200
    assert initial.headers["etag"] == '"v1"'
    assert initial.headers["cache-control"] == "private, no-store"

    payload = {
        "full_name": "Fictional Public Name",
        "email": "private-contact@example.test",
        "contact_preference": "email",
        "public_fields": ["full_name"],
    }
    missing_precondition = await client.put(
        "/api/v1/admin/profile",
        headers=_unsafe_headers(site_harness),
        json=payload,
    )
    assert missing_precondition.status_code == 428
    assert missing_precondition.json()["error"]["code"] == "PRECONDITION_REQUIRED"

    missing_csrf = await client.put(
        "/api/v1/admin/profile",
        headers={"Origin": ORIGIN, "If-Match": '"v1"'},
        json=payload,
    )
    assert missing_csrf.status_code == 422
    assert missing_csrf.json()["error"]["code"] == "VALIDATION_FAILED"

    updated = await client.put(
        "/api/v1/admin/profile",
        headers=_unsafe_headers(site_harness, **{"If-Match": '"v1"'}),
        json=payload,
    )
    assert updated.status_code == 200
    assert updated.headers["etag"] == '"v2"'
    assert updated.json()["data"]["email"] == "private-contact@example.test"

    public = await client.get(
        "/api/v1/public/profile",
        headers={"Authorization": "Bearer ignored-public-credential"},
    )
    assert public.status_code == 200
    assert public.headers["cache-control"].startswith("public, max-age=60")
    assert public.json()["data"] == {
        "configured": True,
        "full_name": "Fictional Public Name",
    }
    assert "private-contact" not in public.text

    stale = await client.put(
        "/api/v1/admin/profile",
        headers=_unsafe_headers(site_harness, **{"If-Match": '"v1"'}),
        json=payload,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"

    mass_assignment = await client.put(
        "/api/v1/admin/profile",
        headers=_unsafe_headers(site_harness, **{"If-Match": '"v2"'}),
        json={**payload, "password": "must-not-cross-the-boundary"},
    )
    assert mass_assignment.status_code == 422
    assert "must-not-cross-the-boundary" not in mass_assignment.text


async def test_settings_reject_secrets_and_public_site_has_distinct_shape(
    site_harness: _SiteHarness,
) -> None:
    """Settings accept public identifiers but reject secret-capable extension fields."""
    client = site_harness.client
    initial = await client.get("/api/v1/admin/settings")
    etag = initial.headers["etag"]
    payload = {
        "website_name": "Fictional Studio",
        "default_title": "Independent work",
        "default_locale": "fr-FR",
        "timezone": "Europe/Paris",
        "theme_policy": "system",
        "analytics_provider": "plausible",
        "analytics_public_id": "fictional.example.test",
    }
    rejected = await client.put(
        "/api/v1/admin/settings",
        headers=_unsafe_headers(site_harness, **{"If-Match": etag}),
        json={**payload, "analytics_secret": "private-secret-value"},
    )
    assert rejected.status_code == 422
    assert "private-secret-value" not in rejected.text

    updated = await client.put(
        "/api/v1/admin/settings",
        headers=_unsafe_headers(site_harness, **{"If-Match": etag}),
        json=payload,
    )
    assert updated.status_code == 200
    assert updated.headers["cache-control"] == "private, no-store"

    public = await client.get("/api/v1/public/site")
    data = public.json()["data"]
    assert public.status_code == 200
    assert data["configured"] is True
    assert data["website_name"] == "Fictional Studio"
    assert data["timezone"] == "Europe/Paris"
    assert "id" not in data
    assert "version" not in data
    assert "created_at" not in data
    assert "logo_media_id" not in data


async def test_navigation_and_footer_replace_are_atomic_idempotent_and_public_safe(
    site_harness: _SiteHarness,
) -> None:
    """Complete tree writes replay once and expose only visible public destinations."""
    client = site_harness.client
    navigation = await client.get("/api/v1/admin/navigation")
    navigation_payload = {
        "items": [
            {
                "id": str(ROOT_ID),
                "label": "About",
                "link_kind": "internal",
                "href": "/about",
                "target": "same_window",
                "visible": True,
                "position": 0,
            },
            {
                "id": str(HIDDEN_ID),
                "label": "Hidden",
                "link_kind": "external",
                "href": "https://example.test/hidden",
                "target": "new_window",
                "visible": False,
                "position": 1,
            },
        ]
    }
    headers = _unsafe_headers(
        site_harness,
        **{
            "If-Match": navigation.headers["etag"],
            "Idempotency-Key": "navigation-replace-0001",
        },
    )
    replaced = await client.put(
        "/api/v1/admin/navigation",
        headers=headers,
        json=navigation_payload,
    )
    assert replaced.status_code == 200
    assert replaced.headers["etag"] == '"v2"'

    replay = await client.put(
        "/api/v1/admin/navigation",
        headers=headers,
        json=navigation_payload,
    )
    assert replay.status_code == 200
    assert replay.headers["etag"] == '"v2"'

    conflict = await client.put(
        "/api/v1/admin/navigation",
        headers=headers,
        json={"items": [navigation_payload["items"][0]]},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    public_navigation = await client.get("/api/v1/public/navigation")
    public_items = public_navigation.json()["data"]["items"]
    assert [item["label"] for item in public_items] == ["About"]
    assert "visible" not in public_navigation.text
    assert "version" not in public_navigation.text

    footer = await client.get("/api/v1/admin/footer")
    footer_payload = {
        "copyright_text": "Fictional Studio",
        "columns": [
            {
                "id": str(COLUMN_ID),
                "title": "Explore",
                "visible": True,
                "position": 0,
                "items": [
                    {
                        "id": str(FOOTER_ITEM_ID),
                        "label": "About",
                        "link_kind": "internal",
                        "item_kind": "legal",
                        "href": "/about",
                        "target": "same_window",
                        "visible": True,
                        "position": 0,
                    }
                ],
            }
        ],
    }
    footer_response = await client.put(
        "/api/v1/admin/footer",
        headers=_unsafe_headers(
            site_harness,
            **{
                "If-Match": footer.headers["etag"],
                "Idempotency-Key": "footer-replace-000001",
            },
        ),
        json=footer_payload,
    )
    assert footer_response.status_code == 200

    public_site = await client.get("/api/v1/public/site")
    public_footer = public_site.json()["data"]["footer"]
    assert public_footer["copyright_text"] == "Fictional Studio"
    assert public_footer["columns"][0]["items"][0]["item_kind"] == "legal"
    assert "id" not in str(public_footer)
    assert "version" not in str(public_footer)

    runtime = site_harness.application.state.database_runtime
    async with runtime.session_factory() as session:
        audits = list((await session.execute(select(AuditEntryRecord))).scalars())
    site_audits = [entry for entry in audits if entry.event_type.endswith(".updated")]
    assert {entry.event_type for entry in site_audits} >= {
        "navigation.updated",
        "footer.updated",
    }
    assert all(set(entry.metadata_json) == {"version"} for entry in site_audits)
    assert "https://example.test/hidden" not in str([entry.metadata_json for entry in site_audits])


def test_openapi_declares_distinct_public_admin_contracts_and_unsafe_headers() -> None:
    """The generated contract encodes no-auth public reads and protected mutations."""
    schema = create_app(settings=Settings(environment=Environment.TEST)).openapi()
    paths = schema["paths"]
    for path in (
        "/api/v1/public/profile",
        "/api/v1/public/site",
        "/api/v1/public/navigation",
    ):
        assert "security" not in paths[path]["get"]

    operation = paths["/api/v1/admin/navigation"]["put"]
    parameters = {(item["name"], item["in"]): item for item in operation["parameters"]}
    assert operation["security"] == [{"AdminSessionCookie": []}]
    assert parameters[("Origin", "header")]["required"] is True
    assert parameters[("X-CSRF-Token", "header")]["required"] is True
    assert parameters[("If-Match", "header")]["required"] is False
    assert parameters[("Idempotency-Key", "header")]["required"] is True

    components = schema["components"]["schemas"]
    public_profile = components["PublicProfileData"]["properties"]
    admin_profile = components["ProfileData"]["properties"]
    assert "public_fields" not in public_profile
    assert "created_at" not in public_profile
    assert "public_fields" in admin_profile
    assert "created_at" in admin_profile


async def test_demo_seed_without_administrator_converges_and_discloses_no_private_values(
    migrated_site_database: None,
    test_database_url: SecretStr,
) -> None:
    """The explicit fictional seed is transactional, idempotent, and auth-independent."""
    del migrated_site_database
    runtime = create_database_engine(DatabaseConfig(url=test_database_url))
    session_factory = create_session_factory(runtime)
    try:
        first = await seed_demo(session_factory)
        second = await seed_demo(session_factory)
        async with session_factory() as session:
            administrator_count = await session.scalar(text("SELECT count(*) FROM administrator"))
            profile = (
                await session.execute(
                    text(
                        "SELECT email, location, availability, profile_image_id, version "
                        "FROM profile"
                    )
                )
            ).one()
            settings = (
                await session.execute(
                    text(
                        "SELECT contact_email, contact_phone, analytics_public_id, "
                        "logo_media_id, favicon_media_id, social_image_media_id, version "
                        "FROM website_settings"
                    )
                )
            ).one()
            demo_audits = await session.scalar(
                text("SELECT count(*) FROM audit_entry WHERE event_type = 'demo.seeded'")
            )
            skill_counts = (
                await session.execute(
                    text(
                        "SELECT count(*), count(*) FILTER (WHERE visible), "
                        "count(*) FILTER (WHERE featured AND visible) FROM skill"
                    )
                )
            ).one()
            category_slugs = tuple(
                (
                    await session.execute(
                        text("SELECT slug FROM skill_category ORDER BY position, id")
                    )
                ).scalars()
            )
    finally:
        await runtime.dispose()

    assert first.changed_aggregates == 5
    assert second.changed_aggregates == 0
    assert first.skill_categories == 2
    assert first.skills == 5
    assert administrator_count == 0
    assert tuple(profile) == (None, None, None, None, 2)
    assert tuple(settings) == (None, None, None, None, None, None, 2)
    assert demo_audits == 1
    assert tuple(skill_counts) == (5, 4, 2)
    assert category_slugs == ("engineering", "product-craft")


async def test_demo_seed_rolls_back_all_aggregates_on_failure(
    migrated_site_database: None,
    test_database_url: SecretStr,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A late aggregate failure leaves earlier profile/settings changes uncommitted."""
    del migrated_site_database

    async def fail_footer_replace(*args: object, **kwargs: object) -> None:
        del args, kwargs
        msg = "synthetic footer failure"
        raise RuntimeError(msg)

    monkeypatch.setattr(FooterRepository, "replace", fail_footer_replace)
    runtime = create_database_engine(DatabaseConfig(url=test_database_url))
    session_factory = create_session_factory(runtime)
    try:
        with pytest.raises(RuntimeError, match="synthetic footer failure"):
            await seed_demo(session_factory)
        async with session_factory() as session:
            profile_name = await session.scalar(text("SELECT full_name FROM profile"))
            settings_name = await session.scalar(text("SELECT website_name FROM website_settings"))
            navigation_count = await session.scalar(text("SELECT count(*) FROM navigation_item"))
            audit_count = await session.scalar(
                text("SELECT count(*) FROM audit_entry WHERE event_type = 'demo.seeded'")
            )
            skill_count = await session.scalar(text("SELECT count(*) FROM skill"))
    finally:
        await runtime.dispose()

    assert profile_name is None
    assert settings_name is None
    assert navigation_count == 0
    assert audit_count == 0
    assert skill_count == 0


def test_demo_seed_refuses_production_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Production refusal happens before parsing or opening a database URL."""
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)

    assert seed_demo_main([]) == EXIT_PRODUCTION_REFUSED
    output = capsys.readouterr()
    assert output.out == ""
    assert "production" in output.err
