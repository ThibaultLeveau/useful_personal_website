"""Deterministic identity-service state-machine and race-path tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID

import pytest

from app.modules.identity.ports import RateLimitDecision
from app.modules.identity.security import digest_session_secret
from app.modules.identity.service import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    BootstrapService,
    ChangePasswordCommand,
    IdentityService,
    IdentityServiceConfiguration,
    LoginCommand,
    PasswordPolicyError,
    RateLimitedError,
)

if TYPE_CHECKING:
    from types import TracebackType

    from app.modules.audit.domain import AuditEntry
    from app.modules.identity.domain import NewAdministrator, NewAdminSession
    from app.modules.identity.ports import IdentityUnitOfWorkFactory
    from app.modules.identity.security import PasswordManager


@dataclass(slots=True)
class _Administrator:
    id: UUID
    display_name: str
    password_hash: str
    must_change_password: bool
    password_changed_at: datetime | None
    updated_at: datetime
    version: int


@dataclass(slots=True)
class _Session:
    id: UUID
    administrator_id: UUID
    token_digest: bytes
    idle_expires_at: datetime
    absolute_expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None


class _PasswordManager:
    dummy_hash = "dummy"

    def __init__(self, *, rehash: bool = False) -> None:
        self.rehash = rehash

    @staticmethod
    def verify(password_hash: str | None, password: str) -> bool:
        return password_hash is not None and password == "correct-password"

    @staticmethod
    def hash(password: str) -> str:
        return f"hash:{password}"

    def needs_rehash(self, _password_hash: str) -> bool:
        return self.rehash


class _Identity:
    def __init__(self, administrator: _Administrator | None) -> None:
        self.administrator = administrator
        self.sessions: dict[bytes, _Session] = {}
        self.stale_on_lock = False
        self.stale_password_on_session_lock = False

    async def acquire_bootstrap_lock(self) -> None: ...

    async def administrator_count(self) -> int:
        return int(self.administrator is not None)

    async def administrator_by_email(
        self,
        _email_normalized: str,
        *,
        for_update: bool = False,
    ) -> _Administrator | None:
        del for_update
        return self.administrator

    async def administrator_by_id(
        self,
        _administrator_id: UUID,
        *,
        for_update: bool = False,
    ) -> _Administrator | None:
        return None if for_update and self.stale_on_lock else self.administrator

    def add_administrator(self, administrator: NewAdministrator) -> None:
        values = asdict(administrator)
        self.administrator = _Administrator(
            id=values["id"],
            display_name=values["display_name"],
            password_hash=values["password_hash"],
            must_change_password=values["must_change_password"],
            password_changed_at=values["password_changed_at"],
            updated_at=values["updated_at"],
            version=values["version"],
        )

    def add_session(self, admin_session: NewAdminSession) -> None:
        self.sessions[admin_session.token_digest] = _Session(
            id=admin_session.id,
            administrator_id=admin_session.administrator_id,
            token_digest=admin_session.token_digest,
            idle_expires_at=admin_session.idle_expires_at,
            absolute_expires_at=admin_session.absolute_expires_at,
            last_seen_at=admin_session.last_seen_at,
            revoked_at=admin_session.revoked_at,
            revocation_reason=admin_session.revocation_reason,
        )

    async def session_with_administrator(
        self,
        token_digest: bytes,
        *,
        for_update: bool = False,
    ) -> tuple[_Session, _Administrator] | None:
        session = self.sessions.get(token_digest)
        if session is None or self.administrator is None:
            return None
        if for_update and self.stale_password_on_session_lock:
            self.administrator.password_hash = "concurrently-changed-hash"
        return session, self.administrator

    async def revoke_other_sessions(
        self,
        *,
        administrator_id: UUID,
        current_session_id: UUID,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        for session in self.sessions.values():
            if session.administrator_id == administrator_id and session.id != current_session_id:
                session.revoked_at = revoked_at
                session.revocation_reason = reason


class _RateLimit:
    def __init__(self) -> None:
        self.checks: list[RateLimitDecision] = []
        self.failure = RateLimitDecision(retry_after_seconds=0)

    async def check_login(self, _subject: bytes, _now: datetime) -> RateLimitDecision:
        if self.checks:
            return self.checks.pop(0)
        return RateLimitDecision(retry_after_seconds=0)

    async def record_login_failure(self, _subject: bytes, _now: datetime) -> RateLimitDecision:
        return self.failure

    async def clear_login_failures(self, _subject: bytes) -> None: ...


class _Audit:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class _UnitOfWork:
    def __init__(self, factory: _Factory) -> None:
        self.identity = factory.identity
        self.rate_limit = factory.rate_limit
        self.audit = factory.audit

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


class _Factory:
    def __init__(self, administrator: _Administrator | None) -> None:
        self.identity = _Identity(administrator)
        self.rate_limit = _RateLimit()
        self.audit = _Audit()

    def __call__(self) -> _UnitOfWork:
        return _UnitOfWork(self)


def _administrator() -> _Administrator:
    return _Administrator(
        id=UUID("019fc34f-0000-7000-8000-000000000001"),
        display_name="Owner",
        password_hash="old-hash",
        must_change_password=True,
        password_changed_at=None,
        updated_at=datetime(2026, 8, 2, tzinfo=UTC),
        version=1,
    )


def _service(
    factory: _Factory,
    *,
    rehash: bool = False,
) -> IdentityService:
    return IdentityService(
        cast("IdentityUnitOfWorkFactory", factory),
        IdentityServiceConfiguration(
            csrf_signing_key=b"c" * 32,
            privacy_hmac_key=b"p" * 32,
            password_manager=cast("PasswordManager", _PasswordManager(rehash=rehash)),
            clock=lambda: datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
        ),
    )


def _login_command(candidate_password: str | None = None) -> LoginCommand:
    password = candidate_password or "correct-password"
    return LoginCommand(
        email="owner@example.test",
        password=password,
        client_ip="127.0.0.1",
        user_agent="test-browser",
        request_id="request-state-machine-0001",
    )


async def test_login_rehashes_and_creates_a_session() -> None:
    """Successful admission can upgrade a stale hash and persist a safe session."""
    factory = _Factory(_administrator())
    issue = await _service(factory, rehash=True).login(_login_command())

    assert issue.view.must_change_password is True
    assert factory.identity.administrator is not None
    assert factory.identity.administrator.password_hash == "hash:correct-password"
    assert digest_session_secret(issue.secret) in factory.identity.sessions
    assert factory.audit.entries[-1].event_type == "admin.login_succeeded"


async def test_login_race_paths_fail_closed_and_are_audited() -> None:
    """Rate and administrator changes between preflight and lock cannot issue sessions."""
    rate_factory = _Factory(_administrator())
    rate_factory.rate_limit.checks = [
        RateLimitDecision(0),
        RateLimitDecision(30),
    ]
    with pytest.raises(RateLimitedError):
        await _service(rate_factory).login(_login_command())
    assert rate_factory.audit.entries[-1].event_type == "admin.login_rate_limited"

    stale_factory = _Factory(_administrator())
    stale_factory.identity.stale_on_lock = True
    with pytest.raises(AuthenticationFailedError):
        await _service(stale_factory).login(_login_command())
    assert stale_factory.audit.entries[-1].event_type == "admin.login_failed"

    failed_factory = _Factory(None)
    failed_factory.rate_limit.failure = RateLimitDecision(60)
    with pytest.raises(RateLimitedError):
        await _service(failed_factory).login(_login_command("wrong"))


async def test_password_refresh_logout_and_expiry_state_machine() -> None:
    """Session mutation paths rotate, slide, revoke, and reject stale credentials."""
    factory = _Factory(_administrator())
    service = _service(factory)
    issue = await service.login(_login_command())
    csrf = service.csrf_token(issue.view.session_id)

    with pytest.raises(PasswordPolicyError, match="must differ"):
        await service.change_password(
            ChangePasswordCommand(
                secret=issue.secret,
                current_password="correct-password",
                new_password="correct-password",
                csrf_cookie=csrf,
                csrf_header=csrf,
                request_id="request-change-same-0001",
                client_ip="127.0.0.1",
                user_agent=None,
            )
        )

    rotated = await service.change_password(
        ChangePasswordCommand(
            secret=issue.secret,
            current_password="correct-password",
            new_password="replacement-password",
            csrf_cookie=csrf,
            csrf_header=csrf,
            request_id="request-change-0002",
            client_ip="127.0.0.1",
            user_agent=None,
        )
    )
    assert rotated.view.must_change_password is False
    rotated_csrf = service.csrf_token(rotated.view.session_id)
    refreshed = await service.refresh_session(
        secret=rotated.secret,
        csrf_cookie=rotated_csrf,
        csrf_header=rotated_csrf,
    )
    assert refreshed.session_id == rotated.view.session_id
    await service.logout(
        secret=rotated.secret,
        csrf_cookie=rotated_csrf,
        csrf_header=rotated_csrf,
        request_id="request-logout-0001",
    )
    with pytest.raises(AuthenticationRequiredError):
        await service.inspect_session(rotated.secret)


async def test_missing_and_concurrently_changed_sessions_fail_closed() -> None:
    """Every unsafe session operation rejects absence and password-change races."""
    factory = _Factory(_administrator())
    service = _service(factory)
    with pytest.raises(AuthenticationRequiredError):
        await service.logout(
            secret="missing",
            csrf_cookie=None,
            csrf_header=None,
            request_id="request-missing-logout",
        )
    with pytest.raises(AuthenticationRequiredError):
        await service.refresh_session(secret="missing", csrf_cookie=None, csrf_header=None)
    missing_change = ChangePasswordCommand(
        secret="missing",
        current_password="correct-password",
        new_password="replacement-password",
        csrf_cookie=None,
        csrf_header=None,
        request_id="request-missing-change",
        client_ip="127.0.0.1",
        user_agent=None,
    )
    with pytest.raises(AuthenticationRequiredError):
        await service.change_password(missing_change)

    issue = await service.login(_login_command())
    csrf = service.csrf_token(issue.view.session_id)
    factory.identity.stale_password_on_session_lock = True
    with pytest.raises(AuthenticationFailedError):
        await service.change_password(
            ChangePasswordCommand(
                secret=issue.secret,
                current_password="correct-password",
                new_password="replacement-password",
                csrf_cookie=csrf,
                csrf_header=csrf,
                request_id="request-race-change",
                client_ip="127.0.0.1",
                user_agent=None,
            )
        )


def test_identity_configuration_and_full_access_allow_path() -> None:
    """Invalid admission capacity is rejected and changed-password sessions pass policy."""
    factory = _Factory(_administrator())
    with pytest.raises(ValueError, match="positive"):
        IdentityService(
            cast("IdentityUnitOfWorkFactory", factory),
            IdentityServiceConfiguration(
                csrf_signing_key=b"c" * 32,
                privacy_hmac_key=b"p" * 32,
                password_manager=cast("PasswordManager", _PasswordManager()),
                hash_concurrency=0,
            ),
        )
    view = _service(factory)._validated_view(  # noqa: SLF001 - focused invariant test.
        (
            _Session(
                id=UUID("019fc34f-0000-7000-8000-000000000002"),
                administrator_id=_administrator().id,
                token_digest=b"x" * 32,
                idle_expires_at=datetime(2026, 8, 2, 12, 30, tzinfo=UTC),
                absolute_expires_at=datetime(2026, 8, 3, tzinfo=UTC),
                last_seen_at=datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
                revoked_at=None,
                revocation_reason=None,
            ),
            _administrator(),
        ),
        datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
    )
    view = type(view)(
        administrator_id=view.administrator_id,
        display_name=view.display_name,
        must_change_password=False,
        idle_expires_at=view.idle_expires_at,
        absolute_expires_at=view.absolute_expires_at,
        session_id=view.session_id,
    )
    IdentityService.require_full_access(view)
    assert _service(factory).cookie_max_age_seconds(view) == 43_200


async def test_bootstrap_rejects_invalid_display_name_before_persistence() -> None:
    """Bootstrap validates bounded operator-visible identity data."""
    factory = _Factory(None)
    service = BootstrapService(
        cast("IdentityUnitOfWorkFactory", factory),
        password_manager=cast("PasswordManager", _PasswordManager()),
    )
    with pytest.raises(ValueError, match="between 1 and 160"):
        await service.bootstrap(
            email="owner@example.test",
            display_name=" ",
            password="correct-password",
        )
