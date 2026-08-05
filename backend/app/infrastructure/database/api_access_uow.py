"""Atomic API-token transaction composition."""

# ruff: noqa: D101, D102, D105, D107
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from app.infrastructure.database.api_access import ApiTokenRepository
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.infrastructure.rate_limit.persistence import RateLimitRepository
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from types import TracebackType

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.api_access.ports import ApiTokenUnitOfWork


class SqlAlchemyApiTokenUnitOfWork:
    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        self._inner = SqlAlchemyUnitOfWork(session_factory)

    async def __aenter__(self) -> Self:
        await self._inner.__aenter__()
        self.tokens = ApiTokenRepository(self._inner.session, id_factory=uuid7)
        self.audit = AuditRepository(self._inner.session)
        self.rate_limits = RateLimitRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemyApiTokenUnitOfWorkFactory:
    session_factory: AsyncSessionFactory

    def __call__(self) -> ApiTokenUnitOfWork:
        return cast("ApiTokenUnitOfWork", SqlAlchemyApiTokenUnitOfWork(self.session_factory))
