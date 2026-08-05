"""PostgreSQL repository proofs for the M7 blog lifecycle and taxonomy."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import DBAPIError

from app.common.domain.pagination import PageRequest
from app.infrastructure.database.blog import PostRecord
from app.infrastructure.database.blog_uow import BlogRepository
from app.infrastructure.database.config import DatabaseConfig
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.blog.domain import (
    Post,
    PostRevision,
    PostValues,
    PublicPostQuery,
    Taxonomy,
    TaxonomyKind,
    validate_post_values,
)
from tests.database.runtime_permissions import reconcile_runtime_permissions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.postgresql
BACKEND_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 4, 16, tzinfo=UTC)
ADMIN_ID = UUID("0198a12c-7000-7000-8000-000000000001")
POST_ID = UUID("0198a12c-7000-7000-8000-000000000002")
DRAFT_ID = UUID("0198a12c-7000-7000-8000-000000000003")
NEXT_DRAFT_ID = UUID("0198a12c-7000-7000-8000-000000000004")
TAG_ID = UUID("0198a12c-7000-7000-8000-000000000005")
CATEGORY_ID = UUID("0198a12c-7000-7000-8000-000000000006")


@pytest.fixture
def migrated_blog_database(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: SecretStr,
    test_database_owner_url: SecretStr,
) -> Iterator[None]:
    """Create and remove the exact M7 schema around repository proofs."""
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
                        "(id,email,email_normalized,display_name,password_hash,"
                        "must_change_password,is_active) VALUES "
                        "(:id,'blog@example.test','blog@example.test','Blog Admin',"
                        "'synthetic-not-a-login-hash',false,true)"
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


def _values(*, title: str = "Safe publication", tag_ids: tuple[UUID, ...] = ()) -> PostValues:
    return validate_post_values(
        PostValues(
            title=title,
            excerpt="A revision-safe article with deterministic public behavior.",
            source="## Safe publication\n\nA **controlled** article with [notes](/about).",
            author_display="Site owner",
            reading_minutes=0,
            content_checksum="",
            content_policy_name="",
            content_policy_version="",
            tag_ids=tag_ids,
            category_ids=(CATEGORY_ID,),
            related_post_ids=(),
            seo_title=None,
            seo_description=None,
            canonical_url="https://example.test/blog/safe-publication",
        ),
        post_id=POST_ID,
    )


def _aggregate() -> Post:
    return Post(
        id=POST_ID,
        slug="safe-publication",
        visible=True,
        position=0,
        draft_revision_id=DRAFT_ID,
        published_revision_id=None,
        publish_at=None,
        unpublished_at=None,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


def _revision(values: PostValues | None = None) -> PostRevision:
    return PostRevision(
        id=DRAFT_ID,
        post_id=POST_ID,
        revision_number=1,
        based_on_revision_id=None,
        values=values or _values(),
        frozen=False,
        created_by=ADMIN_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _taxonomies() -> tuple[Taxonomy, Taxonomy]:
    return (
        Taxonomy(
            id=TAG_ID,
            kind=TaxonomyKind.TAG,
            name="Engineering",
            slug="engineering",
            position=0,
            visible=True,
            created_at=NOW,
            updated_at=NOW,
            version=1,
        ),
        Taxonomy(
            id=CATEGORY_ID,
            kind=TaxonomyKind.CATEGORY,
            name="Delivery",
            slug="delivery",
            position=0,
            visible=True,
            created_at=NOW,
            updated_at=NOW,
            version=1,
        ),
    )


async def _stage_taxonomies(repository: BlogRepository) -> None:
    for taxonomy in _taxonomies():
        await repository.add_taxonomy(taxonomy)


async def test_repository_rolls_back_then_round_trips_canonical_values(
    migrated_blog_database: None,
    database_engine: AsyncEngine,
) -> None:
    """The repository never commits and retains every revision-owned derivation."""
    del migrated_blog_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        await _stage_taxonomies(repository)
        await repository.add_post(_aggregate(), _revision(_values(tag_ids=(TAG_ID,))))
    async with unit_of_work:
        count = (
            await unit_of_work.session.execute(select(func.count()).select_from(PostRecord))
        ).scalar_one()
    assert count == 0

    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        await _stage_taxonomies(repository)
        expected = _values(tag_ids=(TAG_ID,))
        await repository.add_post(_aggregate(), _revision(expected))
        await unit_of_work.commit()
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        snapshot = await repository.get_post(POST_ID)
        slug_exists = await repository.post_slug_exists("SAFE-PUBLICATION")
    assert snapshot is not None
    assert snapshot.draft.values == expected
    assert slug_exists


async def test_publish_is_atomic_copy_on_write_and_frozen_in_postgresql(
    migrated_blog_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Publish creates one mutable copy and PostgreSQL rejects live revision mutation."""
    del migrated_blog_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        await _stage_taxonomies(repository)
        await repository.add_post(_aggregate(), _revision())
        await unit_of_work.commit()
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        snapshot = await repository.get_post(POST_ID)
        assert snapshot is not None
        database_now = await repository.database_now()
        published = await repository.publish_post(
            snapshot,
            publish_at=database_now,
            next_revision_id=NEXT_DRAFT_ID,
            actor_id=ADMIN_ID,
            now=database_now,
        )
        await unit_of_work.commit()
    assert published.published is not None
    assert published.published.frozen
    assert published.draft.values == published.published.values
    async with unit_of_work:
        with pytest.raises(DBAPIError):
            await unit_of_work.session.execute(
                text("UPDATE post_revision SET title='Changed' WHERE id=:id"),
                {"id": DRAFT_ID},
            )


async def test_public_query_uses_frozen_revision_database_time_and_public_taxonomy(
    migrated_blog_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Future content stays absent and draft edits cannot affect public tag-filtered results."""
    del migrated_blog_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        await _stage_taxonomies(repository)
        await repository.add_post(_aggregate(), _revision(_values(tag_ids=(TAG_ID,))))
        await unit_of_work.commit()
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        snapshot = await repository.get_post(POST_ID)
        assert snapshot is not None
        database_now = await repository.database_now()
        future = await repository.publish_post(
            snapshot,
            publish_at=database_now + timedelta(hours=1),
            next_revision_id=NEXT_DRAFT_ID,
            actor_id=ADMIN_ID,
            now=database_now,
        )
        await unit_of_work.commit()
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        assert (
            await repository.list_public_posts(
                PublicPostQuery(PageRequest(), tag_slug="engineering")
            )
        ).metadata.total_items == 0
        visible = await repository.reschedule_post(
            future,
            publish_at=await repository.database_now() - timedelta(seconds=1),
            now=await repository.database_now(),
        )
        revised = replace(visible.draft.values, title="Private draft title", tag_ids=())
        await repository.save_post_draft(visible, revised, now=await repository.database_now())
        await unit_of_work.commit()
    async with unit_of_work:
        page = await BlogRepository(unit_of_work.session).list_public_posts(
            PublicPostQuery(PageRequest(), tag_slug="engineering")
        )
    assert page.metadata.total_items == 1
    assert page.items[0].published is not None
    assert page.items[0].published.values.title == "Safe publication"


async def test_public_page_has_a_fixed_bounded_statement_count(
    migrated_blog_database: None,
    database_engine: AsyncEngine,
) -> None:
    """Public loading uses one page/count plus four bounded aggregate queries, not N+1."""
    del migrated_blog_database
    unit_of_work = SqlAlchemyUnitOfWork(create_session_factory(database_engine))
    async with unit_of_work:
        repository = BlogRepository(unit_of_work.session)
        await _stage_taxonomies(repository)
        await repository.add_post(_aggregate(), _revision())
        await unit_of_work.session.flush()
        snapshot = await repository.get_post(POST_ID)
        assert snapshot is not None
        now = await repository.database_now()
        await repository.publish_post(
            snapshot,
            publish_at=now,
            next_revision_id=NEXT_DRAFT_ID,
            actor_id=ADMIN_ID,
            now=now,
        )
        await unit_of_work.commit()

    statements = 0

    def count_statements(*_args: object) -> None:
        nonlocal statements
        statements += 1

    event.listen(database_engine.sync_engine, "before_cursor_execute", count_statements)
    try:
        async with unit_of_work:
            page = await BlogRepository(unit_of_work.session).list_public_posts(
                PublicPostQuery(PageRequest(page_size=100))
            )
    finally:
        event.remove(database_engine.sync_engine, "before_cursor_execute", count_statements)
    assert page.metadata.total_items == 1
    assert statements == 6
