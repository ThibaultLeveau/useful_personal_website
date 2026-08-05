"""PostgreSQL idempotency record model and atomic repository adapter."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves this type at runtime.
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain.temporal import require_utc

if TYPE_CHECKING:
    from typing import Any

    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyBase(DeclarativeBase):
    """Idempotency-only SQLAlchemy registry."""


class IdempotencyRecord(IdempotencyBase):
    """Digest-only admission record with a replay-safe resource outcome."""

    __tablename__ = "idempotency_record"
    __table_args__ = (
        UniqueConstraint(
            "actor_digest",
            "route",
            "key_digest",
            name="uq_idempotency_actor_route_key",
        ),
        CheckConstraint("octet_length(actor_digest) = 32", name="actor_digest_length"),
        CheckConstraint("octet_length(key_digest) = 32", name="key_digest_length"),
        CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="request_fingerprint_length",
        ),
        CheckConstraint(
            "actor_type IN ('public', 'administrator_session', 'api_token')",
            name="idempotency_actor_type_catalog",
        ),
        CheckConstraint("status IN ('pending', 'completed')", name="idempotency_status_catalog"),
        CheckConstraint("expires_at > created_at", name="idempotency_expiry_after_creation"),
        CheckConstraint(
            "(status = 'pending' AND completed_at IS NULL AND response_status IS NULL "
            "AND result_code IS NULL AND resource_type IS NULL AND resource_id IS NULL "
            "AND resource_version IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL "
            "AND response_status BETWEEN 200 AND 299 AND result_code IS NOT NULL "
            "AND ((resource_type IS NULL AND resource_id IS NULL AND resource_version IS NULL) "
            "OR (resource_type IS NOT NULL AND resource_id IS NOT NULL "
            "AND resource_version > 0)))",
            name="idempotency_outcome_shape",
        ),
        Index("ix_idempotency_expiry", "expires_at", "id"),
        Index("ix_idempotency_status_updated", "status", "updated_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    route: Mapped[str] = mapped_column(String(255))
    key_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    request_fingerprint: Mapped[bytes] = mapped_column(LargeBinary(32))
    status: Mapped[str] = mapped_column(String(16))
    response_status: Mapped[int | None] = mapped_column(Integer)
    result_code: Mapped[str | None] = mapped_column(String(80))
    resource_type: Mapped[str | None] = mapped_column(String(80))
    resource_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    resource_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _completed_outcome(record: IdempotencyRecord) -> IdempotencyOutcome:
    if record.response_status is None or record.result_code is None:
        msg = "a completed idempotency record has no outcome"
        raise RuntimeError(msg)
    return IdempotencyOutcome(
        response_status=record.response_status,
        result_code=record.result_code,
        resource_type=record.resource_type,
        resource_id=record.resource_id,
        resource_version=record.resource_version,
    )


class IdempotencyRepository:
    """Atomic actor/route/key admission without owning the caller transaction."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned transaction session."""
        self._session = session

    async def acquire(self, request: IdempotencyRequest) -> IdempotencyDecision:
        """Insert once, wait on concurrent uniqueness, then replay or reject safely."""
        candidate_id = uuid4()
        statement = (
            insert(IdempotencyRecord)
            .values(
                id=candidate_id,
                actor_type=request.actor_type.value,
                actor_digest=request.actor_digest,
                route=request.route,
                key_digest=request.key_digest,
                request_fingerprint=request.request_fingerprint,
                status="pending",
                response_status=None,
                result_code=None,
                resource_type=None,
                resource_id=None,
                resource_version=None,
                created_at=request.requested_at,
                updated_at=request.requested_at,
                completed_at=None,
                expires_at=request.expires_at,
            )
            .on_conflict_do_nothing(constraint="uq_idempotency_actor_route_key")
            .returning(IdempotencyRecord.id)
        )
        inserted_id = (await self._session.execute(statement)).scalar_one_or_none()
        if inserted_id is not None:
            return IdempotencyDecision(
                decision=IdempotencyDecisionType.ACQUIRED,
                record_id=inserted_id,
            )

        record = (
            await self._session.execute(
                select(IdempotencyRecord)
                .where(
                    IdempotencyRecord.actor_digest == request.actor_digest,
                    IdempotencyRecord.route == request.route,
                    IdempotencyRecord.key_digest == request.key_digest,
                )
                .with_for_update()
            )
        ).scalar_one()
        if record.expires_at <= request.requested_at:
            record.actor_type = request.actor_type.value
            record.request_fingerprint = request.request_fingerprint
            record.status = "pending"
            record.response_status = None
            record.result_code = None
            record.resource_type = None
            record.resource_id = None
            record.resource_version = None
            record.created_at = request.requested_at
            record.updated_at = request.requested_at
            record.completed_at = None
            record.expires_at = request.expires_at
            return IdempotencyDecision(
                decision=IdempotencyDecisionType.ACQUIRED,
                record_id=record.id,
            )
        if record.request_fingerprint != request.request_fingerprint:
            return IdempotencyDecision(decision=IdempotencyDecisionType.PAYLOAD_CONFLICT)
        if record.status == "completed":
            return IdempotencyDecision(
                decision=IdempotencyDecisionType.REPLAY,
                record_id=record.id,
                outcome=_completed_outcome(record),
            )
        return IdempotencyDecision(decision=IdempotencyDecisionType.IN_PROGRESS)

    async def complete(
        self,
        record_id: UUID,
        outcome: IdempotencyOutcome,
        *,
        completed_at: datetime,
    ) -> None:
        """Complete an acquired row in the same transaction as the command effect."""
        require_utc(completed_at)
        record = (
            await self._session.execute(
                select(IdempotencyRecord).where(IdempotencyRecord.id == record_id).with_for_update()
            )
        ).scalar_one_or_none()
        if record is None or record.status != "pending":
            msg = "only a pending idempotency record can be completed"
            raise ValueError(msg)
        record.status = "completed"
        record.response_status = outcome.response_status
        record.result_code = outcome.result_code
        record.resource_type = outcome.resource_type
        record.resource_id = outcome.resource_id
        record.resource_version = outcome.resource_version
        record.completed_at = completed_at
        record.updated_at = completed_at

    async def purge_expired(self, *, before: datetime) -> int:
        """Delete expired operational rows using the dedicated expiry index."""
        require_utc(before)
        result = await self._session.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.expires_at <= before)
        )
        return int(cast("CursorResult[Any]", result).rowcount or 0)
