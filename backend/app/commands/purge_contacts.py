"""Dry-run-first bounded contact retention command."""
# ruff: noqa: EM101, TRY003

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.config import Settings
from app.infrastructure.database import DatabaseConfig, create_database_runtime
from app.infrastructure.database.contacts_uow import SqlAlchemyContactUnitOfWorkFactory
from app.modules.contacts.service import ContactConfiguration, ContactService


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Purge expired private contact submissions.")
    parser.add_argument("--apply", action="store_true", help="apply the reviewed deletion")
    parser.add_argument("--retention-days", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=100)
    return parser.parse_args()


async def _run(arguments: argparse.Namespace) -> None:
    settings = Settings()
    if settings.database_url is None or settings.privacy_hmac_key is None:
        raise RuntimeError("database and privacy key configuration are required")
    runtime = create_database_runtime(DatabaseConfig(url=settings.database_url))
    try:
        service = ContactService(
            SqlAlchemyContactUnitOfWorkFactory(runtime.session_factory),
            ContactConfiguration(
                settings.contact_policy_version,
                settings.contact_source,
                settings.contact_minimum_completion_seconds,
                settings.contact_proof_ttl_seconds,
                settings.privacy_hmac_key.get_secret_value().encode(),
                settings.contact_pseudonym_key_version,
            ),
        )
        cutoff, count = await service.purge(
            retention_days=arguments.retention_days or settings.contact_retention_days,
            batch_size=max(1, min(arguments.batch_size, 1000)),
            apply=bool(arguments.apply),
        )
        sys.stdout.write(
            json.dumps(
                {
                    "applied": bool(arguments.apply),
                    "cutoff": cutoff.isoformat(),
                    "deleted_or_eligible": count,
                },
                sort_keys=True,
            )
            + "\n"
        )
    finally:
        await runtime.dispose()


def main() -> None:
    """Run the operator retention command."""
    asyncio.run(_run(_arguments()))


if __name__ == "__main__":
    main()
