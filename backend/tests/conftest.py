"""Shared backend fixtures, including the isolated PostgreSQL contract."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from pydantic import SecretStr

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.session import create_database_engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture(scope="session")
def test_database_url() -> SecretStr:
    """Return the non-owner runtime URL for application/repository tests."""
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if raw_url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    return SecretStr(raw_url)


@pytest.fixture(scope="session")
def test_database_owner_url() -> SecretStr:
    """Return the migration-owner URL for destructive schema fixtures only."""
    raw_url = os.environ.get("TEST_DATABASE_OWNER_URL")
    if raw_url is None:
        pytest.skip("TEST_DATABASE_OWNER_URL is required for PostgreSQL schema tests")
    return SecretStr(raw_url)


@pytest.fixture
async def database_engine(test_database_url: SecretStr) -> AsyncIterator[AsyncEngine]:
    """Yield a short-lived engine against the isolated test database."""
    engine = create_database_engine(
        DatabaseConfig(
            url=test_database_url,
            max_overflow=1,
            pool_size=1,
            pool_timeout_seconds=3,
        )
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def database_owner_engine(
    test_database_owner_url: SecretStr,
) -> AsyncIterator[AsyncEngine]:
    """Yield an owner engine only to tests that intentionally mutate schema metadata."""
    engine = create_database_engine(
        DatabaseConfig(
            url=test_database_owner_url,
            max_overflow=1,
            pool_size=1,
            pool_timeout_seconds=3,
        )
    )
    try:
        yield engine
    finally:
        await engine.dispose()
