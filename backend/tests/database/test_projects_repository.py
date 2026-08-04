"""PostgreSQL repository proofs for the M6 project lifecycle and graph."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import DBAPIError

from app.common.domain.pagination import PageRequest
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.projects import ProjectRecord
from app.infrastructure.database.projects_uow import ProjectRepository
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.projects.domain import (
    Project,
    ProjectRevision,
    ProjectStatus,
    ProjectValues,
    PublicProjectQuery,
)
from tests.database.runtime_permissions import reconcile_runtime_permissions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)
ADMIN_ID = UUID("0198a12c-4000-7000-8000-000000000001")
PROJECT_ID = UUID("0198a12c-4000-7000-8000-000000000002")
DRAFT_ID = UUID("0198a12c-4000-7000-8000-000000000003")
NEXT_DRAFT_ID = UUID("0198a12c-4000-7000-8000-000000000004")
SECOND_PROJECT_ID = UUID("0198a12c-4000-7000-8000-000000000005")
SECOND_DRAFT_ID = UUID("0198a12c-4000-7000-8000-000000000006")


@pytest.fixture
def migrated_project_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Create and remove the exact M6 schema around repository tests."""
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
                        "(:id, 'projects@example.test', 'projects@example.test', "
                        "'Projects Admin', 'synthetic-not-a-login-hash', false, true)"
                    ),
                    {"id": ADMIN_ID},
                )
        finally:
            await engine.dispose()

    asyncio.run(seed())
    try:
        yield
    finally:
        command.downgrade(config, "base")


def _values(*, name: str = "API Platform", related: tuple[UUID, ...] = ()) -> ProjectValues:
    return ProjectValues(
        name=name,
        short_description="A secure API-first platform.",
        full_description="## Overview\n\nA complete case study.",
        problem="Teams needed reliable delivery.",
        solution="Built bounded services and typed contracts.",
        impact="Reduced lead time and operational risk.",
        owner_role="Technical lead",
        architecture="FastAPI, PostgreSQL, and a generated client.",
        technologies=("Python", "PostgreSQL"),
        status=ProjectStatus.ACTIVE,
        start_date=date(2025, 1, 1),
        end_date=None,
        repository_url="https://example.test/repository",
        demo_url="https://example.test/demo",
        skill_ids=(),
        experience_ids=(),
        related_project_ids=related,
        seo_title=None,
        seo_description=None,
        canonical_url="https://example.test/projects/api-platform",
    )


def _aggregate(
    *,
    identifier: UUID = PROJECT_ID,
    draft_id: UUID = DRAFT_ID,
    slug: str = "api-platform",
    position: int = 0,
) -> Project:
    return Project(
        id=identifier,
        slug=slug,
        visible=True,
        featured=True,
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
    project_id: UUID = PROJECT_ID,
    values: ProjectValues | None = None,
) -> ProjectRevision:
    return ProjectRevision(
        id=identifier,
        project_id=project_id,
        revision_number=1,
        based_on_revision_id=None,
        values=values or _values(),
        frozen=False,
        created_by=ADMIN_ID,
        created_at=NOW,
        updated_at=NOW,
    )


async def test_repository_round_trip_rolls_back_then_persists_all_owned_values(
    migrated_project_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Repository never commits and round-trips revision-owned values exactly."""
    del migrated_project_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        await ProjectRepository(unit_of_work.session).add(_aggregate(), _revision())
    async with unit_of_work:
        count = (
            await unit_of_work.session.execute(select(func.count()).select_from(ProjectRecord))
        ).scalar_one()
    assert count == 0

    async with unit_of_work:
        repository = ProjectRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        await unit_of_work.commit()
    async with unit_of_work:
        snapshot = await ProjectRepository(unit_of_work.session).get(PROJECT_ID)
    assert snapshot is not None
    assert snapshot.draft.values == _values()
    assert await _slug_exists(database_engine, "API-PLATFORM")


async def _slug_exists(database_engine: AsyncEngine, value: str) -> bool:
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        return await ProjectRepository(unit_of_work.session).slug_exists(value)


async def test_publish_is_copy_on_write_trigger_immutable_and_public_time_effective(
    migrated_project_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Publication freezes content, copies a draft, and uses database time."""
    del migrated_project_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = ProjectRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        snapshot = await repository.get(PROJECT_ID, for_update=True)
        assert snapshot is not None
        published = await repository.publish(
            snapshot,
            publish_at=NOW - timedelta(days=1),
            next_revision_id=NEXT_DRAFT_ID,
            actor_id=ADMIN_ID,
            now=NOW,
        )
        await unit_of_work.commit()

    assert published.published is not None
    assert published.published.frozen
    assert published.draft.values == published.published.values
    statements: list[str] = []

    def capture_statement(*args: object) -> None:
        statements.append(str(args[2]))

    event.listen(database_engine.sync_engine, "before_cursor_execute", capture_statement)
    try:
        async with unit_of_work:
            page = await ProjectRepository(unit_of_work.session).list_public(
                PublicProjectQuery(PageRequest(page=1, page_size=20))
            )
    finally:
        event.remove(database_engine.sync_engine, "before_cursor_execute", capture_statement)
    assert [item.project.id for item in page.items] == [PROJECT_ID]
    assert sum(statement.lstrip().upper().startswith("SELECT") for statement in statements) == 8

    async with unit_of_work:
        with pytest.raises(DBAPIError):
            await unit_of_work.session.execute(
                text("UPDATE project_revision SET name = 'mutated' WHERE id = :id"),
                {"id": published.published.id},
            )


async def test_graph_replacement_detects_direct_and_indirect_cycles(
    migrated_project_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Stable-ID draft graph replacement is serialized and cycle-safe."""
    del migrated_project_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = ProjectRepository(unit_of_work.session)
        await repository.add(_aggregate(), _revision())
        await repository.add(
            _aggregate(
                identifier=SECOND_PROJECT_ID,
                draft_id=SECOND_DRAFT_ID,
                slug="second-project",
                position=1,
            ),
            _revision(
                identifier=SECOND_DRAFT_ID,
                project_id=SECOND_PROJECT_ID,
                values=_values(name="Second project"),
            ),
        )
        first = await repository.get(PROJECT_ID, for_update=True)
        assert first is not None
        await repository.save_draft(
            first,
            replace(first.draft.values, related_project_ids=(SECOND_PROJECT_ID,)),
            now=NOW,
        )
        await unit_of_work.commit()

    async with unit_of_work:
        repository = ProjectRepository(unit_of_work.session)
        assert await repository.related_graph_would_cycle(
            SECOND_PROJECT_ID, (PROJECT_ID,), maximum_nodes=256
        )
        assert not await repository.related_graph_would_cycle(
            SECOND_PROJECT_ID, (), maximum_nodes=256
        )
