"""PostgreSQL contract tests for the sole M9 media revision."""

# ruff: noqa: D103

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.revision import EXPECTED_DATABASE_REVISION
from app.infrastructure.database.session import create_database_engine

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncConnection

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
M8_REVISION = "20260802_0009"
M9_REVISION = "20260802_0010"
ADMIN_ID = "0198aa20-0000-7000-8000-000000000001"
READY_ID = "0198aa20-0000-7000-8000-000000000002"
PENDING_ID = "0198aa20-0000-7000-8000-000000000003"
USAGE_ID = "0198aa20-0000-7000-8000-000000000004"


@pytest.fixture
def migration_environment(
    monkeypatch: pytest.MonkeyPatch,
    test_database_owner_url: SecretStr,
) -> Iterator[Config]:
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
            "VALUES (:admin,'m9@example.test','m9@example.test','M9 Admin',"
            "'synthetic-not-a-login-hash',false,true)"
        ),
        {"admin": ADMIN_ID},
    )


async def _insert_asset(connection: AsyncConnection, *, asset_id: str, status: str) -> None:
    ready = status == "ready"
    await connection.execute(
        text(
            "INSERT INTO media_asset "
            "(id,status,display_name,detected_format,width,height,byte_size,checksum_sha256,"
            "original_key,quarantine_key,created_by,created_at,updated_at,version,failure_code,"
            "deleted_at) VALUES (:id,:status,'Synthetic image',:format,:width,:height,:size,"
            ":checksum,:original,:quarantine,:admin,now(),now(),1,NULL,NULL)"
        ),
        {
            "id": asset_id,
            "status": status,
            "format": "jpeg" if ready else None,
            "width": 640 if ready else None,
            "height": 320 if ready else None,
            "size": 512 if ready else 12,
            "checksum": "a" * 64 if ready else "b" * 64,
            "original": f"originals/01/{asset_id}/source.jpg" if ready else None,
            "quarantine": None if ready else f"quarantine/01/{asset_id}/source.bin",
            "admin": ADMIN_ID,
        },
    )


def test_upgrade_from_accepted_m8_enforces_ready_references_and_delete_race(
    migration_environment: Config,
    test_database_owner_url: SecretStr,
) -> None:
    command.upgrade(migration_environment, M8_REVISION)

    async def seed_provider() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _seed_administrator(connection)
        finally:
            await engine.dispose()

    asyncio.run(seed_provider())
    command.upgrade(migration_environment, M9_REVISION)

    async def assert_contract() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await _insert_asset(connection, asset_id=READY_ID, status="ready")
                await _insert_asset(connection, asset_id=PENDING_ID, status="quarantined")
                version = (
                    await connection.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one()
                assert version == M9_REVISION
                profile_id = (
                    await connection.execute(text("SELECT id FROM profile LIMIT 1"))
                ).scalar_one()
                await connection.execute(
                    text("UPDATE profile SET profile_image_id=:asset WHERE id=:profile"),
                    {"asset": READY_ID, "profile": profile_id},
                )

            with pytest.raises((DBAPIError, IntegrityError)):
                async with engine.begin() as connection:
                    await connection.execute(
                        text("UPDATE profile SET profile_image_id=:asset"),
                        {"asset": PENDING_ID},
                    )

            async with engine.begin() as connection:
                profile_id = (
                    await connection.execute(text("SELECT id FROM profile LIMIT 1"))
                ).scalar_one()
                await connection.execute(
                    text(
                        "INSERT INTO media_usage "
                        "(id,asset_id,owner_type,owner_id,role,position,purpose,alt_text,"
                        "caption,focal_x,focal_y,active,public,created_at,updated_at) VALUES "
                        "(:id,:asset,'profile',:owner,'profile_image',0,'meaningful',"
                        "'Portrait of the site owner',NULL,50,50,true,true,now(),now())"
                    ),
                    {
                        "id": USAGE_ID,
                        "asset": READY_ID,
                        "owner": profile_id,
                    },
                )

            with pytest.raises(DBAPIError) as captured:
                async with engine.begin() as connection:
                    await connection.execute(
                        text(
                            "UPDATE media_asset SET status='deleting',deleted_at=now() "
                            "WHERE id=:asset"
                        ),
                        {"asset": READY_ID},
                    )
            assert getattr(captured.value.orig, "sqlstate", None) == "55000"
        finally:
            await engine.dispose()

    asyncio.run(assert_contract())


def test_empty_upgrade_downgrade_and_single_head(
    migration_environment: Config,
) -> None:
    command.upgrade(migration_environment, "head")
    assert ScriptDirectory.from_config(migration_environment).get_heads() == [
        EXPECTED_DATABASE_REVISION
    ]
    command.downgrade(migration_environment, M8_REVISION)
    command.upgrade(migration_environment, M9_REVISION)
