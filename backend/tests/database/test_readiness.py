"""PostgreSQL connectivity, revision, and FastAPI readiness tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.common.health import ReadinessCategory
from app.config import Environment, Settings
from app.infrastructure.database.readiness import DatabaseReadinessProbe
from app.infrastructure.database.revision import EXPECTED_DATABASE_REVISION
from app.main import create_app
from tests.database.runtime_permissions import reconcile_runtime_permissions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncEngine

    from app.infrastructure.database.runtime import DatabaseRuntime

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    return Config(str(BACKEND_ROOT / "alembic.ini"))


@pytest.fixture
def migrated_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[SecretStr]:
    """Upgrade the isolated database and return it to base afterward."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    command.downgrade(_alembic_config(), "base")
    command.upgrade(_alembic_config(), "head")
    asyncio.run(reconcile_runtime_permissions(test_database_owner_url, test_database_url))
    try:
        yield test_database_url
    finally:
        command.downgrade(_alembic_config(), "base")


async def test_probe_reports_ready_at_exact_head(
    database_engine: AsyncEngine,
    migrated_database: SecretStr,
) -> None:
    """A connected database at the frozen revision should be ready."""
    del migrated_database
    result = await DatabaseReadinessProbe(database_engine).check()

    assert result.ready is True
    assert result.category is None


async def test_probe_reports_safe_migration_category_for_revision_mismatch(
    database_engine: AsyncEngine,
    database_owner_engine: AsyncEngine,
    migrated_database: SecretStr,
) -> None:
    """A reachable but incompatible revision must not be reported as ready."""
    del migrated_database
    async with database_owner_engine.begin() as connection:
        await connection.execute(text("UPDATE alembic_version SET version_num = 'unexpected_head'"))

    try:
        result = await DatabaseReadinessProbe(database_engine).check()

        assert result.ready is False
        assert result.category is ReadinessCategory.MIGRATION
    finally:
        async with database_owner_engine.begin() as connection:
            await connection.execute(
                text("UPDATE alembic_version SET version_num = :revision"),
                {"revision": EXPECTED_DATABASE_REVISION},
            )


async def test_default_app_wires_database_probe_without_exposing_url(
    migrated_database: SecretStr,
) -> None:
    """The default factory should use the database probe when a URL is configured."""
    settings = Settings(
        environment=Environment.TEST,
        database_url=migrated_database,
    )
    application = create_app(settings=settings)
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    runtime = cast("DatabaseRuntime", application.state.database_runtime)
    await runtime.dispose()
    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ready"}
    assert migrated_database.get_secret_value() not in response.text
