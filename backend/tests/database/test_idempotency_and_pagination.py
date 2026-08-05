"""PostgreSQL proofs for M2 idempotency and deterministic page traversal."""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url

from app.common.application import (
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain import (
    ActorContext,
    PageRequest,
    QueryCatalog,
    SortTerm,
    parse_collection_query,
)
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.idempotency import (
    IdempotencyRecord,
    IdempotencyRepository,
)
from app.infrastructure.database.pagination import fetch_page
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ROUTE = "/api/v1/admin/m2-idempotency-probe"
PAGINATION_ROUTE = "/api/v1/admin/m2-pagination-probe"
NOW = datetime(2026, 8, 3, 11, tzinfo=UTC)
ACTOR = ActorContext.administrator(UUID("00000000-0000-4000-8000-000000000221"))
RESOURCE_ID = UUID("00000000-0000-4000-8000-000000000222")


async def _remove_probe_rows(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.route.in_((ROUTE, PAGINATION_ROUTE)))
        )


async def _reconcile_runtime_permissions(
    owner_url: SecretStr,
    runtime_url: SecretStr,
) -> None:
    runtime_user = make_url(runtime_url.get_secret_value()).username
    if runtime_user is None or re.fullmatch(r"[a-z_][a-z0-9_]*", runtime_user) is None:
        msg = "TEST_DATABASE_URL must contain a conservative runtime role name"
        raise ValueError(msg)
    quoted_user = f'"{runtime_user}"'
    statements = (
        f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {quoted_user}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM {quoted_user}",
        f"GRANT SELECT ON TABLE public.alembic_version TO {quoted_user}",
        f"REVOKE ALL PRIVILEGES ON TABLE public.audit_entry FROM {quoted_user}",
        f"GRANT SELECT, INSERT ON TABLE public.audit_entry TO {quoted_user}",
    )
    engine = create_database_engine(DatabaseConfig(url=owner_url))
    try:
        async with engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


@pytest.fixture
def migrated_contract_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Run these persistence proofs against the exact packaged M2 head."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(_reconcile_runtime_permissions(test_database_owner_url, test_database_url))
    try:
        yield
    finally:
        command.downgrade(config, "base")


@pytest.fixture(autouse=True)
async def clean_probe_rows(
    migrated_contract_database: None,
    database_engine: AsyncEngine,
) -> AsyncIterator[None]:
    """Isolate only the synthetic M2 routes owned by this test module."""
    del migrated_contract_database
    await _remove_probe_rows(database_engine)
    try:
        yield
    finally:
        await _remove_probe_rows(database_engine)


def _request(
    *,
    key: str = "m2-idempotency-key-000000000001",
    payload: bytes = b'{"command":"create"}',
    requested_at: datetime = NOW,
) -> IdempotencyRequest:
    return IdempotencyRequest.create(
        actor=ACTOR,
        route=ROUTE,
        key=key,
        canonical_payload=payload,
        requested_at=requested_at,
    )


async def test_complete_replay_conflict_expiry_and_purge(
    database_engine: AsyncEngine,
) -> None:
    """The repository must replay safely, reject mismatches, and expire at 24 hours."""
    session_factory = create_session_factory(database_engine)
    initial = _request()
    completed = IdempotencyOutcome(
        response_status=201,
        result_code="probe.created",
        resource_type="probe",
        resource_id=RESOURCE_ID,
        resource_version=1,
    )

    unit_of_work = SqlAlchemyUnitOfWork(session_factory)
    async with unit_of_work:
        repository = IdempotencyRepository(unit_of_work.session)
        acquired = await repository.acquire(initial)
        assert acquired.decision is IdempotencyDecisionType.ACQUIRED
        assert acquired.record_id is not None
        await repository.complete(acquired.record_id, completed, completed_at=NOW)
        await unit_of_work.commit()

    async with unit_of_work:
        replay = await IdempotencyRepository(unit_of_work.session).acquire(initial)
    assert replay.decision is IdempotencyDecisionType.REPLAY
    assert replay.outcome == completed

    async with unit_of_work:
        conflict = await IdempotencyRepository(unit_of_work.session).acquire(
            _request(payload=b'{"command":"different"}')
        )
    assert conflict.decision is IdempotencyDecisionType.PAYLOAD_CONFLICT

    after_expiry = _request(
        payload=b'{"command":"different"}',
        requested_at=NOW + timedelta(hours=25),
    )
    async with unit_of_work:
        repository = IdempotencyRepository(unit_of_work.session)
        recycled = await repository.acquire(after_expiry)
        assert recycled.decision is IdempotencyDecisionType.ACQUIRED
        assert recycled.record_id is not None
        await repository.complete(
            recycled.record_id,
            IdempotencyOutcome(response_status=200, result_code="probe.updated"),
            completed_at=after_expiry.requested_at,
        )
        await unit_of_work.commit()

    async with session_factory() as session:
        stored = (
            await session.execute(select(IdempotencyRecord).where(IdempotencyRecord.route == ROUTE))
        ).scalar_one()
    assert len(stored.actor_digest) == 32
    assert len(stored.key_digest) == 32
    assert len(stored.request_fingerprint) == 32
    assert stored.result_code == "probe.updated"
    assert stored.resource_id is None
    assert not hasattr(stored, "response_body")
    assert b"m2-idempotency-key" not in stored.key_digest

    async with unit_of_work:
        purged = await IdempotencyRepository(unit_of_work.session).purge_expired(
            before=NOW + timedelta(hours=50)
        )
        await unit_of_work.commit()
    assert purged == 1


async def test_concurrent_same_request_executes_one_claim_and_one_replay(
    database_engine: AsyncEngine,
) -> None:
    """PostgreSQL uniqueness must serialize duplicates without a second effect claim."""
    session_factory = create_session_factory(database_engine)
    barrier = asyncio.Barrier(2)
    request = _request(key="m2-concurrent-key-0000000000002")

    async def admit() -> IdempotencyDecisionType:
        await barrier.wait()
        unit_of_work = SqlAlchemyUnitOfWork(session_factory)
        async with unit_of_work:
            repository = IdempotencyRepository(unit_of_work.session)
            decision = await repository.acquire(request)
            if decision.decision is IdempotencyDecisionType.ACQUIRED:
                assert decision.record_id is not None
                await repository.complete(
                    decision.record_id,
                    IdempotencyOutcome(response_status=201, result_code="probe.created"),
                    completed_at=NOW,
                )
                await unit_of_work.commit()
            return decision.decision

    decisions = await asyncio.gather(admit(), admit())
    assert sorted(decision.value for decision in decisions) == ["acquired", "replay"]

    async with database_engine.connect() as connection:
        count = (
            await connection.execute(
                select(func.count(IdempotencyRecord.id)).where(IdempotencyRecord.route == ROUTE)
            )
        ).scalar_one()
    assert count == 1


async def test_postgresql_page_traversal_is_exact_and_id_tied(
    database_engine: AsyncEngine,
) -> None:
    """Mapped columns, exact totals, and ID tie-breaking prevent loss/duplication."""
    session_factory = create_session_factory(database_engine)
    identifiers = [
        UUID(f"00000000-0000-4000-8000-{suffix:012d}") for suffix in (225, 223, 227, 224, 226)
    ]
    unit_of_work = SqlAlchemyUnitOfWork(session_factory)
    async with unit_of_work:
        for position, identifier in enumerate(identifiers):
            digest = hashlib.sha256(f"pagination-{position}".encode()).digest()
            unit_of_work.session.add(
                IdempotencyRecord(
                    id=identifier,
                    actor_type="administrator_session",
                    actor_digest=digest,
                    route=PAGINATION_ROUTE,
                    key_digest=digest,
                    request_fingerprint=digest,
                    status="completed",
                    response_status=200,
                    result_code="probe.listed",
                    resource_type=None,
                    resource_id=None,
                    resource_version=None,
                    created_at=NOW,
                    updated_at=NOW,
                    completed_at=NOW,
                    expires_at=NOW + timedelta(hours=24),
                )
            )
        await unit_of_work.commit()

    catalog = QueryCatalog(
        allowed_filters=frozenset({"status"}),
        allowed_sorts=frozenset({"created_at", "id"}),
        default_sort=(SortTerm("created_at"),),
    )
    parsed = parse_collection_query(
        [("status", "completed"), ("sort", "created_at"), ("page_size", "2")],
        catalog=catalog,
    )
    filter_columns = {"status": IdempotencyRecord.status}
    sort_columns = {
        "created_at": IdempotencyRecord.created_at,
        "id": IdempotencyRecord.id,
    }
    ordered = select(IdempotencyRecord.id).where(
        IdempotencyRecord.route == PAGINATION_ROUTE,
        filter_columns["status"] == parsed.filters["status"],
    )
    for term in parsed.sort:
        column = sort_columns[term.field]
        ordered = ordered.order_by(column.desc() if term.descending else column.asc())
    count_statement = select(func.count(IdempotencyRecord.id)).where(
        IdempotencyRecord.route == PAGINATION_ROUTE,
        IdempotencyRecord.status == "completed",
    )

    traversed: list[UUID] = []
    for page_number in (1, 2, 3):
        async with session_factory() as session:
            page = await fetch_page(
                session,
                ordered_statement=ordered,
                count_statement=count_statement,
                request=PageRequest(page=page_number, page_size=2),
            )
        assert page.metadata.total_items == 5
        assert page.metadata.total_pages == 3
        traversed.extend(page.items)

    assert traversed == sorted(identifiers)
    assert len(traversed) == len(set(traversed)) == 5

    async with session_factory() as session:
        beyond = await fetch_page(
            session,
            ordered_statement=ordered,
            count_statement=count_statement,
            request=PageRequest(page=4, page_size=2),
        )
    assert beyond.items == ()
    assert beyond.metadata.total_items == 5
    assert beyond.metadata.total_pages == 3
