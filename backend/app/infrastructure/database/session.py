"""Async SQLAlchemy engine and session-factory construction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from app.infrastructure.database.config import DatabaseConfig

type AsyncSessionFactory = async_sessionmaker[AsyncSession]


def create_database_engine(config: DatabaseConfig) -> AsyncEngine:
    """Create a PostgreSQL-only engine that never logs bound parameters."""
    return create_async_engine(
        config.url.get_secret_value(),
        echo=False,
        hide_parameters=True,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,
        pool_recycle=config.pool_recycle_seconds,
        pool_size=config.pool_size,
        pool_timeout=config.pool_timeout_seconds,
    )


def create_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    """Create non-expiring sessions; transaction completion belongs to the UoW."""
    return async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
