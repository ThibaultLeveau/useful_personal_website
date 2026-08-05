"""Protected audit inspection use cases."""

# ruff: noqa: D102, D107, TC001

from __future__ import annotations

from typing import TYPE_CHECKING

from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.pagination import Page, PageRequest, page_metadata
from app.common.security.authorization import AccessPolicy, require_authorized

from .domain import AuditEntry, AuditQuery
from .ports import AuditQueryUnitOfWorkFactory

if TYPE_CHECKING:
    from uuid import UUID

_READ_POLICY = AccessPolicy(
    resource="audit",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)


class AuditEntryNotFoundError(Exception):
    """The requested audit event does not exist in the authorized view."""


class AuditQueryService:
    """Expose bounded read-only audit inspection to administrator sessions."""

    def __init__(self, uow_factory: AuditQueryUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list(
        self, actor: ActorContext, query: AuditQuery, page: PageRequest
    ) -> Page[AuditEntry]:
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            items, total = await uow.audit.list(query, page)
        return Page(items=items, metadata=page_metadata(page, total_items=total))

    async def get(self, actor: ActorContext, entry_id: UUID) -> AuditEntry:
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            entry = await uow.audit.get(entry_id)
        if entry is None:
            raise AuditEntryNotFoundError
        return entry
