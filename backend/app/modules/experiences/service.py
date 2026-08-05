"""Professional experience commands, revision lifecycle, and public projection."""

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
from app.modules.experiences.domain import (
    AdminExperienceQuery,
    AdminExperienceView,
    Experience,
    ExperienceReferenceSummary,
    ExperienceRevision,
    ExperienceSnapshot,
    ExperienceValidationError,
    ExperienceValues,
    PublicExperience,
    PublicExperienceQuery,
    PublicExperienceReference,
    PublicSkillReference,
    derive_lifecycle,
    require_mutable_revision,
    validate_experience_values,
)
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.modules.experiences.ports import (
        ExperiencesUnitOfWork,
        ExperiencesUnitOfWorkFactory,
        SkillReferencePort,
    )
    from app.modules.skills.domain import SkillReferenceSummary

_READ_POLICY = AccessPolicy(
    resource="experiences",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_WRITE_POLICY = AccessPolicy(
    resource="experiences",
    action="write",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_NOT_PUBLISHED = "not_published"


class ExperienceNotFoundError(Exception):
    """The requested experience does not exist in the authorized scope."""


class ExperienceIdempotencyRejectedError(Exception):
    """An idempotent experience command conflicts or remains in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain only the common safe admission decision."""
        super().__init__("experience idempotency admission rejected")
        self.decision = decision


class ExperiencePublicationError(Exception):
    """The aggregate is not in a state accepted by a publication action."""

    def __init__(self, code: str) -> None:
        """Retain one stable lifecycle error code."""
        super().__init__("experience publication action rejected")
        self.code = code


@dataclass(frozen=True, slots=True)
class CreateExperienceCommand:
    """Idempotent creation of one aggregate and revision-one draft."""

    actor: ActorContext
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    values: ExperienceValues
    visible: bool = True


@dataclass(frozen=True, slots=True)
class SaveExperienceDraftCommand:
    """Optimistic complete replacement of the current mutable draft."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None
    values: ExperienceValues


@dataclass(frozen=True, slots=True)
class PublishExperienceCommand:
    """Idempotent publication now or at one explicit UTC instant."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RescheduleExperienceCommand:
    """Idempotent scheduling-metadata-only update."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime


@dataclass(frozen=True, slots=True)
class UnpublishExperienceCommand:
    """Idempotent removal of public eligibility while retaining revisions."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class SetExperienceVisibilityCommand:
    """Optimistic independent visibility update."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None
    visible: bool


@dataclass(frozen=True, slots=True)
class ReorderExperiencesCommand:
    """Idempotent complete normalized experience order."""

    actor: ActorContext
    request_id: str
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class DeleteExperienceCommand:
    """Optimistic, distinct soft deletion action."""

    actor: ActorContext
    request_id: str
    experience_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class _IdempotencyFact:
    """Inputs used to acquire one safe common idempotency record."""

    actor: ActorContext
    route: str
    key: str
    payload: bytes
    now: datetime


@dataclass(frozen=True, slots=True)
class _AuditFact:
    """One value-free experience audit event."""

    actor: ActorContext
    request_id: str
    event_type: str
    resource_id: UUID
    version: int
    fields: tuple[str, ...]


class ExperiencesService:
    """Authorize and transact the M5 experience capability."""

    def __init__(
        self,
        uow_factory: ExperiencesUnitOfWorkFactory,
        skills: SkillReferencePort,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Store deterministic transaction, capability, time, and ID seams."""
        self._uow_factory = uow_factory
        self._skills = skills
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def list_admin(
        self,
        actor: ActorContext,
        query: AdminExperienceQuery,
    ) -> Page[AdminExperienceView]:
        """Return an allow-listed administrator page."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            page = await uow.experiences.list_admin(query)
            database_now = await uow.experiences.database_now()
            return Page(
                items=tuple(
                    AdminExperienceView(
                        snapshot=item,
                        lifecycle=derive_lifecycle(item, database_now=database_now),
                    )
                    for item in page.items
                ),
                metadata=page.metadata,
            )

    async def get_admin(self, actor: ActorContext, experience_id: UUID) -> AdminExperienceView:
        """Return one complete administrator snapshot."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, experience_id)
            database_now = await uow.experiences.database_now()
            return AdminExperienceView(
                snapshot=snapshot,
                lifecycle=derive_lifecycle(snapshot, database_now=database_now),
            )

    async def preview(self, actor: ActorContext, experience_id: UUID) -> AdminExperienceView:
        """Return the current draft through the private administrator boundary."""
        return await self.get_admin(actor, experience_id)

    async def admin_view(self, snapshot: ExperienceSnapshot) -> AdminExperienceView:
        """Pair a mutation result with a lifecycle derived from PostgreSQL time."""
        async with self._uow_factory() as uow:
            database_now = await uow.experiences.database_now()
        return AdminExperienceView(
            snapshot=snapshot,
            lifecycle=derive_lifecycle(snapshot, database_now=database_now),
        )

    async def create(self, command: CreateExperienceCommand) -> ExperienceSnapshot:
        """Create one stable aggregate with a mutable revision-one draft."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_experience_values(command.values)
        await self._skills.resolve(values.skill_ids)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/experiences",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            ordered = await uow.experiences.list_ordered(for_update=True)
            aggregate_id = self._id_factory()
            revision_id = self._id_factory()
            actor_id = self._actor_id(command.actor)
            aggregate = Experience(
                id=aggregate_id,
                visible=command.visible,
                position=len(ordered),
                draft_revision_id=revision_id,
                published_revision_id=None,
                publish_at=None,
                unpublished_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            revision = ExperienceRevision(
                id=revision_id,
                experience_id=aggregate_id,
                revision_number=1,
                based_on_revision_id=None,
                values=values,
                frozen=False,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            await uow.experiences.add(aggregate, revision)
            result = ExperienceSnapshot(aggregate, revision, None)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.created",
                    aggregate.id,
                    aggregate.version,
                    ("content", "relations", "visible"),
                ),
            )
            await self._complete(uow, decision, result, status=201, code="experience.created")
            await uow.commit()
            return result

    async def save_draft(self, command: SaveExperienceDraftCommand) -> ExperienceSnapshot:
        """Replace only the current mutable draft under aggregate concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_experience_values(command.values)
        await self._skills.resolve(values.skill_ids)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            require_mutable_revision(snapshot.draft)
            updated = await uow.experiences.save_draft(snapshot, values, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.draft_saved",
                    updated.experience.id,
                    updated.experience.version,
                    ("content", "relations"),
                ),
            )
            await uow.commit()
            return updated

    async def publish(self, command: PublishExperienceCommand) -> ExperienceSnapshot:
        """Freeze the draft, point publication, and create the next mutable copy."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            database_now = await uow.experiences.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/experiences/{experience_id}/actions/publish",
                    command.idempotency_key,
                    command.canonical_payload,
                    database_now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            require_mutable_revision(snapshot.draft)
            values = validate_experience_values(snapshot.draft.values)
            await self._skills.resolve(values.skill_ids)
            publish_at = (
                database_now if command.publish_at is None else require_utc(command.publish_at)
            )
            updated = await uow.experiences.publish(
                snapshot,
                publish_at=publish_at,
                next_revision_id=self._id_factory(),
                actor_id=self._actor_id(command.actor),
                now=database_now,
            )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.published",
                    updated.experience.id,
                    updated.experience.version,
                    ("published_revision", "publish_at"),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="experience.published")
            await uow.commit()
            return updated

    async def reschedule(self, command: RescheduleExperienceCommand) -> ExperienceSnapshot:
        """Change only the schedule for an existing publication pointer."""
        require_authorized(command.actor, _WRITE_POLICY)
        publish_at = require_utc(command.publish_at)
        async with self._uow_factory() as uow:
            now = await uow.experiences.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/experiences/{experience_id}/actions/reschedule",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            if snapshot.experience.published_revision_id is None:
                raise ExperiencePublicationError(_NOT_PUBLISHED)
            updated = await uow.experiences.reschedule(snapshot, publish_at=publish_at, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.rescheduled",
                    updated.experience.id,
                    updated.experience.version,
                    ("publish_at",),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="experience.rescheduled")
            await uow.commit()
            return updated

    async def unpublish(self, command: UnpublishExperienceCommand) -> ExperienceSnapshot:
        """Clear publication eligibility without deleting revision history."""
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.experiences.database_now()
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/experiences/{experience_id}/actions/unpublish",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            replay = await self._replayed_snapshot(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            if snapshot.experience.published_revision_id is None:
                raise ExperiencePublicationError(_NOT_PUBLISHED)
            updated = await uow.experiences.unpublish(snapshot, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.unpublished",
                    updated.experience.id,
                    updated.experience.version,
                    ("published_revision",),
                ),
            )
            await self._complete(uow, decision, updated, status=200, code="experience.unpublished")
            await uow.commit()
            return updated

    async def set_visibility(
        self,
        command: SetExperienceVisibilityCommand,
    ) -> ExperienceSnapshot:
        """Set visibility independently from publication lifecycle."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            updated = await uow.experiences.set_visibility(
                snapshot,
                visible=command.visible,
                now=now,
            )
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.visibility_changed",
                    updated.experience.id,
                    updated.experience.version,
                    ("visible",),
                ),
            )
            await uow.commit()
            return updated

    async def reorder(self, command: ReorderExperiencesCommand) -> tuple[Experience, ...]:
        """Apply a complete duplicate-free order under idempotency and concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                _IdempotencyFact(
                    command.actor,
                    "/api/v1/admin/experiences/actions/reorder",
                    command.idempotency_key,
                    command.canonical_payload,
                    now,
                ),
            )
            current = await uow.experiences.list_ordered(for_update=True)
            if not current:
                raise ExperienceNotFoundError
            replay = decision.decision is IdempotencyDecisionType.REPLAY
            if replay:
                return current
            require_matching_version(command.if_match, current_version=current[0].version)
            expected = {item.id for item in current}
            if len(command.ordered_ids) != len(set(command.ordered_ids)):
                raise ExperienceValidationError(path="items", code="duplicate_id")
            if set(command.ordered_ids) != expected:
                raise ExperienceValidationError(path="items", code="incomplete_order")
            updated = await uow.experiences.reorder(command.ordered_ids, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.reordered",
                    updated[0].id,
                    updated[0].version,
                    ("position",),
                ),
            )
            outcome_snapshot = await self._get(uow, updated[0].id)
            await self._complete(
                uow,
                decision,
                outcome_snapshot,
                status=200,
                code="experience.reordered",
            )
            await uow.commit()
            return updated

    async def delete(self, command: DeleteExperienceCommand) -> ExperienceSnapshot:
        """Soft-delete as an explicit action separate from unpublish."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.experience_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.experience.version)
            updated = await uow.experiences.soft_delete(snapshot, now=now)
            self._audit(
                uow,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "experience.deleted",
                    updated.experience.id,
                    updated.experience.version,
                    (),
                ),
            )
            await uow.commit()
            return updated

    async def public_list(self, query: PublicExperienceQuery) -> Page[PublicExperience]:
        """Project effective snapshots and only visible skill summaries."""
        async with self._uow_factory() as uow:
            page = await uow.experiences.list_public(query)
        skill_ids = tuple(
            dict.fromkeys(
                skill_id
                for snapshot in page.items
                for skill_id in self._published(snapshot).values.skill_ids
            )
        )
        summaries = await self._skills.resolve(skill_ids)
        by_id = {summary.id: summary for summary in summaries if summary.visible}
        return Page(
            items=tuple(self._public(snapshot, by_id) for snapshot in page.items),
            metadata=page.metadata,
        )

    async def reference_summaries(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Resolve every opaque provider reference without leaking persistence types."""
        if len(experience_ids) != len(set(experience_ids)):
            raise ExperienceNotFoundError
        async with self._uow_factory() as uow:
            summaries = await uow.experiences.reference_summaries(experience_ids)
        if {item.id for item in summaries} != set(experience_ids):
            raise ExperienceNotFoundError
        return summaries

    @staticmethod
    async def _get(
        uow: ExperiencesUnitOfWork,
        experience_id: UUID,
        *,
        for_update: bool = False,
    ) -> ExperienceSnapshot:
        snapshot = await uow.experiences.get(experience_id, for_update=for_update)
        if snapshot is None:
            raise ExperienceNotFoundError
        return snapshot

    @staticmethod
    def _actor_id(actor: ActorContext) -> UUID:
        if actor.actor_id is None:
            raise ExperienceNotFoundError
        return actor.actor_id

    @staticmethod
    async def _acquire(
        uow: ExperiencesUnitOfWork,
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
            raise ExperienceIdempotencyRejectedError(decision)
        return decision

    async def _replayed_snapshot(
        self,
        uow: ExperiencesUnitOfWork,
        decision: IdempotencyDecision,
    ) -> ExperienceSnapshot | None:
        if decision.decision is not IdempotencyDecisionType.REPLAY:
            return None
        if decision.outcome is None or decision.outcome.resource_id is None:
            raise ExperienceNotFoundError
        return await self._get(uow, decision.outcome.resource_id)

    @staticmethod
    async def _complete(
        uow: ExperiencesUnitOfWork,
        decision: IdempotencyDecision,
        snapshot: ExperienceSnapshot,
        *,
        status: int,
        code: str,
    ) -> None:
        if decision.record_id is None:
            raise ExperienceNotFoundError
        await uow.idempotency.complete(
            decision.record_id,
            IdempotencyOutcome(
                response_status=status,
                result_code=code,
                resource_type="experience",
                resource_id=snapshot.experience.id,
                resource_version=snapshot.experience.version,
            ),
            completed_at=snapshot.experience.updated_at,
        )

    @staticmethod
    def _published(snapshot: ExperienceSnapshot) -> ExperienceRevision:
        revision = snapshot.published
        if revision is None or revision.id != snapshot.experience.published_revision_id:
            raise ExperienceNotFoundError
        return revision

    @classmethod
    def _public(
        cls,
        snapshot: ExperienceSnapshot,
        skills: dict[UUID, SkillReferenceSummary],
    ) -> PublicExperience:
        values = cls._published(snapshot).values
        return PublicExperience(
            id=snapshot.experience.id,
            company_name=values.company_name,
            company_url=values.company_url,
            role_title=values.role_title,
            employment_type=values.employment_type,
            location=values.location,
            remote_status=values.remote_status,
            start_date=values.start_date,
            end_date=values.end_date,
            current_position=values.current_position,
            short_summary=values.short_summary,
            detailed_description=values.detailed_description,
            responsibilities=values.responsibilities,
            achievements=values.achievements,
            technologies=values.technologies,
            skills=tuple(
                PublicSkillReference(name=skills[item].name, slug=skills[item].slug)
                for item in values.skill_ids
                if item in skills
            ),
        )

    def _audit(
        self,
        uow: ExperiencesUnitOfWork,
        fact: _AuditFact,
    ) -> None:
        uow.audit.append(
            AuditEntry(
                id=uuid7(),
                event_type=fact.event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=fact.actor.actor_id,
                actor_label_snapshot=None,
                resource_type="experience",
                resource_id=fact.resource_id,
                request_id=fact.request_id,
                occurred_at=self._clock(),
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata={"version": fact.version, "fields": ",".join(fact.fields)},
                schema_version=1,
            )
        )


class ExperienceReferenceFacade:
    """Stable provider boundary for project and later content modules."""

    def __init__(self, service: ExperiencesService) -> None:
        """Bind the facade to the experience application service."""
        self._service = service

    async def resolve(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Resolve all requested IDs or fail the complete set."""
        return await self._service.reference_summaries(experience_ids)

    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[ExperienceReferenceSummary, ...]:
        """Return bounded effective experience evidence for page blocks."""
        del featured
        page = await self._service.public_list(
            PublicExperienceQuery(PageRequest(page_size=maximum))
        )
        return tuple(
            ExperienceReferenceSummary(
                id=item.id,
                company_name=item.company_name,
                role_title=item.role_title,
                visible=True,
                deleted=False,
                public=PublicExperienceReference(item.id, item.company_name, item.role_title),
            )
            for item in page.items
        )
