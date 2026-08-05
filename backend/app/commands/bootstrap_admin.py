"""Explicit, noninteractive, takeover-safe administrator bootstrap CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import TYPE_CHECKING

from pydantic import SecretStr

from app.infrastructure.database import DatabaseConfig, create_database_runtime
from app.infrastructure.database.identity_uow import SqlAlchemyIdentityUnitOfWorkFactory
from app.modules.identity.service import BootstrapAlreadyCompletedError, BootstrapService

if TYPE_CHECKING:
    from collections.abc import Sequence

EXIT_ALREADY_BOOTSTRAPPED = 3
EXIT_INVALID_INPUT = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the initial administrator exactly once; never seed content.",
    )
    parser.add_argument("--email", default=os.environ.get("APP_BOOTSTRAP_ADMIN_EMAIL"))
    parser.add_argument(
        "--display-name",
        default=os.environ.get("APP_BOOTSTRAP_ADMIN_DISPLAY_NAME"),
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read the password from standard input instead of the environment.",
    )
    return parser


async def _bootstrap(arguments: argparse.Namespace) -> int:
    database_url = os.environ.get("APP_DATABASE_URL")
    if not database_url or not arguments.email or not arguments.display_name:
        sys.stderr.write("APP_DATABASE_URL, bootstrap email, and display name are required.\n")
        return EXIT_INVALID_INPUT
    password = (
        sys.stdin.readline().rstrip("\r\n")
        if arguments.password_stdin
        else os.environ.get("APP_BOOTSTRAP_ADMIN_PASSWORD")
    )
    if not password:
        sys.stderr.write("Provide APP_BOOTSTRAP_ADMIN_PASSWORD or use --password-stdin.\n")
        return EXIT_INVALID_INPUT

    runtime = create_database_runtime(DatabaseConfig(url=SecretStr(database_url)))
    try:
        service = BootstrapService(SqlAlchemyIdentityUnitOfWorkFactory(runtime.session_factory))
        try:
            result = await service.bootstrap(
                email=arguments.email,
                display_name=arguments.display_name,
                password=password,
            )
        except BootstrapAlreadyCompletedError:
            sys.stderr.write("Bootstrap refused: an administrator already exists.\n")
            return EXIT_ALREADY_BOOTSTRAPPED
    finally:
        del password
        await runtime.dispose()

    sys.stdout.write(f"Administrator bootstrapped: {result.administrator_id}\n")
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Parse safe inputs and run the explicit bootstrap transaction."""
    parsed = _parser().parse_args(arguments)
    try:
        return asyncio.run(_bootstrap(parsed))
    except ValueError as error:
        sys.stderr.write(f"Bootstrap rejected: {error}\n")
        return EXIT_INVALID_INPUT


if __name__ == "__main__":  # pragma: no cover - exercised as an operator process.
    raise SystemExit(main())
