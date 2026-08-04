"""Project commands, immutable lifecycle, relations, and public projections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.concurrency import require_matching_version
from app.common.domain.pagination import Page, PageRequest
from app.common.domain.temporal import require_utc
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7
from app.modules.media.domain import (
    MediaOwnerType,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
)
from app.modules.projects.domain import (
    MAXIMUM_GRAPH_NODES,
    AdminProjectQuery,
    AdminProjectView,
    Project,
    ProjectReferenceSummary,
    ProjectRevision,
    ProjectSnapshot,
    ProjectValidationError,
    ProjectValues,
    PublicProject,
    PublicProjectExperienceReference,
    PublicProjectQuery,
    PublicProjectReference,
    PublicProjectSkillReference,
    derive_project_lifecycle,
    normalize_project_slug,
    project_seo,
    require_mutable_project_revision,
    validate_project_values,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.modules.experiences.domain import ExperienceReferenceSummary
    from app.modules.projects.ports import (
        ExperienceReferencePort,
        ProjectsUnitOfWork,
        ProjectsUnitOfWorkFactory,
        SkillReferencePort,
    )
    from app.modules.skills.domain import SkillReferenceSummary

_READ_POLICY = AccessPolicy(
    resource="projects",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION, ActorType.API_TOKEN}),
    required_token_scopes=frozenset({"content:read"}),
)
_WRITE_POLICY = AccessPolicy(
    resource="projects",
    action="write",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION, ActorType.API_TOKEN}),
    required_token_scopes=frozenset({"content:write"}),
)
_NOT_PUBLISHED = "not_published"
_EXPERIENCE_UNAVAILABLE = "experience_unavailable"
_PROJECT_NOT_FOUND = "project_not_found"
_PROJECT_UNAVAILABLE = "project_unavailable"
_RELATED_PROJECT_CYCLE = "related_project_cycle"


class ProjectNotFoundError(Exception):
    """The project does not exist in the authorized scope."""


class ProjectSlugConflictError(Exception):
    """The immutable normalized route identity already exists."""


class ProjectRelationError(Exception):
    """A revision relation set is incomplete, unavailable, or cyclic."""

    def __init__(self, code: str) -> None:
        """Retain one stable relation error code."""
        super().__init__("project relation rejected")
        self.code = code


class ProjectIdempotencyRejectedError(Exception):
    """An idempotent project command conflicts or remains in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain only the shared admission decision."""
        super().__init__("project idempotency admission rejected")
        self.decision = decision


class ProjectPublicationError(Exception):
    """A lifecycle action is invalid for the current project state."""

    def __init__(self, code: str) -> None:
        """Retain one stable publication error code."""
        super().__init__("project publication action rejected")
        self.code = code


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    """Idempotent creation of one stable route and revision-one draft."""

    actor: ActorContext
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    slug: str
    values: ProjectValues
    visible: bool = True
    featured: bool = False


@dataclass(frozen=True, slots=True)
class SaveProjectDraftCommand:
    """Optimistic complete replacement of the mutable draft."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    values: ProjectValues


@dataclass(frozen=True, slots=True)
class PublishProjectCommand:
    """Idempotent publication now or at an absolute UTC instant."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RescheduleProjectCommand:
    """Idempotent schedule-metadata-only update."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime


@dataclass(frozen=True, slots=True)
class UnpublishProjectCommand:
    """Idempotent removal of public eligibility."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class SetProjectVisibilityCommand:
    """Optimistic visibility update independent from lifecycle."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    visible: bool


@dataclass(frozen=True, slots=True)
class SetProjectFeaturedCommand:
    """Optimistic featured update independent from lifecycle."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    featured: bool


@dataclass(frozen=True, slots=True)
class ReorderProjectsCommand:
    """Idempotent complete replacement of curated project order."""

    actor: ActorContext
    request_id: str
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class DeleteProjectCommand:
    """Optimistic soft delete distinct from unpublish."""

    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class _IdempotencyFact:
    actor: ActorContext
    route: str
    key: str
    payload: bytes
    now: datetime


@dataclass(frozen=True, slots=True)
class _AuditFact:
    actor: ActorContext
    request_id: str
    event_type: str
    resource_id: UUID
    version: int
    fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _FlagFact:
    actor: ActorContext
    request_id: str
    project_id: UUID
    if_match: str | None
    field: str
    value: bool


class ProjectsService:
    """Authorize and transact the M6 project capability."""

    def __init__(
        self,
        uow_factory: ProjectsUnitOfWorkFactory,
        skills: SkillReferencePort,
        experiences: ExperienceReferencePort,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind deterministic transaction, provider, time, and ID seams."""
        self._uow_factory = uow_factory
        self._skills = skills
        self._experiences = experiences
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def list_admin(
        self,
        actor: ActorContext,
        query: AdminProjectQuery,
    ) -> Page[AdminProjectView]:
        """Return one allow-listed administrator page."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            page = await uow.projects.list_admin(query)
            now = await uow.projects.database_now()
        return Page(
            items=tuple(
                AdminProjectView(item, derive_project_lifecycle(item, database_now=now))
                for item in page.items
            ),
            metadata=page.metadata,
        )

    async def get_admin(self, actor: ActorContext, project_id: UUID) -> AdminProjectView:
        """Return one complete administrator project snapshot."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, project_id)
            now = await uow.projects.database_now()
        return AdminProjectView(snapshot, derive_project_lifecycle(snapshot, database_now=now))

    async def preview(self, actor: ActorContext, project_id: UUID) -> AdminProjectView:
        """Return current draft through the private administrator boundary."""
        return await self.get_admin(actor, project_id)

    async def admin_view(self, snapshot: ProjectSnapshot) -> AdminProjectView:
        """Pair a mutation result with database-time lifecycle."""
        async with self._uow_factory() as uow:
            now = await uow.projects.database_now()
        return AdminProjectView(snapshot, derive_project_lifecycle(snapshot, database_now=now))

    async def create(self, command: CreateProjectCommand) -> ProjectSnapshot:
        """Create one immutable route identity and mutable revision-one draft."""
        require_authorized(command.actor, _WRITE_POLICY)
        slug = normalize_project_slug(command.slug)
        values = validate_project_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/projects",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            if await uow.projects.slug_exists(slug):
                raise ProjectSlugConflictError
            ordered = await uow.projects.list_ordered(for_update=True)
            project_id = self._id_factory()
            revision_id = self._id_factory()
            values = validate_project_values(values, project_id=project_id)
            await self._validate_relations(uow, project_id, values)
            actor_id = self._actor_id(command.actor)
            aggregate = Project(
                id=project_id,
                slug=slug,
                visible=command.visible,
                featured=command.featured,
                position=len(ordered),
                draft_revision_id=revision_id,
                published_revision_id=None,
                publish_at=None,
                unpublished_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            revision = ProjectRevision(
                id=revision_id,
                project_id=project_id,
                revision_number=1,
                based_on_revision_id=None,
                values=values,
                frozen=False,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            await self._replace_revision_media(uow, revision, now=now, public=False)
            await uow.projects.add(aggregate, revision)
            result = ProjectSnapshot(aggregate, revision, None)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.created",
                    aggregate.id,
                    aggregate.version,
                    ("content", "relations", "visible", "featured"),
                ),
            )
            await self._complete(uow, decision, result, status=201, code="project.created")
            await uow.commit()
            return result

    async def save_draft(self, command: SaveProjectDraftCommand) -> ProjectSnapshot:
        """Replace only the mutable draft under aggregate concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_project_values(command.values, project_id=command.project_id)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.project_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.project.version)
            require_mutable_project_revision(snapshot.draft)
            await self._validate_relations(uow, command.project_id, values)
            proposed = ProjectRevision(
                id=snapshot.draft.id,
                project_id=snapshot.draft.project_id,
                revision_number=snapshot.draft.revision_number,
                based_on_revision_id=snapshot.draft.based_on_revision_id,
                values=values,
                frozen=False,
                created_by=snapshot.draft.created_by,
                created_at=snapshot.draft.created_at,
                updated_at=now,
            )
            await self._replace_revision_media(uow, proposed, now=now, public=False)
            updated = await uow.projects.save_draft(snapshot, values, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.draft_saved",
                    updated.project.id,
                    updated.project.version,
                    ("content", "relations", "seo"),
                ),
            )
            await uow.commit()
            return updated

    async def publish(self, command: PublishProjectCommand) -> ProjectSnapshot:
        """Freeze the draft, point publication, and create one mutable copy."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.projects.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/projects/{project_id}/actions/publish",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.project_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.project.version)
            require_mutable_project_revision(snapshot.draft)
            values = validate_project_values(snapshot.draft.values, project_id=command.project_id)
            await self._validate_relations(uow, command.project_id, values)
            publish_at = now if command.publish_at is None else require_utc(command.publish_at)
            updated = await uow.projects.publish(
                snapshot,
                publish_at=publish_at,
                next_revision_id=self._id_factory(),
                actor_id=self._actor_id(command.actor),
                now=now,
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow, snapshot.published, now=now, public=False, active=False
                )
            if updated.published is None:
                raise ProjectPublicationError(_NOT_PUBLISHED)
            await self._replace_revision_media(uow, updated.published, now=now, public=True)
            await self._replace_revision_media(uow, updated.draft, now=now, public=False)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.published",
                    updated.project.id,
                    updated.project.version,
                    ("published_revision", "publish_at"),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="project.published")
            await uow.commit()
            return updated

    async def reschedule(self, command: RescheduleProjectCommand) -> ProjectSnapshot:
        """Change only publication schedule metadata."""
        require_authorized(command.actor, _WRITE_POLICY)
        publish_at = require_utc(command.publish_at)
        async with self._uow_factory() as uow:
            now = await uow.projects.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/projects/{project_id}/actions/reschedule",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.project_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.project.version)
            if snapshot.project.published_revision_id is None:
                raise ProjectPublicationError(_NOT_PUBLISHED)
            updated = await uow.projects.reschedule(snapshot, publish_at=publish_at, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.rescheduled",
                    updated.project.id,
                    updated.project.version,
                    ("publish_at",),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="project.rescheduled")
            await uow.commit()
            return updated

    async def unpublish(self, command: UnpublishProjectCommand) -> ProjectSnapshot:
        """Clear public eligibility without deleting revision history."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.projects.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/projects/{project_id}/actions/unpublish",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.project_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.project.version)
            if snapshot.project.published_revision_id is None:
                raise ProjectPublicationError(_NOT_PUBLISHED)
            updated = await uow.projects.unpublish(snapshot, now=now)
            if snapshot.published is not None:
                await self._replace_revision_media(
                    uow, snapshot.published, now=now, public=False, active=False
                )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.unpublished",
                    updated.project.id,
                    updated.project.version,
                    ("published_revision",),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="project.unpublished")
            await uow.commit()
            return updated

    async def set_visibility(self, command: SetProjectVisibilityCommand) -> ProjectSnapshot:
        """Set visibility independently from lifecycle and featured state."""
        require_authorized(command.actor, _WRITE_POLICY)
        return await self._set_flag(
            _FlagFact(
                command.actor,
                command.request_id,
                command.project_id,
                command.if_match,
                "visible",
                command.visible,
            )
        )

    async def set_featured(self, command: SetProjectFeaturedCommand) -> ProjectSnapshot:
        """Set featured independently without widening public eligibility."""
        require_authorized(command.actor, _WRITE_POLICY)
        return await self._set_flag(
            _FlagFact(
                command.actor,
                command.request_id,
                command.project_id,
                command.if_match,
                "featured",
                command.featured,
            )
        )

    async def reorder(self, command: ReorderProjectsCommand) -> tuple[Project, ...]:
        """Apply a complete duplicate-free order under one lock and idempotency key."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/projects/actions/reorder",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            current = await uow.projects.list_ordered(for_update=True)
            if not current:
                raise ProjectNotFoundError
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return current
            require_matching_version(command.if_match, current_version=current[0].version)
            if len(command.ordered_ids) != len(set(command.ordered_ids)):
                raise ProjectValidationError(path="items", code="duplicate_id")
            if set(command.ordered_ids) != {item.id for item in current}:
                raise ProjectValidationError(path="items", code="incomplete_order")
            updated = await uow.projects.reorder(command.ordered_ids, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.reordered",
                    updated[0].id,
                    updated[0].version,
                    ("position",),
                ),
            )
            outcome = await self._get(uow, updated[0].id)
            await self._complete(uow, decision, outcome, status=200, code="project.reordered")
            await uow.commit()
            return updated

    async def delete(self, command: DeleteProjectCommand) -> ProjectSnapshot:
        """Soft-delete as an explicit action separate from unpublish."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.project_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.project.version)
            updated = await uow.projects.soft_delete(snapshot, now=now)
            await self._replace_revision_media(
                uow, snapshot.draft, now=now, public=False, active=False
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow, snapshot.published, now=now, public=False, active=False
                )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "project.deleted",
                    updated.project.id,
                    updated.project.version,
                    (),
                ),
            )
            await uow.commit()
            return updated

    async def public_list(self, query: PublicProjectQuery) -> Page[PublicProject]:
        """Project one public page through provider-safe relation summaries."""
        async with self._uow_factory() as uow:
            page = await uow.projects.list_public(query)
            related = await uow.projects.reference_summaries(
                self._relation_ids(page.items, "related_project_ids")
            )
        skills, experiences = await self._provider_summaries(page.items)
        return Page(
            items=tuple(self._public(item, skills, experiences, related) for item in page.items),
            metadata=page.metadata,
        )

    async def public_detail(self, slug: str) -> PublicProject:
        """Resolve one effective project or return indistinguishable not-found."""
        normalized = normalize_project_slug(slug)
        if normalized != slug:
            raise ProjectNotFoundError
        async with self._uow_factory() as uow:
            snapshot = await uow.projects.get_public_by_slug(slug)
            if snapshot is None:
                raise ProjectNotFoundError
            related = await uow.projects.reference_summaries(
                snapshot.published.values.related_project_ids if snapshot.published else ()
            )
        skills, experiences = await self._provider_summaries((snapshot,))
        return self._public(snapshot, skills, experiences, related)

    async def reference_summaries(
        self,
        project_ids: tuple[UUID, ...],
    ) -> tuple[ProjectReferenceSummary, ...]:
        """Resolve every project provider reference or fail the complete set."""
        if len(project_ids) != len(set(project_ids)):
            raise ProjectNotFoundError
        async with self._uow_factory() as uow:
            summaries = await uow.projects.reference_summaries(project_ids)
        if {item.id for item in summaries} != set(project_ids):
            raise ProjectNotFoundError
        return summaries

    async def _set_flag(self, fact: _FlagFact) -> ProjectSnapshot:
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, fact.project_id, for_update=True)
            require_matching_version(fact.if_match, current_version=snapshot.project.version)
            if fact.field == "visible":
                updated = await uow.projects.set_visibility(
                    snapshot,
                    visible=fact.value,
                    now=now,
                )
                if updated.published is not None:
                    await self._replace_revision_media(
                        uow,
                        updated.published,
                        now=now,
                        public=fact.value,
                    )
            else:
                updated = await uow.projects.set_featured(
                    snapshot,
                    featured=fact.value,
                    now=now,
                )
            self._audit(
                uow,
                _AuditFact(
                    fact.actor,
                    fact.request_id,
                    f"project.{fact.field}_changed",
                    updated.project.id,
                    updated.project.version,
                    (fact.field,),
                ),
            )
            await uow.commit()
            return updated

    async def _validate_relations(
        self,
        uow: ProjectsUnitOfWork,
        project_id: UUID,
        values: ProjectValues,
    ) -> None:
        await self._skills.resolve(values.skill_ids)
        experience_summaries = await self._experiences.resolve(values.experience_ids)
        if any(item.deleted for item in experience_summaries):
            raise ProjectRelationError(_EXPERIENCE_UNAVAILABLE)
        project_summaries = await uow.projects.reference_summaries(values.related_project_ids)
        if {item.id for item in project_summaries} != set(values.related_project_ids):
            raise ProjectRelationError(_PROJECT_NOT_FOUND)
        if any(item.deleted for item in project_summaries):
            raise ProjectRelationError(_PROJECT_UNAVAILABLE)
        if await uow.projects.related_graph_would_cycle(
            project_id,
            values.related_project_ids,
            maximum_nodes=MAXIMUM_GRAPH_NODES,
        ):
            raise ProjectRelationError(_RELATED_PROJECT_CYCLE)

    @staticmethod
    async def _replace_revision_media(
        uow: ProjectsUnitOfWork,
        revision: ProjectRevision,
        *,
        now: datetime,
        public: bool,
        active: bool = True,
    ) -> None:
        values = revision.values
        uses: list[MediaUse] = []
        if values.cover_media_id is not None:
            uses.append(
                MediaUse(
                    asset_id=values.cover_media_id,
                    owner_type=MediaOwnerType.PROJECT_REVISION,
                    owner_id=revision.id,
                    role=MediaUsageRole.PROJECT_COVER,
                    position=0,
                    purpose=MediaUsePurpose.MEANINGFUL,
                    alt_text=f"{values.name} project cover",
                    caption=None,
                    active=active,
                    public=public,
                )
            )
        uses.extend(
            MediaUse(
                asset_id=asset_id,
                owner_type=MediaOwnerType.PROJECT_REVISION,
                owner_id=revision.id,
                role=MediaUsageRole.PROJECT_SCREENSHOT,
                position=position,
                purpose=MediaUsePurpose.MEANINGFUL,
                alt_text=f"{values.name} project screenshot {position + 1}",
                caption=None,
                active=active,
                public=public,
            )
            for position, asset_id in enumerate(values.screenshot_media_ids)
        )
        await uow.media.replace_owner_usages(
            owner_type=MediaOwnerType.PROJECT_REVISION.value,
            owner_id=revision.id,
            usages=tuple(uses),
            now=now,
        )

    async def _provider_summaries(
        self,
        snapshots: tuple[ProjectSnapshot, ...],
    ) -> tuple[tuple[SkillReferenceSummary, ...], tuple[ExperienceReferenceSummary, ...]]:
        skill_ids = self._relation_ids(snapshots, "skill_ids")
        experience_ids = self._relation_ids(snapshots, "experience_ids")
        return await self._skills.resolve(skill_ids), await self._experiences.resolve(
            experience_ids
        )

    @staticmethod
    def _relation_ids(snapshots: tuple[ProjectSnapshot, ...], field: str) -> tuple[UUID, ...]:
        return tuple(
            dict.fromkeys(
                relation_id
                for snapshot in snapshots
                for relation_id in getattr(ProjectsService._published(snapshot).values, field)
            )
        )

    @staticmethod
    async def _get(
        uow: ProjectsUnitOfWork,
        project_id: UUID,
        *,
        for_update: bool = False,
    ) -> ProjectSnapshot:
        snapshot = await uow.projects.get(project_id, for_update=for_update)
        if snapshot is None:
            raise ProjectNotFoundError
        return snapshot

    @staticmethod
    def _actor_id(actor: ActorContext) -> UUID:
        if actor.actor_id is None:
            raise ProjectNotFoundError
        return actor.actor_id

    @staticmethod
    async def _acquire(
        uow: ProjectsUnitOfWork,
        fact: _IdempotencyFact,
    ) -> IdempotencyDecision:
        decision = await uow.idempotency.acquire(
            IdempotencyRequest.create(
                actor=fact.actor,
                route=fact.route,
                key=fact.key,
                canonical_payload=fact.payload,
                requested_at=fact.now,
            )
        )
        if decision.decision not in {
            IdempotencyDecisionType.ACQUIRED,
            IdempotencyDecisionType.REPLAY,
        }:
            raise ProjectIdempotencyRejectedError(decision)
        return decision

    async def _replayed_snapshot(
        self,
        uow: ProjectsUnitOfWork,
        decision: IdempotencyDecision,
    ) -> ProjectSnapshot | None:
        if decision.decision is not IdempotencyDecisionType.REPLAY:
            return None
        if decision.outcome is None or decision.outcome.resource_id is None:
            raise ProjectNotFoundError
        return await self._get(uow, decision.outcome.resource_id)

    @staticmethod
    async def _complete(
        uow: ProjectsUnitOfWork,
        decision: IdempotencyDecision,
        snapshot: ProjectSnapshot,
        *,
        status: int,
        code: str,
    ) -> None:
        if decision.record_id is None:
            raise ProjectNotFoundError
        await uow.idempotency.complete(
            decision.record_id,
            IdempotencyOutcome(
                response_status=status,
                result_code=code,
                resource_type="project",
                resource_id=snapshot.project.id,
                resource_version=snapshot.project.version,
            ),
            completed_at=snapshot.project.updated_at,
        )

    @staticmethod
    def _published(snapshot: ProjectSnapshot) -> ProjectRevision:
        revision = snapshot.published
        if revision is None or revision.id != snapshot.project.published_revision_id:
            raise ProjectNotFoundError
        return revision

    @classmethod
    def _public(
        cls,
        snapshot: ProjectSnapshot,
        skills: tuple[SkillReferenceSummary, ...],
        experiences: tuple[ExperienceReferenceSummary, ...],
        projects: tuple[ProjectReferenceSummary, ...],
    ) -> PublicProject:
        values = cls._published(snapshot).values
        skill_map = {item.id: item for item in skills if item.visible}
        experience_map = {item.id: item.public for item in experiences if item.public is not None}
        project_map = {item.id: item.public for item in projects if item.public is not None}
        seo_title, seo_description = project_seo(values)
        return PublicProject(
            id=snapshot.project.id,
            slug=snapshot.project.slug,
            name=values.name,
            short_description=values.short_description,
            full_description=values.full_description,
            problem=values.problem,
            solution=values.solution,
            impact=values.impact,
            owner_role=values.owner_role,
            architecture=values.architecture,
            technologies=values.technologies,
            status=values.status,
            start_date=values.start_date,
            end_date=values.end_date,
            repository_url=values.repository_url,
            demo_url=values.demo_url,
            featured=snapshot.project.featured,
            seo_title=seo_title,
            seo_description=seo_description,
            canonical_url=values.canonical_url,
            cover_media_id=values.cover_media_id,
            screenshot_media_ids=values.screenshot_media_ids,
            skills=tuple(
                PublicProjectSkillReference(name=skill_map[item].name, slug=skill_map[item].slug)
                for item in values.skill_ids
                if item in skill_map
            ),
            experiences=tuple(
                PublicProjectExperienceReference(
                    id=experience_map[item].id,
                    company_name=experience_map[item].company_name,
                    role_title=experience_map[item].role_title,
                )
                for item in values.experience_ids
                if item in experience_map and experience_map[item] is not None
            ),
            related_projects=tuple(
                project_map[item]
                for item in values.related_project_ids
                if item in project_map and project_map[item] is not None
            ),
        )

    def _audit(self, uow: ProjectsUnitOfWork, fact: _AuditFact) -> None:
        uow.audit.append(
            AuditEntry(
                id=uuid7(),
                event_type=fact.event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=fact.actor.actor_id,
                actor_label_snapshot=None,
                resource_type="project",
                resource_id=fact.resource_id,
                request_id=fact.request_id,
                occurred_at=self._clock(),
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata={"version": fact.version, "fields": ",".join(fact.fields)},
                schema_version=1,
            )
        )


class ProjectReferenceFacade:
    """Stable provider boundary for blog/pages and later content modules."""

    def __init__(self, service: ProjectsService) -> None:
        """Bind to the project application service."""
        self._service = service

    async def resolve(
        self,
        project_ids: tuple[UUID, ...],
    ) -> tuple[ProjectReferenceSummary, ...]:
        """Resolve all requested project IDs or fail the complete set."""
        return await self._service.reference_summaries(project_ids)

    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[ProjectReferenceSummary, ...]:
        """Return bounded effective project evidence for page blocks."""
        page = await self._service.public_list(
            PublicProjectQuery(PageRequest(page_size=maximum), featured=featured)
        )
        return tuple(
            ProjectReferenceSummary(
                id=item.id,
                slug=item.slug,
                name=item.name,
                visible=True,
                deleted=False,
                public=PublicProjectReference(item.id, item.slug, item.name),
            )
            for item in page.items
        )
