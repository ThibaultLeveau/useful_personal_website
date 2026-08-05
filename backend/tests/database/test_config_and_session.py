"""Tests for PostgreSQL-only configuration and engine/session construction."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.session import create_database_engine, create_session_factory


def test_database_config_rejects_non_postgresql_and_invalid_pool_values() -> None:
    """SQLite and invalid pool bounds must never enter the runtime path."""
    with pytest.raises(ValueError, match=r"postgresql\+asyncpg"):
        DatabaseConfig(url=SecretStr("sqlite+aiosqlite:///local.db"))
    with pytest.raises(ValueError, match="name a database"):
        DatabaseConfig(url=SecretStr("postgresql+asyncpg://app:value@db/"))
    with pytest.raises(ValueError, match="pool_size"):
        DatabaseConfig(
            url=SecretStr("postgresql+asyncpg://app:value@db/portfolio"),
            pool_size=0,
        )
    with pytest.raises(ValueError, match="max_overflow"):
        DatabaseConfig(
            url=SecretStr("postgresql+asyncpg://app:value@db/portfolio"),
            max_overflow=-1,
        )
    with pytest.raises(ValueError, match="timeout"):
        DatabaseConfig(
            url=SecretStr("postgresql+asyncpg://app:value@db/portfolio"),
            pool_timeout_seconds=0,
        )


def test_engine_and_session_factory_are_async_postgresql_and_secret_safe() -> None:
    """The factory must select asyncpg without exposing its password in repr."""
    password = "private-database-value"
    config = DatabaseConfig(
        url=SecretStr(f"postgresql+asyncpg://portfolio_app:{password}@db/portfolio")
    )
    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)

    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "asyncpg"
        assert password not in repr(engine.url)
        assert session_factory.kw["autoflush"] is False
        assert session_factory.kw["expire_on_commit"] is False
    finally:
        engine.sync_engine.dispose(close=False)
