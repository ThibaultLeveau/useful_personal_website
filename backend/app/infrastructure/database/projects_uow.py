"""PostgreSQL repository and unit of work for project case studies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from sqlalchemy import column, delete, exists, func, or_, select, table
from sqlalchemy.orm import aliased

from app.common.domain.pagination import Page
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.media import MediaRepository
from app.infrastructure.database.pagination import fetch_page
from app.infrastructure.database.projects import (
    ProjectExperienceRecord,
    ProjectRecord,
    ProjectRevisionMediaRecord,
    ProjectRevisionRecord,
    ProjectSkillRecord,
    ProjectTechnologyRecord,
    RelatedProjectRecord,
)
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.identity.domain import uuid7
from app.modules.projects.domain import (
    AdminProjectQuery,
    FrozenProjectRevisionError,
    Project,
    ProjectLifecycle,
    ProjectReferenceSummary,
    ProjectRevision,
    ProjectSnapshot,
    ProjectStatus,
    ProjectValues,
    PublicProjectQuery,
    PublicProjectReference,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from types import TracebackType
    from typing import Any
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.elements import ColumnElement

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.projects.ports import ProjectsUnitOfWork

_skill_table = table("skill", column("id"), column("slug"))
_GRAPH_LOCK_KEY = 6007
_MAXIMUM_RELATIONS_PER_PROJECT = 50


class ProjectRepository:
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
        """Read PostgreSQL transaction time."""
        return (await self._session.execute(select(func.now()))).scalar_one()

    async def slug_exists(self, slug: str) -> bool:
        """Check the normalized immutable slug including soft-deleted reservations."""
        return bool(
            (
                await self._session.execute(
                    select(exists().where(func.lower(ProjectRecord.slug) == slug.casefold()))
                )
            ).scalar_one()
        )

    async def list_admin(self, query: AdminProjectQuery) -> Page[ProjectSnapshot]:
        """Return one exact filtered administrator page."""
        draft = aliased(ProjectRevisionRecord, name="draft_revision")
        statement = select(ProjectRecord).join(draft, draft.id == ProjectRecord.draft_revision_id)
        count_statement = (
            select(func.count())
            .select_from(ProjectRecord)
            .join(draft, draft.id == ProjectRecord.draft_revision_id)
        )
        predicates = self._admin_predicates(query, draft)
        statement = statement.where(*predicates).order_by(*self._admin_order(query.sort, draft))
        records = await fetch_page(
            self._session,
            ordered_statement=statement,
            count_statement=count_statement.where(*predicates),
            request=query.page,
        )
        return Page(items=await self._snapshots(records.items), metadata=records.metadata)

    async def list_public(self, query: PublicProjectQuery) -> Page[ProjectSnapshot]:
        """Return only database-time-effective public projects."""
        published = aliased(ProjectRevisionRecord, name="published_revision")
        statement = select(ProjectRecord).join(
            published, published.id == ProjectRecord.published_revision_id
        )
        count_statement = (
            select(func.count())
            .select_from(ProjectRecord)
            .join(published, published.id == ProjectRecord.published_revision_id)
        )
        predicates: list[ColumnElement[bool]] = [
            ProjectRecord.visible.is_(True),
            ProjectRecord.deleted_at.is_(None),
            ProjectRecord.published_revision_id.is_not(None),
            ProjectRecord.publish_at.is_not(None),
            ProjectRecord.publish_at <= func.now(),
            published.frozen.is_(True),
        ]
        if query.status is not None:
            predicates.append(published.status == query.status.value)
        if query.featured is not None:
            predicates.append(ProjectRecord.featured.is_(query.featured))
        if query.technology is not None:
            predicates.append(
                exists(
                    select(1).where(
                        ProjectTechnologyRecord.revision_id == published.id,
                        func.lower(ProjectTechnologyRecord.value) == query.technology.casefold(),
                    )
                )
            )
        if query.skill_slug is not None:
            predicates.append(
                exists(
                    select(1)
                    .select_from(
                        ProjectSkillRecord.__table__.join(
                            _skill_table, _skill_table.c.id == ProjectSkillRecord.skill_id
                        )
                    )
                    .where(
                        ProjectSkillRecord.revision_id == published.id,
                        _skill_table.c.slug == query.skill_slug,
                    )
                )
            )
        if query.experience_id is not None:
            predicates.append(
                exists(
                    select(1).where(
                        ProjectExperienceRecord.revision_id == published.id,
                        ProjectExperienceRecord.experience_id == query.experience_id,
                    )
                )
            )
        if query.search is not None:
            pattern = f"%{query.search.casefold()}%"
            predicates.append(
                or_(
                    func.lower(published.name).like(pattern),
                    func.lower(published.short_description).like(pattern),
                )
            )
        if query.sort in {"id", "-id"}:
            key = ProjectRecord.id.desc() if query.sort.startswith("-") else ProjectRecord.id
            order: tuple[Any, ...] = (key,)
        elif query.sort == "-start_date":
            order = (published.start_date.desc(), ProjectRecord.id)
        else:
            order = (
                ProjectRecord.featured.desc(),
                ProjectRecord.position,
                published.start_date.desc(),
                ProjectRecord.id,
            )
        records = await fetch_page(
            self._session,
            ordered_statement=statement.where(*predicates).order_by(*order),
            count_statement=count_statement.where(*predicates),
            request=query.page,
        )
        return Page(items=await self._snapshots(records.items), metadata=records.metadata)

    async def get(self, project_id: UUID, *, for_update: bool = False) -> ProjectSnapshot | None:
        """Load one aggregate plus draft and optional publication."""
        statement = select(ProjectRecord).where(ProjectRecord.id == project_id)
        if for_update:
            statement = statement.with_for_update()
        record = (await self._session.execute(statement)).scalar_one_or_none()
        return None if record is None else (await self._snapshots((record,)))[0]

    async def get_public_by_slug(self, slug: str) -> ProjectSnapshot | None:
        """Resolve a public slug with all eligibility rules in SQL."""
        published = aliased(ProjectRevisionRecord, name="published_revision")
        record = (
            await self._session.execute(
                select(ProjectRecord)
                .join(published, published.id == ProjectRecord.published_revision_id)
                .where(
                    ProjectRecord.slug == slug,
                    ProjectRecord.visible.is_(True),
                    ProjectRecord.deleted_at.is_(None),
                    ProjectRecord.publish_at.is_not(None),
                    ProjectRecord.publish_at <= func.now(),
                    published.frozen.is_(True),
                )
            )
        ).scalar_one_or_none()
        return None if record is None else (await self._snapshots((record,)))[0]

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Project, ...]:
        """Return nondeleted aggregates in curated order."""
        statement = (
            select(ProjectRecord)
            .where(ProjectRecord.deleted_at.is_(None))
            .order_by(ProjectRecord.position, ProjectRecord.id)
        )
        if for_update:
            statement = statement.with_for_update()
        return tuple(
            self._project(row) for row in (await self._session.execute(statement)).scalars()
        )

    async def reference_summaries(
        self, project_ids: tuple[UUID, ...]
    ) -> tuple[ProjectReferenceSummary, ...]:
        """Return admin labels and optional effective public summaries."""
        if not project_ids:
            return ()
        records = tuple(
            (
                await self._session.execute(
                    select(ProjectRecord).where(ProjectRecord.id.in_(project_ids))
                )
            ).scalars()
        )
        now = await self.database_now()
        by_id: dict[UUID, ProjectReferenceSummary] = {}
        for snapshot in await self._snapshots(records):
            aggregate = snapshot.project
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
            by_id[aggregate.id] = ProjectReferenceSummary(
                id=aggregate.id,
                slug=aggregate.slug,
                name=snapshot.draft.values.name,
                visible=aggregate.visible,
                deleted=aggregate.deleted_at is not None,
                public=(
                    PublicProjectReference(
                        id=aggregate.id, slug=aggregate.slug, name=published.values.name
                    )
                    if effective and published is not None
                    else None
                ),
            )
        return tuple(by_id[item] for item in project_ids if item in by_id)

    async def related_graph_would_cycle(
        self,
        source_id: UUID,
        target_ids: tuple[UUID, ...],
        *,
        maximum_nodes: int,
    ) -> bool:
        """Serialize and inspect the bounded graph built from current drafts."""
        await self._session.execute(select(func.pg_advisory_xact_lock(_GRAPH_LOCK_KEY)))
        row_limit = maximum_nodes * _MAXIMUM_RELATIONS_PER_PROJECT + 1
        rows = tuple(
            (
                await self._session.execute(
                    select(
                        RelatedProjectRecord.project_id,
                        RelatedProjectRecord.related_project_id,
                    )
                    .join(
                        ProjectRecord,
                        ProjectRecord.draft_revision_id == RelatedProjectRecord.revision_id,
                    )
                    .where(
                        ProjectRecord.deleted_at.is_(None),
                        RelatedProjectRecord.project_id != source_id,
                    )
                    .order_by(
                        RelatedProjectRecord.project_id,
                        RelatedProjectRecord.related_project_id,
                    )
                    .limit(row_limit)
                )
            ).all()
        )
        if len(rows) == row_limit:
            return True
        graph: dict[UUID, set[UUID]] = {source_id: set(target_ids)}
        nodes: set[UUID] = {source_id, *target_ids}
        for source, target in rows:
            graph.setdefault(source, set()).add(target)
            nodes.update((source, target))
            if len(nodes) > maximum_nodes:
                return True
        frontier = list(target_ids)
        visited: set[UUID] = set()
        while frontier:
            node = frontier.pop()
            if node == source_id:
                return True
            if node in visited:
                continue
            visited.add(node)
            frontier.extend(graph.get(node, ()))
        return False

    async def add(self, project: Project, revision: ProjectRevision) -> None:
        """Stage the circular aggregate/revision pair."""
        self._session.add(self._project_record(project))
        await self._add_revision(revision)
        await self._session.flush()

    async def save_draft(
        self, snapshot: ProjectSnapshot, values: ProjectValues, *, now: datetime
    ) -> ProjectSnapshot:
        """Replace mutable draft values and children."""
        revision = await self._locked_revision(snapshot.draft.id)
        if revision.frozen:
            raise FrozenProjectRevisionError
        revision.based_on_revision_id = (
            snapshot.published.id
            if snapshot.published is not None and values == snapshot.published.values
            else None
        )
        self._set_revision_values(revision, values)
        revision.updated_at = now
        await self._replace_children(revision.id, snapshot.project.id, values)
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def publish(
        self,
        snapshot: ProjectSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ProjectSnapshot:
        """Freeze current draft and create its next mutable copy."""
        revision = await self._locked_revision(snapshot.draft.id)
        if revision.frozen:
            raise FrozenProjectRevisionError
        revision.frozen = True
        revision.updated_at = now
        await self._add_revision(
            ProjectRevision(
                id=next_revision_id,
                project_id=snapshot.project.id,
                revision_number=snapshot.draft.revision_number + 1,
                based_on_revision_id=snapshot.draft.id,
                values=snapshot.draft.values,
                frozen=False,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
        )
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.draft_revision_id = next_revision_id
        aggregate.published_revision_id = revision.id
        aggregate.publish_at = publish_at
        aggregate.unpublished_at = None
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def reschedule(
        self, snapshot: ProjectSnapshot, *, publish_at: datetime, now: datetime
    ) -> ProjectSnapshot:
        """Change schedule metadata only."""
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.publish_at = publish_at
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def unpublish(self, snapshot: ProjectSnapshot, *, now: datetime) -> ProjectSnapshot:
        """Clear public pointers without deleting revisions."""
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.published_revision_id = None
        aggregate.publish_at = None
        aggregate.unpublished_at = now
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def set_visibility(
        self, snapshot: ProjectSnapshot, *, visible: bool, now: datetime
    ) -> ProjectSnapshot:
        """Set visibility independently from publication."""
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.visible = visible
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def set_featured(
        self, snapshot: ProjectSnapshot, *, featured: bool, now: datetime
    ) -> ProjectSnapshot:
        """Set featured independently from eligibility."""
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.featured = featured
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    async def reorder(self, ordered_ids: tuple[UUID, ...], *, now: datetime) -> tuple[Project, ...]:
        """Normalize complete curated order without committing."""
        rows = {
            row.id: row
            for row in (
                await self._session.execute(
                    select(ProjectRecord).where(ProjectRecord.id.in_(ordered_ids)).with_for_update()
                )
            ).scalars()
        }
        for position, identifier in enumerate(ordered_ids):
            row = rows[identifier]
            row.position = position
            row.updated_at = now
            row.version += 1
        await self._session.flush()
        return tuple(self._project(rows[item]) for item in ordered_ids)

    async def soft_delete(self, snapshot: ProjectSnapshot, *, now: datetime) -> ProjectSnapshot:
        """Soft-delete while preserving route and revision history."""
        aggregate = await self._locked_project(snapshot.project.id)
        aggregate.published_revision_id = None
        aggregate.publish_at = None
        aggregate.deleted_at = now
        aggregate.updated_at = now
        aggregate.version += 1
        await self._session.flush()
        return (await self._snapshots((aggregate,)))[0]

    def _admin_predicates(
        self, query: AdminProjectQuery, draft: type[ProjectRevisionRecord]
    ) -> list[ColumnElement[bool]]:
        predicates = self._lifecycle_predicates(query.lifecycle, draft)
        if query.visible is not None:
            predicates.append(ProjectRecord.visible.is_(query.visible))
        if query.featured is not None:
            predicates.append(ProjectRecord.featured.is_(query.featured))
        if query.status is not None:
            predicates.append(draft.status == query.status.value)
        if query.skill_id is not None:
            predicates.append(
                exists(
                    select(1).where(
                        ProjectSkillRecord.revision_id == draft.id,
                        ProjectSkillRecord.skill_id == query.skill_id,
                    )
                )
            )
        if query.experience_id is not None:
            predicates.append(
                exists(
                    select(1).where(
                        ProjectExperienceRecord.revision_id == draft.id,
                        ProjectExperienceRecord.experience_id == query.experience_id,
                    )
                )
            )
        if query.search is not None:
            pattern = f"%{query.search.casefold()}%"
            predicates.append(
                or_(
                    func.lower(draft.name).like(pattern),
                    func.lower(draft.short_description).like(pattern),
                    func.lower(ProjectRecord.slug).like(pattern),
                )
            )
        return predicates

    @staticmethod
    def _lifecycle_predicates(
        lifecycle: ProjectLifecycle | None, draft: type[ProjectRevisionRecord]
    ) -> list[ColumnElement[bool]]:
        if lifecycle is ProjectLifecycle.DELETED:
            return [ProjectRecord.deleted_at.is_not(None)]
        values: list[ColumnElement[bool]] = [ProjectRecord.deleted_at.is_(None)]
        if lifecycle is ProjectLifecycle.DRAFT:
            values += [
                ProjectRecord.published_revision_id.is_(None),
                ProjectRecord.unpublished_at.is_(None),
            ]
        elif lifecycle is ProjectLifecycle.UNPUBLISHED:
            values += [
                ProjectRecord.published_revision_id.is_(None),
                ProjectRecord.unpublished_at.is_not(None),
            ]
        elif lifecycle is ProjectLifecycle.SCHEDULED:
            values += [
                ProjectRecord.published_revision_id.is_not(None),
                ProjectRecord.publish_at > func.now(),
            ]
        elif lifecycle is ProjectLifecycle.PUBLISHED:
            values += [
                ProjectRecord.published_revision_id.is_not(None),
                ProjectRecord.publish_at <= func.now(),
                draft.based_on_revision_id == ProjectRecord.published_revision_id,
            ]
        elif lifecycle is ProjectLifecycle.PUBLISHED_CHANGES_PENDING:
            values += [
                ProjectRecord.published_revision_id.is_not(None),
                ProjectRecord.publish_at <= func.now(),
                or_(
                    draft.based_on_revision_id.is_(None),
                    draft.based_on_revision_id != ProjectRecord.published_revision_id,
                ),
            ]
        return values

    @staticmethod
    def _admin_order(
        sort: str, draft: type[ProjectRevisionRecord]
    ) -> tuple[ColumnElement[Any], ...]:
        descending = sort.startswith("-")
        key = sort[1:] if descending else sort
        selected = {
            "position": ProjectRecord.position,
            "name": draft.name,
            "status": draft.status,
            "start_date": draft.start_date,
            "updated_at": ProjectRecord.updated_at,
            "id": ProjectRecord.id,
        }[key]
        return (selected.desc() if descending else selected.asc(), ProjectRecord.id.asc())

    async def _snapshots(self, aggregates: Sequence[ProjectRecord]) -> tuple[ProjectSnapshot, ...]:
        if not aggregates:
            return ()
        revision_ids = {
            identifier
            for aggregate in aggregates
            for identifier in (aggregate.draft_revision_id, aggregate.published_revision_id)
            if identifier is not None
        }
        revisions = tuple(
            (
                await self._session.execute(
                    select(ProjectRevisionRecord).where(ProjectRevisionRecord.id.in_(revision_ids))
                )
            ).scalars()
        )
        technologies = await self._ordered_values(revision_ids)
        skills = await self._ordered_ids(ProjectSkillRecord, "skill_id", revision_ids)
        experiences = await self._ordered_ids(
            ProjectExperienceRecord, "experience_id", revision_ids
        )
        related = await self._ordered_ids(RelatedProjectRecord, "related_project_id", revision_ids)
        media = await self._project_media(revision_ids)
        by_id = {
            row.id: self._revision(
                row,
                technologies.get(row.id, ()),
                skills.get(row.id, ()),
                experiences.get(row.id, ()),
                related.get(row.id, ()),
                media.get(row.id, (None, ())),
            )
            for row in revisions
        }
        return tuple(
            ProjectSnapshot(
                project=self._project(row),
                draft=by_id[row.draft_revision_id],
                published=(
                    by_id[row.published_revision_id]
                    if row.published_revision_id is not None
                    else None
                ),
            )
            for row in aggregates
        )

    async def _ordered_values(self, revision_ids: set[UUID]) -> dict[UUID, tuple[str, ...]]:
        statement = (
            select(ProjectTechnologyRecord)
            .where(ProjectTechnologyRecord.revision_id.in_(revision_ids))
            .order_by(
                ProjectTechnologyRecord.revision_id,
                ProjectTechnologyRecord.position,
                ProjectTechnologyRecord.id,
            )
        )
        grouped: dict[UUID, list[str]] = {}
        for row in (await self._session.execute(statement)).scalars():
            grouped.setdefault(row.revision_id, []).append(row.value)
        return {key: tuple(values) for key, values in grouped.items()}

    async def _project_media(
        self, revision_ids: set[UUID]
    ) -> dict[UUID, tuple[UUID | None, tuple[UUID, ...]]]:
        statement = (
            select(ProjectRevisionMediaRecord)
            .where(ProjectRevisionMediaRecord.revision_id.in_(revision_ids))
            .order_by(
                ProjectRevisionMediaRecord.revision_id,
                ProjectRevisionMediaRecord.role,
                ProjectRevisionMediaRecord.position,
                ProjectRevisionMediaRecord.id,
            )
        )
        covers: dict[UUID, UUID] = {}
        screenshots: dict[UUID, list[UUID]] = {}
        for row in (await self._session.execute(statement)).scalars():
            if row.role == "project_cover":
                covers[row.revision_id] = row.media_id
            else:
                screenshots.setdefault(row.revision_id, []).append(row.media_id)
        return {
            revision_id: (covers.get(revision_id), tuple(screenshots.get(revision_id, [])))
            for revision_id in revision_ids
        }

    async def _ordered_ids(
        self, record_type: type[Any], attribute: str, revision_ids: set[UUID]
    ) -> dict[UUID, tuple[UUID, ...]]:
        statement = (
            select(record_type)
            .where(record_type.revision_id.in_(revision_ids))
            .order_by(record_type.revision_id, record_type.position, record_type.id)
        )
        grouped: dict[UUID, list[UUID]] = {}
        for row in (await self._session.execute(statement)).scalars():
            grouped.setdefault(row.revision_id, []).append(getattr(row, attribute))
        return {key: tuple(values) for key, values in grouped.items()}

    async def _replace_children(
        self, revision_id: UUID, project_id: UUID, values: ProjectValues
    ) -> None:
        for record_type in (
            ProjectTechnologyRecord,
            ProjectSkillRecord,
            ProjectExperienceRecord,
            RelatedProjectRecord,
            ProjectRevisionMediaRecord,
        ):
            await self._session.execute(
                delete(record_type).where(record_type.revision_id == revision_id)
            )
        self._add_children(revision_id, project_id, values)

    async def _add_revision(self, revision: ProjectRevision) -> None:
        values = revision.values
        row = ProjectRevisionRecord(
            id=revision.id,
            project_id=revision.project_id,
            revision_number=revision.revision_number,
            based_on_revision_id=revision.based_on_revision_id,
            name=values.name,
            short_description=values.short_description,
            full_description=values.full_description,
            problem=values.problem,
            solution=values.solution,
            impact=values.impact,
            owner_role=values.owner_role,
            architecture=values.architecture,
            status=values.status.value,
            start_date=values.start_date,
            end_date=values.end_date,
            repository_url=values.repository_url,
            demo_url=values.demo_url,
            seo_title=values.seo_title,
            seo_description=values.seo_description,
            canonical_url=values.canonical_url,
            frozen=revision.frozen,
            created_by=revision.created_by,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )
        self._session.add(row)
        await self._session.flush((row,))
        self._add_children(revision.id, revision.project_id, values)

    def _add_children(self, revision_id: UUID, project_id: UUID, values: ProjectValues) -> None:
        for position, value in enumerate(values.technologies):
            self._session.add(
                ProjectTechnologyRecord(
                    id=self._id_factory(), revision_id=revision_id, position=position, value=value
                )
            )
        for record_type, identifiers, attribute in (
            (ProjectSkillRecord, values.skill_ids, "skill_id"),
            (ProjectExperienceRecord, values.experience_ids, "experience_id"),
        ):
            for position, identifier in enumerate(identifiers):
                self._session.add(
                    record_type(
                        id=self._id_factory(),
                        revision_id=revision_id,
                        position=position,
                        **{attribute: identifier},
                    )
                )
        for position, identifier in enumerate(values.related_project_ids):
            self._session.add(
                RelatedProjectRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    project_id=project_id,
                    related_project_id=identifier,
                    position=position,
                )
            )
        if values.cover_media_id is not None:
            self._session.add(
                ProjectRevisionMediaRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    media_id=values.cover_media_id,
                    role="project_cover",
                    position=0,
                )
            )
        for position, identifier in enumerate(values.screenshot_media_ids):
            self._session.add(
                ProjectRevisionMediaRecord(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    media_id=identifier,
                    role="project_screenshot",
                    position=position,
                )
            )

    @staticmethod
    def _set_revision_values(row: ProjectRevisionRecord, values: ProjectValues) -> None:
        row.name = values.name
        row.short_description = values.short_description
        row.full_description = values.full_description
        row.problem = values.problem
        row.solution = values.solution
        row.impact = values.impact
        row.owner_role = values.owner_role
        row.architecture = values.architecture
        row.status = values.status.value
        row.start_date = values.start_date
        row.end_date = values.end_date
        row.repository_url = values.repository_url
        row.demo_url = values.demo_url
        row.seo_title = values.seo_title
        row.seo_description = values.seo_description
        row.canonical_url = values.canonical_url

    async def _locked_project(self, project_id: UUID) -> ProjectRecord:
        return (
            await self._session.execute(
                select(ProjectRecord).where(ProjectRecord.id == project_id).with_for_update()
            )
        ).scalar_one()

    async def _locked_revision(self, revision_id: UUID) -> ProjectRevisionRecord:
        return (
            await self._session.execute(
                select(ProjectRevisionRecord)
                .where(ProjectRevisionRecord.id == revision_id)
                .with_for_update()
            )
        ).scalar_one()

    @staticmethod
    def _project(row: ProjectRecord) -> Project:
        return Project(
            id=row.id,
            slug=row.slug,
            visible=row.visible,
            featured=row.featured,
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
    def _project_record(value: Project) -> ProjectRecord:
        return ProjectRecord(
            id=value.id,
            slug=value.slug,
            visible=value.visible,
            featured=value.featured,
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
    def _revision(  # noqa: PLR0913, PLR0917
        row: ProjectRevisionRecord,
        technologies: tuple[str, ...],
        skill_ids: tuple[UUID, ...],
        experience_ids: tuple[UUID, ...],
        related_project_ids: tuple[UUID, ...],
        media: tuple[UUID | None, tuple[UUID, ...]],
    ) -> ProjectRevision:
        return ProjectRevision(
            id=row.id,
            project_id=row.project_id,
            revision_number=row.revision_number,
            based_on_revision_id=row.based_on_revision_id,
            values=ProjectValues(
                name=row.name,
                short_description=row.short_description,
                full_description=row.full_description,
                problem=row.problem,
                solution=row.solution,
                impact=row.impact,
                owner_role=row.owner_role,
                architecture=row.architecture,
                technologies=technologies,
                status=ProjectStatus(row.status),
                start_date=row.start_date,
                end_date=row.end_date,
                repository_url=row.repository_url,
                demo_url=row.demo_url,
                skill_ids=skill_ids,
                experience_ids=experience_ids,
                related_project_ids=related_project_ids,
                seo_title=row.seo_title,
                seo_description=row.seo_description,
                canonical_url=row.canonical_url,
                cover_media_id=media[0],
                screenshot_media_ids=media[1],
            ),
            frozen=row.frozen,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SqlAlchemyProjectsUnitOfWork:
    """Bind M6 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.projects: ProjectRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository
        self.media: MediaRepository

    async def __aenter__(self) -> Self:
        """Open the transaction and bind repositories."""
        await self._inner.__aenter__()
        self.projects = ProjectRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        self.media = MediaRepository(self._inner.session, id_factory=uuid7)
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
class SqlAlchemyProjectsUnitOfWorkFactory:
    """Create structurally typed project transactions."""

    session_factory: AsyncSessionFactory

    def __call__(self) -> ProjectsUnitOfWork:
        """Return a fresh unopened project transaction."""
        return cast("ProjectsUnitOfWork", SqlAlchemyProjectsUnitOfWork(self.session_factory))
