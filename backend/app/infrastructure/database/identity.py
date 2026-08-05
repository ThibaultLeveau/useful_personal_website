"""SQLAlchemy identity models and repository adapter."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves this type at runtime.
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves this type at runtime.

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.modules.identity.domain import NewAdministrator, NewAdminSession


class IdentityBase(DeclarativeBase):
    """Identity-only SQLAlchemy registry."""


class AdministratorRecord(IdentityBase):
    """Single-privilege R1 administrator persistence record."""

    __tablename__ = "administrator"
    __table_args__ = (Index("ix_administrator_active_lookup", "is_active", "id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    email_normalized: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(512))
    must_change_password: Mapped[bool] = mapped_column(Boolean)
    is_active: Mapped[bool] = mapped_column(Boolean)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer)


class AdminSessionRecord(IdentityBase):
    """Digest-only opaque browser session record."""

    __tablename__ = "admin_session"
    __table_args__ = (
        Index("ix_admin_session_active_expiry", "revoked_at", "idle_expires_at"),
        Index("ix_admin_session_administrator", "administrator_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    administrator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("administrator.id", ondelete="CASCADE"),
    )
    token_digest: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(64))
    user_agent_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    ip_pseudonym: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    rotated_from_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admin_session.id", ondelete="SET NULL"),
    )


@dataclass(slots=True)
class _AdministratorSnapshot:
    """Persistence-neutral values safe to use after a read transaction closes."""

    id: UUID
    display_name: str
    password_hash: str
    must_change_password: bool
    password_changed_at: datetime | None
    updated_at: datetime
    version: int


@dataclass(slots=True)
class _AdminSessionSnapshot:
    """Persistence-neutral session values safe after a read transaction closes."""

    id: UUID
    administrator_id: UUID
    idle_expires_at: datetime
    absolute_expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None


def _administrator_snapshot(record: AdministratorRecord) -> _AdministratorSnapshot:
    return _AdministratorSnapshot(
        id=record.id,
        display_name=record.display_name,
        password_hash=record.password_hash,
        must_change_password=record.must_change_password,
        password_changed_at=record.password_changed_at,
        updated_at=record.updated_at,
        version=record.version,
    )


def _session_snapshot(record: AdminSessionRecord) -> _AdminSessionSnapshot:
    return _AdminSessionSnapshot(
        id=record.id,
        administrator_id=record.administrator_id,
        idle_expires_at=record.idle_expires_at,
        absolute_expires_at=record.absolute_expires_at,
        last_seen_at=record.last_seen_at,
        revoked_at=record.revoked_at,
        revocation_reason=record.revocation_reason,
    )


class IdentityRepository:
    """Repository adapter with no transaction ownership."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned transaction session."""
        self._session = session

    async def acquire_bootstrap_lock(self) -> None:
        """Serialize bootstrap attempts without a permanent singleton constraint."""
        await self._session.execute(text("SELECT pg_advisory_xact_lock(824608020001)"))

    async def administrator_count(self) -> int:
        """Count every administrator row so deactivation cannot reopen bootstrap."""
        result = await self._session.execute(select(AdministratorRecord.id))
        return len(result.scalars().all())

    async def administrator_by_email(
        self,
        email_normalized: str,
        *,
        for_update: bool = False,
    ) -> AdministratorRecord | _AdministratorSnapshot | None:
        """Find an administrator by normalized unique identifier."""
        statement = select(AdministratorRecord).where(
            AdministratorRecord.email_normalized == email_normalized,
            AdministratorRecord.is_active.is_(True),
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None or for_update:
            return record
        return _administrator_snapshot(record)

    async def administrator_by_id(
        self,
        administrator_id: UUID,
        *,
        for_update: bool = False,
    ) -> AdministratorRecord | _AdministratorSnapshot | None:
        """Find an active administrator by ID."""
        statement = select(AdministratorRecord).where(
            AdministratorRecord.id == administrator_id,
            AdministratorRecord.is_active.is_(True),
        )
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None or for_update:
            return record
        return _administrator_snapshot(record)

    def add_administrator(self, administrator: NewAdministrator) -> None:
        """Stage a new administrator record."""
        self._session.add(AdministratorRecord(**asdict(administrator)))

    def add_session(self, admin_session: NewAdminSession) -> None:
        """Stage a new opaque session record."""
        self._session.add(AdminSessionRecord(**asdict(admin_session)))

    async def session_with_administrator(
        self,
        token_digest: bytes,
        *,
        for_update: bool = False,
    ) -> (
        tuple[
            AdminSessionRecord | _AdminSessionSnapshot,
            AdministratorRecord | _AdministratorSnapshot,
        ]
        | None
    ):
        """Load a session candidate and active administrator."""
        statement = (
            select(AdminSessionRecord, AdministratorRecord)
            .join(
                AdministratorRecord,
                AdministratorRecord.id == AdminSessionRecord.administrator_id,
            )
            .where(
                AdminSessionRecord.token_digest == token_digest,
                AdministratorRecord.is_active.is_(True),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        if not for_update:
            return _session_snapshot(row[0]), _administrator_snapshot(row[1])
        return row[0], row[1]

    async def revoke_other_sessions(
        self,
        *,
        administrator_id: UUID,
        current_session_id: UUID,
        revoked_at: datetime,
        reason: str,
    ) -> None:
        """Revoke all other live sessions after password rotation."""
        result = await self._session.execute(
            select(AdminSessionRecord).where(
                AdminSessionRecord.administrator_id == administrator_id,
                AdminSessionRecord.id != current_session_id,
                AdminSessionRecord.revoked_at.is_(None),
            )
        )
        for record in result.scalars():
            record.revoked_at = revoked_at
            record.revocation_reason = reason
