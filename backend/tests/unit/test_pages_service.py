"""Focused M8 page-service provider and projection budgets."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest

from app.modules.pages.domain import (
    BlockLayout,
    BlockTheme,
    PageBlock,
    PageBlockValues,
    ResponsiveValues,
    validate_block_values,
)
from app.modules.pages.registry import BlockType, ReferenceKind
from app.modules.pages.service import PageReferenceError, PageService
from app.modules.skills.service import SkillsNotFoundError

if TYPE_CHECKING:
    from app.modules.pages.ports import (
        BlogReferencePort,
        ExperienceReferencePort,
        PagesUnitOfWorkFactory,
        ProfilePublicPort,
        ProjectReferencePort,
        SkillReferencePort,
    )

_NOW = datetime(2026, 8, 4, tzinfo=UTC)
_SKILL_REFERENCE = "skill_reference"


class _Provider:
    def __init__(self) -> None:
        self.calls: list[tuple[int, bool | None]] = []

    async def resolve(self, _ids: tuple[UUID, ...]) -> tuple[object, ...]:
        return ()

    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[object, ...]:
        self.calls.append((maximum, featured))
        return (object(),)


class _MissingSkillProvider(_Provider):
    async def resolve(self, _ids: tuple[UUID, ...]) -> tuple[object, ...]:
        raise SkillsNotFoundError(_SKILL_REFERENCE)


class _Profile:
    async def public_get(self) -> object:
        return object()


def _block(block_type: BlockType, config: dict[str, object], *, ordinal: int) -> PageBlock:
    values, references = validate_block_values(
        PageBlockValues(
            block_type=block_type,
            schema_version=1,
            visible=True,
            title=None,
            subtitle=None,
            description=None,
            theme=BlockTheme.DEFAULT,
            layout=BlockLayout.CONTAINED,
            responsive=ResponsiveValues(),
            config=config,
        )
    )
    return PageBlock(
        id=UUID(int=ordinal),
        revision_id=UUID(int=100),
        position=ordinal - 1,
        values=values,
        references=references,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _service(
    skills: _Provider,
    experiences: _Provider,
    projects: _Provider,
    posts: _Provider,
) -> PageService:
    return PageService(
        cast("PagesUnitOfWorkFactory", object()),
        cast("SkillReferencePort", skills),
        cast("ExperienceReferencePort", experiences),
        cast("ProjectReferencePort", projects),
        cast("BlogReferencePort", posts),
        cast("ProfilePublicPort", _Profile()),
    )


async def test_automatic_collections_are_grouped_into_bounded_provider_calls() -> None:
    """Use one maximum-sized call per provider/featured selection, never per block."""
    skills, experiences, projects, posts = (_Provider() for _ in range(4))
    service = _service(skills, experiences, projects, posts)
    blocks = (
        _block(BlockType.SKILLS_GRID, {"maximum_items": 4}, ordinal=1),
        _block(BlockType.SKILLS_GRID, {"maximum_items": 9}, ordinal=2),
        _block(BlockType.FEATURED_SKILLS, {"maximum_items": 3}, ordinal=3),
        _block(BlockType.EXPERIENCE_LIST, {"maximum_items": 8}, ordinal=4),
        _block(BlockType.PROJECT_GRID, {"maximum_items": 7}, ordinal=5),
        _block(BlockType.FEATURED_PROJECTS, {"maximum_items": 5}, ordinal=6),
        _block(BlockType.LATEST_POSTS, {"maximum_items": 3}, ordinal=7),
    )

    result = await service._automatic_provider_summaries(blocks)  # noqa: SLF001

    assert skills.calls == [(9, None), (3, True)]
    assert experiences.calls == [(8, None)]
    assert projects.calls == [(7, None), (5, True)]
    assert posts.calls == [(3, None)]
    assert set(result) == {
        (ReferenceKind.SKILL, None),
        (ReferenceKind.SKILL, True),
        (ReferenceKind.EXPERIENCE, None),
        (ReferenceKind.PROJECT, None),
        (ReferenceKind.PROJECT, True),
        (ReferenceKind.POST, None),
    }


async def test_explicit_selection_skips_automatic_list_and_missing_provider_is_safe() -> None:
    """Prefer normalized IDs and translate provider not-found errors into page validation."""
    skills = _MissingSkillProvider()
    service = _service(skills, _Provider(), _Provider(), _Provider())
    skill_id = UUID("0198a13d-8300-7000-8000-000000000001")
    explicit = _block(
        BlockType.SKILLS_GRID,
        {"skill_ids": [str(skill_id)], "maximum_items": 12},
        ordinal=1,
    )

    assert await service._automatic_provider_summaries((explicit,)) == {}  # noqa: SLF001
    assert skills.calls == []
    with pytest.raises(PageReferenceError) as captured:
        await service._provider_summaries(  # noqa: SLF001
            {ReferenceKind.SKILL: (skill_id,)}
        )
    assert captured.value.path == "references"
    assert captured.value.code == "skill_not_found"
