"""Navigation/footer application service and public projection facade."""

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
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7
from app.modules.navigation.domain import (
    FooterTree,
    NavigationTree,
    public_footer,
    public_navigation,
    validate_footer,
    validate_navigation,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.modules.navigation.ports import NavigationUnitOfWorkFactory

_READ_POLICY = AccessPolicy(
    resource="site_navigation",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_UPDATE_POLICY = AccessPolicy(
    resource="site_navigation",
    action="update",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)


@dataclass(frozen=True, slots=True)
class ReplaceNavigationCommand:
    """Complete navigation replacement input."""

    actor: ActorContext
    if_match: str | None
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    tree: NavigationTree


@dataclass(frozen=True, slots=True)
class ReplaceFooterCommand:
    """Complete footer replacement input."""

    actor: ActorContext
    if_match: str | None
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    tree: FooterTree


class NavigationService:
    """Authorize and transact navigation/footer trees and public projections."""

    def __init__(
        self,
        uow_factory: NavigationUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store deterministic transaction and time seams."""
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def admin_navigation_get(self, actor: ActorContext) -> NavigationTree:
        """Return the complete navigation tree to an administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return await uow.navigation.get()

    async def replace_navigation(self, command: ReplaceNavigationCommand) -> NavigationTree:
        """Validate and atomically replace the navigation tree."""
        require_authorized(command.actor, _UPDATE_POLICY)
        validate_navigation(command.tree.items)
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=command.actor,
                    route="/api/v1/admin/navigation",
                    key=command.idempotency_key,
                    canonical_payload=command.canonical_payload,
                    requested_at=self._clock(),
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return await uow.navigation.get()
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                raise IdempotencyRejectedError(decision)
            current = await uow.navigation.get(for_update=True)
            require_matching_version(command.if_match, current_version=current.version)
            updated = await uow.navigation.replace(
                command.tree,
                expected_version=current.version,
                now=self._clock(),
            )
            uow.audit.append(
                self._audit(command.actor, command.request_id, "navigation.updated", updated)
            )
            if decision.record_id is None:
                msg = "an acquired idempotency decision has no record"
                raise RuntimeError(msg)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=200,
                    result_code="navigation.updated",
                    resource_type="navigation",
                    resource_id=updated.id,
                    resource_version=updated.version,
                ),
                completed_at=self._clock(),
            )
            await uow.commit()
            return updated

    async def admin_footer_get(self, actor: ActorContext) -> FooterTree:
        """Return the complete footer tree to an administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return await uow.footer.get()

    async def replace_footer(self, command: ReplaceFooterCommand) -> FooterTree:
        """Validate and atomically replace the footer tree."""
        require_authorized(command.actor, _UPDATE_POLICY)
        validate_footer(command.tree.columns)
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=command.actor,
                    route="/api/v1/admin/footer",
                    key=command.idempotency_key,
                    canonical_payload=command.canonical_payload,
                    requested_at=self._clock(),
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return await uow.footer.get()
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                raise IdempotencyRejectedError(decision)
            current = await uow.footer.get(for_update=True)
            require_matching_version(command.if_match, current_version=current.version)
            updated = await uow.footer.replace(
                command.tree,
                expected_version=current.version,
                now=self._clock(),
            )
            uow.audit.append(
                self._audit(command.actor, command.request_id, "footer.updated", updated)
            )
            if decision.record_id is None:
                msg = "an acquired idempotency decision has no record"
                raise RuntimeError(msg)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=200,
                    result_code="footer.updated",
                    resource_type="footer",
                    resource_id=updated.id,
                    resource_version=updated.version,
                ),
                completed_at=self._clock(),
            )
            await uow.commit()
            return updated

    async def public_navigation_get(self) -> NavigationTree:
        """Return the visibility-filtered primary navigation projection."""
        async with self._uow_factory() as uow:
            return public_navigation(await uow.navigation.get())

    async def public_footer_get(self) -> FooterTree:
        """Return the visibility-filtered footer projection."""
        async with self._uow_factory() as uow:
            return public_footer(await uow.footer.get())

    def _audit(
        self,
        actor: ActorContext,
        request_id: str,
        event_type: str,
        tree: NavigationTree | FooterTree,
    ) -> AuditEntry:
        """Create a value-free audit fact for an aggregate replacement."""
        return AuditEntry(
            id=uuid7(),
            event_type=event_type,
            actor_type=AuditActorType.ADMINISTRATOR,
            actor_id=actor.actor_id,
            actor_label_snapshot=None,
            resource_type="navigation" if isinstance(tree, NavigationTree) else "footer",
            resource_id=tree.id,
            request_id=request_id,
            occurred_at=self._clock(),
            outcome=AuditOutcome.SUCCESS,
            ip_pseudonym=None,
            metadata={"version": tree.version},
            schema_version=1,
        )


class IdempotencyRejectedError(Exception):
    """A full-tree command key conflicts or is still in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain only the safe common decision for transport mapping."""
        super().__init__("idempotency admission rejected")
        self.decision = decision
