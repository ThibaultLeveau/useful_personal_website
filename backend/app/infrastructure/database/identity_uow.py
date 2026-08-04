"""SQLAlchemy composition for the inward-facing identity UoW port."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.identity import IdentityRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.infrastructure.rate_limit import RateLimitRepository

if TYPE_CHECKING:
    from types import TracebackType

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.identity.ports import (
        AuditPort,
        IdentityRepositoryPort,
        IdentityUnitOfWork,
        RateLimitPort,
    )


class SqlAlchemyIdentityUnitOfWork:
    """Adapt the shared SQLAlchemy transaction to identity ports."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Prepare a fresh transaction without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.identity: IdentityRepositoryPort
        self.rate_limit: RateLimitPort
        self.audit: AuditPort

    async def __aenter__(self) -> Self:
        """Open the transaction and bind all adapter repositories."""
        await self._inner.__aenter__()
        self.identity = IdentityRepository(self._inner.session)
        self.rate_limit = RateLimitRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        """Commit at the application-service boundary."""
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Delegate rollback and resource cleanup to the shared UoW."""
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemyIdentityUnitOfWorkFactory:
    """Create one adapter transaction per identity operation."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> IdentityUnitOfWork:
        """Return a fresh unopened identity transaction."""
        return SqlAlchemyIdentityUnitOfWork(self.session_factory)
