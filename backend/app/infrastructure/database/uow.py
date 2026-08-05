"""Transaction-owning SQLAlchemy unit of work."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

    from app.infrastructure.database.session import AsyncSessionFactory


class SqlAlchemyUnitOfWork:
    """Own one explicit transaction and roll it back unless explicitly committed."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._transaction: AsyncSessionTransaction | None = None

    @property
    def session(self) -> AsyncSession:
        """Expose the active session to repositories without commit ownership."""
        if self._session is None:
            msg = "unit of work is not active"
            raise RuntimeError(msg)
        return self._session

    async def __aenter__(self) -> Self:
        """Open a session and transaction."""
        if self._session is not None:
            msg = "unit of work cannot be entered twice"
            raise RuntimeError(msg)
        self._session = self._session_factory()
        self._transaction = await self._session.begin()
        return self

    async def commit(self) -> None:
        """Commit the transaction at the application-service boundary."""
        transaction = self._require_transaction()
        await transaction.commit()
        self._transaction = None

    async def rollback(self) -> None:
        """Explicitly roll back the active transaction."""
        transaction = self._require_transaction()
        await transaction.rollback()
        self._transaction = None

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work on normal exit or failure, then close."""
        del exception_type, exception, traceback
        session = self._session
        if session is None:
            return
        try:
            if self._transaction is not None:
                await self._transaction.rollback()
                self._transaction = None
        finally:
            await session.close()
            self._session = None

    def _require_transaction(self) -> AsyncSessionTransaction:
        transaction = self._transaction
        if transaction is None:
            msg = "unit of work has no active transaction"
            raise RuntimeError(msg)
        return transaction
