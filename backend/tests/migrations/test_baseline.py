"""Empty/prior-baseline lifecycle tests for the linear M9 Alembic head."""

from __future__ import annotations

import asyncio
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.revision import EXPECTED_DATABASE_REVISION
from app.infrastructure.database.session import create_database_engine

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr

pytestmark = pytest.mark.postgresql
M0_BASE_REVISION = "20260802_0001"
M1_IDENTITY_REVISION = "20260802_0002"
M2_API_REVISION = "20260802_0003"
M3_SITE_REVISION = "20260802_0004"
M4_SKILLS_REVISION = "20260802_0005"
EXPECTED_TABLES = [
    "admin_session",
    "administrator",
    "alembic_version",
    "api_token",
    "api_token_scope",
    "audit_entry",
    "contact_submission",
    "experience",
    "experience_achievement",
    "experience_responsibility",
    "experience_revision",
    "experience_skill",
    "experience_technology",
    "footer",
    "footer_column",
    "footer_item",
    "idempotency_record",
    "media_asset",
    "media_usage",
    "media_variant",
    "navigation_item",
    "navigation_menu",
    "page",
    "page_block",
    "page_block_reference",
    "page_revision",
    "post",
    "post_category",
    "post_category_link",
    "post_revision",
    "post_tag",
    "profile",
    "project",
    "project_experience",
    "project_revision",
    "project_revision_media",
    "project_skill",
    "project_technology",
    "rate_limit_bucket",
    "related_post",
    "related_project",
    "skill",
    "skill_category",
    "tag",
    "website_settings",
]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    return Config(str(BACKEND_ROOT / "alembic.ini"))


@pytest.fixture
def migration_environment(
    monkeypatch: pytest.MonkeyPatch,
    test_database_owner_url: SecretStr,
) -> Iterator[Config]:
    """Bind Alembic to the isolated test DB and reset it to base."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = _alembic_config()
    command.downgrade(config, "base")
    try:
        yield config
    finally:
        command.downgrade(config, "base")


def test_migration_history_has_one_exact_linear_head() -> None:
    """Every accepted milestone must extend the migration history linearly."""
    script = ScriptDirectory.from_config(_alembic_config())

    assert script.get_heads() == [EXPECTED_DATABASE_REVISION]
    assert script.get_base() == M0_BASE_REVISION
    revision_files = sorted(
        path
        for path in (BACKEND_ROOT / "migrations" / "versions").glob("*.py")
        if path.name != "__init__.py"
    )
    assert [path.name for path in revision_files] == [
        "20260802_0001_empty_baseline.py",
        "20260802_0002_identity_auth.py",
        "20260802_0003_api_conventions.py",
        "20260802_0004_site_configuration.py",
        "20260802_0005_skills.py",
        "20260802_0006_experiences.py",
        "20260802_0007_projects.py",
        "20260802_0008_blog.py",
        "20260802_0009_pages_blocks.py",
        "20260802_0010_media.py",
        "20260802_0011_contacts.py",
        "20260802_0012_api_tokens.py",
        "20260802_0013_audit_system.py",
    ]


async def _schema_state(database_url: SecretStr) -> tuple[list[str], str | None]:
    engine = create_database_engine(DatabaseConfig(url=database_url))
    try:
        async with engine.connect() as connection:
            table_result = await connection.execute(
                text(
                    "SELECT tablename FROM pg_catalog.pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            tables = list(table_result.scalars())
            revision_result = await connection.execute(
                text("SELECT version_num FROM alembic_version")
            )
            revision = revision_result.scalar_one_or_none()
    finally:
        await engine.dispose()
    return tables, revision if isinstance(revision, str) else None


def test_empty_database_upgrade_current_schema_and_downgrade(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade from base, inspect current/schema, and return to base."""
    command.upgrade(migration_environment, "head")
    current_stream = StringIO()
    migration_environment.stdout = current_stream
    command.current(migration_environment, verbose=True)
    current_output = current_stream.getvalue()
    tables, revision = asyncio.run(_schema_state(test_database_owner_url))

    assert revision == EXPECTED_DATABASE_REVISION
    assert tables == EXPECTED_TABLES
    assert EXPECTED_DATABASE_REVISION in current_output

    command.check(migration_environment)
    command.downgrade(migration_environment, "base")
    _, revision_after_downgrade = asyncio.run(_schema_state(test_database_owner_url))
    assert revision_after_downgrade is None


def test_prior_baseline_upgrades_to_site_configuration_head(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade an existing M0 baseline without requiring manual schema edits."""
    command.upgrade(migration_environment, M0_BASE_REVISION)
    tables_at_base, revision_at_base = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_base == ["alembic_version"]
    assert revision_at_base == M0_BASE_REVISION

    command.upgrade(migration_environment, "head")
    tables_at_head, revision_at_head = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_head == EXPECTED_TABLES
    assert revision_at_head == EXPECTED_DATABASE_REVISION


def test_prior_identity_revision_upgrades_to_site_configuration_head(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade an accepted M1 database without altering its existing tables."""
    command.upgrade(migration_environment, M1_IDENTITY_REVISION)
    tables_at_identity, revision_at_identity = asyncio.run(_schema_state(test_database_owner_url))

    assert "idempotency_record" not in tables_at_identity
    assert revision_at_identity == M1_IDENTITY_REVISION

    command.upgrade(migration_environment, "head")
    tables_at_head, revision_at_head = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_head == EXPECTED_TABLES
    assert revision_at_head == EXPECTED_DATABASE_REVISION


def test_prior_api_revision_upgrades_to_site_configuration_head(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade the accepted M2 database through the sole M3 revision."""
    command.upgrade(migration_environment, M2_API_REVISION)
    tables_at_api, revision_at_api = asyncio.run(_schema_state(test_database_owner_url))

    assert "profile" not in tables_at_api
    assert revision_at_api == M2_API_REVISION

    command.upgrade(migration_environment, "head")
    tables_at_head, revision_at_head = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_head == EXPECTED_TABLES
    assert revision_at_head == EXPECTED_DATABASE_REVISION


def test_prior_site_revision_upgrades_to_skills_head(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade the accepted M3 database through only the M4 skills revision."""
    command.upgrade(migration_environment, M3_SITE_REVISION)
    tables_at_site, revision_at_site = asyncio.run(_schema_state(test_database_owner_url))

    assert "skill" not in tables_at_site
    assert revision_at_site == M3_SITE_REVISION

    command.upgrade(migration_environment, "head")
    tables_at_head, revision_at_head = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_head == EXPECTED_TABLES
    assert revision_at_head == EXPECTED_DATABASE_REVISION


def test_prior_skills_revision_upgrades_to_experiences_head(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade accepted M4 skills data through only the M5 experience revision."""
    command.upgrade(migration_environment, M4_SKILLS_REVISION)
    tables_at_skills, revision_at_skills = asyncio.run(_schema_state(test_database_owner_url))

    assert "experience" not in tables_at_skills
    assert "skill" in tables_at_skills
    assert revision_at_skills == M4_SKILLS_REVISION

    command.upgrade(migration_environment, "head")
    tables_at_head, revision_at_head = asyncio.run(_schema_state(test_database_owner_url))

    assert tables_at_head == EXPECTED_TABLES
    assert revision_at_head == EXPECTED_DATABASE_REVISION


def test_offline_upgrade_sql_is_deterministic_and_secret_free(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Offline SQL should contain lineage DDL but never the configured URL."""
    command.upgrade(migration_environment, "head", sql=True)
    output = capsys.readouterr().out

    assert "CREATE TABLE alembic_version" in output
    assert EXPECTED_DATABASE_REVISION in output
    assert test_database_owner_url.get_secret_value() not in output
