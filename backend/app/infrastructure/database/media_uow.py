"""Transaction composition for private image media."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.media import MediaRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from types import TracebackType

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.media.ports import MediaUnitOfWork


class SqlAlchemyMediaUnitOfWork:
    """Bind the media repository to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.media: MediaRepository
        self.idempotency: IdempotencyRepository
        self.audit: AuditRepository

    async def __aenter__(self) -> Self:
        """Open one transaction and bind the media repository."""
        await self._inner.__aenter__()
        self.media = MediaRepository(self._inner.session, id_factory=uuid7)
        self.idempotency = IdempotencyRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
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
class SqlAlchemyMediaUnitOfWorkFactory:
    """Create structurally typed media transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> MediaUnitOfWork:
        """Return one fresh unopened media transaction."""
        return cast("MediaUnitOfWork", SqlAlchemyMediaUnitOfWork(self.session_factory))
