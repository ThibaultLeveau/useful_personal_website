"""PostgreSQL repositories and unit of work for the skills capability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.common.domain.pagination import Page
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.pagination import fetch_page
from app.infrastructure.database.skills import SkillCategoryRecord, SkillRecord
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.skills.domain import (
    AdminSkillQuery,
    PublicSkillQuery,
    Skill,
    SkillCategory,
    SkillCategoryValues,
    SkillReferenceSummary,
    SkillsSlugConflictError,
    SkillValues,
)

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from typing import Any
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.elements import ColumnElement

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.skills.ports import SkillsUnitOfWork


def _constraint_name(error: IntegrityError) -> str | None:
    current: BaseException | None = error.orig
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        diagnostic = getattr(current, "diag", None)
        for candidate in (
            getattr(diagnostic, "constraint_name", None),
            getattr(current, "constraint_name", None),
        ):
            if isinstance(candidate, str):
                return candidate
        current = current.__cause__ or current.__context__
    return None


def _map_integrity(error: IntegrityError, *, path: str) -> None:
    constraint = _constraint_name(error)
    if constraint is not None and "slug" in constraint:
        raise SkillsSlugConflictError(path) from error
    raise error


class CategoryRepository:
    """SQLAlchemy category adapter without commit ownership."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind one active transaction-owned session."""
        self._session = session

    async def list_all(self, *, for_update: bool = False) -> tuple[SkillCategory, ...]:
        """List categories in global deterministic order."""
        statement = select(SkillCategoryRecord).order_by(
            SkillCategoryRecord.position,
            SkillCategoryRecord.id,
        )
        if for_update:
            statement = statement.with_for_update()
        rows = (await self._session.execute(statement)).scalars()
        return tuple(self._category(row) for row in rows)

    async def get(
        self,
        category_id: UUID,
        *,
        for_update: bool = False,
    ) -> SkillCategory | None:
        """Load one category, optionally locking it."""
        statement = select(SkillCategoryRecord).where(SkillCategoryRecord.id == category_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else self._category(row)

    async def add(self, category: SkillCategory) -> None:
        """Stage and flush one category without committing."""
        self._session.add(
            SkillCategoryRecord(
                id=category.id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                position=category.position,
                created_at=category.created_at,
                updated_at=category.updated_at,
                version=category.version,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            _map_integrity(error, path="slug")

    async def update(
        self,
        category: SkillCategory,
        values: SkillCategoryValues,
        *,
        now: datetime,
    ) -> SkillCategory:
        """Stage validated category values and increment its version."""
        row = await self._locked_record(category.id)
        row.name = values.name
        row.slug = values.slug
        row.description = values.description
        row.updated_at = now
        row.version += 1
        try:
            await self._session.flush()
        except IntegrityError as error:
            _map_integrity(error, path="slug")
        return self._category(row)

    async def delete(self, category: SkillCategory) -> None:
        """Stage one category deletion."""
        await self._session.execute(
            delete(SkillCategoryRecord).where(SkillCategoryRecord.id == category.id)
        )

    async def reorder(
        self,
        categories: tuple[SkillCategory, ...],
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[SkillCategory, ...]:
        """Stage the complete normalized category order."""
        del categories
        if not ordered_ids:
            return ()
        statement = (
            select(SkillCategoryRecord)
            .where(SkillCategoryRecord.id.in_(ordered_ids))
            .with_for_update()
        )
        records = {
            record.id: record for record in (await self._session.execute(statement)).scalars()
        }
        for position, identifier in enumerate(ordered_ids):
            record = records[identifier]
            record.position = position
            record.updated_at = now
            record.version += 1
        await self._session.flush()
        return tuple(self._category(records[identifier]) for identifier in ordered_ids)

    async def count_skills(self, category_id: UUID) -> int:
        """Count category use with one aggregate query."""
        statement = (
            select(func.count())
            .select_from(SkillRecord)
            .where(SkillRecord.category_id == category_id)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def _locked_record(self, category_id: UUID) -> SkillCategoryRecord:
        statement = (
            select(SkillCategoryRecord)
            .where(SkillCategoryRecord.id == category_id)
            .with_for_update()
        )
        return (await self._session.execute(statement)).scalar_one()

    @staticmethod
    def _category(row: SkillCategoryRecord) -> SkillCategory:
        return SkillCategory(
            id=row.id,
            name=row.name,
            slug=row.slug,
            description=row.description,
            position=row.position,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
        )


class SkillRepository:
    """Bound-parameter skill adapter with purpose-built public queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind one active transaction-owned session."""
        self._session = session

    async def list_admin(self, query: AdminSkillQuery) -> Page[Skill]:
        """Return one allow-listed administrator page."""
        statement = select(SkillRecord)
        count_statement = select(func.count()).select_from(SkillRecord)
        predicates = self._admin_predicates(query)
        if predicates:
            statement = statement.where(*predicates)
            count_statement = count_statement.where(*predicates)
        statement = statement.order_by(*self._admin_order(query.sort))
        records = await fetch_page(
            self._session,
            ordered_statement=statement,
            count_statement=count_statement,
            request=query.page,
        )
        return Page(
            items=tuple(self._skill(row) for row in records.items), metadata=records.metadata
        )

    async def list_by_category(
        self,
        category_id: UUID,
        *,
        for_update: bool = False,
    ) -> tuple[Skill, ...]:
        """List one category's skills in stable order."""
        statement = (
            select(SkillRecord)
            .where(SkillRecord.category_id == category_id)
            .order_by(SkillRecord.position, SkillRecord.id)
        )
        if for_update:
            statement = statement.with_for_update()
        records = (await self._session.execute(statement)).scalars()
        return tuple(self._skill(record) for record in records)

    async def list_public(self, query: PublicSkillQuery) -> Page[Skill]:
        """Return one visibility-enforced public page."""
        statement = select(SkillRecord).join(
            SkillCategoryRecord,
            SkillCategoryRecord.id == SkillRecord.category_id,
        )
        count_statement = (
            select(func.count())
            .select_from(SkillRecord)
            .join(
                SkillCategoryRecord,
                SkillCategoryRecord.id == SkillRecord.category_id,
            )
        )
        predicates: list[ColumnElement[bool]] = [SkillRecord.visible.is_(True)]
        if query.category_slug is not None:
            predicates.append(SkillCategoryRecord.slug == query.category_slug)
        if query.featured is not None:
            predicates.append(SkillRecord.featured.is_(query.featured))
        if query.search is not None:
            predicates.append(func.lower(SkillRecord.name).contains(query.search.lower()))
        statement = statement.where(*predicates).order_by(*self._public_order(query.sort))
        count_statement = count_statement.where(*predicates)
        records = await fetch_page(
            self._session,
            ordered_statement=statement,
            count_statement=count_statement,
            request=query.page,
        )
        return Page(
            items=tuple(self._skill(row) for row in records.items), metadata=records.metadata
        )

    async def get(self, skill_id: UUID, *, for_update: bool = False) -> Skill | None:
        """Load one skill, optionally locking it."""
        statement = select(SkillRecord).where(SkillRecord.id == skill_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else self._skill(row)

    async def add(self, skill: Skill) -> None:
        """Stage and flush one skill without committing."""
        self._session.add(self._record(skill))
        try:
            await self._session.flush()
        except IntegrityError as error:
            _map_integrity(error, path="slug")

    async def update(self, skill: Skill, values: SkillValues, *, now: datetime) -> Skill:
        """Stage complete values and increment the skill version."""
        row = await self._locked_record(skill.id)
        row.name = values.name
        row.slug = values.slug
        row.category_id = values.category_id
        row.description = values.description
        row.proficiency_label = values.proficiency_label
        row.proficiency_score = values.proficiency_score
        row.years_experience = values.years_experience
        row.icon_key = values.icon_key
        row.position = skill.position
        row.featured = values.featured
        row.visible = values.visible
        row.updated_at = now
        row.version += 1
        try:
            await self._session.flush()
        except IntegrityError as error:
            _map_integrity(error, path="slug")
        return self._skill(row)

    async def delete(self, skill: Skill) -> None:
        """Stage one skill deletion."""
        await self._session.execute(delete(SkillRecord).where(SkillRecord.id == skill.id))

    async def reorder(
        self,
        skills: tuple[Skill, ...],
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Skill, ...]:
        """Stage one category's complete normalized skill order."""
        del skills
        if not ordered_ids:
            return ()
        statement = select(SkillRecord).where(SkillRecord.id.in_(ordered_ids)).with_for_update()
        records = {
            record.id: record for record in (await self._session.execute(statement)).scalars()
        }
        for position, identifier in enumerate(ordered_ids):
            record = records[identifier]
            record.position = position
            record.updated_at = now
            record.version += 1
        await self._session.flush()
        return tuple(self._skill(records[identifier]) for identifier in ordered_ids)

    async def reference_summaries(
        self,
        skill_ids: tuple[UUID, ...],
    ) -> tuple[SkillReferenceSummary, ...]:
        """Resolve safe summaries while preserving requested order."""
        if not skill_ids:
            return ()
        statement = select(SkillRecord).where(SkillRecord.id.in_(skill_ids))
        records = {
            record.id: record for record in (await self._session.execute(statement)).scalars()
        }
        return tuple(
            SkillReferenceSummary(
                id=records[identifier].id,
                name=records[identifier].name,
                slug=records[identifier].slug,
                visible=records[identifier].visible,
            )
            for identifier in skill_ids
            if identifier in records
        )

    @staticmethod
    def _admin_predicates(query: AdminSkillQuery) -> list[ColumnElement[bool]]:
        predicates: list[ColumnElement[bool]] = []
        if query.category_id is not None:
            predicates.append(SkillRecord.category_id == query.category_id)
        if query.visible is not None:
            predicates.append(SkillRecord.visible.is_(query.visible))
        if query.featured is not None:
            predicates.append(SkillRecord.featured.is_(query.featured))
        if query.search is not None:
            predicates.append(func.lower(SkillRecord.name).contains(query.search.lower()))
        return predicates

    @staticmethod
    def _admin_order(sort: str) -> tuple[ColumnElement[Any], ...]:
        descending = sort.startswith("-")
        key = sort[1:] if descending else sort
        columns = {
            "position": SkillRecord.position,
            "name": SkillRecord.name,
            "created_at": SkillRecord.created_at,
            "updated_at": SkillRecord.updated_at,
            "id": SkillRecord.id,
        }
        column = columns[key]
        return ((column.desc() if descending else column.asc()), SkillRecord.id.asc())

    @staticmethod
    def _public_order(sort: str) -> tuple[ColumnElement[Any], ...]:
        descending = sort.startswith("-")
        key = sort[1:] if descending else sort
        columns = {
            "position": SkillRecord.position,
            "name": SkillRecord.name,
            "featured": SkillRecord.featured,
            "id": SkillRecord.id,
        }
        column = columns[key]
        return (
            SkillCategoryRecord.position.asc(),
            column.desc() if descending else column.asc(),
            SkillRecord.id.asc(),
        )

    async def _locked_record(self, skill_id: UUID) -> SkillRecord:
        statement = select(SkillRecord).where(SkillRecord.id == skill_id).with_for_update()
        return (await self._session.execute(statement)).scalar_one()

    @staticmethod
    def _record(skill: Skill) -> SkillRecord:
        return SkillRecord(
            id=skill.id,
            name=skill.name,
            slug=skill.slug,
            category_id=skill.category_id,
            description=skill.description,
            proficiency_label=skill.proficiency_label,
            proficiency_score=skill.proficiency_score,
            years_experience=skill.years_experience,
            icon_key=skill.icon_key,
            position=skill.position,
            featured=skill.featured,
            visible=skill.visible,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
            version=skill.version,
        )

    @staticmethod
    def _skill(row: SkillRecord) -> Skill:
        return Skill(
            id=row.id,
            name=row.name,
            slug=row.slug,
            category_id=row.category_id,
            description=row.description,
            proficiency_label=row.proficiency_label,
            proficiency_score=row.proficiency_score,
            years_experience=row.years_experience,
            icon_key=row.icon_key,
            position=row.position,
            featured=row.featured,
            visible=row.visible,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
        )


class SqlAlchemySkillsUnitOfWork:
    """Bind M4 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.categories: CategoryRepository
        self.skills: SkillRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository

    async def __aenter__(self) -> Self:
        """Open the transaction and bind repositories."""
        await self._inner.__aenter__()
        self.categories = CategoryRepository(self._inner.session)
        self.skills = SkillRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        """Commit at the application-service boundary."""
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Delegate rollback and resource cleanup."""
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemySkillsUnitOfWorkFactory:
    """Create structurally typed skills transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> SkillsUnitOfWork:
        """Return a fresh unopened skills transaction."""
        return cast("SkillsUnitOfWork", SqlAlchemySkillsUnitOfWork(self.session_factory))
