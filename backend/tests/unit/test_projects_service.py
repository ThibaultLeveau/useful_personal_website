"""M6 project application tests over deterministic in-memory ports."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
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
    ExperienceReferenceSummary,
    PublicExperienceReference,
)
from app.modules.projects.domain import (
    AdminProjectQuery,
    Project,
    ProjectReferenceSummary,
    ProjectRevision,
    ProjectSnapshot,
    ProjectStatus,
    ProjectValues,
    PublicProjectQuery,
    PublicProjectReference,
)
from app.modules.projects.service import (
    CreateProjectCommand,
    DeleteProjectCommand,
    ProjectNotFoundError,
    ProjectReferenceFacade,
    ProjectRelationError,
    ProjectSlugConflictError,
    ProjectsService,
    PublishProjectCommand,
    ReorderProjectsCommand,
    SaveProjectDraftCommand,
    SetProjectFeaturedCommand,
    SetProjectVisibilityCommand,
    UnpublishProjectCommand,
)
from app.modules.skills.domain import SkillReferenceSummary

if TYPE_CHECKING:
    from types import TracebackType

    from app.common.application.idempotency import IdempotencyOutcome, IdempotencyRequest
    from app.modules.audit.domain import AuditEntry
    from app.modules.projects.ports import ProjectsUnitOfWorkFactory

NOW = datetime(2026, 8, 4, 9, tzinfo=UTC)
ACTOR_ID = UUID("0198a13d-1000-7000-8000-000000000001")
PROJECT_ID = UUID("0198a13d-1000-7000-8000-000000000002")
DRAFT_ID = UUID("0198a13d-1000-7000-8000-000000000003")
NEXT_DRAFT_ID = UUID("0198a13d-1000-7000-8000-000000000004")
RELATED_ID = UUID("0198a13d-1000-7000-8000-000000000005")
RELATED_DRAFT_ID = UUID("0198a13d-1000-7000-8000-000000000006")
SKILL_ID = UUID("0198a13d-1000-7000-8000-000000000007")
HIDDEN_SKILL_ID = UUID("0198a13d-1000-7000-8000-000000000008")
EXPERIENCE_ID = UUID("0198a13d-1000-7000-8000-000000000009")
HIDDEN_EXPERIENCE_ID = UUID("0198a13d-1000-7000-8000-000000000010")
IDEMPOTENCY_ID = UUID("0198a13d-1000-7000-8000-000000000011")


def _values(
    *,
    impact: str = "Reduced diagnosis time by making release risk visible.",
    related: tuple[UUID, ...] = (),
) -> ProjectValues:
    return ProjectValues(
        name="Release observability platform",
        short_description="Connected delivery changes to service health.",
        full_description="A **complete** controlled case study.",
        problem="Teams lacked a shared model of release risk.",
        solution="Built typed ingestion and review workflows.",
        impact=impact,
        owner_role="Technical lead",
        architecture="FastAPI, PostgreSQL, and server-rendered Next.js.",
        technologies=("Python", "PostgreSQL"),
        status=ProjectStatus.ACTIVE,
        start_date=date(2025, 1, 1),
        end_date=None,
        repository_url="https://github.com/example/release-observability",
        demo_url="https://projects.example.test/release-observability",
        skill_ids=(SKILL_ID, HIDDEN_SKILL_ID),
        experience_ids=(EXPERIENCE_ID, HIDDEN_EXPERIENCE_ID),
        related_project_ids=related,
        seo_title=None,
        seo_description=None,
        canonical_url=None,
    )


class _FakeProjectsRepository:
    def __init__(self) -> None:
        self.snapshots: dict[UUID, ProjectSnapshot] = {}
        self.now = NOW
        self.publish_calls = 0
        self.forced_cycle = False

    async def database_now(self) -> datetime:
        return self.now

    async def slug_exists(self, slug: str) -> bool:
        return any(
            item.project.slug.casefold() == slug.casefold() for item in self.snapshots.values()
        )

    async def list_admin(self, query: AdminProjectQuery) -> Page[ProjectSnapshot]:
        rows = tuple(self.snapshots.values())
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def list_public(self, query: PublicProjectQuery) -> Page[ProjectSnapshot]:
        rows = tuple(
            item
            for item in self.snapshots.values()
            if item.project.visible
            and item.project.deleted_at is None
            and item.project.publish_at is not None
            and item.project.publish_at <= self.now
            and item.published is not None
            and (query.featured is None or item.project.featured is query.featured)
        )
        return Page(rows, page_metadata(query.page, total_items=len(rows)))

    async def get(
        self,
        project_id: UUID,
        *,
        for_update: bool = False,
    ) -> ProjectSnapshot | None:
        del for_update
        return self.snapshots.get(project_id)

    async def get_public_by_slug(self, slug: str) -> ProjectSnapshot | None:
        page = await self.list_public(PublicProjectQuery(PageRequest(page_size=100)))
        return next((item for item in page.items if item.project.slug == slug), None)

    async def list_ordered(self, *, for_update: bool = False) -> tuple[Project, ...]:
        del for_update
        return tuple(
            sorted(
                (
                    item.project
                    for item in self.snapshots.values()
                    if item.project.deleted_at is None
                ),
                key=lambda item: (item.position, item.id),
            )
        )

    async def reference_summaries(
        self,
        project_ids: tuple[UUID, ...],
    ) -> tuple[ProjectReferenceSummary, ...]:
        summaries: list[ProjectReferenceSummary] = []
        for identifier in project_ids:
            snapshot = self.snapshots.get(identifier)
            if snapshot is None:
                continue
            effective = (
                snapshot.project.visible
                and snapshot.project.deleted_at is None
                and snapshot.project.publish_at is not None
                and snapshot.project.publish_at <= self.now
                and snapshot.published is not None
            )
            summaries.append(
                ProjectReferenceSummary(
                    id=identifier,
                    slug=snapshot.project.slug,
                    name=snapshot.draft.values.name,
                    visible=snapshot.project.visible,
                    deleted=snapshot.project.deleted_at is not None,
                    public=(
                        PublicProjectReference(
                            id=identifier,
                            slug=snapshot.project.slug,
                            name=snapshot.published.values.name,
                        )
                        if effective and snapshot.published is not None
                        else None
                    ),
                )
            )
        return tuple(summaries)

    async def related_graph_would_cycle(
        self,
        source_id: UUID,
        target_ids: tuple[UUID, ...],
        *,
        maximum_nodes: int,
    ) -> bool:
        del source_id, target_ids, maximum_nodes
        return self.forced_cycle

    async def add(self, project: Project, revision: ProjectRevision) -> None:
        self.snapshots[project.id] = ProjectSnapshot(project, revision, None)

    async def save_draft(
        self,
        snapshot: ProjectSnapshot,
        values: ProjectValues,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        updated = ProjectSnapshot(
            replace(
                snapshot.project,
                updated_at=now,
                version=snapshot.project.version + 1,
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
        self.snapshots[updated.project.id] = updated
        return updated

    async def publish(
        self,
        snapshot: ProjectSnapshot,
        *,
        publish_at: datetime,
        next_revision_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> ProjectSnapshot:
        self.publish_calls += 1
        frozen = replace(snapshot.draft, frozen=True, updated_at=now)
        draft = ProjectRevision(
            id=next_revision_id,
            project_id=snapshot.project.id,
            revision_number=frozen.revision_number + 1,
            based_on_revision_id=frozen.id,
            values=frozen.values,
            frozen=False,
            created_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        aggregate = replace(
            snapshot.project,
            draft_revision_id=draft.id,
            published_revision_id=frozen.id,
            publish_at=publish_at,
            unpublished_at=None,
            updated_at=now,
            version=snapshot.project.version + 1,
        )
        updated = ProjectSnapshot(aggregate, draft, frozen)
        self.snapshots[aggregate.id] = updated
        return updated

    async def reschedule(
        self,
        snapshot: ProjectSnapshot,
        *,
        publish_at: datetime,
        now: datetime,
    ) -> ProjectSnapshot:
        updated = replace(
            snapshot,
            project=replace(
                snapshot.project,
                publish_at=publish_at,
                updated_at=now,
                version=snapshot.project.version + 1,
            ),
        )
        self.snapshots[updated.project.id] = updated
        return updated

    async def unpublish(
        self,
        snapshot: ProjectSnapshot,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        aggregate = replace(
            snapshot.project,
            published_revision_id=None,
            publish_at=None,
            unpublished_at=now,
            updated_at=now,
            version=snapshot.project.version + 1,
        )
        updated = ProjectSnapshot(aggregate, snapshot.draft, None)
        self.snapshots[aggregate.id] = updated
        return updated

    async def set_visibility(
        self,
        snapshot: ProjectSnapshot,
        *,
        visible: bool,
        now: datetime,
    ) -> ProjectSnapshot:
        return self._flag(snapshot, "visible", value=visible, now=now)

    async def set_featured(
        self,
        snapshot: ProjectSnapshot,
        *,
        featured: bool,
        now: datetime,
    ) -> ProjectSnapshot:
        return self._flag(snapshot, "featured", value=featured, now=now)

    def _flag(
        self,
        snapshot: ProjectSnapshot,
        field: str,
        *,
        value: bool,
        now: datetime,
    ) -> ProjectSnapshot:
        aggregate = (
            replace(snapshot.project, visible=value)
            if field == "visible"
            else replace(snapshot.project, featured=value)
        )
        aggregate = replace(
            aggregate,
            updated_at=now,
            version=aggregate.version + 1,
        )
        updated = replace(snapshot, project=aggregate)
        self.snapshots[aggregate.id] = updated
        return updated

    async def reorder(
        self,
        ordered_ids: tuple[UUID, ...],
        *,
        now: datetime,
    ) -> tuple[Project, ...]:
        updated: list[Project] = []
        for position, identifier in enumerate(ordered_ids):
            snapshot = self.snapshots[identifier]
            aggregate = replace(
                snapshot.project,
                position=position,
                updated_at=now,
                version=snapshot.project.version + 1,
            )
            self.snapshots[identifier] = replace(snapshot, project=aggregate)
            updated.append(aggregate)
        return tuple(updated)

    async def soft_delete(
        self,
        snapshot: ProjectSnapshot,
        *,
        now: datetime,
    ) -> ProjectSnapshot:
        aggregate = replace(
            snapshot.project,
            published_revision_id=None,
            publish_at=None,
            deleted_at=now,
            updated_at=now,
            version=snapshot.project.version + 1,
        )
        updated = ProjectSnapshot(aggregate, snapshot.draft, None)
        self.snapshots[aggregate.id] = updated
        return updated


class _FakeIdempotency:
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


class _FakeMediaRepository:
    def __init__(self) -> None:
        self.owner_usages: dict[tuple[str, UUID], tuple[object, ...]] = {}

    async def replace_owner_usages(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        usages: tuple[object, ...],
        now: datetime,
    ) -> None:
        del now
        self.owner_usages[(owner_type, owner_id)] = usages


class _FakeUnitOfWork:
    def __init__(self, repository: _FakeProjectsRepository) -> None:
        self.projects = repository
        self.media = _FakeMediaRepository()
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
    async def resolve(self, skill_ids: tuple[UUID, ...]) -> tuple[SkillReferenceSummary, ...]:
        catalog = {
            SKILL_ID: SkillReferenceSummary(
                id=SKILL_ID,
                name="Python",
                slug="python",
                visible=True,
            ),
            HIDDEN_SKILL_ID: SkillReferenceSummary(
                id=HIDDEN_SKILL_ID,
                name="Internal skill",
                slug="internal-skill",
                visible=False,
            ),
        }
        return tuple(catalog[item] for item in skill_ids)


class _FakeExperiences:
    async def resolve(
        self,
        experience_ids: tuple[UUID, ...],
    ) -> tuple[ExperienceReferenceSummary, ...]:
        catalog = {
            EXPERIENCE_ID: ExperienceReferenceSummary(
                id=EXPERIENCE_ID,
                company_name="Example Studio",
                role_title="Staff Engineer",
                visible=True,
                deleted=False,
                public=PublicExperienceReference(
                    id=EXPERIENCE_ID,
                    company_name="Example Studio",
                    role_title="Staff Engineer",
                ),
            ),
            HIDDEN_EXPERIENCE_ID: ExperienceReferenceSummary(
                id=HIDDEN_EXPERIENCE_ID,
                company_name="Private Studio",
                role_title="Consultant",
                visible=False,
                deleted=False,
                public=None,
            ),
        }
        return tuple(catalog[item] for item in experience_ids)


@pytest.fixture
def harness() -> tuple[ProjectsService, _FakeUnitOfWork]:
    """Build a deterministic service over shared in-memory transaction ports."""
    repository = _FakeProjectsRepository()
    uow = _FakeUnitOfWork(repository)
    identifiers = iter((PROJECT_ID, DRAFT_ID, NEXT_DRAFT_ID))
    service = ProjectsService(
        cast("ProjectsUnitOfWorkFactory", lambda: uow),
        _FakeSkills(),
        _FakeExperiences(),
        clock=lambda: NOW,
        id_factory=lambda: next(identifiers),
    )
    return service, uow


async def _create(service: ProjectsService, *, related: tuple[UUID, ...] = ()) -> ProjectSnapshot:
    return await service.create(
        CreateProjectCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-create",
            idempotency_key="create-project-001",
            canonical_payload=b"create",
            slug="Release Observability",
            values=_values(related=related),
        )
    )


def _related_snapshot() -> ProjectSnapshot:
    """Create one existing nonpublic related-project provider record."""
    project = Project(
        id=RELATED_ID,
        slug="related-platform",
        visible=True,
        featured=False,
        position=1,
        draft_revision_id=RELATED_DRAFT_ID,
        published_revision_id=None,
        publish_at=None,
        unpublished_at=None,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    revision = ProjectRevision(
        id=RELATED_DRAFT_ID,
        project_id=RELATED_ID,
        revision_number=1,
        based_on_revision_id=None,
        values=replace(_values(), name="Related platform"),
        frozen=False,
        created_by=ACTOR_ID,
        created_at=NOW,
        updated_at=NOW,
    )
    return ProjectSnapshot(project, revision, None)


@pytest.mark.asyncio
async def test_create_normalizes_stable_slug_and_commits_revision_relations(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Create freezes a normalized route and validates revision-owned evidence."""
    service, uow = harness
    created = await _create(service)
    assert created.project.slug == "release-observability"
    assert created.draft.values.skill_ids == (SKILL_ID, HIDDEN_SKILL_ID)
    assert [entry.event_type for entry in uow.audit.entries] == ["project.created"]
    assert uow.commits == 1


@pytest.mark.asyncio
async def test_create_rejects_slug_collision_and_unknown_related_target(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Stable slugs and unknown graph targets fail safely before persistence."""
    service, uow = harness
    await _create(service)
    with pytest.raises(ProjectSlugConflictError):
        await service.create(
            CreateProjectCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-two",
                "create-project-002",
                b"two",
                "release-observability",
                _values(),
            )
        )
    uow.projects.forced_cycle = True
    with pytest.raises(ProjectRelationError) as caught:
        await service.save_draft(
            SaveProjectDraftCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-save",
                PROJECT_ID,
                '"v1"',
                _values(related=(RELATED_ID,)),
            )
        )
    assert caught.value.code == "project_not_found"


@pytest.mark.asyncio
async def test_save_rejects_bounded_related_project_cycle(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """A transaction-time graph check rejects a cycle of any reachable length."""
    service, uow = harness
    await _create(service)
    uow.projects.snapshots[RELATED_ID] = _related_snapshot()
    uow.projects.forced_cycle = True
    with pytest.raises(ProjectRelationError) as caught:
        await service.save_draft(
            SaveProjectDraftCommand(
                ActorContext.administrator(ACTOR_ID),
                "req-save-cycle",
                PROJECT_ID,
                '"v1"',
                _values(related=(RELATED_ID,)),
            )
        )
    assert caught.value.code == "related_project_cycle"


@pytest.mark.asyncio
async def test_publish_is_copy_on_write_and_replay_has_one_effect(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """A same-key publish retry returns the single frozen effect."""
    service, uow = harness
    created = await _create(service)
    command = PublishProjectCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-publish",
        created.project.id,
        '"v1"',
        "publish-project-01",
        b"publish",
    )
    published = await service.publish(command)
    replayed = await service.publish(command)
    assert published == replayed
    assert published.published is not None
    assert published.published.frozen
    assert published.draft.values == published.published.values
    assert published.draft.id == NEXT_DRAFT_ID
    assert uow.projects.publish_calls == 1


@pytest.mark.asyncio
async def test_edit_after_publish_keeps_public_content_and_relations_frozen(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Draft content and hidden provider labels never widen the public projection."""
    service, _uow = harness
    created = await _create(service)
    await service.publish(
        PublishProjectCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-publish",
            created.project.id,
            '"v1"',
            "publish-project-01",
            b"publish",
        )
    )
    await service.save_draft(
        SaveProjectDraftCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-save",
            PROJECT_ID,
            '"v2"',
            _values(impact="Draft-only outcome."),
        )
    )
    public = await service.public_detail("release-observability")
    assert public.impact == _values().impact
    assert [item.slug for item in public.skills] == ["python"]
    assert [item.id for item in public.experiences] == [EXPERIENCE_ID]


@pytest.mark.asyncio
async def test_feature_visibility_unpublish_and_delete_remain_distinct(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Stable flags and lifecycle/deletion actions retain distinct semantics."""
    service, _uow = harness
    created = await _create(service)
    published = await service.publish(
        PublishProjectCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-publish",
            created.project.id,
            '"v1"',
            "publish-project-01",
            b"publish",
        )
    )
    featured = await service.set_featured(
        SetProjectFeaturedCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-feature",
            project_id=PROJECT_ID,
            if_match='"v2"',
            featured=True,
        )
    )
    hidden = await service.set_visibility(
        SetProjectVisibilityCommand(
            actor=ActorContext.administrator(ACTOR_ID),
            request_id="req-hide",
            project_id=PROJECT_ID,
            if_match='"v3"',
            visible=False,
        )
    )
    assert published.project.featured is False
    assert featured.project.featured is True
    assert hidden.project.visible is False
    unpublished = await service.unpublish(
        UnpublishProjectCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-unpublish",
            PROJECT_ID,
            '"v4"',
            "unpublish-project",
            b"unpublish",
        )
    )
    deleted = await service.delete(
        DeleteProjectCommand(
            ActorContext.administrator(ACTOR_ID),
            "req-delete",
            PROJECT_ID,
            '"v5"',
        )
    )
    assert unpublished.project.deleted_at is None
    assert deleted.project.deleted_at == NOW


@pytest.mark.asyncio
async def test_reorder_requires_complete_unique_set_and_replays(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Complete ordering is deterministic and safely replayable."""
    service, _uow = harness
    await _create(service)
    command = ReorderProjectsCommand(
        ActorContext.administrator(ACTOR_ID),
        "req-order",
        '"v1"',
        "reorder-projects-1",
        b"order",
        (PROJECT_ID,),
    )
    first = await service.reorder(command)
    second = await service.reorder(command)
    assert first[0].id == second[0].id == PROJECT_ID


@pytest.mark.asyncio
async def test_reference_facade_does_not_widen_hidden_project_state(
    harness: tuple[ProjectsService, _FakeUnitOfWork],
) -> None:
    """Provider consumers see admin identity without public eligibility leakage."""
    service, _uow = harness
    await _create(service)
    facade = ProjectReferenceFacade(service)
    draft = (await facade.resolve((PROJECT_ID,)))[0]
    assert draft.name == _values().name
    assert draft.public is None
    with pytest.raises(ProjectNotFoundError):
        await facade.resolve((PROJECT_ID, PROJECT_ID))
