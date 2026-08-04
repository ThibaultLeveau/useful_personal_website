"""M5 application-service tests with deterministic in-memory ports."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID

import pytest

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
)
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import Page, PageRequest, page_metadata
from app.modules.experiences.domain import (
    AdminExperienceQuery,
    EmploymentType,
    Experience,
    ExperienceReferenceSummary,
    ExperienceRevision,
    ExperienceSnapshot,
    ExperienceValidationError,
    ExperienceValues,
    PublicExperienceQuery,
    PublicExperienceReference,
    PublicSkillReference,
    RemoteStatus,
)
from app.modules.experiences.service import (
    CreateExperienceCommand,
    DeleteExperienceCommand,
    ExperienceNotFoundError,
    ExperienceReferenceFacade,
    ExperiencesService,
    PublishExperienceCommand,
    ReorderExperiencesCommand,
    RescheduleExperienceCommand,
    SaveExperienceDraftCommand,
    SetExperienceVisibilityCommand,
    UnpublishExperienceCommand,
)
from app.modules.skills.domain import SkillReferenceSummary

if TYPE_CHECKING:
    from types import TracebackType

    from app.common.application.idempotency import IdempotencyOutcome, IdempotencyRequest
    from app.modules.audit.domain import AuditEntry
    from app.modules.experiences.ports import ExperiencesUnitOfWorkFactory

NOW = datetime(2026, 8, 3, 10, tzinfo=UTC)
ACTOR_ID = UUID("0198a12c-1000-7000-8000-000000000001")
EXPERIENCE_ID = UUID("0198a12c-1000-7000-8000-000000000002")
REVISION_ONE_ID = UUID("0198a12c-1000-7000-8000-000000000003")
REVISION_TWO_ID = UUID("0198a12c-1000-7000-8000-000000000004")
SKILL_ID = UUID("0198a12c-1000-7000-8000-000000000005")
HIDDEN_SKILL_ID = UUID("0198a12c-1000-7000-8000-000000000006")
IDEMPOTENCY_ID = UUID("0198a12c-1000-7000-8000-000000000007")


def _values(*, role: str = "Staff Engineer") -> ExperienceValues:
    return ExperienceValues(
        company_name="Example Studio",
        company_url="https://example.test",
        role_title=role,
        employment_type=EmploymentType.FULL_TIME,
        location="Paris, France",
        remote_status=RemoteStatus.HYBRID,
        start_date=date(2024, 1, 1),
        end_date=None,
        current_position=True,
        short_summary="Led the platform team.",
        detailed_description="Plain text detail.",
        responsibilities=("Designed service boundaries",),
        achievements=("Reduced deployment time",),
        technologies=("Python",),
        skill_ids=(SKILL_ID, HIDDEN_SKILL_ID),
    )


class _FakeExperiencesRepository:
    """Minimal behavioral repository matching the frozen application port."""

    def __init__(self) -> None:
        self.snapshots: dict[UUID, ExperienceSnapshot] = {}
        self.now = NOW
        self.publish_calls = 0

    async def database_now(self) -> datetime:
        return self.now

    async def list_admin(self, query: AdminExperienceQuery) -> Page[ExperienceSnapshot]:
        rows = tuple(self.snapshots.values())
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def list_public(self, query: PublicExperienceQuery) -> Page[ExperienceSnapshot]:
        rows = tuple(
            snapshot
            for snapshot in self.snapshots.values()
            if snapshot.experience.visible
            and snapshot.experience.deleted_at is None
            and snapshot.experience.published_revision_id is not None
            and snapshot.experience.publish_at is not None
            and snapshot.experience.publish_at <= self.now
        )
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Experience, ...]:
        del for_update
        return tuple(
            sorted(
                (
                    snapshot.experience
                    for snapshot in self.snapshots.values()
                    if snapshot.experience.deleted_at is None
                ),
                key=lambda item: (item.position, item.id),
            )
        )

    async def reference_summaries(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        summaries: list[ExperienceReferenceSummary] = []
        for identifier in experience_ids:
            snapshot = self.snapshots.get(identifier)
            if snapshot is None:
                continue
            aggregate = snapshot.experience
            published = snapshot.published
            effective = (
                aggregate.visible
                and aggregate.deleted_at is None
                and aggregate.publish_at is not None
                and aggregate.publish_at <= self.now
                and published is not None
                and published.frozen
            )
            summaries.append(
                ExperienceReferenceSummary(
                    id=identifier,
                    company_name=snapshot.draft.values.company_name,
                    role_title=snapshot.draft.values.role_title,
                    visible=aggregate.visible,
                    deleted=aggregate.deleted_at is not None,
                    public=(
                        PublicExperienceReference(
                            id=identifier,
                            company_name=published.values.company_name,
                            role_title=published.values.role_title,
                        )
                        if effective and published is not None
                        else None
                    ),
                )
            )
        return tuple(summaries)

    async def get(
        self,
        experience_id: UUID,
        *,
        for_update: bool = False,
    ) -> ExperienceSnapshot | None:
        del for_update
        return self.snapshots.get(experience_id)

    async def add(self, experience: Experience, revision: ExperienceRevision) -> None:
        self.snapshots[experience.id] = ExperienceSnapshot(experience, revision, None)

    async def save_draft(
        self,
        snapshot: ExperienceSnapshot,
        values: ExperienceValues,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        updated = ExperienceSnapshot(
            replace(
                snapshot.experience,
                updated_at=now,
                version=snapshot.experience.version + 1,
            ),
            replace(
                snapshot.draft,
                based_on_revision_id=(
                    snapshot.published.id
                    if snapshot.published is not None and values == snapshot.published.values
                    else None
                ),
                values=values,
                updated_at=now,
            ),
            snapshot.published,
        )
        self.snapshots[updated.experience.id] = updated
        return updated

    async def publish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ExperienceSnapshot:
        self.publish_calls += 1
        frozen = replace(snapshot.draft, frozen=True, updated_at=now)
        draft = ExperienceRevision(
            id=next_revision_id,
            experience_id=snapshot.experience.id,
            revision_number=frozen.revision_number + 1,
            based_on_revision_id=frozen.id,
            values=frozen.values,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        aggregate = replace(
            snapshot.experience,
            draft_revision_id=draft.id,
            published_revision_id=frozen.id,
            publish_at=publish_at,
            unpublished_at=None,
            updated_at=now,
            version=snapshot.experience.version + 1,
        )
        updated = ExperienceSnapshot(aggregate, draft, frozen)
        self.snapshots[aggregate.id] = updated
        return updated

    async def reschedule(
        self,
        snapshot: ExperienceSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> ExperienceSnapshot:
        aggregate = replace(
            snapshot.experience,
            publish_at=publish_at,
            updated_at=now,
            version=snapshot.experience.version + 1,
        )
        updated = replace(snapshot, experience=aggregate)
        self.snapshots[aggregate.id] = updated
        return updated

    async def unpublish(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        aggregate = replace(
            snapshot.experience,
            published_revision_id=None,
            publish_at=None,
            unpublished_at=now,
            updated_at=now,
            version=snapshot.experience.version + 1,
        )
        updated = ExperienceSnapshot(aggregate, snapshot.draft, None)
        self.snapshots[aggregate.id] = updated
        return updated

    async def set_visibility(
        self,
        snapshot: ExperienceSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> ExperienceSnapshot:
        aggregate = replace(
            snapshot.experience,
            visible=visible,
            updated_at=now,
            version=snapshot.experience.version + 1,
        )
        updated = replace(snapshot, experience=aggregate)
        self.snapshots[aggregate.id] = updated
        return updated

    async def reorder(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Experience, ...]:
        updated: list[Experience] = []
        for position, identifier in enumerate(ordered_ids):
            snapshot = self.snapshots[identifier]
            aggregate = replace(
                snapshot.experience,
                position=position,
                updated_at=now,
                version=snapshot.experience.version + 1,
            )
            self.snapshots[identifier] = replace(snapshot, experience=aggregate)
            updated.append(aggregate)
        return tuple(updated)

    async def soft_delete(
        self,
        snapshot: ExperienceSnapshot,
        *,
        now: datetime,
    ) -> ExperienceSnapshot:
        aggregate = replace(
            snapshot.experience,
            published_revision_id=None,
            publish_at=None,
            deleted_at=now,
            updated_at=now,
            version=snapshot.experience.version + 1,
        )
        updated = ExperienceSnapshot(aggregate, snapshot.draft, None)
        self.snapshots[aggregate.id] = updated
        return updated


class _FakeIdempotency:
    """Replay completed operations and reject mismatched payloads."""

    def __init__(self) -> None:
        self.requests: dict[tuple[bytes, str, bytes], tuple[bytes, UUID]] = {}
        self.outcomes: dict[UUID, IdempotencyOutcome] = {}

    async def acquire(self, request: IdempotencyRequest) -> IdempotencyDecision:
        key = (request.actor_digest, request.route, request.key_digest)
        existing = self.requests.get(key)
        if existing is None:
            self.requests[key] = (request.request_fingerprint, IDEMPOTENCY_ID)
            return IdempotencyDecision(IdempotencyDecisionType.ACQUIRED, IDEMPOTENCY_ID)
        fingerprint, record_id = existing
        if fingerprint != request.request_fingerprint:
            return IdempotencyDecision(IdempotencyDecisionType.PAYLOAD_CONFLICT)
        outcome = self.outcomes.get(record_id)
        if outcome is None:
            return IdempotencyDecision(IdempotencyDecisionType.IN_PROGRESS)
        return IdempotencyDecision(IdempotencyDecisionType.REPLAY, record_id, outcome)

    async def complete(
        self,
        record_id: UUID,
        outcome: IdempotencyOutcome,
        *,
        completed_at: datetime,
    ) -> None:
        del completed_at
        self.outcomes[record_id] = outcome

    async def purge_expired(self, *, before: datetime) -> int:
        del before
        return 0


class _FakeAudit:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class _FakeUnitOfWork:
    def __init__(self, repository: _FakeExperiencesRepository) -> None:
        self.experiences = repository
        self.audit = _FakeAudit()
        self.idempotency = _FakeIdempotency()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception_type, exception, traceback

    async def commit(self) -> None:
        self.commits += 1


class _FakeSkills:
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, ...]] = []

    async def resolve(self, skill_ids: tuple[UUID, ...]) -> tuple[SkillReferenceSummary, ...]:
        self.calls.append(skill_ids)
        catalog = {
            SKILL_ID: SkillReferenceSummary(
                id=SKILL_ID,
                name="Python",
                slug="python",
                visible=True,
            ),
            HIDDEN_SKILL_ID: SkillReferenceSummary(
                id=HIDDEN_SKILL_ID,
                name="Internal tool",
                slug="internal-tool",
                visible=False,
            ),
        }
        return tuple(catalog[item] for item in skill_ids)


@pytest.fixture
def harness() -> tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills]:
    """Build a deterministic service over shared in-memory transaction ports."""
    repository = _FakeExperiencesRepository()
    uow = _FakeUnitOfWork(repository)
    skills = _FakeSkills()
    identifiers = iter((EXPERIENCE_ID, REVISION_ONE_ID, REVISION_TWO_ID))
    service = ExperiencesService(
        cast("ExperiencesUnitOfWorkFactory", lambda: uow),
        skills,
        clock=lambda: NOW,
        id_factory=lambda: next(identifiers),
    )
    return service, uow, skills


async def _create(service: ExperiencesService) -> ExperienceSnapshot:
    return await service.create(
        CreateExperienceCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-create",
            idempotency_key="create-key-000001",
            canonical_payload=b"create",
            values=_values(),
        )
    )


@pytest.mark.asyncio
async def test_create_is_atomic_revision_one_and_validates_skills(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Create stages the stable shell, revision one, audit, and idempotency together."""
    service, uow, skills = harness

    snapshot = await _create(service)

    assert snapshot.experience.draft_revision_id == REVISION_ONE_ID
    assert snapshot.experience.published_revision_id is None
    assert snapshot.draft.revision_number == 1
    assert snapshot.draft.frozen is False
    assert skills.calls == [(SKILL_ID, HIDDEN_SKILL_ID)]
    assert uow.commits == 1
    assert [entry.event_type for entry in uow.audit.entries] == ["experience.created"]


@pytest.mark.asyncio
async def test_publish_copies_draft_once_and_idempotent_replay_has_no_second_effect(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """A publish freezes once and a same-key retry returns the stored aggregate."""
    service, uow, _skills = harness
    created = await _create(service)
    command = PublishExperienceCommand(
        actor=ActorContext.administrator(ACTOR_ID),
        request_id="req-publish",
        experience_id=created.experience.id,
        if_match='"v1"',
        idempotency_key="publish-key-00001",
        canonical_payload=b"publish",
    )

    published = await service.publish(command)
    replayed = await service.publish(command)

    assert published == replayed
    assert published.published is not None
    assert published.published.id == REVISION_ONE_ID
    assert published.published.frozen is True
    assert published.draft.id == REVISION_TWO_ID
    assert published.draft.values == published.published.values
    assert published.experience.publish_at == NOW
    assert uow.experiences.publish_calls == 1


@pytest.mark.asyncio
async def test_edit_after_publish_changes_only_copy_on_write_draft(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Saving live changes cannot mutate the frozen public revision."""
    service, _uow, _skills = harness
    created = await _create(service)
    await service.publish(
        PublishExperienceCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-publish",
            experience_id=created.experience.id,
            if_match='"v1"',
            idempotency_key="publish-key-00001",
            canonical_payload=b"publish",
        )
    )

    changed = await service.save_draft(
        SaveExperienceDraftCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-save",
            experience_id=created.experience.id,
            if_match='"v2"',
            values=_values(role="Principal Engineer"),
        )
    )

    assert changed.draft.values.role_title == "Principal Engineer"
    assert changed.published is not None
    assert changed.published.values.role_title == "Staff Engineer"
    assert changed.published.frozen is True


@pytest.mark.asyncio
async def test_public_projection_uses_effective_database_time_and_omits_hidden_skills(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Future content is absent and public skill evidence is visibility-filtered."""
    service, uow, skills = harness
    created = await _create(service)
    scheduled = await service.publish(
        PublishExperienceCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-publish",
            experience_id=created.experience.id,
            if_match='"v1"',
            idempotency_key="publish-key-00001",
            canonical_payload=b"future",
            publish_at=NOW + timedelta(hours=1),
        )
    )
    query = PublicExperienceQuery(PageRequest())

    assert (await service.public_list(query)).items == ()
    uow.experiences.now = NOW + timedelta(hours=1)
    public = await service.public_list(query)

    assert scheduled.published is not None
    assert public.items[0].role_title == scheduled.published.values.role_title
    assert public.items[0].skills == (PublicSkillReference(name="Python", slug="python"),)
    assert skills.calls[-1] == (SKILL_ID, HIDDEN_SKILL_ID)


@pytest.mark.asyncio
async def test_reference_facade_distinguishes_admin_identity_from_public_eligibility(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Downstream modules can validate a target without widening its public state."""
    service, uow, _skills = harness
    created = await _create(service)
    await service.publish(
        PublishExperienceCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-publish",
            experience_id=created.experience.id,
            if_match='"v1"',
            idempotency_key="publish-key-00001",
            canonical_payload=b"future",
            publish_at=NOW + timedelta(hours=1),
        )
    )
    facade = ExperienceReferenceFacade(service)

    scheduled = (await facade.resolve((EXPERIENCE_ID,)))[0]
    assert scheduled.role_title == "Staff Engineer"
    assert scheduled.public is None

    uow.experiences.now = NOW + timedelta(hours=1)
    effective = (await facade.resolve((EXPERIENCE_ID,)))[0]
    assert effective.public == PublicExperienceReference(
        id=EXPERIENCE_ID,
        company_name="Example Studio",
        role_title="Staff Engineer",
    )

    with pytest.raises(ExperienceNotFoundError):
        await facade.resolve((EXPERIENCE_ID, EXPERIENCE_ID))
    with pytest.raises(ExperienceNotFoundError):
        await facade.resolve((UUID("0198a12c-1000-7000-8000-000000000099"),))


@pytest.mark.asyncio
async def test_visibility_reschedule_unpublish_and_delete_are_distinct(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Independent lifecycle actions advance versions without erasing revisions."""
    service, _uow, _skills = harness
    created = await _create(service)
    published = await service.publish(
        PublishExperienceCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-publish",
            experience_id=created.experience.id,
            if_match='"v1"',
            idempotency_key="publish-key-00001",
            canonical_payload=b"publish",
        )
    )
    hidden = await service.set_visibility(
        SetExperienceVisibilityCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-hide",
            experience_id=EXPERIENCE_ID,
            if_match='"v2"',
            visible=False,
        )
    )
    rescheduled = await service.reschedule(
        RescheduleExperienceCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-reschedule",
            EXPERIENCE_ID,
            '"v3"',
            "reschedule-key-001",
            b"reschedule",
            NOW + timedelta(days=1),
        )
    )
    unpublished = await service.unpublish(
        UnpublishExperienceCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-unpublish",
            EXPERIENCE_ID,
            '"v4"',
            "unpublish-key-0001",
            b"unpublish",
        )
    )
    deleted = await service.delete(
        DeleteExperienceCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-delete",
            EXPERIENCE_ID,
            '"v5"',
        )
    )

    assert published.published is not None
    assert hidden.experience.visible is False
    assert rescheduled.experience.publish_at == NOW + timedelta(days=1)
    assert unpublished.experience.published_revision_id is None
    assert unpublished.draft.id == REVISION_TWO_ID
    assert deleted.experience.deleted_at == NOW
    assert deleted.draft.id == REVISION_TWO_ID


@pytest.mark.asyncio
async def test_reorder_requires_one_complete_unique_set_and_replays_safely(
    harness: tuple[ExperiencesService, _FakeUnitOfWork, _FakeSkills],
) -> None:
    """Ordering is complete, duplicate-free, versioned, audited, and idempotent."""
    service, uow, _skills = harness
    first = await _create(service)
    second_id = UUID("0198a12c-1000-7000-8000-000000000008")
    second_revision_id = UUID("0198a12c-1000-7000-8000-000000000009")
    second = ExperienceSnapshot(
        replace(first.experience, id=second_id, draft_revision_id=second_revision_id, position=1),
        replace(first.draft, id=second_revision_id, experience_id=second_id),
        None,
    )
    uow.experiences.snapshots[second_id] = second
    command = ReorderExperiencesCommand(
        actor=ActorContext.administrator(ACTOR_ID),
        request_id="req-reorder",
        if_match='"v1"',
        idempotency_key="reorder-key-0001",
        canonical_payload=b"second-first",
        ordered_ids=(second_id, EXPERIENCE_ID),
    )

    ordered = await service.reorder(command)
    replayed = await service.reorder(command)

    assert [item.id for item in ordered] == [second_id, EXPERIENCE_ID]
    assert [item.position for item in ordered] == [0, 1]
    assert [item.id for item in replayed] == [second_id, EXPERIENCE_ID]
    assert [entry.event_type for entry in uow.audit.entries][-1] == "experience.reordered"

    with pytest.raises(ExperienceValidationError) as duplicate_error:
        await service.reorder(
            replace(
                command,
                idempotency_key="reorder-key-0002",
                canonical_payload=b"duplicate",
                if_match='"v2"',
                ordered_ids=(second_id, second_id),
            )
        )
    assert duplicate_error.value.code == "duplicate_id"
    with pytest.raises(ExperienceValidationError) as incomplete_error:
        await service.reorder(
            replace(
                command,
                idempotency_key="reorder-key-0003",
                canonical_payload=b"incomplete",
                if_match='"v2"',
                ordered_ids=(second_id,),
            )
        )
    assert incomplete_error.value.code == "incomplete_order"

    uow.experiences.snapshots.clear()
    with pytest.raises(ExperienceNotFoundError):
        await service.reorder(
            replace(
                command,
                idempotency_key="reorder-key-0004",
                canonical_payload=b"empty",
            )
        )
