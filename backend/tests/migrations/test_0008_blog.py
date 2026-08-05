"""PostgreSQL contract tests for the sole M7 blog revision."""

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
M6_REVISION = "20260802_0007"
M7_REVISION = "20260802_0008"
ADMIN_ID = "0198a12c-6000-7000-8000-000000000001"
POST_ID = "0198a12c-6000-7000-8000-000000000002"
REVISION_ID = "0198a12c-6000-7000-8000-000000000003"
TAG_ID = "0198a12c-6000-7000-8000-000000000004"
POST_TAG_ID = "0198a12c-6000-7000-8000-000000000005"


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


async def _seed_provider(connection: AsyncConnection) -> None:
    await connection.execute(
        text(
            "INSERT INTO administrator "
            "(id,email,email_normalized,display_name,password_hash,must_change_password,is_active) "
            "VALUES (:admin,'m7@example.test','m7@example.test','M7 Admin',"
            "'synthetic-not-a-login-hash',false,true)"
        ),
        {"admin": ADMIN_ID},
    )


async def _seed_post(connection: AsyncConnection) -> None:
    await connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    await connection.execute(
        text(
            "INSERT INTO tag "
            "(id,name,slug,position,visible,created_at,updated_at,version,deleted_at) "
            "VALUES (:tag,'Engineering','engineering',0,true,now(),now(),1,NULL)"
        ),
        {"tag": TAG_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO post "
            "(id,slug,visible,position,draft_revision_id,published_revision_id,publish_at,"
            "unpublished_at,created_at,updated_at,version,deleted_at) VALUES "
            "(:post,'safe-publishing',true,0,:revision,NULL,NULL,NULL,now(),now(),1,NULL)"
        ),
        {"post": POST_ID, "revision": REVISION_ID},
    )
    await connection.execute(
        text(
            "INSERT INTO post_revision "
            "(id,post_id,revision_number,based_on_revision_id,title,excerpt,source,"
            "author_display,reading_minutes,content_checksum,content_policy_name,"
            "content_policy_version,seo_title,seo_description,canonical_url,frozen,"
            "created_by,created_at,updated_at) VALUES "
            "(:revision,:post,1,NULL,'Safe publishing','An immutable article.',"
            "'## Safe publishing', 'Site owner',1,"
            "'0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',"
            "'upw-commonmark','1.0.0',NULL,NULL,NULL,false,:admin,now(),now())"
        ),
        {"revision": REVISION_ID, "post": POST_ID, "admin": ADMIN_ID},
    )
    await connection.execute(
        text("INSERT INTO post_tag (id,revision_id,tag_id,position) VALUES (:id,:revision,:tag,0)"),
        {"id": POST_TAG_ID, "revision": REVISION_ID, "tag": TAG_ID},
    )


def test_upgrade_from_accepted_0007_and_frozen_revision_guards(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """Upgrade M6 data and prove pointers, identity, relations, and immutability."""
    command.upgrade(migration_environment, M6_REVISION)

    async def arrange() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_provider(connection)
        finally:
            await engine.dispose()

    asyncio.run(arrange())
    command.upgrade(migration_environment, M7_REVISION)

    async def assert_contract() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.connect() as connection:
                async with connection.begin():
                    await _seed_post(connection)
                assert (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one() == M7_REVISION
                await connection.rollback()
                with pytest.raises(IntegrityError):
                    async with connection.begin():
                        await connection.execute(
                            text(
                                "INSERT INTO related_post "
                                "(id,revision_id,post_id,related_post_id,position) VALUES "
                                "('0198a12c-6000-7000-8000-000000000006',:revision,"
                                ":post,:post,0)"
                            ),
                            {"revision": REVISION_ID, "post": POST_ID},
                        )
                async with connection.begin():
                    await connection.execute(
                        text("UPDATE post_revision SET frozen=true WHERE id=:revision"),
                        {"revision": REVISION_ID},
                    )
                for statement in (
                    "UPDATE post_revision SET title='Changed' WHERE id=:revision",
                    "DELETE FROM post_tag WHERE revision_id=:revision",
                ):
                    with pytest.raises(DBAPIError):
                        async with connection.begin():
                            await connection.execute(text(statement), {"revision": REVISION_ID})
        finally:
            await engine.dispose()

    asyncio.run(assert_contract())
    command.upgrade(migration_environment, "head")
    command.check(migration_environment)


def test_empty_upgrade_has_one_current_head_and_case_insensitive_identities(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    """A clean database reaches one head and expression indexes reject case variants."""
    command.upgrade(migration_environment, "head")

    async def assert_contract() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_provider(connection)
                await _seed_post(connection)
            async with engine.connect() as connection:
                with pytest.raises(IntegrityError):
                    async with connection.begin():
                        await connection.execute(
                            text(
                                "INSERT INTO tag "
                                "(id,name,slug,position,visible,created_at,updated_at,version) "
                                "VALUES ('0198a12c-6000-7000-8000-000000000007',"
                                "'Duplicate','ENGINEERING',1,true,now(),now(),1)"
                            )
                        )
        finally:
            await engine.dispose()

    asyncio.run(assert_contract())
    command.check(migration_environment)
