"""Adversarial unit tests for identity admission and blocked fast paths."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import TYPE_CHECKING, Self, cast

import pytest

from app.modules.identity.ports import RateLimitDecision
from app.modules.identity.service import (
    AuthenticationFailedError,
    IdentityService,
    IdentityServiceConfiguration,
    LoginCommand,
    RateLimitedError,
)

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType

    from app.modules.audit.domain import AuditEntry
    from app.modules.identity.domain import NewAdministrator, NewAdminSession
    from app.modules.identity.ports import (
        AdministratorState,
        AdminSessionState,
        IdentityUnitOfWorkFactory,
    )
    from app.modules.identity.security import PasswordManager


class _TrackingPasswordManager:
    dummy_hash = "dummy-hash"

    def __init__(self) -> None:
        self.active = 0
        self.maximum_active = 0
        self._lock = threading.Lock()

    def verify(self, _password_hash: str | None, _password: str) -> bool:
        with self._lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
        time.sleep(0.04)
        with self._lock:
            self.active -= 1
        return False

    @staticmethod
    def needs_rehash(_password_hash: str) -> bool:
        return False

    @staticmethod
    def hash(password: str) -> str:
        return f"hash:{len(password)}"


class _FakeIdentityRepository:
    def __init__(self) -> None:
        self.email_lookup_calls = 0

    async def acquire_bootstrap_lock(self) -> None: ...

    async def administrator_count(self) -> int:
        return 0

    async def administrator_by_email(
        self,
        _email_normalized: str,
        *,
        for_update: bool = False,
    ) -> AdministratorState | None:
        del for_update
        self.email_lookup_calls += 1
        return None

    async def administrator_by_id(
        self,
        _administrator_id: object,
        *,
        for_update: bool = False,
    ) -> AdministratorState | None:
        del for_update
        return None

    def add_administrator(self, _administrator: NewAdministrator) -> None: ...

    def add_session(self, _admin_session: NewAdminSession) -> None: ...

    async def session_with_administrator(
        self,
        _token_digest: bytes,
        *,
        for_update: bool = False,
    ) -> tuple[AdminSessionState, AdministratorState] | None:
        del for_update
        return None

    async def revoke_other_sessions(self, **_kwargs: object) -> None: ...


class _FakeRateLimit:
    def __init__(self, *, blocked: bool = False) -> None:
        self.blocked = blocked

    async def check_login(self, _subject_digest: bytes, _now: datetime) -> RateLimitDecision:
        return RateLimitDecision(retry_after_seconds=60 if self.blocked else 0)

    async def record_login_failure(
        self,
        _subject_digest: bytes,
        _now: datetime,
    ) -> RateLimitDecision:
        return RateLimitDecision(retry_after_seconds=0)

    async def clear_login_failures(self, _subject_digest: bytes) -> None: ...


class _FakeAudit:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class _FakeUnitOfWork:
    def __init__(self, identity: _FakeIdentityRepository, rate_limit: _FakeRateLimit) -> None:
        self.identity = identity
        self.rate_limit = rate_limit
        self.audit = _FakeAudit()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


class _FakeUnitOfWorkFactory:
    def __init__(self, *, blocked: bool = False) -> None:
        self.identity = _FakeIdentityRepository()
        self.rate_limit = _FakeRateLimit(blocked=blocked)

    def __call__(self) -> _FakeUnitOfWork:
        return _FakeUnitOfWork(self.identity, self.rate_limit)


def _command(index: int) -> LoginCommand:
    return LoginCommand(
        email=f"unknown-{index}@example.test",
        password="invalid password",
        client_ip="127.0.0.1",
        user_agent="test",
        request_id=f"request-{index:016d}",
    )


async def test_argon2_admission_is_bounded_under_concurrent_unknown_logins() -> None:
    """A burst cannot schedule more than the configured number of hash jobs."""
    tracker = _TrackingPasswordManager()
    service = IdentityService(
        cast("IdentityUnitOfWorkFactory", _FakeUnitOfWorkFactory()),
        IdentityServiceConfiguration(
            csrf_signing_key=b"c" * 32,
            privacy_hmac_key=b"p" * 32,
            password_manager=cast("PasswordManager", tracker),
            hash_concurrency=2,
        ),
    )

    results = await asyncio.gather(
        *(service.login(_command(index)) for index in range(8)),
        return_exceptions=True,
    )

    assert all(isinstance(result, AuthenticationFailedError) for result in results)
    assert tracker.maximum_active == 2


async def test_blocked_login_skips_candidate_dependent_administrator_lookup() -> None:
    """The 429 fast path performs no known-vs-unknown administrator query."""
    factory = _FakeUnitOfWorkFactory(blocked=True)
    tracker = _TrackingPasswordManager()
    service = IdentityService(
        cast("IdentityUnitOfWorkFactory", factory),
        IdentityServiceConfiguration(
            csrf_signing_key=b"c" * 32,
            privacy_hmac_key=b"p" * 32,
            password_manager=cast("PasswordManager", tracker),
        ),
    )

    with pytest.raises(RateLimitedError):
        await service.login(_command(1))

    assert factory.identity.email_lookup_calls == 0
    assert tracker.maximum_active == 0
