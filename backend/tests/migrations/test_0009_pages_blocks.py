"""PostgreSQL contract tests for the sole M8 page/block revision."""

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
M7_REVISION = "20260802_0008"
M8_REVISION = "20260802_0009"
ADMIN_ID = "0198a13d-8200-7000-8000-000000000001"
PAGE_ID = "0198a13d-8200-7000-8000-000000000002"
REVISION_ID = "0198a13d-8200-7000-8000-000000000003"
BLOCK_ID = "0198a13d-8200-7000-8000-000000000004"
REFERENCE_ID = "0198a13d-8200-7000-8000-000000000005"


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


async def _seed_administrator(connection: AsyncConnection) -> None:
    await connection.execute(
        text(
            "INSERT INTO administrator "
            "(id,email,email_normalized,display_name,password_hash,must_change_password,is_active) "
            "VALUES (:admin,'m8@example.test','m8@example.test','M8 Admin',"
            "'synthetic-not-a-login-hash',false,true)"
        ),
        {"admin": ADMIN_ID},
    )


async def _seed_page_tree(connection: AsyncConnection) -> None:
    await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    await connection.execute(
        text(
            "INSERT INTO page "
            "(id,route_kind,slug,visible,navigation_visible,position,draft_revision_id,"
            "published_revision_id,publish_at,unpublished_at,created_at,updated_at,version,"
            "deleted_at) VALUES (:page,'custom','selected-work',true,true,0,:revision,NULL,"
            "NULL,NULL,now(),now(),1,NULL)"
        ),
        {"page": PAGE_ID, "revision": REVISION_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO page_revision "
            "(id,page_id,revision_number,based_on_revision_id,title,description,seo_title,"
            "seo_description,canonical_url,frozen,created_by,created_at,updated_at) VALUES "
            "(:revision,:page,1,NULL,'Selected work','Evidence over claims.',NULL,NULL,NULL,"
            "false,:admin,now(),now())"
        ),
        {"revision": REVISION_ID, "page": PAGE_ID, "admin": ADMIN_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO page_block "
            "(id,revision_id,block_type,schema_version,position,visible,title,subtitle,"
            "description,theme,layout,responsive,config,created_at,updated_at) VALUES "
            "(:block,:revision,'hero',1,0,true,NULL,NULL,NULL,'default','contained',"
            "CAST(:responsive AS jsonb),CAST(:config AS jsonb),"
            "now(),now())"
        ),
        {
            "block": BLOCK_ID,
            "revision": REVISION_ID,
            "responsive": ('{"hide_on_small":false,"hide_on_large":false,"density":"comfortable"}'),
            "config": '{"heading":"Selected work","body":"Evidence over claims."}',
        },
    )


def test_upgrade_from_accepted_0008_preserves_provider_data_and_enforces_shape(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade from M7 and prove identity, JSON, order, and ownership constraints."""
    command.upgrade(migration_environment, M7_REVISION)

    async def arrange() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_administrator(connection)
        finally:
            await engine.dispose()

    asyncio.run(arrange())
    command.upgrade(migration_environment, M8_REVISION)

    async def assert_contract() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_page_tree(connection)
                version = (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one()
                assert version == M8_REVISION
                count = (
                    await connection.execute(
                        text("SELECT count(*) FROM administrator WHERE id=:id"),
                        {"id": ADMIN_ID},
                    )
                ).scalar_one()
                assert count == 1

            invalid_statements: tuple[tuple[str, dict[str, str]], ...] = (
                (
                    (
                        "INSERT INTO page (id,route_kind,slug,visible,navigation_visible,position,"
                        "draft_revision_id,published_revision_id,publish_at,created_at,updated_at,"
                        "version) VALUES (gen_random_uuid(),'custom','admin',true,false,1,"
                        "gen_random_uuid(),NULL,NULL,now(),now(),1)"
                    ),
                    {},
                ),
                (
                    (
                        "INSERT INTO page_block (id,revision_id,block_type,schema_version,position,"
                        "visible,theme,layout,responsive,config,created_at,updated_at) VALUES "
                        "(gen_random_uuid(),:revision,'attacker',1,1,true,'default','contained',"
                        "'{}'::jsonb,'{}'::jsonb,now(),now())"
                    ),
                    {"revision": REVISION_ID},
                ),
                (
                    (
                        "INSERT INTO page_block (id,revision_id,block_type,schema_version,position,"
                        "visible,theme,layout,responsive,config,created_at,updated_at) VALUES "
                        "(gen_random_uuid(),:revision,'divider',1,0,true,'default','contained',"
                        "'{}'::jsonb,'{}'::jsonb,now(),now())"
                    ),
                    {"revision": REVISION_ID},
                ),
            )
            for statement, parameters in invalid_statements:
                with pytest.raises((DBAPIError, IntegrityError)):
                    async with engine.begin() as connection:
                        await connection.execute(text(statement), parameters)
        finally:
            await engine.dispose()

    asyncio.run(assert_contract())


def test_empty_upgrade_one_head_and_frozen_parent_child_rejection(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Fresh M8 schema rejects every frozen parent/child mutation direction."""
    command.upgrade(migration_environment, M8_REVISION)

    async def assert_guards() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_administrator(connection)
                await _seed_page_tree(connection)
                await connection.execute(
                    text("UPDATE page_revision SET frozen=true WHERE id=:revision"),
                    {"revision": REVISION_ID},
                )
            statements = (
                "UPDATE page_revision SET title='Mutated' WHERE id=:revision",
                "UPDATE page_block SET title='Mutated' WHERE id=:block",
                "DELETE FROM page_block WHERE id=:block",
                (
                    "INSERT INTO page_block_reference "
                    "(id,revision_id,block_id,reference_kind,target_id,role,position,required) "
                    "VALUES (:reference,:revision,:block,'media',gen_random_uuid(),"
                    "'media_primary',0,true)"
                ),
            )
            parameters = {
                "revision": REVISION_ID,
                "block": BLOCK_ID,
                "reference": REFERENCE_ID,
            }
            for statement in statements:
                with pytest.raises(DBAPIError) as captured:
                    async with engine.begin() as connection:
                        await connection.execute(text(statement), parameters)
                assert getattr(captured.value.orig, "sqlstate", None) == "55000"
        finally:
            await engine.dispose()

    asyncio.run(assert_guards())
