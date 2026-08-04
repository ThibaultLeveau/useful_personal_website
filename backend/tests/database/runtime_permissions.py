"""Least-privilege grants for repository tests that rebuild the schema."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.session import create_database_engine

if TYPE_CHECKING:
    from pydantic import SecretStr


async def reconcile_runtime_permissions(
    owner_url: SecretStr,
    runtime_url: SecretStr,
) -> None:
    """Grant application DML while preserving protected-table restrictions."""
    runtime_user = make_url(runtime_url.get_secret_value()).username
    if runtime_user is None or re.fullmatch(r"[a-z_][a-z0-9_]*", runtime_user) is None:
        msg = "TEST_DATABASE_URL requires a conservative runtime role"
        raise ValueError(msg)
    quoted_user = f'"{runtime_user}"'
    statements = (
        f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {quoted_user}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM {quoted_user}",
        f"GRANT SELECT ON TABLE public.alembic_version TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.audit_entry FROM {quoted_user}",
        f"GRANT SELECT, INSERT ON TABLE public.audit_entry TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {quoted_user}",
    )
    engine = create_database_engine(DatabaseConfig(url=owner_url))
    try:
        async with engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()
