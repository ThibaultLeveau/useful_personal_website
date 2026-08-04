"""Dry-run-first, operator-only bounded audit retention command."""

# ruff: noqa: EM101, EM102, PLR2004, TRY003
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import timedelta

from sqlalchemy import func, select, text

from app.config import Settings
from app.infrastructure.database import DatabaseConfig, create_database_runtime
from app.infrastructure.database.audit import AuditEntryRecord, AuditRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.audit.domain import ActorType, AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7

_OPERATOR_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")
_APPLY_CONFIRMATION = "delete-expired-audit-entries"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Purge expired append-only audit entries.")
    parser.add_argument("--apply", action="store_true", help="apply the reviewed deletion")
    parser.add_argument("--confirm", default="", help="required exact confirmation for --apply")
    parser.add_argument("--operator-id", required=True, help="safe deployment operator identifier")
    parser.add_argument("--retention-days", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=100)
    return parser.parse_args()


async def _run(arguments: argparse.Namespace) -> None:
    settings = Settings()
    operator_url = settings.audit_retention_database_url
    runtime_url = settings.database_url
    if operator_url is None:
        raise RuntimeError("audit retention operator database configuration is required")
    if (
        runtime_url is not None
        and operator_url.get_secret_value() == runtime_url.get_secret_value()
    ):
        raise RuntimeError("audit retention refuses the ordinary runtime credential")
    if _OPERATOR_PATTERN.fullmatch(arguments.operator_id) is None:
        raise RuntimeError("operator-id must be a bounded safe identifier")
    if arguments.apply and arguments.confirm != _APPLY_CONFIRMATION:
        raise RuntimeError(f"--apply requires --confirm {_APPLY_CONFIRMATION}")
    retention_days = arguments.retention_days or settings.audit_retention_days
    if not 30 <= retention_days <= 3650:
        raise RuntimeError("retention-days must be between 30 and 3650")
    batch_size = max(1, min(int(arguments.batch_size), 1000))

    runtime = create_database_runtime(DatabaseConfig(url=operator_url))
    try:
        run_id = uuid7()
        async with SqlAlchemyUnitOfWork(runtime.session_factory) as uow:
            database_now = await uow.session.scalar(select(func.now()))
            if database_now is None:
                raise RuntimeError("database time is unavailable")
            cutoff = database_now - timedelta(days=retention_days)
            eligible = int(
                await uow.session.scalar(
                    select(func.count())
                    .select_from(AuditEntryRecord)
                    .where(AuditEntryRecord.occurred_at < cutoff)
                )
                or 0
            )
            if not arguments.apply:
                output = {
                    "applied": False,
                    "cutoff": cutoff.isoformat(),
                    "eligible": eligible,
                    "retention_days": retention_days,
                    "run_id": str(run_id),
                }
            else:
                deleted = 0
                while True:
                    result = await uow.session.scalar(
                        text("SELECT purge_audit_entries_before(:cutoff, :batch_size)"),
                        {"cutoff": cutoff, "batch_size": batch_size},
                    )
                    count = int(result or 0)
                    deleted += count
                    if count < batch_size:
                        break
                AuditRepository(uow.session).append(
                    AuditEntry(
                        id=uuid7(),
                        event_type="audit.retention_executed",
                        actor_type=ActorType.SYSTEM,
                        actor_id=None,
                        actor_label_snapshot=arguments.operator_id,
                        resource_type="audit_entry",
                        resource_id=None,
                        request_id=f"operation:{run_id}",
                        occurred_at=database_now,
                        outcome=AuditOutcome.SUCCESS,
                        ip_pseudonym=None,
                        metadata={
                            "deleted_count": deleted,
                            "retention_days": retention_days,
                            "run_id": str(run_id),
                        },
                        schema_version=1,
                    )
                )
                await uow.commit()
                output = {
                    "applied": True,
                    "cutoff": cutoff.isoformat(),
                    "deleted": deleted,
                    "retention_days": retention_days,
                    "run_id": str(run_id),
                }
        sys.stdout.write(json.dumps(output, sort_keys=True) + "\n")
    finally:
        await runtime.dispose()


def main() -> None:
    """Run the bounded operator command."""
    asyncio.run(_run(_arguments()))


if __name__ == "__main__":
    main()
