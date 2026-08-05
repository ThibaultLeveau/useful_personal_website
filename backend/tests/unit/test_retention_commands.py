"""Operator retention command safeguards and bounded execution."""

# ruff: noqa: D103, FBT001

from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self

import pytest
from pydantic import SecretStr

from app.commands import purge_audit, purge_contacts, reconcile_media

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


class _Runtime:
    def __init__(self, session: object = object()) -> None:
        self.session_factory = session
        self.disposed = False

    async def dispose(self) -> None:
        self.disposed = True


class _AuditSession:
    def __init__(self, *, apply: bool) -> None:
        self.values = [NOW, 7, 2, 0] if apply else [NOW, 7]
        self.added: list[object] = []

    async def scalar(self, _statement: object, _parameters: object = None) -> object:
        return self.values.pop(0)

    def add(self, value: object) -> None:
        self.added.append(value)


class _AuditUow:
    session: _AuditSession

    def __init__(self, session: _AuditSession) -> None:
        self.session = session
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


class _AuditSettings:
    audit_retention_database_url = SecretStr(
        "postgresql+asyncpg://audit_operator:synthetic@db/site"
    )
    database_url = SecretStr("postgresql+asyncpg://runtime:synthetic@db/site")
    audit_retention_days = 400


@pytest.mark.parametrize("apply", [False, True])
async def test_audit_retention_is_dry_run_first_and_bounded(
    apply: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _AuditSession(apply=apply)
    runtime = _Runtime(session)
    unit = _AuditUow(session)
    monkeypatch.setattr(purge_audit, "Settings", _AuditSettings)
    monkeypatch.setattr(purge_audit, "create_database_runtime", lambda _config: runtime)
    monkeypatch.setattr(purge_audit, "SqlAlchemyUnitOfWork", lambda _factory: unit)

    await purge_audit._run(  # noqa: SLF001 - operator contract is intentionally exercised.
        Namespace(
            apply=apply,
            confirm="delete-expired-audit-entries" if apply else "",
            operator_id="release-operator",
            retention_days=400,
            batch_size=2,
        )
    )

    output = capsys.readouterr().out
    assert f'"applied": {str(apply).lower()}' in output
    assert '"retention_days": 400' in output
    assert runtime.disposed
    assert unit.committed is apply
    assert len(session.added) == (1 if apply else 0)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"audit_retention_database_url": None}, "configuration is required"),
        (
            {
                "audit_retention_database_url": SecretStr(
                    "postgresql+asyncpg://same:synthetic@db/site"
                ),
                "database_url": SecretStr("postgresql+asyncpg://same:synthetic@db/site"),
            },
            "ordinary runtime credential",
        ),
        ({}, "bounded safe identifier"),
    ],
)
async def test_audit_retention_rejects_unsafe_operator_configuration(
    changes: dict[str, object],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {
        "audit_retention_database_url": _AuditSettings.audit_retention_database_url,
        "database_url": _AuditSettings.database_url,
        "audit_retention_days": 400,
        **changes,
    }
    settings_type = type("SettingsFixture", (), values)
    monkeypatch.setattr(purge_audit, "Settings", settings_type)
    operator_id = "unsafe operator" if not changes else "release-operator"
    with pytest.raises(RuntimeError, match=message):
        await purge_audit._run(  # noqa: SLF001
            Namespace(
                apply=False,
                confirm="",
                operator_id=operator_id,
                retention_days=400,
                batch_size=100,
            )
        )


async def test_audit_retention_requires_apply_confirmation_and_valid_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(purge_audit, "Settings", _AuditSettings)
    with pytest.raises(RuntimeError, match="requires --confirm"):
        await purge_audit._run(  # noqa: SLF001
            Namespace(
                apply=True,
                confirm="wrong",
                operator_id="release-operator",
                retention_days=400,
                batch_size=100,
            )
        )
    with pytest.raises(RuntimeError, match="between 30 and 3650"):
        await purge_audit._run(  # noqa: SLF001
            Namespace(
                apply=False,
                confirm="",
                operator_id="release-operator",
                retention_days=3,
                batch_size=100,
            )
        )


class _ContactSettings:
    database_url = SecretStr("postgresql+asyncpg://runtime:synthetic@db/site")
    privacy_hmac_key = SecretStr("p" * 32)
    contact_policy_version = "privacy-v1"
    contact_source = "contact_page"
    contact_minimum_completion_seconds = 2
    contact_proof_ttl_seconds = 3600
    contact_pseudonym_key_version = "key-v1"
    contact_retention_days = 365


async def test_contact_retention_clamps_batch_and_reports_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime = _Runtime()
    captured: dict[str, object] = {}

    class _Service:
        def __init__(self, *_args: object) -> None:
            pass

        async def purge(self, **values: object) -> tuple[datetime, int]:
            captured.update(values)
            return NOW, 4

    monkeypatch.setattr(purge_contacts, "Settings", _ContactSettings)
    monkeypatch.setattr(purge_contacts, "create_database_runtime", lambda _config: runtime)
    monkeypatch.setattr(purge_contacts, "ContactService", _Service)
    monkeypatch.setattr(
        purge_contacts, "SqlAlchemyContactUnitOfWorkFactory", lambda _factory: object()
    )

    await purge_contacts._run(  # noqa: SLF001
        Namespace(apply=True, retention_days=None, batch_size=5000)
    )

    assert captured == {"retention_days": 365, "batch_size": 1000, "apply": True}
    assert '"deleted_or_eligible": 4' in capsys.readouterr().out
    assert runtime.disposed


async def test_contact_retention_requires_database_and_privacy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_type = type(
        "MissingContactSettings",
        (),
        {"database_url": None, "privacy_hmac_key": None},
    )
    monkeypatch.setattr(purge_contacts, "Settings", settings_type)
    with pytest.raises(RuntimeError, match="configuration are required"):
        await purge_contacts._run(  # noqa: SLF001
            Namespace(apply=False, retention_days=365, batch_size=100)
        )


class _MediaSettings:
    database_url = SecretStr("postgresql+asyncpg://runtime:synthetic@db/site")


async def test_media_reconciliation_command_reports_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime = _Runtime()

    @dataclass(frozen=True)
    class _Result:
        mode: str = "dry_run"
        scanned_objects: int = 3
        orphan_objects: int = 1
        stale_quarantine_objects: int = 0
        missing_registered_objects: int = 0
        deleted_objects: int = 0

    class _Reconciler:
        def __init__(self, *_args: object) -> None:
            pass

        async def run(self, **values: object) -> _Result:
            assert values == {"apply": False, "confirmation": None}
            return _Result()

    monkeypatch.setattr(reconcile_media, "Settings", _MediaSettings)
    monkeypatch.setattr(reconcile_media, "build_media_storage", lambda _settings: object())
    monkeypatch.setattr(reconcile_media, "create_database_runtime", lambda _config: runtime)
    monkeypatch.setattr(
        reconcile_media, "SqlAlchemyMediaUnitOfWorkFactory", lambda _factory: object()
    )
    monkeypatch.setattr(reconcile_media, "MediaReconciler", _Reconciler)

    await reconcile_media._run(Namespace(apply=False, confirm=None))  # noqa: SLF001
    assert '"mode": "dry_run"' in capsys.readouterr().out
    assert runtime.disposed


@pytest.mark.parametrize(
    ("database_url", "storage", "message"),
    [
        (None, object(), "APP_DATABASE_URL is required"),
        (_MediaSettings.database_url, None, "media storage configuration is required"),
    ],
)
async def test_media_reconciliation_requires_explicit_dependencies(
    database_url: object,
    storage: object,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_type = type("MediaSettingsFixture", (), {"database_url": database_url})
    monkeypatch.setattr(reconcile_media, "Settings", settings_type)
    monkeypatch.setattr(reconcile_media, "build_media_storage", lambda _settings: storage)
    with pytest.raises(RuntimeError, match=message):
        await reconcile_media._run(Namespace(apply=False, confirm=None))  # noqa: SLF001
