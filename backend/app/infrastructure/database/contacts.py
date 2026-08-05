"""PostgreSQL contact submission model and repository."""
# ruff: noqa: D101, D102, D107, E501, PLR0913, TC003

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, delete, func, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.contacts.domain import ContactState, ContactSubmission

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession


class ContactsBase(DeclarativeBase):
    """Contact-only registry."""


class ContactSubmissionRecord(ContactsBase):
    __tablename__ = "contact_submission"
    __table_args__ = (
        CheckConstraint("state IN ('unread','read','archived')", name="contact_state_catalog"),
        CheckConstraint("version > 0", name="contact_positive_version"),
        CheckConstraint(
            "(state = 'unread' AND read_at IS NULL AND archived_at IS NULL) OR (state = 'read' AND read_at IS NOT NULL AND archived_at IS NULL) OR (state = 'archived' AND read_at IS NOT NULL AND archived_at IS NOT NULL)",
            name="contact_lifecycle_shape",
        ),
        Index("ix_contact_state_created", "state", "created_at", "id"),
        Index("ix_contact_retention", "created_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    policy_version: Mapped[str] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(16))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)


def _domain(r: ContactSubmissionRecord) -> ContactSubmission:
    return ContactSubmission(
        id=r.id,
        name=r.name,
        email=r.email,
        subject=r.subject,
        message=r.message,
        consented_at=r.consented_at,
        policy_version=r.policy_version,
        source=r.source,
        state=ContactState(r.state),
        read_at=r.read_at,
        archived_at=r.archived_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
        version=r.version,
    )


class ContactRepository:
    def __init__(self, session: AsyncSession, *, id_factory: Callable[[], UUID]) -> None:
        self._session = session
        self.id_factory = id_factory

    async def database_now(self) -> datetime:
        value = (await self._session.execute(select(func.clock_timestamp()))).scalar_one()
        return cast("datetime", value)

    async def add(self, c: ContactSubmission) -> None:
        self._session.add(
            ContactSubmissionRecord(**{name: getattr(c, name) for name in c.__dataclass_fields__})
        )

    async def get(self, contact_id: UUID, *, for_update: bool = False) -> ContactSubmission | None:
        q = select(ContactSubmissionRecord).where(ContactSubmissionRecord.id == contact_id)
        if for_update:
            q = q.with_for_update()
        row = (await self._session.execute(q)).scalar_one_or_none()
        return None if row is None else _domain(row)

    async def list(
        self,
        *,
        state: ContactState | None,
        created_from: datetime | None,
        created_to: datetime | None,
        offset: int,
        limit: int,
        oldest_first: bool,
    ) -> tuple[tuple[ContactSubmission, ...], int]:
        filters = []
        if state is not None:
            filters.append(ContactSubmissionRecord.state == state.value)
        if created_from is not None:
            filters.append(ContactSubmissionRecord.created_at >= created_from)
        if created_to is not None:
            filters.append(ContactSubmissionRecord.created_at < created_to)
        count = (
            await self._session.execute(
                select(func.count()).select_from(ContactSubmissionRecord).where(*filters)
            )
        ).scalar_one()
        order = (
            ContactSubmissionRecord.created_at.asc()
            if oldest_first
            else ContactSubmissionRecord.created_at.desc()
        )
        rows = (
            await self._session.execute(
                select(ContactSubmissionRecord)
                .where(*filters)
                .order_by(order, ContactSubmissionRecord.id.asc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars()
        return tuple(_domain(row) for row in rows), count

    async def update(self, c: ContactSubmission, *, expected_version: int) -> None:
        row = (
            await self._session.execute(
                select(ContactSubmissionRecord)
                .where(
                    ContactSubmissionRecord.id == c.id,
                    ContactSubmissionRecord.version == expected_version,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise LookupError
        for name in ("state", "read_at", "archived_at", "updated_at", "version"):
            setattr(row, name, getattr(c, name).value if name == "state" else getattr(c, name))

    async def delete(self, contact_id: UUID, *, expected_version: int) -> None:
        result = cast(
            "CursorResult[object]",
            await self._session.execute(
                delete(ContactSubmissionRecord).where(
                    ContactSubmissionRecord.id == contact_id,
                    ContactSubmissionRecord.version == expected_version,
                )
            ),
        )
        if result.rowcount != 1:
            raise LookupError

    async def purge(self, *, before: datetime, limit: int) -> int:
        ids = (
            select(ContactSubmissionRecord.id)
            .where(ContactSubmissionRecord.created_at < before)
            .order_by(ContactSubmissionRecord.created_at, ContactSubmissionRecord.id)
            .limit(limit)
        )
        result = cast(
            "CursorResult[object]",
            await self._session.execute(
                delete(ContactSubmissionRecord).where(ContactSubmissionRecord.id.in_(ids))
            ),
        )
        return result.rowcount
