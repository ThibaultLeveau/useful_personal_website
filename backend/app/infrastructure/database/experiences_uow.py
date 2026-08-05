"""PostgreSQL repository and unit of work for professional experiences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from sqlalchemy import column, delete, exists, func, or_, select, table
from sqlalchemy.orm import aliased

from app.common.domain.pagination import Page
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.experiences import (
    ExperienceAchievementRecord,
    ExperienceRecord,
    ExperienceResponsibilityRecord,
    ExperienceRevisionRecord,
    ExperienceSkillRecord,
    ExperienceTechnologyRecord,
)
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.pagination import fetch_page
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.experiences.domain import (
    AdminExperienceQuery,
    EmploymentType,
    Experience,
    ExperienceLifecycle,
    ExperienceReferenceSummary,
    ExperienceRevision,
    ExperienceSnapshot,
    ExperienceValues,
    FrozenRevisionError,
    PublicExperienceQuery,
    PublicExperienceReference,
    RemoteStatus,
)
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from types import TracebackType
    from typing import Any
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.elements import ColumnElement

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.experiences.ports import ExperiencesUnitOfWork

_skill_table = table("skill", column("id"), column("slug"))


class ExperienceRepository:
    """Bound-query, immutable-revision PostgreSQL adapter."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind one transaction-owned session and opaque child-ID seam."""
        self._session = session
        self._id_factory = id_factory

    async def database_now(self) -> datetime:
        """Read PostgreSQL transaction time, never the application clock."""
        return (await self._session.execute(select(func.now()))).scalar_one()

    async def list_admin(self, query: AdminExperienceQuery) -> Page[ExperienceSnapshot]:
        """Return one exact filtered administrator page with bounded loading."""
        draft = aliased(ExperienceRevisionRecord, name="draft_revision")
        statement = select(ExperienceRecord).join(
            draft,
            draft.id == ExperienceRecord.draft_revision_id,
        )
        count_statement = (
            select(func.count())
            .select_from(ExperienceRecord)
            .join(
                draft,
                draft.id == ExperienceRecord.draft_revision_id,
            )
        )
        predicates = self._admin_predicates(query, draft)
        statement = statement.where(*predicates).order_by(*self._admin_order(query.sort, draft))
        count_statement = count_statement.where(*predicates)
        records = await fetch_page(
            self._session,
            ordered_statement=statement,
            count_statement=count_statement,
            request=query.page,
        )
        snapshots = await self._snapshots(records.items)
        return Page(items=snapshots, metadata=records.metadata)

    async def list_public(self, query: PublicExperienceQuery) -> Page[ExperienceSnapshot]:
        """Return only PostgreSQL-time-effective visible publication snapshots."""
        published = aliased(ExperienceRevisionRecord, name="published_revision")
        statement = select(ExperienceRecord).join(
            published,
            published.id == ExperienceRecord.published_revision_id,
        )
        count_statement = (
            select(func.count())
            .select_from(ExperienceRecord)
            .join(
                published,
                published.id == ExperienceRecord.published_revision_id,
            )
        )
        predicates: list[ColumnElement[bool]] = [
            ExperienceRecord.visible.is_(True),
            ExperienceRecord.deleted_at.is_(None),
            ExperienceRecord.published_revision_id.is_not(None),
            ExperienceRecord.publish_at.is_not(None),
            ExperienceRecord.publish_at <= func.now(),
            published.frozen.is_(True),
        ]
        if query.current is not None:
            predicates.append(published.current_position.is_(query.current))
        if query.employment_type is not None:
            predicates.append(published.employment_type == query.employment_type.value)
        if query.remote_status is not None:
            predicates.append(published.remote_status == query.remote_status.value)
        if query.skill_slug is not None:
            predicates.append(
                exists(
                    select(1)
                    .select_from(
                        ExperienceSkillRecord.__table__.join(
                            _skill_table,
                            _skill_table.c.id == ExperienceSkillRecord.skill_id,
                        )
                    )
                    .where(
                        ExperienceSkillRecord.revision_id == published.id,
                        _skill_table.c.slug == query.skill_slug,
                    )
                )
            )
        if query.sort in {"id", "-id"}:
            identifier = (
                ExperienceRecord.id.desc() if query.sort.startswith("-") else ExperienceRecord.id
            )
            statement = statement.where(*predicates).order_by(identifier)
        else:
            statement = statement.where(*predicates).order_by(
                published.current_position.desc(),
                published.start_date.desc(),
                published.end_date.desc().nulls_last(),
                ExperienceRecord.position,
                ExperienceRecord.id,
            )
        count_statement = count_statement.where(*predicates)
        records = await fetch_page(
            self._session,
            ordered_statement=statement,
            count_statement=count_statement,
            request=query.page,
        )
        snapshots = await self._snapshots(records.items)
        return Page(items=snapshots, metadata=records.metadata)

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Experience, ...]:
        """Return nondeleted aggregates in deterministic curated order."""
        statement = (
            select(ExperienceRecord)
            .where(ExperienceRecord.deleted_at.is_(None))
            .order_by(ExperienceRecord.position, ExperienceRecord.id)
        )
        if for_update:
            statement = statement.with_for_update()
        records = (await self._session.execute(statement)).scalars()
        return tuple(self._experience(row) for row in records)

    async def reference_summaries(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Return provider-owned labels and only database-time-effective public values."""
        if not experience_ids:
            return ()
        records = tuple(
            (
                await self._session.execute(
                    select(ExperienceRecord).where(ExperienceRecord.id.in_(experience_ids))
                )
            ).scalars()
        )
        snapshots = await self._snapshots(records)
        now = await self.database_now()
        by_id: dict[UUID, ExperienceReferenceSummary] = {}
        for snapshot in snapshots:
            aggregate = snapshot.experience
            published = snapshot.published
            effective = (
                aggregate.visible
                and aggregate.deleted_at is None
                and aggregate.publish_at is not None
                and aggregate.publish_at <= now
                and published is not None
                and published.frozen
                and aggregate.published_revision_id == published.id
            )
            by_id[aggregate.id] = ExperienceReferenceSummary(
                id=aggregate.id,
                company_name=snapshot.draft.values.company_name,
                role_title=snapshot.draft.values.role_title,
                visible=aggregate.visible,
                deleted=aggregate.deleted_at is not None,
                public=(
                    PublicExperienceReference(
                        id=aggregate.id,
                        company_name=published.values.company_name,
                        role_title=published.values.role_title,
                    )
                    if effective and published is not None
                    else None
                ),
            )
        return tuple(by_id[item] for item in experience_ids if item in by_id)

    async def get(
        self,
        experience_id: UUID,
        *,
        for_update: bool = False,
    ) -> ExperienceSnapshot | None:
        """Load one aggregate plus draft/publication in bounded queries."""
        statement = select(ExperienceRecord).where(ExperienceRecord.id == experience_id)
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            return None
        return (await self._snapshots((record,)))[0]

    async def add(self, experience: Experience, revision: ExperienceRevision) -> None:
        """Stage the circular aggregate/revision pair under deferrable pointers."""
        self._session.add(self._experience_record(experience))
        await self._add_revision(revision)
        await self._session.flush()

    async def save_draft(
        self,
        snapshot: ExperienceSnapshot,
        values: ExperienceValues,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Replace only mutable draft-owned rows and advance aggregate version."""
        revision = await self._locked_revision(snapshot.draft.id)
        if revision.frozen:
            raise FrozenRevisionError
        based_on = (
            snapshot.published.id
            if snapshot.published is not None and values == snapshot.published.values
            else None
        )
        self._set_revision_values(revision, values)
        revision.based_on_revision_id = based_on
        revision.updated_at = now
        await self._replace_children(revision.id, values)
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def publish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Freeze current draft and create the next mutable copy exactly once."""
        revision = await self._locked_revision(snapshot.draft.id)
        if revision.frozen:
            raise FrozenRevisionError
        revision.frozen = True
        revision.updated_at = now
        next_revision = ExperienceRevision(
            id=next_revision_id,
            experience_id=snapshot.experience.id,
            revision_number=snapshot.draft.revision_number + 1,
            based_on_revision_id=snapshot.draft.id,
            values=snapshot.draft.values,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        await self._add_revision(next_revision)
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.draft_revision_id = next_revision_id
        aggregate.published_revision_id = revision.id
        aggregate.publish_at = publish_at
        aggregate.unpublished_at = None
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def reschedule(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Update only aggregate schedule metadata."""
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.publish_at = publish_at
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def unpublish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Clear public pointers while preserving every revision row."""
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.published_revision_id = None
        aggregate.publish_at = None
        aggregate.unpublished_at = now
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def set_visibility(
        self,
        snapshot: ExperienceSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Update independent visibility without revision mutation."""
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.visible = visible
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def reorder(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Experience, ...]:
        """Normalize a complete order without committing."""
        statement = (
            select(ExperienceRecord).where(ExperienceRecord.id.in_(ordered_ids)).with_for_update()
        )
        records = {row.id: row for row in (await self._session.execute(statement)).scalars()}
        for position, identifier in enumerate(ordered_ids):
            record = records[identifier]
            record.position = position
            record.updated_at = now
            record.version += 1
        await self._session.flush()
        return tuple(self._experience(records[item]) for item in ordered_ids)

    async def soft_delete(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        """Soft-delete and clear public eligibility without deleting revisions."""
        aggregate = await self._locked_experience(snapshot.experience.id)
        aggregate.published_revision_id = None
        aggregate.publish_at = None
        aggregate.deleted_at = now
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    def _admin_predicates(
        self,
        query: AdminExperienceQuery,
        draft: type[ExperienceRevisionRecord],
    ) -> list[ColumnElement[bool]]:
        predicates = self._lifecycle_predicates(query.lifecycle, draft)
        if query.visible is not None:
            predicates.append(ExperienceRecord.visible.is_(query.visible))
        if query.current is not None:
            predicates.append(draft.current_position.is_(query.current))
        if query.employment_type is not None:
            predicates.append(draft.employment_type == query.employment_type.value)
        if query.remote_status is not None:
            predicates.append(draft.remote_status == query.remote_status.value)
        if query.skill_id is not None:
            predicates.append(
                exists(
                    select(1).where(
                        ExperienceSkillRecord.revision_id == draft.id,
                        ExperienceSkillRecord.skill_id == query.skill_id,
                    )
                )
            )
        if query.search is not None:
            pattern = f"%{query.search.casefold()}%"
            predicates.append(
                or_(
                    func.lower(draft.company_name).like(pattern),
                    func.lower(draft.role_title).like(pattern),
                    func.lower(draft.short_summary).like(pattern),
                )
            )
        return predicates

    @staticmethod
    def _lifecycle_predicates(
        lifecycle: ExperienceLifecycle | None,
        draft: type[ExperienceRevisionRecord],
    ) -> list[ColumnElement[bool]]:
        if lifecycle is ExperienceLifecycle.DELETED:
            return [ExperienceRecord.deleted_at.is_not(None)]
        predicates: list[ColumnElement[bool]] = [ExperienceRecord.deleted_at.is_(None)]
        if lifecycle is ExperienceLifecycle.DRAFT:
            predicates.extend(
                (
                    ExperienceRecord.published_revision_id.is_(None),
                    ExperienceRecord.unpublished_at.is_(None),
                )
            )
        elif lifecycle is ExperienceLifecycle.UNPUBLISHED:
            predicates.extend(
                (
                    ExperienceRecord.published_revision_id.is_(None),
                    ExperienceRecord.unpublished_at.is_not(None),
                )
            )
        elif lifecycle is ExperienceLifecycle.SCHEDULED:
            predicates.extend(
                (
                    ExperienceRecord.published_revision_id.is_not(None),
                    ExperienceRecord.publish_at > func.now(),
                )
            )
        elif lifecycle is ExperienceLifecycle.PUBLISHED:
            predicates.extend(
                (
                    ExperienceRecord.published_revision_id.is_not(None),
                    ExperienceRecord.publish_at <= func.now(),
                    draft.based_on_revision_id == ExperienceRecord.published_revision_id,
                )
            )
        elif lifecycle is ExperienceLifecycle.PUBLISHED_CHANGES_PENDING:
            predicates.extend(
                (
                    ExperienceRecord.published_revision_id.is_not(None),
                    ExperienceRecord.publish_at <= func.now(),
                    or_(
                        draft.based_on_revision_id.is_(None),
                        draft.based_on_revision_id != ExperienceRecord.published_revision_id,
                    ),
                )
            )
        return predicates

    @staticmethod
    def _admin_order(
        sort: str,
        draft: type[ExperienceRevisionRecord],
    ) -> tuple[ColumnElement[Any], ...]:
        descending = sort.startswith("-")
        key = sort[1:] if descending else sort
        columns = {
            "position": ExperienceRecord.position,
            "company_name": draft.company_name,
            "role_title": draft.role_title,
            "start_date": draft.start_date,
            "updated_at": ExperienceRecord.updated_at,
            "id": ExperienceRecord.id,
        }
        selected = columns[key]
        return (
            selected.desc() if descending else selected.asc(),
            ExperienceRecord.id.asc(),
        )

    async def _snapshots(
        self,
        aggregate_records: Sequence[ExperienceRecord],
    ) -> tuple[ExperienceSnapshot, ...]:
        if not aggregate_records:
            return ()
        revision_ids = {
            revision_id
            for aggregate in aggregate_records
            for revision_id in (
                aggregate.draft_revision_id,
                aggregate.published_revision_id,
            )
            if revision_id is not None
        }
        revision_records = tuple(
            (
                await self._session.execute(
                    select(ExperienceRevisionRecord).where(
                        ExperienceRevisionRecord.id.in_(revision_ids)
                    )
                )
            ).scalars()
        )
        responsibilities = await self._ordered_values(
            ExperienceResponsibilityRecord,
            revision_ids,
        )
        achievements = await self._ordered_values(
            ExperienceAchievementRecord,
            revision_ids,
        )
        technologies = await self._ordered_values(
            ExperienceTechnologyRecord,
            revision_ids,
        )
        skills = await self._ordered_skill_ids(revision_ids)
        revisions = {
            row.id: self._revision(
                row,
                responsibilities.get(row.id, ()),
                achievements.get(row.id, ()),
                technologies.get(row.id, ()),
                skills.get(row.id, ()),
            )
            for row in revision_records
        }
        return tuple(
            ExperienceSnapshot(
                experience=self._experience(aggregate),
                draft=revisions[aggregate.draft_revision_id],
                published=(
                    revisions[aggregate.published_revision_id]
                    if aggregate.published_revision_id is not None
                    else None
                ),
            )
            for aggregate in aggregate_records
        )

    async def _ordered_values(
        self,
        record_type: type[Any],
        revision_ids: set[UUID],
    ) -> dict[UUID, tuple[str, ...]]:
        statement = (
            select(record_type)
            .where(record_type.revision_id.in_(revision_ids))
            .order_by(record_type.revision_id, record_type.position, record_type.id)
        )
        grouped: dict[UUID, list[str]] = {}
        for row in (await self._session.execute(statement)).scalars():
            grouped.setdefault(row.revision_id, []).append(row.value)
        return {key: tuple(values) for key, values in grouped.items()}

    async def _ordered_skill_ids(
        self,
        revision_ids: set[UUID],
    ) -> dict[UUID, tuple[UUID, ...]]:
        statement = (
            select(ExperienceSkillRecord)
            .where(ExperienceSkillRecord.revision_id.in_(revision_ids))
            .order_by(
                ExperienceSkillRecord.revision_id,
                ExperienceSkillRecord.position,
                ExperienceSkillRecord.id,
            )
        )
        grouped: dict[UUID, list[UUID]] = {}
        for row in (await self._session.execute(statement)).scalars():
            grouped.setdefault(row.revision_id, []).append(row.skill_id)
        return {key: tuple(values) for key, values in grouped.items()}

    async def _replace_children(self, revision_id: UUID, values: ExperienceValues) -> None:
        for record_type in (
            ExperienceResponsibilityRecord,
            ExperienceAchievementRecord,
            ExperienceTechnologyRecord,
            ExperienceSkillRecord,
        ):
            await self._session.execute(
                delete(record_type).where(record_type.revision_id == revision_id)
            )
        self._add_children(revision_id, values)

    async def _add_revision(self, revision: ExperienceRevision) -> None:
        values = revision.values
        record = ExperienceRevisionRecord(
            id=revision.id,
            experience_id=revision.experience_id,
            revision_number=revision.revision_number,
            based_on_revision_id=revision.based_on_revision_id,
            company_name=values.company_name,
            company_url=values.company_url,
            role_title=values.role_title,
            employment_type=values.employment_type.value,
            location=values.location,
            remote_status=values.remote_status.value,
            start_date=values.start_date,
            end_date=values.end_date,
            current_position=values.current_position,
            short_summary=values.short_summary,
            detailed_description=values.detailed_description,
            frozen=revision.frozen,
            created_by=revision.created_by,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )
        self._session.add(record)
        # No ORM relationships cross this immutable aggregate boundary. Flush
        # the parent revision explicitly before staging its ordered child rows.
        await self._session.flush((record,))
        self._add_children(revision.id, values)

    def _add_children(self, revision_id: UUID, values: ExperienceValues) -> None:
        for position, value in enumerate(values.responsibilities):
            self._session.add(
                ExperienceResponsibilityRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    position=position,
                    value=value,
                )
            )
        for position, value in enumerate(values.achievements):
            self._session.add(
                ExperienceAchievementRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    position=position,
                    value=value,
                )
            )
        for position, value in enumerate(values.technologies):
            self._session.add(
                ExperienceTechnologyRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    position=position,
                    value=value,
                )
            )
        for position, skill_id in enumerate(values.skill_ids):
            self._session.add(
                ExperienceSkillRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    skill_id=skill_id,
                    position=position,
                )
            )

    @staticmethod
    def _set_revision_values(
        record: ExperienceRevisionRecord,
        values: ExperienceValues,
    ) -> None:
        record.company_name = values.company_name
        record.company_url = values.company_url
        record.role_title = values.role_title
        record.employment_type = values.employment_type.value
        record.location = values.location
        record.remote_status = values.remote_status.value
        record.start_date = values.start_date
        record.end_date = values.end_date
        record.current_position = values.current_position
        record.short_summary = values.short_summary
        record.detailed_description = values.detailed_description

    async def _locked_experience(self, experience_id: UUID) -> ExperienceRecord:
        statement = (
            select(ExperienceRecord).where(ExperienceRecord.id == experience_id).with_for_update()
        )
        return (await self._session.execute(statement)).scalar_one()

    async def _locked_revision(self, revision_id: UUID) -> ExperienceRevisionRecord:
        statement = (
            select(ExperienceRevisionRecord)
            .where(ExperienceRevisionRecord.id == revision_id)
            .with_for_update()
        )
        return (await self._session.execute(statement)).scalar_one()

    @staticmethod
    def _experience(row: ExperienceRecord) -> Experience:
        return Experience(
            id=row.id,
            visible=row.visible,
            position=row.position,
            draft_revision_id=row.draft_revision_id,
            published_revision_id=row.published_revision_id,
            publish_at=row.publish_at,
            unpublished_at=row.unpublished_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def _experience_record(value: Experience) -> ExperienceRecord:
        return ExperienceRecord(
            id=value.id,
            visible=value.visible,
            position=value.position,
            draft_revision_id=value.draft_revision_id,
            published_revision_id=value.published_revision_id,
            publish_at=value.publish_at,
            unpublished_at=value.unpublished_at,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=value.version,
            deleted_at=value.deleted_at,
        )

    @staticmethod
    def _revision(
        row: ExperienceRevisionRecord,
        responsibilities: tuple[str, ...],
        achievements: tuple[str, ...],
        technologies: tuple[str, ...],
        skill_ids: tuple[UUID, ...],
    ) -> ExperienceRevision:
        return ExperienceRevision(
            id=row.id,
            experience_id=row.experience_id,
            revision_number=row.revision_number,
            based_on_revision_id=row.based_on_revision_id,
            values=ExperienceValues(
                company_name=row.company_name,
                company_url=row.company_url,
                role_title=row.role_title,
                employment_type=EmploymentType(row.employment_type),
                location=row.location,
                remote_status=RemoteStatus(row.remote_status),
                start_date=row.start_date,
                end_date=row.end_date,
                current_position=row.current_position,
                short_summary=row.short_summary,
                detailed_description=row.detailed_description,
                responsibilities=responsibilities,
                achievements=achievements,
                technologies=technologies,
                skill_ids=skill_ids,
            ),
            frozen=row.frozen,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SqlAlchemyExperiencesUnitOfWork:
    """Bind M5 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.experiences: ExperienceRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository

    async def __aenter__(self) -> Self:
        """Open the transaction and bind repositories."""
        await self._inner.__aenter__()
        self.experiences = ExperienceRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        return self

    async def commit(self) -> None:
        """Commit only at the application-service boundary."""
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
class SqlAlchemyExperiencesUnitOfWorkFactory:
    """Create structurally typed experience transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> ExperiencesUnitOfWork:
        """Return a fresh unopened experience transaction."""
        return cast(
            "ExperiencesUnitOfWork",
            SqlAlchemyExperiencesUnitOfWork(self.session_factory),
        )
