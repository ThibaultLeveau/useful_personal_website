"""Safe PostgreSQL connectivity and migration readiness adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.common.health import ReadinessCategory, ReadinessResult
from app.infrastructure.database.revision import database_revision_is_current

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class DatabaseReadinessProbe:
    """Check PostgreSQL connectivity and exact migration compatibility."""

    def __init__(self, engine: AsyncEngine) -> None:
        """Bind the shared application engine without opening a connection."""
        self._engine = engine

    async def check(self) -> ReadinessResult:
        """Return only safe database or migration availability categories."""
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                if not await database_revision_is_current(connection):
                    return ReadinessResult(
                        ready=False,
                        category=ReadinessCategory.MIGRATION,
                    )
        except SQLAlchemyError:
            return ReadinessResult(
                ready=False,
                category=ReadinessCategory.DATABASE,
            )
        return ReadinessResult(ready=True)
