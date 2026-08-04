"""Transaction composition for configurable pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.media import MediaRepository
from app.infrastructure.database.pages import PageRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from types import TracebackType

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.pages.ports import PagesUnitOfWork


class SqlAlchemyPagesUnitOfWork:
    """Bind M8 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.pages: PageRepository
        self.media: MediaRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository

    async def __aenter__(self) -> Self:
        """Open one transaction and bind page/shared repositories."""
        await self._inner.__aenter__()
        self.pages = PageRepository(self._inner.session, id_factory=uuid7)
        self.media = MediaRepository(self._inner.session, id_factory=uuid7)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        """Commit only at the application-service boundary."""
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Delegate rollback and connection cleanup."""
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemyPagesUnitOfWorkFactory:
    """Create structurally typed page transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> PagesUnitOfWork:
        """Return one fresh unopened page transaction."""
        return cast("PagesUnitOfWork", SqlAlchemyPagesUnitOfWork(self.session_factory))
