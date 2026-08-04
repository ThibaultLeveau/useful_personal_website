"""Operator-only dry-run-first private media reconciliation command."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict

from app.config import Settings
from app.infrastructure.database import DatabaseConfig, create_database_runtime
from app.infrastructure.database.media_uow import SqlAlchemyMediaUnitOfWorkFactory
from app.infrastructure.storage.media_factory import build_media_storage
from app.modules.media.reconcile import MediaReconciler


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile managed private media objects.")
    parser.add_argument("--apply", action="store_true", help="delete reviewed stable orphans")
    parser.add_argument("--confirm", help="exact apply confirmation token")
    return parser.parse_args()


async def _run(arguments: argparse.Namespace) -> None:
    settings = Settings()
    if settings.database_url is None:
        msg = "APP_DATABASE_URL is required"
        raise RuntimeError(msg)
    storage = build_media_storage(settings)
    if storage is None:
        msg = "explicit media storage configuration is required"
        raise RuntimeError(msg)
    runtime = create_database_runtime(DatabaseConfig(url=settings.database_url))
    try:
        result = await MediaReconciler(
            SqlAlchemyMediaUnitOfWorkFactory(runtime.session_factory), storage
        ).run(apply=bool(arguments.apply), confirmation=arguments.confirm)
        sys.stdout.write(f"{json.dumps(asdict(result), sort_keys=True)}\n")
    finally:
        await runtime.dispose()


def main() -> None:
    """Execute one bounded reconciliation run."""
    asyncio.run(_run(_arguments()))


if __name__ == "__main__":
    main()
