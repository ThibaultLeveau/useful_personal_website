"""PostgreSQL contract tests for the sole M6 projects revision."""

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
M5_REVISION = "20260802_0006"
M6_REVISION = "20260802_0007"
ADMIN_ID = "0198a12c-5000-7000-8000-000000000001"
PROJECT_ID = "0198a12c-5000-7000-8000-000000000002"
REVISION_ID = "0198a12c-5000-7000-8000-000000000003"
SKILL_ID = "0198a12c-5000-7000-8000-000000000004"
EXPERIENCE_ID = "0198a12c-5000-7000-8000-000000000005"
EXPERIENCE_REVISION_ID = "0198a12c-5000-7000-8000-000000000006"


@pytest.fixture
def migration_environment(
    monkeypatch: pytest.MonkeyPatch,
    test_database_owner_url: SecretStr,
) -> Iterator[Config]:
    """Reset the isolated owner database around each migration proof."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    try:
        yield config
    finally:
        command.downgrade(config, "base")


async def _seed_m5_provider_rows(connection: AsyncConnection) -> None:
    await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    await connection.execute(
        text(
            "INSERT INTO administrator "
            "(id,email,email_normalized,display_name,password_hash,must_change_password,is_active) "
            "VALUES (:admin,'m6@example.test','m6@example.test','M6 Admin',"
            "'synthetic-not-a-login-hash',false,true)"
        ),
        {"admin": ADMIN_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO skill_category "
            "(id,name,slug,description,position,created_at,updated_at,version) VALUES "
            "('0198a12c-5000-7000-8000-000000000007','Languages','languages',NULL,"
            "0,now(),now(),1)"
        )
    )
    await connection.execute(
        text(
            "INSERT INTO skill "
            "(id,name,slug,category_id,description,proficiency_label,proficiency_score,"
            "years_experience,icon_key,position,featured,visible,created_at,updated_at,version) "
            "VALUES (:skill,'Python','python','0198a12c-5000-7000-8000-000000000007',"
            "NULL,NULL,90,8.00,'python',0,true,true,now(),now(),1)"
        ),
        {"skill": SKILL_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO experience "
            "(id,visible,position,draft_revision_id,published_revision_id,publish_at,"
            "unpublished_at,created_at,updated_at,version,deleted_at) VALUES "
            "(:experience,true,0,:revision,NULL,NULL,NULL,now(),now(),1,NULL)"
        ),
        {"experience": EXPERIENCE_ID, "revision": EXPERIENCE_REVISION_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO experience_revision "
            "(id,experience_id,revision_number,based_on_revision_id,company_name,company_url,"
            "role_title,employment_type,location,remote_status,start_date,end_date,"
            "current_position,short_summary,detailed_description,frozen,created_by,"
            "created_at,updated_at) VALUES (:revision,:experience,1,NULL,'Example',NULL,"
            "'Engineer','full_time',NULL,'remote',DATE '2025-01-01',NULL,true,'Summary',"
            "NULL,false,:admin,now(),now())"
        ),
        {
            "revision": EXPERIENCE_REVISION_ID,
            "experience": EXPERIENCE_ID,
            "admin": ADMIN_ID,
        },
    )


async def _seed_project(connection: AsyncConnection) -> None:
    await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    await connection.execute(
        text(
            "INSERT INTO project "
            "(id,slug,visible,featured,position,draft_revision_id,published_revision_id,"
            "publish_at,unpublished_at,created_at,updated_at,version,deleted_at) VALUES "
            "(:project,'api-platform',true,true,0,:revision,NULL,NULL,NULL,now(),now(),1,NULL)"
        ),
        {"project": PROJECT_ID, "revision": REVISION_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO project_revision "
            "(id,project_id,revision_number,based_on_revision_id,name,short_description,"
            "full_description,problem,solution,impact,owner_role,architecture,status,"
            "start_date,end_date,repository_url,demo_url,seo_title,seo_description,"
            "canonical_url,frozen,created_by,created_at,updated_at) VALUES "
            "(:revision,:project,1,NULL,'API Platform','Secure API platform.','Full case study.',"
            "'Problem.','Solution.','Impact.','Lead','Architecture.','active',DATE '2025-01-01',"
            "NULL,'https://example.test/repository','https://example.test/demo',NULL,NULL,NULL,"
            "false,:admin,now(),now())"
        ),
        {"revision": REVISION_ID, "project": PROJECT_ID, "admin": ADMIN_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO project_skill (id,revision_id,skill_id,position) VALUES "
            "('0198a12c-5000-7000-8000-000000000008',:revision,:skill,0)"
        ),
        {"revision": REVISION_ID, "skill": SKILL_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO project_experience (id,revision_id,experience_id,position) VALUES "
            "('0198a12c-5000-7000-8000-000000000009',:revision,:experience,0)"
        ),
        {"revision": REVISION_ID, "experience": EXPERIENCE_ID},
    )


def test_upgrade_from_accepted_0006_preserves_providers_and_enforces_boundaries(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade representative M5 data and prove project integrity constraints."""
    command.upgrade(migration_environment, M5_REVISION)

    async def arrange() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_m5_provider_rows(connection)
        finally:
            await engine.dispose()

    asyncio.run(arrange())
    command.upgrade(migration_environment, M6_REVISION)

    async def assert_contract() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.connect() as connection:
                async with connection.begin():
                    await _seed_project(connection)
                revision = (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one()
                assert revision == M6_REVISION
                assert (
                    await connection.execute(text("SELECT count(*) FROM project_skill"))
                ).scalar_one() == 1
                technology_index = (
                    await connection.execute(
                        text(
                            "SELECT indexdef FROM pg_indexes "
                            "WHERE schemaname='public' "
                            "AND indexname='ix_project_technology_value_revision'"
                        )
                    )
                ).scalar_one()
                assert "lower((value)::text)" in technology_index
                assert "revision_id" in technology_index
                await connection.rollback()
                with pytest.raises(IntegrityError):
                    async with connection.begin():
                        await connection.execute(
                            text(
                                "INSERT INTO related_project "
                                "(id,revision_id,project_id,related_project_id,position) VALUES "
                                "('0198a12c-5000-7000-8000-000000000010',:revision,"
                                ":project,:project,0)"
                            ),
                            {"revision": REVISION_ID, "project": PROJECT_ID},
                        )
                async with connection.begin():
                    await connection.execute(
                        text("UPDATE project_revision SET frozen=true WHERE id=:revision"),
                        {"revision": REVISION_ID},
                    )
                with pytest.raises(DBAPIError):
                    async with connection.begin():
                        await connection.execute(
                            text("UPDATE project_revision SET name='Changed' WHERE id=:revision"),
                            {"revision": REVISION_ID},
                        )
        finally:
            await engine.dispose()

    asyncio.run(assert_contract())
    command.upgrade(migration_environment, "head")
    command.check(migration_environment)
