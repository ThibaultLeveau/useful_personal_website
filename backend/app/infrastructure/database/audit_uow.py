"""Read-only SQLAlchemy composition for protected audit inspection."""

# ruff: noqa: D102, D105, D107

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from types import TracebackType

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.audit.ports import AuditQueryUnitOfWork


class SqlAlchemyAuditQueryUnitOfWork:
    """Own one read transaction and expose no audit mutation capability."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        self._inner = SqlAlchemyUnitOfWork(session_factory)

    async def __aenter__(self) -> Self:
        await self._inner.__aenter__()
        self.audit = AuditRepository(self._inner.session)
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemyAuditQueryUnitOfWorkFactory:
    """Create one read transaction per audit query."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> AuditQueryUnitOfWork:
        return cast("AuditQueryUnitOfWork", SqlAlchemyAuditQueryUnitOfWork(self.session_factory))
