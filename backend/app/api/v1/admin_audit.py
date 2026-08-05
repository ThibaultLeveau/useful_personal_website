"""Read-only administrator audit transport."""

# ruff: noqa: D103, EM101, PLR0913, TC001, TC003
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.v1.audit_schemas import AuditEntryData, AuditEventCatalogData
from app.api.v1.auth import require_full_admin_session
from app.api.v1.conventions import list_success, set_private_no_store, success
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import PageRequest
from app.common.errors import ApiError
from app.modules.audit.domain import (
    AUDIT_EVENT_CATALOG,
    ActorType,
    AuditEntry,
    AuditOutcome,
    AuditQuery,
    AuditValidationError,
)
from app.modules.audit.service import AuditEntryNotFoundError, AuditQueryService
from app.modules.identity.domain import SessionView

router = APIRouter(prefix="/admin/audit", tags=["Audit administration"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope} for status in (401, 403, 404, 422, 503)
}


def _service(request: Request) -> AuditQueryService:
    service = getattr(request.app.state, "audit_query_service", None)
    if not isinstance(service, AuditQueryService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _data(entry: AuditEntry) -> AuditEntryData:
    metadata = {
        key: (
            str(value).lower()
            if isinstance(value, bool)
            else "none"
            if value is None
            else str(value)
        )
        for key, value in entry.metadata.items()
    }
    return AuditEntryData(
        id=entry.id,
        event_type=entry.event_type,
        actor_type=entry.actor_type,
        actor_id=entry.actor_id,
        actor_label=entry.actor_label_snapshot,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        request_id=entry.request_id,
        occurred_at=entry.occurred_at,
        outcome=entry.outcome,
        metadata=metadata,
        schema_version=entry.schema_version,
    )


@router.get(
    "/events",
    operation_id="admin_audit_event_catalog",
    response_model=SuccessEnvelope[AuditEventCatalogData],
    responses=_RESPONSES,
)
async def event_catalog(
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[AuditEventCatalogData]:
    set_private_no_store(response)
    return success(request, AuditEventCatalogData(events=sorted(AUDIT_EVENT_CATALOG)))


@router.get(
    "",
    operation_id="admin_audit_list",
    response_model=ListEnvelope[AuditEntryData],
    responses=_RESPONSES,
)
async def list_audit_entries(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
    event_type: str | None = None,
    actor_type: ActorType | None = None,
    actor_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    outcome: AuditOutcome | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    request_id: Annotated[str | None, Query(max_length=128)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ListEnvelope[AuditEntryData]:
    allowed_parameters = {
        "event_type",
        "actor_type",
        "actor_id",
        "resource_type",
        "resource_id",
        "outcome",
        "occurred_from",
        "occurred_to",
        "request_id",
        "page",
        "page_size",
    }
    pairs = request.query_params.multi_items()
    names = [name for name, _value in pairs]
    if any(name not in allowed_parameters for name in names) or len(names) != len(set(names)):
        raise ApiError.from_code("VALIDATION_FAILED")
    try:
        query = AuditQuery(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            request_id=request_id,
        )
        result = await _service(request).list(
            _actor(session), query, PageRequest(page=page, page_size=page_size)
        )
    except AuditValidationError as error:
        raise ApiError.from_code("VALIDATION_FAILED") from error
    set_private_no_store(response)
    return list_success(request, [_data(item) for item in result.items], result.metadata)


@router.get(
    "/{entry_id}",
    operation_id="admin_audit_get",
    response_model=SuccessEnvelope[AuditEntryData],
    responses=_RESPONSES,
)
async def get_audit_entry(
    request: Request,
    response: Response,
    entry_id: UUID,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[AuditEntryData]:
    try:
        entry = await _service(request).get(_actor(session), entry_id)
    except AuditEntryNotFoundError as error:
        raise ApiError.from_code("NOT_FOUND") from error
    set_private_no_store(response)
    return success(request, _data(entry))
