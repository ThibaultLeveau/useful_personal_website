"""SQLAlchemy append-only audit model and adapter."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves this type at runtime.
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves this type at runtime.

from sqlalchemy import DateTime, Index, Integer, LargeBinary, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.audit.domain import (
    ActorType,
    AuditEntry,
    AuditOutcome,
    validate_audit_entry,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.common.domain.pagination import PageRequest
    from app.modules.audit.domain import AuditQuery


class AuditBase(DeclarativeBase):
    """Audit-only SQLAlchemy registry."""


class AuditEntryRecord(AuditBase):
    """Append-only, allow-listed audit row."""

    __tablename__ = "audit_entry"
    __table_args__ = (
        Index("ix_audit_entry_occurred", "occurred_at", "id"),
        Index("ix_audit_entry_event_time", "event_type", "occurred_at"),
        Index("ix_audit_entry_actor_time", "actor_type", "actor_id", "occurred_at"),
        Index("ix_audit_entry_resource_time", "resource_type", "resource_id", "occurred_at"),
        Index("ix_audit_entry_request_id", "request_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80))
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    actor_label_snapshot: Mapped[str | None] = mapped_column(String(80))
    resource_type: Mapped[str | None] = mapped_column(String(80))
    resource_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    request_id: Mapped[str] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str] = mapped_column(String(32))
    ip_pseudonym: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    metadata_json: Mapped[dict[str, str | int | bool | None]] = mapped_column(
        "metadata",
        JSONB,
    )
    schema_version: Mapped[int] = mapped_column(Integer)


class AuditRepository:
    """Insert-only adapter; no update/delete capability is exposed."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned transaction session."""
        self._session = session

    def append(self, entry: AuditEntry) -> None:
        """Translate and stage one controlled audit fact."""
        validate_audit_entry(entry)
        self._session.add(
            AuditEntryRecord(
                id=entry.id,
                event_type=entry.event_type,
                actor_type=entry.actor_type,
                actor_id=entry.actor_id,
                actor_label_snapshot=entry.actor_label_snapshot,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                request_id=entry.request_id,
                occurred_at=entry.occurred_at,
                outcome=entry.outcome,
                ip_pseudonym=entry.ip_pseudonym,
                metadata_json=entry.metadata,
                schema_version=entry.schema_version,
            )
        )

    async def list(
        self, query: AuditQuery, page: PageRequest
    ) -> tuple[tuple[AuditEntry, ...], int]:
        """Return one deterministic newest-first page using bound predicates."""
        predicates = []
        for column, value in (
            (AuditEntryRecord.event_type, query.event_type),
            (AuditEntryRecord.actor_type, query.actor_type.value if query.actor_type else None),
            (AuditEntryRecord.actor_id, query.actor_id),
            (AuditEntryRecord.resource_type, query.resource_type),
            (AuditEntryRecord.resource_id, query.resource_id),
            (AuditEntryRecord.outcome, query.outcome.value if query.outcome else None),
            (AuditEntryRecord.request_id, query.request_id),
        ):
            if value is not None:
                predicates.append(column == value)
        if query.occurred_from is not None:
            predicates.append(AuditEntryRecord.occurred_at >= query.occurred_from)
        if query.occurred_to is not None:
            predicates.append(AuditEntryRecord.occurred_at < query.occurred_to)
        total = int(
            await self._session.scalar(
                select(func.count()).select_from(AuditEntryRecord).where(*predicates)
            )
            or 0
        )
        rows = (
            await self._session.scalars(
                select(AuditEntryRecord)
                .where(*predicates)
                .order_by(AuditEntryRecord.occurred_at.desc(), AuditEntryRecord.id.desc())
                .offset(page.offset)
                .limit(page.page_size)
            )
        ).all()
        return tuple(self._domain(row) for row in rows), total

    async def get(self, entry_id: UUID) -> AuditEntry | None:
        """Load one safe detail projection by opaque identifier."""
        row = await self._session.get(AuditEntryRecord, entry_id)
        return None if row is None else self._domain(row)

    @staticmethod
    def _domain(row: AuditEntryRecord) -> AuditEntry:
        entry = AuditEntry(
            id=row.id,
            event_type=row.event_type,
            actor_type=ActorType(row.actor_type),
            actor_id=row.actor_id,
            actor_label_snapshot=row.actor_label_snapshot,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            request_id=row.request_id,
            occurred_at=row.occurred_at,
            outcome=AuditOutcome(row.outcome),
            ip_pseudonym=None,
            metadata=dict(row.metadata_json),
            schema_version=row.schema_version,
        )
        validate_audit_entry(entry)
        return entry
