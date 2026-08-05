"""PostgreSQL transaction tests for the SQLAlchemy unit of work."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import create_session_factory
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.postgresql


@pytest.fixture
async def uow_table(database_owner_engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    """Create an isolated test-only table and remove it after each test."""
    async with database_owner_engine.begin() as connection:
        await connection.execute(text("DROP TABLE IF EXISTS m0_uow_probe"))
        await connection.execute(
            text("CREATE TABLE m0_uow_probe (id integer PRIMARY KEY, value text NOT NULL)")
        )
    try:
        yield database_owner_engine
    finally:
        async with database_owner_engine.begin() as connection:
            await connection.execute(text("DROP TABLE IF EXISTS m0_uow_probe"))


async def _row_count(engine: AsyncEngine) -> int:
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT count(*) FROM m0_uow_probe"))
        return int(result.scalar_one())


async def _write_then_fail(unit_of_work: SqlAlchemyUnitOfWork) -> None:
    async with unit_of_work:
        await unit_of_work.session.execute(
            text("INSERT INTO m0_uow_probe (id, value) VALUES (1, 'failed')")
        )
        msg = "application failure"
        raise RuntimeError(msg)


async def test_explicit_commit_persists_transaction(uow_table: AsyncEngine) -> None:
    """Only an application-level explicit commit should persist work."""
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(uow_table))
    async with unit_of_work:
        await unit_of_work.session.execute(
            text("INSERT INTO m0_uow_probe (id, value) VALUES (1, 'committed')")
        )
        await unit_of_work.commit()

    assert await _row_count(uow_table) == 1


async def test_normal_exit_without_commit_rolls_back(uow_table: AsyncEngine) -> None:
    """A forgotten commit must fail closed through rollback."""
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(uow_table))
    async with unit_of_work:
        await unit_of_work.session.execute(
            text("INSERT INTO m0_uow_probe (id, value) VALUES (1, 'rolled-back')")
        )

    assert await _row_count(uow_table) == 0


async def test_exception_rolls_back_and_propagates(uow_table: AsyncEngine) -> None:
    """Application exceptions must roll back and remain visible to the caller."""
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(uow_table))
    with pytest.raises(RuntimeError, match="application failure"):
        await _write_then_fail(unit_of_work)

    assert await _row_count(uow_table) == 0


async def test_session_and_transaction_guards_are_explicit(uow_table: AsyncEngine) -> None:
    """Inactive/reused units of work must reject ambiguous transaction access."""
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(uow_table))
    with pytest.raises(RuntimeError, match="not active"):
        _ = unit_of_work.session
    async with unit_of_work:
        with pytest.raises(RuntimeError, match="entered twice"):
            await unit_of_work.__aenter__()
        await unit_of_work.rollback()
        with pytest.raises(RuntimeError, match="no active transaction"):
            await unit_of_work.commit()
