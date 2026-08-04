"""Skills application commands, queries, public projection, and reference facade."""

from __future__ import annotations

from dataclasses import dataclass, replace
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
from app.common.domain.pagination import PageRequest
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7
from app.modules.skills.domain import (
    AdminSkillQuery,
    CategoryInUseError,
    PublicSkillGroup,
    PublicSkillQuery,
    RelationProviderUnavailableError,
    Skill,
    SkillCategory,
    SkillCategoryValues,
    SkillReferenceSummary,
    SkillValues,
    public_skill_groups,
    require_complete_order,
    validate_category_values,
    validate_skill_values,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.common.domain.pagination import Page
    from app.modules.skills.ports import SkillsUnitOfWork, SkillsUnitOfWorkFactory

_CATEGORY_RESOURCE = "category"
_SKILL_RESOURCE = "skill"
_ORDER_RESOURCE = "order"
_REFERENCE_RESOURCE = "skill_reference"

_READ_POLICY = AccessPolicy(
    resource="skills",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_WRITE_POLICY = AccessPolicy(
    resource="skills",
    action="write",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)


class SkillsNotFoundError(Exception):
    """A requested skill/category does not exist in the authorized scope."""

    def __init__(self, resource: str) -> None:
        """Retain only a safe resource-kind discriminator."""
        super().__init__("skills resource not found")
        self.resource = resource


class SkillsIdempotencyRejectedError(Exception):
    """An idempotent skills command conflicts or remains in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain the safe common idempotency decision."""
        super().__init__("idempotency admission rejected")
        self.decision = decision


@dataclass(frozen=True, slots=True)
class CategoryCommand:
    """Create/update category request."""

    actor: ActorContext
    request_id: str
    values: SkillCategoryValues
    idempotency_key: str | None = None
    canonical_payload: bytes = b""
    category_id: UUID | None = None
    if_match: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteCategoryCommand:
    """Delete one empty category."""

    actor: ActorContext
    request_id: str
    category_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class SkillCommand:
    """Create/update skill request."""

    actor: ActorContext
    request_id: str
    values: SkillValues
    idempotency_key: str | None = None
    canonical_payload: bytes = b""
    skill_id: UUID | None = None
    if_match: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteSkillCommand:
    """Delete one skill."""

    actor: ActorContext
    request_id: str
    skill_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class ReorderCommand:
    """Idempotent complete order for categories or one category's skills."""

    actor: ActorContext
    request_id: str
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]
    category_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class _AuditFact:
    """One value-free audit fact staged with a command."""

    actor: ActorContext
    request_id: str
    event_type: str
    resource_id: UUID
    version: int
    fields: tuple[str, ...]


class SkillsService:
    """Authorize and transact all M4 skills behavior."""

    def __init__(
        self,
        uow_factory: SkillsUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Store deterministic transaction, clock, and opaque-ID seams."""
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def list_categories(self, actor: ActorContext) -> tuple[SkillCategory, ...]:
        """Return every ordered category to an administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return await uow.categories.list_all()

    async def get_category(self, actor: ActorContext, category_id: UUID) -> SkillCategory:
        """Return one category without leaking unauthorized existence."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            category = await uow.categories.get(category_id)
            if category is None:
                raise SkillsNotFoundError(_CATEGORY_RESOURCE)
            return category

    async def create_category(self, command: CategoryCommand) -> SkillCategory:
        """Create one category at the end of global deterministic order."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_category_values(command.values)
        now = self._clock()
        if command.idempotency_key is None:
            message = "category creation requires an idempotency key"
            raise RuntimeError(message)
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=command.actor,
                    route="/api/v1/admin/skill-categories",
                    key=command.idempotency_key,
                    canonical_payload=command.canonical_payload,
                    requested_at=now,
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                if decision.outcome is None or decision.outcome.resource_id is None:
                    message = "a category replay has no resource outcome"
                    raise RuntimeError(message)
                replay = await uow.categories.get(decision.outcome.resource_id)
                if replay is None:
                    raise SkillsNotFoundError(_CATEGORY_RESOURCE)
                return replay
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                raise SkillsIdempotencyRejectedError(decision)
            categories = await uow.categories.list_all(for_update=True)
            category = SkillCategory(
                id=self._id_factory(),
                name=values.name,
                slug=values.slug,
                description=values.description,
                position=len(categories),
                created_at=now,
                updated_at=now,
                version=1,
            )
            await uow.categories.add(category)
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill_category.created",
                    category.id,
                    category.version,
                    ("name", "slug", "description"),
                ),
            )
            if decision.record_id is None:
                message = "an acquired idempotency decision has no record"
                raise RuntimeError(message)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=201,
                    result_code="skill_category.created",
                    resource_type="skill_category",
                    resource_id=category.id,
                    resource_version=category.version,
                ),
                completed_at=now,
            )
            await uow.commit()
            return category

    async def update_category(self, command: CategoryCommand) -> SkillCategory:
        """Update one category with optimistic concurrency."""
        require_authorized(command.actor, _WRITE_POLICY)
        if command.category_id is None:
            raise SkillsNotFoundError(_CATEGORY_RESOURCE)
        values = validate_category_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            category = await uow.categories.get(command.category_id, for_update=True)
            if category is None:
                raise SkillsNotFoundError(_CATEGORY_RESOURCE)
            require_matching_version(command.if_match, current_version=category.version)
            updated = await uow.categories.update(category, values, now=now)
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill_category.updated",
                    updated.id,
                    updated.version,
                    ("name", "slug", "description"),
                ),
            )
            await uow.commit()
            return updated

    async def delete_category(self, command: DeleteCategoryCommand) -> None:
        """Delete only an empty category and normalize remaining order."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            category = await uow.categories.get(command.category_id, for_update=True)
            if category is None:
                raise SkillsNotFoundError(_CATEGORY_RESOURCE)
            require_matching_version(command.if_match, current_version=category.version)
            if await uow.categories.count_skills(category.id):
                raise CategoryInUseError
            await uow.categories.delete(category)
            remaining = tuple(
                item
                for item in await uow.categories.list_all(for_update=True)
                if item.id != category.id
            )
            await uow.categories.reorder(remaining, tuple(item.id for item in remaining), now=now)
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill_category.deleted",
                    category.id,
                    category.version,
                    (),
                ),
            )
            await uow.commit()

    async def list_skills(self, actor: ActorContext, query: AdminSkillQuery) -> Page[Skill]:
        """Return one exact admin page through allow-listed repository inputs."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return await uow.skills.list_admin(query)

    async def get_skill(self, actor: ActorContext, skill_id: UUID) -> Skill:
        """Return one administrator skill."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            skill = await uow.skills.get(skill_id)
            if skill is None:
                raise SkillsNotFoundError(_SKILL_RESOURCE)
            return skill

    async def create_skill(self, command: SkillCommand) -> Skill:
        """Create one skill at the end of its category order."""
        require_authorized(command.actor, _WRITE_POLICY)
        values = validate_skill_values(command.values)
        now = self._clock()
        if command.idempotency_key is None:
            message = "skill creation requires an idempotency key"
            raise RuntimeError(message)
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=command.actor,
                    route="/api/v1/admin/skills",
                    key=command.idempotency_key,
                    canonical_payload=command.canonical_payload,
                    requested_at=now,
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                if decision.outcome is None or decision.outcome.resource_id is None:
                    message = "a skill replay has no resource outcome"
                    raise RuntimeError(message)
                replay = await uow.skills.get(decision.outcome.resource_id)
                if replay is None:
                    raise SkillsNotFoundError(_SKILL_RESOURCE)
                return replay
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                raise SkillsIdempotencyRejectedError(decision)
            category = await uow.categories.get(values.category_id, for_update=True)
            if category is None:
                raise SkillsNotFoundError(_CATEGORY_RESOURCE)
            existing = await uow.skills.list_by_category(category.id, for_update=True)
            skill = Skill(
                id=self._id_factory(),
                name=values.name,
                slug=values.slug,
                category_id=values.category_id,
                description=values.description,
                proficiency_label=values.proficiency_label,
                proficiency_score=values.proficiency_score,
                years_experience=values.years_experience,
                icon_key=values.icon_key,
                position=len(existing),
                featured=values.featured,
                visible=values.visible,
                created_at=now,
                updated_at=now,
                version=1,
            )
            await uow.skills.add(skill)
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill.created",
                    skill.id,
                    skill.version,
                    self._skill_fields(),
                ),
            )
            if decision.record_id is None:
                message = "an acquired idempotency decision has no record"
                raise RuntimeError(message)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=201,
                    result_code="skill.created",
                    resource_type="skill",
                    resource_id=skill.id,
                    resource_version=skill.version,
                ),
                completed_at=now,
            )
            await uow.commit()
            return skill

    async def update_skill(self, command: SkillCommand) -> Skill:
        """Update or explicitly reassign a skill with order normalization."""
        require_authorized(command.actor, _WRITE_POLICY)
        if command.skill_id is None:
            raise SkillsNotFoundError(_SKILL_RESOURCE)
        values = validate_skill_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            skill = await uow.skills.get(command.skill_id, for_update=True)
            if skill is None:
                raise SkillsNotFoundError(_SKILL_RESOURCE)
            require_matching_version(command.if_match, current_version=skill.version)
            target = await uow.categories.get(values.category_id, for_update=True)
            if target is None:
                raise SkillsNotFoundError(_CATEGORY_RESOURCE)
            source_id = skill.category_id
            if target.id != source_id:
                target_skills = await uow.skills.list_by_category(target.id, for_update=True)
                skill = replace(skill, position=len(target_skills))
            updated = await uow.skills.update(skill, values, now=now)
            if target.id != source_id:
                source_skills = tuple(
                    item
                    for item in await uow.skills.list_by_category(source_id, for_update=True)
                    if item.id != updated.id
                )
                await uow.skills.reorder(
                    source_skills, tuple(item.id for item in source_skills), now=now
                )
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill.updated",
                    updated.id,
                    updated.version,
                    self._skill_fields(),
                ),
            )
            await uow.commit()
            return updated

    async def delete_skill(self, command: DeleteSkillCommand) -> None:
        """Delete one skill and atomically close its order gap."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            skill = await uow.skills.get(command.skill_id, for_update=True)
            if skill is None:
                raise SkillsNotFoundError(_SKILL_RESOURCE)
            require_matching_version(command.if_match, current_version=skill.version)
            await uow.skills.delete(skill)
            remaining = tuple(
                item
                for item in await uow.skills.list_by_category(skill.category_id, for_update=True)
                if item.id != skill.id
            )
            await uow.skills.reorder(remaining, tuple(item.id for item in remaining), now=now)
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    "skill.deleted",
                    skill.id,
                    skill.version,
                    (),
                ),
            )
            await uow.commit()

    async def reorder(
        self, command: ReorderCommand
    ) -> tuple[SkillCategory, ...] | tuple[Skill, ...]:
        """Apply one idempotent complete global/category-scoped order."""
        require_authorized(command.actor, _WRITE_POLICY)
        route = (
            "/api/v1/admin/skill-categories/actions/reorder"
            if command.category_id is None
            else "/api/v1/admin/skill-categories/{category_id}/skills/reorder"
        )
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=command.actor,
                    route=route,
                    key=command.idempotency_key,
                    canonical_payload=command.canonical_payload,
                    requested_at=now,
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return await self._current_order(uow, command.category_id)
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                raise SkillsIdempotencyRejectedError(decision)
            if command.category_id is None:
                current_categories = await uow.categories.list_all(for_update=True)
                if not current_categories:
                    raise SkillsNotFoundError(_ORDER_RESOURCE)
                require_matching_version(
                    command.if_match,
                    current_version=current_categories[0].version,
                )
                require_complete_order(
                    command.ordered_ids,
                    (item.id for item in current_categories),
                )
                updated_categories = await uow.categories.reorder(
                    current_categories,
                    command.ordered_ids,
                    now=now,
                )
                result: tuple[SkillCategory, ...] | tuple[Skill, ...] = updated_categories
                event_type = "skill_category.reordered"
                resource_id = updated_categories[0].id
                updated_version = updated_categories[0].version
            else:
                category = await uow.categories.get(command.category_id, for_update=True)
                if category is None:
                    raise SkillsNotFoundError(_CATEGORY_RESOURCE)
                current_skills = await uow.skills.list_by_category(
                    command.category_id,
                    for_update=True,
                )
                if not current_skills:
                    raise SkillsNotFoundError(_ORDER_RESOURCE)
                require_matching_version(
                    command.if_match,
                    current_version=current_skills[0].version,
                )
                require_complete_order(command.ordered_ids, (item.id for item in current_skills))
                updated_skills = await uow.skills.reorder(
                    current_skills,
                    command.ordered_ids,
                    now=now,
                )
                result = updated_skills
                event_type = "skill.reordered"
                resource_id = command.category_id
                updated_version = updated_skills[0].version
            self._audit(
                uow.audit.append,
                _AuditFact(
                    command.actor,
                    command.request_id,
                    event_type,
                    resource_id,
                    updated_version,
                    ("position",),
                ),
            )
            if decision.record_id is None:
                message = "an acquired idempotency decision has no record"
                raise RuntimeError(message)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=200,
                    result_code=event_type,
                    resource_type="skills",
                    resource_id=resource_id,
                    resource_version=updated_version,
                ),
                completed_at=now,
            )
            await uow.commit()
            return result

    async def public_list(
        self, query: PublicSkillQuery
    ) -> tuple[Page[Skill], tuple[PublicSkillGroup, ...]]:
        """Return a visibility-enforced public page plus non-empty groups."""
        async with self._uow_factory() as uow:
            page = await uow.skills.list_public(query)
            categories = await uow.categories.list_all()
            return page, public_skill_groups(categories, page.items)

    async def reference_summaries(
        self, skill_ids: tuple[UUID, ...]
    ) -> tuple[SkillReferenceSummary, ...]:
        """Validate complete opaque references for future content modules."""
        if len(skill_ids) != len(set(skill_ids)):
            raise SkillsNotFoundError(_REFERENCE_RESOURCE)
        async with self._uow_factory() as uow:
            summaries = await uow.skills.reference_summaries(skill_ids)
            if {item.id for item in summaries} != set(skill_ids):
                raise SkillsNotFoundError(_REFERENCE_RESOURCE)
            return summaries

    @staticmethod
    def reject_unavailable_relations(relation_ids: tuple[UUID, ...]) -> None:
        """Reject non-empty relation writes until real providers exist."""
        if relation_ids:
            raise RelationProviderUnavailableError

    async def _current_order(
        self,
        uow: SkillsUnitOfWork,
        category_id: UUID | None,
        *,
        for_update: bool = False,
    ) -> tuple[SkillCategory, ...] | tuple[Skill, ...]:
        if category_id is None:
            return await uow.categories.list_all(for_update=for_update)
        category = await uow.categories.get(category_id, for_update=for_update)
        if category is None:
            raise SkillsNotFoundError(_CATEGORY_RESOURCE)
        return await uow.skills.list_by_category(category_id, for_update=for_update)

    @staticmethod
    def _skill_fields() -> tuple[str, ...]:
        return (
            "name",
            "slug",
            "category_id",
            "description",
            "proficiency_label",
            "proficiency_score",
            "years_experience",
            "icon_key",
            "featured",
            "visible",
        )

    def _audit(
        self,
        append: Callable[[AuditEntry], None],
        fact: _AuditFact,
    ) -> None:
        append(
            AuditEntry(
                id=uuid7(),
                event_type=fact.event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=fact.actor.actor_id,
                actor_label_snapshot=None,
                resource_type="skills",
                resource_id=fact.resource_id,
                request_id=fact.request_id,
                occurred_at=self._clock(),
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata={"version": fact.version, "fields": ",".join(fact.fields)},
                schema_version=1,
            )
        )


class SkillReferenceFacade:
    """Stable consumer boundary for future experience/project modules."""

    def __init__(self, service: SkillsService) -> None:
        """Bind the facade to the skills application service."""
        self._service = service

    async def resolve(self, skill_ids: tuple[UUID, ...]) -> tuple[SkillReferenceSummary, ...]:
        """Resolve every requested opaque ID or fail the complete set."""
        return await self._service.reference_summaries(skill_ids)

    async def list_public(
        self, maximum: int, *, featured: bool | None = None
    ) -> tuple[SkillReferenceSummary, ...]:
        """Return one bounded effective public selection for page blocks."""
        page, _groups = await self._service.public_list(
            PublicSkillQuery(PageRequest(page_size=maximum), featured=featured)
        )
        return tuple(
            SkillReferenceSummary(id=item.id, name=item.name, slug=item.slug, visible=True)
            for item in page.items
        )
