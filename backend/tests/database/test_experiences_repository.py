"""PostgreSQL repository proofs for the M5 experience lifecycle."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text

from app.common.domain.pagination import PageRequest
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.experiences import ExperienceRecord
from app.infrastructure.database.experiences_uow import ExperienceRepository
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.experiences.domain import (
    EmploymentType,
    Experience,
    ExperienceRevision,
    ExperienceValues,
    FrozenRevisionError,
    PublicExperienceQuery,
    RemoteStatus,
)
from tests.database.runtime_permissions import reconcile_runtime_permissions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 3, 20, tzinfo=UTC)
ADMIN_ID = UUID("0198a12c-3000-7000-8000-000000000001")
SKILL_ID = UUID("0198a12c-3000-7000-8000-000000000002")
EXPERIENCE_ID = UUID("0198a12c-3000-7000-8000-000000000003")
DRAFT_ID = UUID("0198a12c-3000-7000-8000-000000000004")
NEXT_DRAFT_ID = UUID("0198a12c-3000-7000-8000-000000000005")


@pytest.fixture
def migrated_experience_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Create and remove the exact M5 schema around repository tests."""
    monkeypatch.setenv("APP_DATABASE_URL", test_database_owner_url.get_secret_value())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(reconcile_runtime_permissions(test_database_owner_url, test_database_url))

    async def seed() -> None:
        engine = create_database_engine(DatabaseConfig(url=test_database_owner_url))
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO administrator "
                        "(id, email, email_normalized, display_name, password_hash, "
                        "must_change_password, is_active) VALUES "
                        "(:id, 'repository@example.test', 'repository@example.test', "
                        "'Repository Admin', 'synthetic-not-a-login-hash', false, true)"
                    ),
                    {"id": ADMIN_ID},
                )
                await connection.execute(
                    text(
                        "INSERT INTO skill_category "
                        "(id, name, slug, description, position, created_at, updated_at, version) "
                        "VALUES ('0198a12c-3000-7000-8000-000000000006', 'Languages', "
                        "'languages', NULL, 0, now(), now(), 1)"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO skill "
                        "(id, name, slug, category_id, description, proficiency_label, "
                        "proficiency_score, years_experience, icon_key, position, featured, "
                        "visible, created_at, updated_at, version) VALUES "
                        "(:id, 'Python', 'python', "
                        "'0198a12c-3000-7000-8000-000000000006', NULL, NULL, 90, 8.00, "
                        "'python', 0, true, true, now(), now(), 1)"
                    ),
                    {"id": SKILL_ID},
                )
        finally:
            await engine.dispose()

    asyncio.run(seed())
    try:
        yield
    finally:
        command.downgrade(config, "base")


def _values(*, role_title: str = "Staff Engineer") -> ExperienceValues:
    return ExperienceValues(
        company_name="Example Studio",
        company_url="https://example.test",
        role_title=role_title,
        employment_type=EmploymentType.FULL_TIME,
        location="Paris",
        remote_status=RemoteStatus.HYBRID,
        start_date=date(2024, 1, 1),
        end_date=None,
        current_position=True,
        short_summary="Led the platform team.",
        detailed_description="Plain text detail.",
        responsibilities=("Designed service boundaries", "Mentored engineers"),
        achievements=("Reduced deployment time",),
        technologies=("Python", "PostgreSQL"),
        skill_ids=(SKILL_ID,),
    )


def _aggregate(
    *,
    identifier: UUID = EXPERIENCE_ID,
    draft_id: UUID = DRAFT_ID,
    position: int = 0,
) -> Experience:
    return Experience(
        id=identifier,
        visible=True,
        position=position,
        draft_revision_id=draft_id,
        published_revision_id=None,
        publish_at=None,
        unpublished_at=None,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


def _revision(
    *,
    identifier: UUID = DRAFT_ID,
    experience_id: UUID = EXPERIENCE_ID,
) -> ExperienceRevision:
    return ExperienceRevision(
        id=identifier,
        experience_id=experience_id,
        revision_number=1,
        based_on_revision_id=None,
        values=_values(),
        frozen=False,
        created_by=ADMIN_ID,
        created_at=NOW,
        updated_at=NOW,
    )


async def test_repository_round_trips_ordered_revision_data_and_never_commits(
    migrated_experience_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Uncommitted work rolls back; committed work round-trips every ordered field."""
    del migrated_experience_database
    session_factory = create_session_factory(database_engine)
    unit_of_work = SqlAlchemyUnitOfWork(session_factory)
    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())

    async with session_factory() as session:
        count_after_rollback = (
            await session.execute(select(func.count()).select_from(ExperienceRecord))
        ).scalar_one()
    assert count_after_rollback == 0

    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        await unit_of_work.commit()

    async with unit_of_work:
        snapshot = await ExperienceRepository(unit_of_work.session).get(EXPERIENCE_ID)
    assert snapshot is not None
    assert snapshot.draft.values == _values()
    assert snapshot.published is None


async def test_publish_is_copy_on_write_and_database_trigger_blocks_frozen_mutation(
    migrated_experience_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Publish persists one frozen snapshot and one equal mutable next draft."""
    del migrated_experience_database
    session_factory = create_session_factory(database_engine)
    unit_of_work = SqlAlchemyUnitOfWork(session_factory)
    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        await unit_of_work.commit()

    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        snapshot = await repository.get(EXPERIENCE_ID, for_update=True)
        assert snapshot is not None
        published = await repository.publish(
            snapshot,
            publish_at=NOW - timedelta(seconds=1),
            next_revision_id=NEXT_DRAFT_ID,
            actor_id=ADMIN_ID,
            now=NOW,
        )
        await unit_of_work.commit()

    assert published.published is not None
    assert published.published.frozen is True
    assert published.draft.based_on_revision_id == published.published.id
    assert published.draft.values == published.published.values

    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        with pytest.raises(FrozenRevisionError):
            await repository.save_draft(
                replace(published, draft=published.published),
                _values(role_title="Changed"),
                now=NOW + timedelta(minutes=1),
            )


async def test_public_query_uses_database_time_chronology_and_bounded_selects(
    migrated_experience_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Only effective publications return in stable order with a fixed query count."""
    del migrated_experience_database
    session_factory = create_session_factory(database_engine)
    unit_of_work = SqlAlchemyUnitOfWork(session_factory)
    future_experience_id = UUID("0198a12c-3000-7000-8000-000000000007")
    future_draft_id = UUID("0198a12c-3000-7000-8000-000000000008")
    async with unit_of_work:
        repository = ExperienceRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        await repository.add(
            _aggregate(
                identifier=future_experience_id,
                draft_id=future_draft_id,
                position=1,
            ),
            _revision(identifier=future_draft_id, experience_id=future_experience_id),
        )
        first = await repository.get(EXPERIENCE_ID, for_update=True)
        future = await repository.get(future_experience_id, for_update=True)
        assert first is not None
        assert future is not None
        await repository.publish(
            first,
            publish_at=NOW - timedelta(days=1),
            next_revision_id=uuid4(),
            actor_id=ADMIN_ID,
            now=NOW,
        )
        await repository.publish(
            future,
            publish_at=NOW + timedelta(days=3650),
            next_revision_id=uuid4(),
            actor_id=ADMIN_ID,
            now=NOW,
        )
        await unit_of_work.commit()

    query_count = 0

    def count_selects(
        _connection: Connection,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: object,
    ) -> None:
        nonlocal query_count
        if statement.lstrip().upper().startswith("SELECT"):
            query_count += 1

    event.listen(database_engine.sync_engine, "before_cursor_execute", count_selects)
    try:
        async with unit_of_work:
            page = await ExperienceRepository(unit_of_work.session).list_public(
                PublicExperienceQuery(PageRequest(page=1, page_size=20))
            )
    finally:
        event.remove(database_engine.sync_engine, "before_cursor_execute", count_selects)

    assert [item.experience.id for item in page.items] == [EXPERIENCE_ID]
    assert page.metadata.total_items == 1
    assert query_count <= 7

    async with unit_of_work:
        summaries = await ExperienceRepository(unit_of_work.session).reference_summaries(
            (EXPERIENCE_ID, future_experience_id)
        )
    assert summaries[0].public is not None
    assert summaries[0].public.role_title == "Staff Engineer"
    assert summaries[1].public is None
