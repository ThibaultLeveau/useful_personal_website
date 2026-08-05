"""Framework-independent identity values and deterministic seams."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Callable

type Clock = Callable[[], datetime]
type UUIDFactory = Callable[[], UUID]


def utc_now() -> datetime:
    """Return an aware UTC instant."""
    return datetime.now(UTC)


def uuid7() -> UUID:
    """Create an RFC 9562 UUIDv7 without relying on a newer Python runtime."""
    timestamp_ms = int(utc_now().timestamp() * 1000) & ((1 << 48) - 1)
    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)
    value = (timestamp_ms << 80) | (0x7 << 76) | (random_a << 64) | (0b10 << 62) | random_b
    return UUID(int=value)


@dataclass(frozen=True, slots=True)
class SessionView:
    """Safe session projection returned to the transport."""

    administrator_id: UUID
    display_name: str
    must_change_password: bool
    idle_expires_at: datetime
    absolute_expires_at: datetime
    session_id: UUID


@dataclass(frozen=True, slots=True)
class SessionIssue:
    """New secret plus its safe public session projection."""

    secret: str
    view: SessionView


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Safe result of creating the initial administrator."""

    administrator_id: UUID


@dataclass(frozen=True, slots=True)
class NewAdministrator:
    """Persistence-neutral initial administrator values."""

    id: UUID
    email: str
    email_normalized: str
    display_name: str
    password_hash: str
    must_change_password: bool
    is_active: bool
    password_changed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class NewAdminSession:
    """Persistence-neutral digest-only session values."""

    id: UUID
    administrator_id: UUID
    token_digest: bytes
    created_at: datetime
    last_seen_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    user_agent_digest: bytes | None
    ip_pseudonym: bytes | None
    rotated_from_id: UUID | None
