"""Inward-facing persistence and transaction ports for identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.modules.audit.domain import AuditEntry
    from app.modules.identity.domain import NewAdministrator, NewAdminSession


class AdministratorState(Protocol):
    """Mutable administrator state required by identity use cases."""

    id: UUID
    display_name: str
    password_hash: str
    must_change_password: bool
    password_changed_at: datetime | None
    updated_at: datetime
    version: int


class AdminSessionState(Protocol):
    """Mutable session state required by identity use cases."""

    id: UUID
    administrator_id: UUID
    idle_expires_at: datetime
    absolute_expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None


class IdentityRepositoryPort(Protocol):
    """Identity persistence operations without commit ownership."""

    async def acquire_bootstrap_lock(self) -> None:
        """Serialize bootstrap attempts."""
        ...

    async def administrator_count(self) -> int:
        """Count all administrator rows."""
        ...

    async def administrator_by_email(
        self,
        email_normalized: str,
        *,
        for_update: bool = False,
    ) -> AdministratorState | None:
        """Find an active administrator by normalized email."""
        ...

    async def administrator_by_id(
        self,
        administrator_id: UUID,
        *,
        for_update: bool = False,
    ) -> AdministratorState | None:
        """Find an active administrator by ID."""
        ...

    def add_administrator(self, administrator: NewAdministrator) -> None:
        """Stage a new administrator."""
        ...

    def add_session(self, admin_session: NewAdminSession) -> None:
        """Stage a new session."""
        ...

    async def session_with_administrator(
        self,
        token_digest: bytes,
        *,
        for_update: bool = False,
    ) -> tuple[AdminSessionState, AdministratorState] | None:
        """Load a session candidate and active administrator."""
        ...

    async def revoke_other_sessions(
        self,
        *,
        administrator_id: UUID,
        current_session_id: UUID,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        """Revoke every other live session."""
        ...


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Safe rate decision containing only a retry interval."""

    retry_after_seconds: int

    @property
    def allowed(self) -> bool:
        """Return whether the request may proceed."""
        return self.retry_after_seconds == 0


class RateLimitPort(Protocol):
    """Pseudonymous authentication-rate operations."""

    async def check_login(self, subject_digest: bytes, now: datetime) -> RateLimitDecision:
        """Check whether the subject is currently blocked."""
        ...

    async def record_login_failure(
        self,
        subject_digest: bytes,
        now: datetime,
    ) -> RateLimitDecision:
        """Atomically record a failed login."""
        ...

    async def clear_login_failures(self, subject_digest: bytes) -> None:
        """Clear failures after successful authentication."""
        ...


class AuditPort(Protocol):
    """Insert-only audit port."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed append-only fact."""
        ...


class IdentityUnitOfWork(Protocol):
    """One identity transaction with inward-facing repositories."""

    identity: IdentityRepositoryPort
    rate_limit: RateLimitPort
    audit: AuditPort

    async def __aenter__(self) -> Self:
        """Open a transaction and bind ports."""
        ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work and release resources."""
        ...

    async def commit(self) -> None:
        """Commit the application operation."""
        ...


class IdentityUnitOfWorkFactory(Protocol):
    """Create a fresh request/command transaction."""

    def __call__(self) -> IdentityUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
