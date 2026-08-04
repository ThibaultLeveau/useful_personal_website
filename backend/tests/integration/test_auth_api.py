"""PostgreSQL-backed administrator authentication contract tests."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient, Headers, Response
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.commands.bootstrap_admin import EXIT_ALREADY_BOOTSTRAPPED, EXIT_INVALID_INPUT, main
from app.config import Environment, Settings
from app.infrastructure.database.audit import AuditEntryRecord
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.identity import AdministratorRecord, AdminSessionRecord
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.infrastructure.database.session import create_database_engine
from app.infrastructure.rate_limit import RateLimitRepository
from app.infrastructure.rate_limit.persistence import RateLimitBucketRecord
from app.main import create_app
from app.modules.identity.security import PasswordManager
from app.modules.identity.service import (
    BootstrapAlreadyCompletedError,
    BootstrapService,
    IdentityService,
    IdentityServiceConfiguration,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI

    from app.modules.identity.ports import RateLimitDecision

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]

ORIGIN = "https://testserver"
EMAIL = "owner@example.test"
INITIAL_PASSWORD = "M1!Initial-9Frost"
REPLACEMENT_PASSWORD = "M1!Replacement-7River"


@dataclass(slots=True)
class _MutableClock:
    now: datetime

    def __call__(self) -> datetime:
        return self.now


@dataclass(frozen=True, slots=True)
class _AuthHarness:
    application: FastAPI
    client: AsyncClient


async def _reconcile_runtime_permissions(
    owner_url: SecretStr,
    runtime_url: SecretStr,
) -> None:
    """Apply the test stack's post-migration least-privilege grant contract."""
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


async def _assert_runtime_privilege_boundary(harness: _AuthHarness) -> None:
    """Prove the app connection is non-owner and cannot mutate audit/schema controls."""
    runtime = harness.application.state.database_runtime
    expected_runtime_user = make_url(
        harness.application.state.settings.database_url.get_secret_value()
    ).username
    async with runtime.engine.connect() as connection:
        assert await connection.scalar(text("SELECT current_user")) == expected_runtime_user
    for statement in (
        "UPDATE audit_entry SET outcome = 'failure'",
        "DELETE FROM audit_entry",
        "TRUNCATE audit_entry",
        "ALTER TABLE audit_entry DISABLE TRIGGER audit_entry_append_only",
        "DROP TRIGGER audit_entry_append_only ON audit_entry",
        "CREATE TABLE runtime_ddl_probe (id integer)",
        "CREATE TEMP TABLE runtime_temp_probe (id integer)",
        "UPDATE alembic_version SET version_num = 'runtime_write'",
    ):
        with pytest.raises(DBAPIError):
            async with runtime.engine.begin() as connection:
                await connection.execute(text(statement))


@pytest.fixture
def migrated_auth_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Reset the isolated database and apply the exact M1 head."""
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
async def auth_harness(
    migrated_auth_database: None,
    test_database_url: SecretStr,
) -> AsyncIterator[_AuthHarness]:
    """Yield an app with one explicitly bootstrapped initial administrator."""
    del migrated_auth_database
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
        yield _AuthHarness(application=application, client=client)
    await runtime.dispose()


async def _login(client: AsyncClient, *, password: str = INITIAL_PASSWORD) -> Response:
    return await client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": EMAIL, "password": password},
    )


async def test_contact_inbox_and_scoped_token_lifecycles(  # noqa: PLR0915
    auth_harness: _AuthHarness,
) -> None:
    """Exercise M10/M11 persistence, admin lifecycle, and bearer boundaries end to end."""
    client = auth_harness.client
    issued_at = int(datetime.now(UTC).timestamp()) - 3
    proof_material = f"contact-proof:v1:contact_page:{issued_at}".encode()
    proof = hmac.new(b"p" * 32, proof_material, hashlib.sha256).hexdigest()
    contact_payload = {
        "name": "Release Reviewer",
        "email": "reviewer@example.test",
        "subject": "Release evidence",
        "message": "Please verify the contact and token lifecycle.",
        "consent": True,
        "policy_version": "development-policy-v1",
        "source": "contact_page",
        "issued_at": issued_at,
        "proof": proof,
        "website": "",
    }
    idempotency_headers = {"Idempotency-Key": "m13-contact-proof-0001"}

    context = await client.get("/api/v1/public/contacts/form-context")
    assert context.status_code == 200
    assert context.headers["Cache-Control"] == "private, no-store"
    assert context.json()["data"]["policy_version"] == "development-policy-v1"

    accepted = await client.post(
        "/api/v1/public/contacts", headers=idempotency_headers, json=contact_payload
    )
    assert accepted.status_code == 202
    assert accepted.json()["data"] == {"status": "accepted"}
    replay = await client.post(
        "/api/v1/public/contacts", headers=idempotency_headers, json=contact_payload
    )
    assert replay.status_code == 202
    for key, value in (
        ("email", "not-an-email"),
        ("consent", False),
        ("policy_version", "retired-policy"),
        ("website", "bot-filled"),
    ):
        rejected = await client.post(
            "/api/v1/public/contacts",
            headers={"Idempotency-Key": f"m13-invalid-{key}-0001"},
            json={**contact_payload, key: value},
        )
        assert rejected.status_code == 422

    login = await _login(client)
    assert login.status_code == 200
    csrf = client.cookies["__Host-admin_csrf"]
    changed = await client.post(
        "/api/v1/auth/password/change",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        json={"current_password": INITIAL_PASSWORD, "new_password": REPLACEMENT_PASSWORD},
    )
    assert changed.status_code == 200
    csrf = client.cookies["__Host-admin_csrf"]
    unsafe = {"Origin": ORIGIN, "X-CSRF-Token": csrf}

    contacts = await client.get("/api/v1/admin/contacts?state=unread&sort=oldest")
    assert contacts.status_code == 200
    assert contacts.json()["meta"]["pagination"]["total_items"] == 1
    contact_id = contacts.json()["data"][0]["id"]
    detail = await client.get(f"/api/v1/admin/contacts/{contact_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["email"] == "reviewer@example.test"

    missing_precondition = await client.patch(
        f"/api/v1/admin/contacts/{contact_id}/state",
        headers=unsafe,
        json={"state": "read"},
    )
    assert missing_precondition.status_code == 428
    read = await client.patch(
        f"/api/v1/admin/contacts/{contact_id}/state",
        headers={**unsafe, "If-Match": detail.headers["ETag"]},
        json={"state": "read"},
    )
    assert read.status_code == 200
    assert read.json()["data"]["state"] == "read"
    archived = await client.patch(
        f"/api/v1/admin/contacts/{contact_id}/state",
        headers={**unsafe, "If-Match": read.headers["ETag"]},
        json={"state": "archived"},
    )
    assert archived.status_code == 200
    stale_transition = await client.patch(
        f"/api/v1/admin/contacts/{contact_id}/state",
        headers={**unsafe, "If-Match": read.headers["ETag"]},
        json={"state": "archived"},
    )
    assert stale_transition.status_code == 409

    events = await client.get("/api/v1/admin/audit/events")
    assert events.status_code == 200
    assert "contact.submitted" in events.json()["data"]["events"]
    audits = await client.get("/api/v1/admin/audit?event_type=contact.submitted&page_size=5")
    assert audits.status_code == 200
    assert audits.json()["data"][0]["event_type"] == "contact.submitted"
    audit_id = audits.json()["data"][0]["id"]
    audit_detail = await client.get(f"/api/v1/admin/audit/{audit_id}")
    assert audit_detail.status_code == 200
    assert audit_detail.json()["data"]["metadata"]["source"] == "contact_page"
    assert (await client.get("/api/v1/admin/audit?page=1&page=2")).status_code == 422

    scopes = await client.get("/api/v1/admin/api-tokens/scopes")
    assert scopes.status_code == 200
    assert "contacts:read" in scopes.json()["data"]["scopes"]
    created = await client.post(
        "/api/v1/admin/api-tokens",
        headers=unsafe,
        json={
            "name": "Release integration",
            "scopes": ["contacts:read"],
            "expires_at": None,
            "confirm_no_expiry": True,
        },
    )
    assert created.status_code == 201
    token_data = created.json()["data"]
    plaintext = token_data["plaintext_token"]
    token_id = token_data["token"]["id"]
    assert plaintext not in str(token_data["token"])
    duplicate = await client.post(
        "/api/v1/admin/api-tokens",
        headers=unsafe,
        json={
            "name": "Release integration",
            "scopes": ["contacts:read"],
            "expires_at": None,
            "confirm_no_expiry": True,
        },
    )
    assert duplicate.status_code == 422

    listed = await client.get("/api/v1/admin/api-tokens?status=active")
    assert listed.status_code == 200
    assert listed.json()["meta"]["pagination"]["total_items"] == 1
    token_detail = await client.get(f"/api/v1/admin/api-tokens/{token_id}")
    assert token_detail.status_code == 200
    assert "plaintext_token" not in token_detail.text

    bearer = {"Authorization": f"Bearer {plaintext}"}
    integration_list = await client.get("/api/v1/integrations/contacts", headers=bearer)
    assert integration_list.status_code == 200
    integration_detail = await client.get(
        f"/api/v1/integrations/contacts/{contact_id}", headers=bearer
    )
    assert integration_detail.status_code == 200
    assert (await client.get("/api/v1/integrations/projects", headers=bearer)).status_code == 401
    assert (await client.get("/api/v1/integrations/contacts")).status_code == 401
    assert (
        await client.get(
            "/api/v1/integrations/contacts", headers={"Authorization": "Bearer invalid"}
        )
    ).status_code == 401

    rotated = await client.post(
        f"/api/v1/admin/api-tokens/{token_id}/rotate",
        headers={**unsafe, "If-Match": token_detail.headers["ETag"]},
        json={"expires_at": None, "confirm_no_expiry": True},
    )
    assert rotated.status_code == 201
    replacement = rotated.json()["data"]
    replacement_id = replacement["token"]["id"]
    replacement_plaintext = replacement["plaintext_token"]
    assert (await client.get("/api/v1/integrations/contacts", headers=bearer)).status_code == 401

    revoked = await client.post(
        f"/api/v1/admin/api-tokens/{replacement_id}/revoke",
        headers={**unsafe, "If-Match": rotated.headers["ETag"]},
    )
    assert revoked.status_code == 200
    assert revoked.json()["data"]["status"] == "revoked"
    assert (
        await client.get(
            "/api/v1/integrations/contacts",
            headers={"Authorization": f"Bearer {replacement_plaintext}"},
        )
    ).status_code == 401

    deleted = await client.delete(
        f"/api/v1/admin/contacts/{contact_id}",
        headers={**unsafe, "If-Match": archived.headers["ETag"]},
    )
    assert deleted.status_code == 200
    assert (await client.get(f"/api/v1/admin/contacts/{contact_id}")).status_code == 404


def test_bootstrap_cli_reads_stdin_without_disclosing_password_and_refuses_replay(
    migrated_auth_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> None:
    """The operator path is explicit, noninteractive, secret-safe, and one-time."""
    del migrated_auth_database
    monkeypatch.setenv("APP_DATABASE_URL", test_database_url.get_secret_value())
    monkeypatch.delenv("APP_BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr("sys.stdin", StringIO(f"{INITIAL_PASSWORD}\n"))
    assert main(["--email", EMAIL, "--display-name", "Site Owner", "--password-stdin"]) == 0
    first = capsys.readouterr()
    assert "Administrator bootstrapped:" in first.out
    assert INITIAL_PASSWORD not in first.out + first.err

    monkeypatch.setattr("sys.stdin", StringIO("M1!Replay-8Canyon\n"))
    assert (
        main(["--email", "replay@example.test", "--display-name", "Replay", "--password-stdin"])
        == EXIT_ALREADY_BOOTSTRAPPED
    )
    replay = capsys.readouterr()
    assert "Bootstrap refused" in replay.err
    assert "M1!Replay-8Canyon" not in replay.out + replay.err

    monkeypatch.delenv("APP_DATABASE_URL")
    assert main(["--email", EMAIL, "--display-name", "Owner"]) == EXIT_INVALID_INPUT
    assert "required" in capsys.readouterr().err
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())


def test_openapi_auth_transport_is_precise_and_generator_safe() -> None:
    """Generated clients see one cookie scheme plus explicit unsafe headers."""
    schema = create_app(settings=Settings(environment=Environment.TEST)).openapi()
    paths = schema["paths"]
    expected = {
        "/api/v1/auth/login": ("post", "auth_login"),
        "/api/v1/auth/session": ("get", "auth_session_get"),
        "/api/v1/auth/session/refresh": ("post", "auth_session_refresh"),
        "/api/v1/auth/password/change": ("post", "auth_password_change"),
        "/api/v1/auth/logout": ("post", "auth_logout"),
    }
    assert "/api/v1/auth/csrf" not in paths
    for path, (method, operation_id) in expected.items():
        assert paths[path][method]["operationId"] == operation_id

    session_get = paths["/api/v1/auth/session"]["get"]
    assert set(session_get["responses"]) == {"200", "401", "503"}
    assert "429" not in session_get["responses"]
    login = paths["/api/v1/auth/login"]["post"]
    assert set(login["responses"]) == {"200", "401", "403", "422", "429", "503"}
    expected_unsafe_responses = {"200", "401", "403", "422", "503"}
    error_envelope_ref = "#/components/schemas/ErrorEnvelope"
    assert (
        login["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        == error_envelope_ref
    )
    for path in (
        "/api/v1/auth/session/refresh",
        "/api/v1/auth/password/change",
        "/api/v1/auth/logout",
    ):
        operation = paths[path]["post"]
        assert set(operation["responses"]) == expected_unsafe_responses
        assert (
            operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
            == error_envelope_ref
        )
        assert operation["security"] == [{"AdminSessionCookie": []}]
        parameters = {(item["name"], item["in"]): item for item in operation["parameters"]}
        assert parameters[("X-CSRF-Token", "header")]["required"] is True
        assert parameters[("Origin", "header")]["required"] is True


async def test_bootstrap_refuses_replay_even_when_existing_admin_is_inactive(
    auth_harness: _AuthHarness,
) -> None:
    """Deactivation never reopens the one-time takeover surface."""
    runtime = auth_harness.application.state.database_runtime
    async with runtime.engine.begin() as connection:
        await connection.execute(text("UPDATE administrator SET is_active = false"))
    bootstrap = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
    with pytest.raises(BootstrapAlreadyCompletedError):
        await bootstrap.bootstrap(
            email="attacker@example.test",
            display_name="Attacker",
            password="M1!Attacker-4Storm",
        )

    async with runtime.engine.connect() as connection:
        count = await connection.scalar(text("SELECT count(*) FROM administrator"))
    assert count == 1


async def test_login_password_rotation_logout_and_append_only_audit(
    auth_harness: _AuthHarness,
) -> None:
    """Exercise the full initial-password lifecycle and persistence invariants."""
    client = auth_harness.client
    runtime = auth_harness.application.state.database_runtime
    login = await _login(client)
    assert login.status_code == 200
    assert login.json()["data"]["must_change_password"] is True
    cookies = login.headers.get_list("set-cookie")
    assert any(
        "__Host-admin_session=" in item
        and "HttpOnly" in item
        and "Secure" in item
        and "SameSite=lax" in item
        and "Domain=" not in item
        for item in cookies
    )
    assert any("__Host-admin_csrf=" in item and "HttpOnly" not in item for item in cookies)
    old_secret = client.cookies["__Host-admin_session"]
    csrf = client.cookies["__Host-admin_csrf"]

    session_get = await client.get("/api/v1/auth/session")
    assert session_get.status_code == 200
    assert "set-cookie" not in session_get.headers
    assert session_get.headers["Cache-Control"] == "private, no-store"

    missing_csrf = await client.post(
        "/api/v1/auth/password/change",
        headers={"Origin": ORIGIN},
        json={"current_password": INITIAL_PASSWORD, "new_password": REPLACEMENT_PASSWORD},
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["error"]["code"] == "CSRF_INVALID"
    assert missing_csrf.headers["Cache-Control"] == "private, no-store"

    changed = await client.post(
        "/api/v1/auth/password/change",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        json={"current_password": INITIAL_PASSWORD, "new_password": REPLACEMENT_PASSWORD},
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["must_change_password"] is False
    assert client.cookies["__Host-admin_session"] != old_secret

    async with runtime.session_factory() as session:
        administrator = (await session.execute(select(AdministratorRecord))).scalar_one()
        sessions = list((await session.execute(select(AdminSessionRecord))).scalars())
        audits = list((await session.execute(select(AuditEntryRecord))).scalars())
    assert administrator.password_hash.startswith("$argon2id$")
    assert INITIAL_PASSWORD not in administrator.password_hash
    assert administrator.must_change_password is False
    assert len(sessions) == 2
    assert len({entry.token_digest for entry in sessions}) == 2
    assert all(len(entry.token_digest) == 32 for entry in sessions)
    assert any(entry.revocation_reason == "password_changed" for entry in sessions)
    assert all(entry.metadata_json.keys() <= {"source"} for entry in audits)
    assert all(EMAIL not in str(entry.metadata_json) for entry in audits)

    client.cookies.set("__Host-admin_session", old_secret)
    assert (await client.get("/api/v1/auth/session")).status_code == 401
    client.cookies.clear()
    login_again = await _login(client, password=REPLACEMENT_PASSWORD)
    assert login_again.status_code == 200
    csrf = client.cookies["__Host-admin_csrf"]
    logged_out = await client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
    )
    assert logged_out.status_code == 200
    assert (await client.get("/api/v1/auth/session")).status_code == 401

    await _assert_runtime_privilege_boundary(auth_harness)


async def test_admin_health_denies_unready_sessions_and_exposes_only_safe_aggregates(
    auth_harness: _AuthHarness,
) -> None:
    """Admin health requires full access, is private, and fails closed after expiry."""
    client = auth_harness.client
    unauthenticated = await client.get("/api/v1/admin/health")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert unauthenticated.headers["Cache-Control"] == "private, no-store"

    assert (await _login(client)).status_code == 200
    forced_change = await client.get("/api/v1/admin/health")
    assert forced_change.status_code == 403
    assert forced_change.json()["error"]["code"] == "PASSWORD_CHANGE_REQUIRED"

    changed = await client.post(
        "/api/v1/auth/password/change",
        headers={
            "Origin": ORIGIN,
            "X-CSRF-Token": client.cookies["__Host-admin_csrf"],
        },
        json={"current_password": INITIAL_PASSWORD, "new_password": REPLACEMENT_PASSWORD},
    )
    assert changed.status_code == 200

    healthy = await client.get("/api/v1/admin/health")
    assert healthy.status_code == 200
    assert healthy.headers["Cache-Control"] == "private, no-store"
    assert healthy.headers["Pragma"] == "no-cache"
    assert healthy.json()["data"] | {"checked_at": "ignored"} == {
        "status": "operational",
        "application_status": "operational",
        "database_status": "operational",
        "migration_status": "current",
        "build_version": "0.0.0",
        "build_commit": "unknown",
        "checked_at": "ignored",
    }
    serialized = healthy.text.casefold()
    for forbidden in (
        "postgresql",
        "127.0.0.1",
        "database_url",
        "select ",
        "password",
        "asyncpg",
        "traceback",
    ):
        assert forbidden not in serialized

    runtime = auth_harness.application.state.database_runtime
    async with runtime.engine.begin() as connection:
        await connection.execute(
            text(
                "UPDATE admin_session "
                "SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 hours', "
                "last_seen_at = CURRENT_TIMESTAMP - INTERVAL '1 hour', "
                "idle_expires_at = CURRENT_TIMESTAMP - INTERVAL '1 minute' "
                "WHERE revoked_at IS NULL"
            )
        )
    expired = await client.get("/api/v1/admin/health")
    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


async def test_origin_csrf_mass_assignment_and_wrong_current_password_fail_closed(
    auth_harness: _AuthHarness,
) -> None:
    """Adversarial transport inputs fail without mutating identity state."""
    client = auth_harness.client
    missing_origin = await client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": INITIAL_PASSWORD},
    )
    assert missing_origin.status_code == 403
    assert missing_origin.json()["error"]["code"] == "ORIGIN_INVALID"
    untrusted_origin = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example"},
        json={"email": EMAIL, "password": INITIAL_PASSWORD},
    )
    assert untrusted_origin.status_code == 403
    extra_field = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": EMAIL, "password": INITIAL_PASSWORD, "is_active": True},
    )
    assert extra_field.status_code == 422
    assert extra_field.json()["error"]["code"] == "VALIDATION_FAILED"

    assert (await _login(client)).status_code == 200
    csrf = client.cookies["__Host-admin_csrf"]
    forged_csrf = await client.post(
        "/api/v1/auth/session/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": "forged"},
    )
    assert forged_csrf.status_code == 403
    assert forged_csrf.json()["error"]["code"] == "CSRF_INVALID"
    wrong_origin = await client.post(
        "/api/v1/auth/session/refresh",
        headers={"Origin": "https://evil.example", "X-CSRF-Token": csrf},
    )
    assert wrong_origin.status_code == 403

    runtime = auth_harness.application.state.database_runtime
    async with runtime.session_factory() as session:
        hash_before = await session.scalar(select(AdministratorRecord.password_hash))
        session_count_before = await session.scalar(
            select(text("count(*)")).select_from(AdminSessionRecord)
        )
    wrong_current = await client.post(
        "/api/v1/auth/password/change",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        json={"current_password": "wrong credential", "new_password": REPLACEMENT_PASSWORD},
    )
    assert wrong_current.status_code == 401
    async with runtime.session_factory() as session:
        assert await session.scalar(select(AdministratorRecord.password_hash)) == hash_before
        assert (
            await session.scalar(select(text("count(*)")).select_from(AdminSessionRecord))
            == session_count_before
        )
        failed_change_count = await session.scalar(
            select(text("count(*)"))
            .select_from(AuditEntryRecord)
            .where(AuditEntryRecord.event_type == "admin.password_change_failed")
        )
    assert failed_change_count == 1


async def test_non_enumerating_failures_rate_limit_and_malformed_cookie(
    auth_harness: _AuthHarness,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Known/unknown failures match, malformed cookies fail closed, and attempt five blocks."""
    client = auth_harness.client
    known = await _login(client, password="wrong credential")
    unknown = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "unknown@example.test", "password": "wrong credential"},
    )
    assert known.status_code == unknown.status_code == 401
    assert known.json()["error"]["code"] == unknown.json()["error"]["code"]
    assert known.json()["error"]["message"] == unknown.json()["error"]["message"]
    injection = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "' OR 1=1 --", "password": "wrong credential"},
    )
    assert injection.status_code == 401
    assert injection.json()["error"]["code"] == "AUTHENTICATION_FAILED"

    client.cookies.set("__Host-admin_session", "x" * 4_096)
    malformed = await client.get("/api/v1/auth/session")
    assert malformed.status_code == 401
    assert malformed.headers["Cache-Control"] == "private, no-store"
    client.cookies.clear()
    raw_non_ascii = await client.get(
        "/api/v1/auth/session",
        headers=Headers({"cookie": "__Host-admin_session=ÿ"}, encoding="latin-1"),
    )
    assert raw_non_ascii.status_code == 401
    assert raw_non_ascii.headers["Cache-Control"] == "private, no-store"

    responses = [await _login(client, password="wrong credential") for _ in range(4)]
    assert [response.status_code for response in responses[:3]] == [401, 401, 401]
    blocked = responses[3]
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"

    runtime = auth_harness.application.state.database_runtime
    boundary_subject = b"b" * 32
    before_boundary = datetime(2026, 8, 2, 14, 59, 50, tzinfo=UTC)
    async with runtime.session_factory.begin() as session:
        repository = RateLimitRepository(session)
        decisions = [
            await repository.record_login_failure(boundary_subject, before_boundary)
            for _ in range(5)
        ]
    assert decisions[-1].retry_after_seconds == 60
    async with runtime.session_factory.begin() as session:
        repository = RateLimitRepository(session)
        carried = await repository.check_login(
            boundary_subject,
            datetime(2026, 8, 2, 15, 0, 5, tzinfo=UTC),
        )
    assert carried.retry_after_seconds == 45
    async with runtime.session_factory.begin() as session:
        repository = RateLimitRepository(session)
        progressive = [
            await repository.record_login_failure(
                boundary_subject,
                before_boundary + timedelta(seconds=index),
            )
            for index in range(1, 7)
        ]
    assert progressive[0].retry_after_seconds == 120
    assert progressive[-1].retry_after_seconds == 3_600
    assert EMAIL not in caplog.text
    assert "wrong credential" not in caplog.text
    async with runtime.engine.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM administrator")) == 1


async def test_concurrent_same_subject_rate_failures_are_atomic(
    auth_harness: _AuthHarness,
) -> None:
    """Independent runtime transactions cannot lose or undercount a login burst."""
    runtime = auth_harness.application.state.database_runtime
    subject = b"c" * 32
    now = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
    attempts = 12
    barrier = asyncio.Barrier(attempts)

    async def record_one() -> RateLimitDecision:
        async with runtime.session_factory.begin() as session:
            await barrier.wait()
            return await RateLimitRepository(session).record_login_failure(subject, now)

    decisions = await asyncio.gather(*(record_one() for _ in range(attempts)))

    assert sorted(decision.retry_after_seconds for decision in decisions) == [
        0,
        0,
        0,
        0,
        60,
        120,
        240,
        480,
        960,
        1_920,
        3_600,
        3_600,
    ]
    async with runtime.session_factory() as session:
        bucket = (
            await session.execute(
                select(RateLimitBucketRecord).where(RateLimitBucketRecord.subject_digest == subject)
            )
        ).scalar_one()
    assert bucket.count == attempts
    assert bucket.blocked_until == now + timedelta(seconds=3_600)


async def test_explicit_refresh_slides_idle_but_never_absolute_expiry(
    auth_harness: _AuthHarness,
) -> None:
    """POST activity extends idle expiry while the twelve-hour cap remains fixed."""
    runtime = auth_harness.application.state.database_runtime
    clock = _MutableClock(datetime(2026, 8, 2, 8, 0, tzinfo=UTC))
    service = IdentityService(
        SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory),
        IdentityServiceConfiguration(
            csrf_signing_key=b"c" * 32,
            privacy_hmac_key=b"p" * 32,
            password_manager=PasswordManager.create(),
            clock=clock,
        ),
    )
    auth_harness.application.state.identity_service = service
    client = auth_harness.client
    login = await _login(client)
    assert login.status_code == 200
    original = login.json()["data"]
    csrf = client.cookies["__Host-admin_csrf"]

    clock.now += timedelta(minutes=20)
    refreshed = await client.post(
        "/api/v1/auth/session/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
    )
    assert refreshed.status_code == 200
    refreshed_data = refreshed.json()["data"]
    assert refreshed_data["absolute_expires_at"] == original["absolute_expires_at"]
    assert refreshed_data["idle_expires_at"] > original["idle_expires_at"]
    session_cookie = next(
        item
        for item in refreshed.headers.get_list("set-cookie")
        if item.startswith("__Host-admin_session=")
    )
    assert "Max-Age=43200" not in session_cookie

    clock.now += timedelta(minutes=11)
    assert (await client.get("/api/v1/auth/session")).status_code == 200
    clock.now = datetime(2026, 8, 2, 20, 0, tzinfo=UTC)
    assert (await client.get("/api/v1/auth/session")).status_code == 401
