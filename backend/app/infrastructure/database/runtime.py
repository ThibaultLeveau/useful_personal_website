"""Composition of the shared engine, sessions, and readiness adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.infrastructure.database.readiness import DatabaseReadinessProbe
from app.infrastructure.database.session import create_database_engine, create_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from app.infrastructure.database.config import DatabaseConfig
    from app.infrastructure.database.session import AsyncSessionFactory


@dataclass(frozen=True, slots=True)
class DatabaseRuntime:
    """Shared database process resources."""

    engine: AsyncEngine
    session_factory: AsyncSessionFactory
    readiness_probe: DatabaseReadinessProbe

    async def dispose(self) -> None:
        """Close engine pool resources at application shutdown."""
        await self.engine.dispose()


def create_database_runtime(config: DatabaseConfig) -> DatabaseRuntime:
    """Build one engine shared by sessions and readiness checks."""
    engine = create_database_engine(config)
    return DatabaseRuntime(
        engine=engine,
        session_factory=create_session_factory(engine),
        readiness_probe=DatabaseReadinessProbe(engine),
    )
