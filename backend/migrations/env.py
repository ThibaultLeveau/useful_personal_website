"""PostgreSQL-only Alembic migration environment."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from pydantic import SecretStr
from sqlalchemy import MetaData, pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.api_access import ApiAccessBase
from app.infrastructure.database.audit import AuditBase
from app.infrastructure.database.blog import BlogBase
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.contacts import ContactsBase
from app.infrastructure.database.experiences import ExperiencesBase
from app.infrastructure.database.idempotency import IdempotencyBase
from app.infrastructure.database.identity import IdentityBase
from app.infrastructure.database.media import MediaBase
from app.infrastructure.database.pages import PagesBase
from app.infrastructure.database.projects import ProjectsBase
from app.infrastructure.database.site_configuration import SiteConfigurationBase
from app.infrastructure.database.skills import SkillsBase
from app.infrastructure.rate_limit.persistence import RateLimitBase

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

ALEMBIC_VERSION_TABLE = "alembic_version"
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

alembic_config = context.config
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name, disable_existing_loggers=False)

# Feature metadata is added by dispatched modules. M0 intentionally establishes
# a migration lineage without creating speculative feature tables.
target_metadata = MetaData(naming_convention=NAMING_CONVENTION)
for module_metadata in (
    IdentityBase.metadata,
    RateLimitBase.metadata,
    AuditBase.metadata,
    IdempotencyBase.metadata,
    SiteConfigurationBase.metadata,
    SkillsBase.metadata,
):
    for table in module_metadata.sorted_tables:
        table.to_metadata(target_metadata)

# Experience revisions intentionally reference accepted identity and skills
# tables owned by other registries. Copy them only after those providers exist
# in the combined Alembic metadata; do not sort the isolated feature registry.
for table in ExperiencesBase.metadata.tables.values():
    table.to_metadata(target_metadata)

# Projects consume accepted identity, skill, and experience tables and therefore
# join the combined metadata only after every provider registry is present.
for table in ProjectsBase.metadata.tables.values():
    table.to_metadata(target_metadata)

# Blog relations reference identity and their own post/taxonomy tables, so the M7 registry joins
# only after every accepted provider registry and the project consumer registry are present.
for table in BlogBase.metadata.tables.values():
    table.to_metadata(target_metadata)

# Pages and media join only after every accepted provider and identity table is available.
for feature_metadata in (PagesBase.metadata, MediaBase.metadata):
    for table in feature_metadata.sorted_tables:
        table.to_metadata(target_metadata)

for table in ContactsBase.metadata.sorted_tables:
    table.to_metadata(target_metadata)

for table in ApiAccessBase.metadata.tables.values():
    table.to_metadata(target_metadata)


def _database_url() -> str:
    raw_url = os.environ.get("APP_DATABASE_URL")
    if raw_url is None:
        msg = "APP_DATABASE_URL is required for explicit migration commands"
        raise RuntimeError(msg)
    return DatabaseConfig(url=SecretStr(raw_url)).url.get_secret_value()


def run_migrations_offline() -> None:
    """Render PostgreSQL migration SQL without establishing a connection."""
    context.configure(
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
        literal_binds=True,
        target_metadata=target_metadata,
        transaction_per_migration=True,
        url=_database_url(),
        version_table=ALEMBIC_VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        compare_type=True,
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
        version_table=ALEMBIC_VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_online_migrations() -> None:
    engine = create_async_engine(
        _database_url(),
        echo=False,
        hide_parameters=True,
        poolclass=pool.NullPool,
    )
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run_migrations)
    finally:
        await engine.dispose()


def run_migrations_online() -> None:
    """Apply migrations with a short-lived async PostgreSQL engine."""
    asyncio.run(_run_online_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
