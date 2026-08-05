"""PostgreSQL contract tests for the sole M5 experience revision."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.session import create_database_engine

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncConnection

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
M4_REVISION = "20260802_0005"
M5_REVISION = "20260802_0006"
ADMIN_ID = "0198a12c-2000-7000-8000-000000000001"
SKILL_ID = "0198a12c-2000-7000-8000-000000000002"
EXPERIENCE_ID = "0198a12c-2000-7000-8000-000000000003"
REVISION_ID = "0198a12c-2000-7000-8000-000000000004"
CHILD_ID = "0198a12c-2000-7000-8000-000000000005"
OTHER_EXPERIENCE_ID = "0198a12c-2000-7000-8000-000000000006"
OTHER_REVISION_ID = "0198a12c-2000-7000-8000-000000000007"


def _config() -> Config:
    return Config(str(BACKEND_ROOT / "alembic.ini"))


@pytest.fixture
def migration_environment(
    monkeypatch: pytest.MonkeyPatch,
    test_database_owner_url: SecretStr,
) -> Iterator[Config]:
    """Reset the isolated owner database around each destructive migration test."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = _config()
    command.downgrade(config, "base")
    try:
        yield config
    finally:
        command.downgrade(config, "base")


async def _seed_provider_rows(connection: AsyncConnection) -> None:
    await connection.execute(
        text(
            "INSERT INTO administrator "
            "(id, email, email_normalized, display_name, password_hash, "
            "must_change_password, is_active) VALUES "
            "(:id, 'm5-admin@example.test', 'm5-admin@example.test', "
            "'M5 Admin', 'synthetic-not-a-login-hash', false, true)"
        ),
        {"id": ADMIN_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO skill_category "
            "(id, name, slug, description, position, created_at, updated_at, version) "
            "VALUES ('0198a12c-2000-7000-8000-000000000008', 'Languages', "
            "'languages', NULL, 0, now(), now(), 1)"
        )
    )
    await connection.execute(
        text(
            "INSERT INTO skill "
            "(id, name, slug, category_id, description, proficiency_label, "
            "proficiency_score, years_experience, icon_key, position, featured, "
            "visible, created_at, updated_at, version) VALUES "
            "(:id, 'Python', 'python', "
            "'0198a12c-2000-7000-8000-000000000008', NULL, NULL, 90, 8.00, "
            "'python', 0, true, true, now(), now(), 1)"
        ),
        {"id": SKILL_ID},
    )


async def _seed_experience(
    connection: AsyncConnection,
    *,
    experience_id: str = EXPERIENCE_ID,
    revision_id: str = REVISION_ID,
) -> None:
    await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    await connection.execute(
        text(
            "INSERT INTO experience "
            "(id, visible, position, draft_revision_id, published_revision_id, "
            "publish_at, unpublished_at, created_at, updated_at, version, deleted_at) "
            "VALUES (:experience_id, true, 0, :revision_id, NULL, NULL, NULL, "
            "now(), now(), 1, NULL)"
        ),
        {"experience_id": experience_id, "revision_id": revision_id},
    )
    await connection.execute(
        text(
            "INSERT INTO experience_revision "
            "(id, experience_id, revision_number, based_on_revision_id, company_name, "
            "company_url, role_title, employment_type, location, remote_status, "
            "start_date, end_date, current_position, short_summary, detailed_description, "
            "frozen, created_by, created_at, updated_at) VALUES "
            "(:revision_id, :experience_id, 1, NULL, 'Example Studio', "
            "'https://example.test', 'Staff Engineer', 'full_time', 'Paris', 'hybrid', "
            "DATE '2024-01-01', NULL, true, 'Led the platform team.', 'Plain text.', "
            "false, :admin_id, now(), now())"
        ),
        {
            "revision_id": revision_id,
            "experience_id": experience_id,
            "admin_id": ADMIN_ID,
        },
    )


async def _corrupt_pointer(connection: AsyncConnection) -> None:
    async with connection.begin():
        await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        await connection.execute(
            text(
                "UPDATE experience SET draft_revision_id=:foreign_revision WHERE id=:experience_id"
            ),
            {
                "foreign_revision": OTHER_REVISION_ID,
                "experience_id": EXPERIENCE_ID,
            },
        )


def test_upgrade_from_accepted_0005_preserves_provider_data_and_matches_models(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade representative M4 data through exactly one M5 revision."""
    command.upgrade(migration_environment, M4_REVISION)

    async def arrange() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_provider_rows(connection)
        finally:
            await engine.dispose()

    asyncio.run(arrange())
    command.upgrade(migration_environment, M5_REVISION)

    async def inspect() -> tuple[str, int, int, list[str]]:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.connect() as connection:
                revision = (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one()
                skills = (await connection.execute(text("SELECT count(*) FROM skill"))).scalar_one()
                experiences = (
                    await connection.execute(text("SELECT count(*) FROM experience"))
                ).scalar_one()
                indexes = list(
                    (
                        await connection.execute(
                            text(
                                "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
                                "AND tablename LIKE 'experience%' ORDER BY indexname"
                            )
                        )
                    ).scalars()
                )
        finally:
            await engine.dispose()
        return str(revision), int(skills), int(experiences), indexes

    revision, skills, experiences, indexes = asyncio.run(inspect())
    assert (revision, skills, experiences) == (M5_REVISION, 1, 0)
    assert "ix_experience_effective_public" in indexes
    assert "ix_experience_revision_chronology" in indexes
    assert "ix_experience_skill_skill_revision" in indexes
    # Head-level model parity is asserted by the current milestone after 0007;
    # this historical proof intentionally stops at the accepted M5 revision.


def test_same_aggregate_pointers_and_date_catalog_constraints_are_enforced(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Migrated PostgreSQL rejects pointer corruption and invalid content rows."""
    command.upgrade(migration_environment, M5_REVISION)

    async def assert_constraints() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.connect() as connection:
                async with connection.begin():
                    await _seed_provider_rows(connection)
                    await _seed_experience(connection)
                    await _seed_experience(
                        connection,
                        experience_id=OTHER_EXPERIENCE_ID,
                        revision_id=OTHER_REVISION_ID,
                    )

                with pytest.raises(IntegrityError):
                    await _corrupt_pointer(connection)

                invalid_statements = (
                    (
                        "INSERT INTO experience_revision "
                        "(id, experience_id, revision_number, based_on_revision_id, "
                        "company_name, company_url, role_title, employment_type, location, "
                        "remote_status, start_date, end_date, current_position, short_summary, "
                        "detailed_description, frozen, created_by, created_at, updated_at) "
                        "VALUES ('0198a12c-2000-7000-8000-000000000010', :experience_id, 2, "
                        "NULL, 'Company', NULL, 'Role', 'unknown', NULL, 'remote', "
                        "DATE '2025-01-02', NULL, false, 'Summary', NULL, false, :admin_id, "
                        "now(), now())"
                    ),
                    (
                        "INSERT INTO experience_revision "
                        "(id, experience_id, revision_number, based_on_revision_id, "
                        "company_name, company_url, role_title, employment_type, location, "
                        "remote_status, start_date, end_date, current_position, short_summary, "
                        "detailed_description, frozen, created_by, created_at, updated_at) "
                        "VALUES ('0198a12c-2000-7000-8000-000000000011', :experience_id, 2, "
                        "NULL, 'Company', NULL, 'Role', 'contract', NULL, 'remote', "
                        "DATE '2025-01-02', DATE '2025-01-01', false, 'Summary', NULL, false, "
                        ":admin_id, now(), now())"
                    ),
                    (
                        "INSERT INTO experience_revision "
                        "(id, experience_id, revision_number, based_on_revision_id, "
                        "company_name, company_url, role_title, employment_type, location, "
                        "remote_status, start_date, end_date, current_position, short_summary, "
                        "detailed_description, frozen, created_by, created_at, updated_at) "
                        "VALUES ('0198a12c-2000-7000-8000-000000000012', :experience_id, 2, "
                        "NULL, 'Company', NULL, 'Role', 'contract', NULL, 'remote', "
                        "DATE '2025-01-01', DATE '2025-01-02', true, 'Summary', NULL, false, "
                        ":admin_id, now(), now())"
                    ),
                )
                for statement in invalid_statements:
                    with pytest.raises(IntegrityError):
                        async with connection.begin():
                            await connection.execute(
                                text(statement),
                                {"experience_id": EXPERIENCE_ID, "admin_id": ADMIN_ID},
                            )
        finally:
            await engine.dispose()

    asyncio.run(assert_constraints())


def test_frozen_revision_and_owned_rows_reject_update_and_delete(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """The database reinforces immutable published revision content and relations."""
    command.upgrade(migration_environment, M5_REVISION)

    async def assert_immutable() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.connect() as connection:
                async with connection.begin():
                    await _seed_provider_rows(connection)
                    await _seed_experience(connection)
                    await connection.execute(
                        text(
                            "INSERT INTO experience_responsibility "
                            "(id, revision_id, position, value) VALUES "
                            "(:child_id, :revision_id, 0, 'Original responsibility')"
                        ),
                        {"child_id": CHILD_ID, "revision_id": REVISION_ID},
                    )
                    await connection.execute(
                        text(
                            "INSERT INTO experience_skill "
                            "(id, revision_id, skill_id, position) VALUES "
                            "('0198a12c-2000-7000-8000-000000000013', :revision_id, "
                            ":skill_id, 0)"
                        ),
                        {"revision_id": REVISION_ID, "skill_id": SKILL_ID},
                    )
                    await connection.execute(
                        text("UPDATE experience_revision SET frozen=true WHERE id=:revision_id"),
                        {"revision_id": REVISION_ID},
                    )

                frozen = (
                    await connection.execute(
                        text("SELECT frozen FROM experience_revision WHERE id=:revision_id"),
                        {"revision_id": REVISION_ID},
                    )
                ).scalar_one()
                assert frozen is True
                await connection.rollback()

                attempts = (
                    (
                        "UPDATE experience_revision SET role_title='Changed' WHERE id=:id",
                        REVISION_ID,
                    ),
                    ("DELETE FROM experience_revision WHERE id=:id", REVISION_ID),
                    (
                        "UPDATE experience_responsibility SET value='Changed' WHERE id=:id",
                        CHILD_ID,
                    ),
                    ("DELETE FROM experience_responsibility WHERE id=:id", CHILD_ID),
                    (
                        "DELETE FROM experience_skill WHERE id=:id",
                        "0198a12c-2000-7000-8000-000000000013",
                    ),
                )
                for statement, identifier in attempts:
                    with pytest.raises(DBAPIError) as caught:
                        async with connection.begin():
                            await connection.execute(text(statement), {"id": identifier})
                    assert "frozen experience revisions are immutable" in str(caught.value)
        finally:
            await engine.dispose()

    asyncio.run(assert_immutable())
