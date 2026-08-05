"""PostgreSQL token metadata, digest, scope, and lifecycle persistence."""

# ruff: noqa: D101, D102, D107, E501, TC003
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    String,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.api_access.domain import ApiTokenMetadata, ApiTokenScope

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession


class ApiAccessBase(DeclarativeBase):
    pass


class ApiTokenRecord(ApiAccessBase):
    __tablename__ = "api_token"
    __table_args__ = (
        CheckConstraint("octet_length(secret_digest)=32", name="api_token_digest_length"),
        CheckConstraint("version>0", name="api_token_positive_version"),
        CheckConstraint(
            "expires_at IS NULL OR expires_at>created_at", name="api_token_expiry_after_creation"
        ),
        CheckConstraint(
            "(revoked_at IS NULL)=(revocation_reason IS NULL)", name="api_token_revocation_shape"
        ),
        ForeignKeyConstraint(
            ["owner_id"],
            ["administrator.id"],
            name="fk_api_token_owner_id_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_api_token_owner_created", "owner_id", "created_at", "id"),
        Index("ix_api_token_active_expiry", "owner_id", "revoked_at", "expires_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    public_id: Mapped[str] = mapped_column(String(22), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    display_suffix: Mapped[str] = mapped_column(String(6))
    secret_digest: Mapped[bytes] = mapped_column(LargeBinary(32))
    digest_key_version: Mapped[str] = mapped_column(String(40))
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(32))
    rotated_from_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("api_token.id", ondelete="RESTRICT"), unique=True
    )
    version: Mapped[int] = mapped_column(Integer)


class ApiTokenScopeRecord(ApiAccessBase):
    __tablename__ = "api_token_scope"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('content:read','content:write','media:read','media:write','contacts:read','admin:read')",
            name="api_token_scope_catalog",
        ),
    )
    token_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("api_token.id", ondelete="CASCADE"), primary_key=True
    )
    scope: Mapped[str] = mapped_column(String(32), primary_key=True)


def _metadata(
    row: tuple[
        UUID,
        str,
        str,
        str,
        datetime,
        datetime | None,
        datetime | None,
        datetime | None,
        str | None,
        UUID | None,
        int,
    ],
    scopes: frozenset[ApiTokenScope],
) -> ApiTokenMetadata:
    return ApiTokenMetadata(
        id=row[0],
        public_id=row[1],
        name=row[2],
        display_suffix=row[3],
        created_at=row[4],
        expires_at=row[5],
        last_used_at=row[6],
        revoked_at=row[7],
        revocation_reason=row[8],
        rotated_from_id=row[9],
        version=row[10],
        scopes=scopes,
    )


_PROJECTION = (
    ApiTokenRecord.id,
    ApiTokenRecord.public_id,
    ApiTokenRecord.name,
    ApiTokenRecord.display_suffix,
    ApiTokenRecord.created_at,
    ApiTokenRecord.expires_at,
    ApiTokenRecord.last_used_at,
    ApiTokenRecord.revoked_at,
    ApiTokenRecord.revocation_reason,
    ApiTokenRecord.rotated_from_id,
    ApiTokenRecord.version,
)


class ApiTokenRepository:
    def __init__(self, session: AsyncSession, *, id_factory: Callable[[], UUID]) -> None:
        self._session = session
        self.id_factory = id_factory

    async def database_now(self) -> datetime:
        value = (await self._session.execute(select(func.clock_timestamp()))).scalar_one()
        return cast("datetime", value)

    async def add(
        self,
        *,
        metadata: ApiTokenMetadata,
        secret_digest: bytes,
        key_version: str,
        owner_id: UUID,
        display_suffix: str,
    ) -> None:
        self._session.add(
            ApiTokenRecord(
                id=metadata.id,
                public_id=metadata.public_id,
                name=metadata.name,
                display_suffix=display_suffix,
                secret_digest=secret_digest,
                digest_key_version=key_version,
                owner_id=owner_id,
                created_at=metadata.created_at,
                expires_at=metadata.expires_at,
                last_used_at=None,
                revoked_at=metadata.revoked_at,
                revocation_reason=metadata.revocation_reason,
                rotated_from_id=metadata.rotated_from_id,
                version=metadata.version,
            )
        )
        self._session.add_all(
            ApiTokenScopeRecord(token_id=metadata.id, scope=scope.value)
            for scope in metadata.scopes
        )

    async def _scopes(self, ids: tuple[UUID, ...]) -> dict[UUID, frozenset[ApiTokenScope]]:
        values: dict[UUID, set[ApiTokenScope]] = {item: set() for item in ids}
        if ids:
            for token_id, scope in (
                await self._session.execute(
                    select(ApiTokenScopeRecord.token_id, ApiTokenScopeRecord.scope).where(
                        ApiTokenScopeRecord.token_id.in_(ids)
                    )
                )
            ).all():
                values[token_id].add(ApiTokenScope(scope))
        return {key: frozenset(value) for key, value in values.items()}

    async def list(
        self, *, owner_id: UUID, offset: int, limit: int, status: str | None
    ) -> tuple[tuple[ApiTokenMetadata, ...], int]:
        now = await self.database_now()
        pred = [ApiTokenRecord.owner_id == owner_id]
        if status == "active":
            pred += [
                ApiTokenRecord.revoked_at.is_(None),
                ApiTokenRecord.expires_at.is_(None) | (ApiTokenRecord.expires_at > now),
            ]
        elif status == "revoked":
            pred.append(ApiTokenRecord.revoked_at.is_not(None))
        elif status == "expired":
            pred += [ApiTokenRecord.revoked_at.is_(None), ApiTokenRecord.expires_at <= now]
        total = (
            await self._session.execute(
                select(func.count()).select_from(ApiTokenRecord).where(*pred)
            )
        ).scalar_one()
        rows = (
            (
                await self._session.execute(
                    select(*_PROJECTION)
                    .where(*pred)
                    .order_by(ApiTokenRecord.created_at.desc(), ApiTokenRecord.id)
                    .offset(offset)
                    .limit(limit)
                )
            )
            .tuples()
            .all()
        )
        scope_map = await self._scopes(tuple(row[0] for row in rows))
        return tuple(_metadata(row, scope_map[row[0]]) for row in rows), total

    async def get_metadata(
        self, token_id: UUID, *, for_update: bool = False
    ) -> ApiTokenMetadata | None:
        q = select(*_PROJECTION).where(ApiTokenRecord.id == token_id)
        if for_update:
            q = q.with_for_update()
        row = (await self._session.execute(q)).tuples().one_or_none()
        if row is None:
            return None
        return _metadata(row, (await self._scopes((token_id,)))[token_id])

    async def find_auth(self, public_id: str) -> tuple[ApiTokenMetadata, bytes, str] | None:
        row = (
            (
                await self._session.execute(
                    select(
                        *_PROJECTION,
                        ApiTokenRecord.secret_digest,
                        ApiTokenRecord.digest_key_version,
                    )
                    .where(ApiTokenRecord.public_id == public_id)
                    .with_for_update()
                )
            )
            .tuples()
            .one_or_none()
        )
        if row is None:
            return None
        metadata = _metadata(row[:11], (await self._scopes((row[0],)))[row[0]])
        return metadata, row[11], row[12]

    async def revoke(
        self, token_id: UUID, *, expected_version: int, now: datetime, reason: str
    ) -> None:
        row = (
            await self._session.execute(
                select(ApiTokenRecord)
                .where(ApiTokenRecord.id == token_id, ApiTokenRecord.version == expected_version)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise LookupError
        row.revoked_at = now
        row.revocation_reason = reason
        row.version += 1

    async def touch_used(self, token_id: UUID, *, now: datetime) -> None:
        row = (
            await self._session.execute(
                select(ApiTokenRecord).where(ApiTokenRecord.id == token_id).with_for_update()
            )
        ).scalar_one()
        row.last_used_at = now

    async def active_count(self, owner_id: UUID, *, now: datetime) -> int:
        return (
            await self._session.execute(
                select(func.count())
                .select_from(ApiTokenRecord)
                .where(
                    ApiTokenRecord.owner_id == owner_id,
                    ApiTokenRecord.revoked_at.is_(None),
                    ApiTokenRecord.expires_at.is_(None) | (ApiTokenRecord.expires_at > now),
                )
            )
        ).scalar_one()

    async def name_exists(
        self, owner_id: UUID, name: str, *, exclude_id: UUID | None = None
    ) -> bool:
        pred = [
            ApiTokenRecord.owner_id == owner_id,
            func.lower(ApiTokenRecord.name) == name.casefold(),
            ApiTokenRecord.revoked_at.is_(None),
        ]
        if exclude_id is not None:
            pred.append(ApiTokenRecord.id != exclude_id)
        return bool(
            (
                await self._session.execute(
                    select(func.count()).select_from(ApiTokenRecord).where(*pred)
                )
            ).scalar_one()
        )
