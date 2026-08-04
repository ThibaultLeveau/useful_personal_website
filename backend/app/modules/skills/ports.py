"""Inward-facing persistence ports for the skills capability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.common.domain.pagination import Page
    from app.modules.audit.domain import AuditEntry
    from app.modules.skills.domain import (
        AdminSkillQuery,
        PublicSkillQuery,
        Skill,
        SkillCategory,
        SkillCategoryValues,
        SkillReferenceSummary,
        SkillValues,
    )


class CategoryRepositoryPort(Protocol):
    """Category persistence without transaction ownership."""

    async def list_all(self, *, for_update: bool = False) -> tuple[SkillCategory, ...]:
        """List categories in deterministic global order."""
        ...

    async def get(self, category_id: UUID, *, for_update: bool = False) -> SkillCategory | None:
        """Load one category, optionally locking it."""
        ...

    async def add(self, category: SkillCategory) -> None:
        """Stage one new category."""
        ...

    async def update(
        self,
        category: SkillCategory,
        values: SkillCategoryValues,
        *,
        now: datetime,
    ) -> SkillCategory:
        """Stage category values and return its new version."""
        ...

    async def delete(self, category: SkillCategory) -> None:
        """Stage one already-validated empty category deletion."""
        ...

    async def reorder(
        self,
        categories: tuple[SkillCategory, ...],
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[SkillCategory, ...]:
        """Normalize and stage the complete category order."""
        ...

    async def count_skills(self, category_id: UUID) -> int:
        """Count category usage for restrictive deletion."""
        ...


class SkillRepositoryPort(Protocol):
    """Skill persistence and purpose-built public/reference reads."""

    async def list_admin(self, query: AdminSkillQuery) -> Page[Skill]:
        """Return one filtered exact administrator page."""
        ...

    async def list_by_category(
        self,
        category_id: UUID,
        *,
        for_update: bool = False,
    ) -> tuple[Skill, ...]:
        """List one category's skills in deterministic order."""
        ...

    async def list_public(self, query: PublicSkillQuery) -> Page[Skill]:
        """Return one visibility-enforced public page."""
        ...

    async def get(self, skill_id: UUID, *, for_update: bool = False) -> Skill | None:
        """Load one skill, optionally locking it."""
        ...

    async def add(self, skill: Skill) -> None:
        """Stage one new skill."""
        ...

    async def update(self, skill: Skill, values: SkillValues, *, now: datetime) -> Skill:
        """Stage complete values and return the new version."""
        ...

    async def delete(self, skill: Skill) -> None:
        """Stage one skill deletion."""
        ...

    async def reorder(
        self,
        skills: tuple[Skill, ...],
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Skill, ...]:
        """Normalize and stage one category's complete skill order."""
        ...

    async def reference_summaries(
        self,
        skill_ids: tuple[UUID, ...],
    ) -> tuple[SkillReferenceSummary, ...]:
        """Resolve safe summaries for opaque IDs."""
        ...


class AuditPort(Protocol):
    """Insert-only controlled audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one controlled audit fact."""
        ...


class SkillsUnitOfWork(Protocol):
    """One skills application transaction."""

    categories: CategoryRepositoryPort
    skills: SkillRepositoryPort
    audit: AuditPort
    idempotency: IdempotencyStore

    async def __aenter__(self) -> Self:
        """Open one transaction and bind repositories."""
        ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work and release resources."""
        ...

    async def commit(self) -> None:
        """Commit the complete application operation."""
        ...


class SkillsUnitOfWorkFactory(Protocol):
    """Create a fresh skills transaction."""

    def __call__(self) -> SkillsUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
