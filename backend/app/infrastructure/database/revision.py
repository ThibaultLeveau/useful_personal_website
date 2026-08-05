"""Runtime migration revision compatibility check."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

EXPECTED_DATABASE_REVISION = "20260802_0013"


async def current_database_revision(connection: AsyncConnection) -> str | None:
    """Read Alembic's current revision without exposing connection details."""
    try:
        result = await connection.execute(text("SELECT version_num FROM alembic_version"))
        revision = result.scalar_one_or_none()
    except SQLAlchemyError:
        return None
    return revision if isinstance(revision, str) else None


async def database_revision_is_current(connection: AsyncConnection) -> bool:
    """Return whether the database exactly matches the supported single head."""
    return await current_database_revision(connection) == EXPECTED_DATABASE_REVISION
