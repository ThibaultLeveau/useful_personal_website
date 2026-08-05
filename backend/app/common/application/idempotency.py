"""Safe idempotency port and result contracts for atomic command use cases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from app.common.domain.temporal import require_utc
from app.common.security.idempotency import (
    digest_actor,
    digest_idempotency_key,
    fingerprint_bytes,
    validate_route_template,
)

if TYPE_CHECKING:
    from uuid import UUID

    from app.common.domain.actors import ActorContext, ActorType

IDEMPOTENCY_RETENTION = timedelta(hours=24)
SHA256_DIGEST_LENGTH = 32
MINIMUM_SUCCESS_STATUS = 200
MAXIMUM_SUCCESS_STATUS = 299
_OUTCOME_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9._:-]{0,79}$")


class IdempotencyDecisionType(StrEnum):
    """Possible outcomes when admitting one command key."""

    ACQUIRED = "acquired"
    REPLAY = "replay"
    PAYLOAD_CONFLICT = "payload_conflict"
    IN_PROGRESS = "in_progress"


@dataclass(frozen=True, slots=True)
class IdempotencyRequest:
    """Digest-only actor/route/key/payload facts supplied to persistence."""

    actor_type: ActorType
    actor_digest: bytes
    route: str
    key_digest: bytes
    request_fingerprint: bytes
    requested_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        """Enforce digest sizes, UTC bounds, and the fixed retention window."""
        if (
            len(self.actor_digest) != SHA256_DIGEST_LENGTH
            or len(self.key_digest) != SHA256_DIGEST_LENGTH
        ):
            msg = "actor and idempotency-key digests must be SHA-256 values"
            raise ValueError(msg)
        if len(self.request_fingerprint) != SHA256_DIGEST_LENGTH:
            msg = "request fingerprints must be SHA-256 values"
            raise ValueError(msg)
        validate_route_template(self.route)
        require_utc(self.requested_at)
        require_utc(self.expires_at)
        if self.expires_at - self.requested_at != IDEMPOTENCY_RETENTION:
            msg = "idempotency records must use the fixed 24-hour retention"
            raise ValueError(msg)

    @classmethod
    def create(
        cls,
        *,
        actor: ActorContext,
        route: str,
        key: str,
        canonical_payload: bytes,
        requested_at: datetime,
    ) -> IdempotencyRequest:
        """Build a safe persistence request without retaining raw command material."""
        require_utc(requested_at)
        return cls(
            actor_type=actor.actor_type,
            actor_digest=digest_actor(actor),
            route=validate_route_template(route),
            key_digest=digest_idempotency_key(key),
            request_fingerprint=fingerprint_bytes(canonical_payload),
            requested_at=requested_at,
            expires_at=requested_at + IDEMPOTENCY_RETENTION,
        )


@dataclass(frozen=True, slots=True)
class IdempotencyOutcome:
    """Replay-safe resource reference; deliberately never a response body."""

    response_status: int
    result_code: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    resource_version: int | None = None

    def __post_init__(self) -> None:
        """Allow only bounded success metadata and paired resource facts."""
        if not MINIMUM_SUCCESS_STATUS <= self.response_status <= MAXIMUM_SUCCESS_STATUS:
            msg = "idempotency outcomes must describe successful responses"
            raise ValueError(msg)
        if _OUTCOME_NAME_PATTERN.fullmatch(self.result_code) is None:
            msg = "result_code must be a bounded catalog value"
            raise ValueError(msg)
        resource_values = (self.resource_type, self.resource_id, self.resource_version)
        if any(value is not None for value in resource_values):
            if any(value is None for value in resource_values):
                msg = "resource outcome fields must be all present or all absent"
                raise ValueError(msg)
            if (
                _OUTCOME_NAME_PATTERN.fullmatch(self.resource_type or "") is None
                or isinstance(self.resource_version, bool)
                or (self.resource_version or 0) < 1
            ):
                msg = "resource outcome fields are invalid"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class IdempotencyDecision:
    """Admission result returned under the caller-owned database transaction."""

    decision: IdempotencyDecisionType
    record_id: UUID | None = None
    outcome: IdempotencyOutcome | None = None

    def __post_init__(self) -> None:
        """Keep acquired and replay decisions structurally unambiguous."""
        if self.decision is IdempotencyDecisionType.ACQUIRED:
            if self.record_id is None or self.outcome is not None:
                msg = "an acquired decision requires only its record identifier"
                raise ValueError(msg)
        elif self.decision is IdempotencyDecisionType.REPLAY:
            if self.record_id is None or self.outcome is None:
                msg = "a replay decision requires its safe completed outcome"
                raise ValueError(msg)
        elif self.record_id is not None or self.outcome is not None:
            msg = "conflict decisions cannot expose persistence identifiers or outcomes"
            raise ValueError(msg)


class IdempotencyStore(Protocol):
    """Caller-transaction-owned port for exactly-once command admission."""

    async def acquire(self, request: IdempotencyRequest) -> IdempotencyDecision:
        """Acquire, replay, or safely reject an actor/route/key command."""
        ...

    async def complete(
        self,
        record_id: UUID,
        outcome: IdempotencyOutcome,
        *,
        completed_at: datetime,
    ) -> None:
        """Complete a newly acquired record in the same transaction as its effect."""
        ...

    async def purge_expired(self, *, before: datetime) -> int:
        """Delete expired operational records and return the affected count."""
        ...
