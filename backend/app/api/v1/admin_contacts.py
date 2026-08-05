"""Authenticated private contact inbox and lifecycle API."""
# ruff: noqa: D103, EM101, FAST001, PLR0913, PLR0917

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.contact_schemas import (
    ContactAcceptedData,
    ContactDetailData,
    ContactSummaryData,
    ContactTransitionRequest,
)
from app.api.v1.conventions import list_success, set_private_no_store, set_resource_etag, success
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.concurrency import parse_etag
from app.common.domain.pagination import PageRequest, page_metadata
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.contacts.domain import ContactState, ContactSubmission, ContactValidationError
from app.modules.contacts.service import ContactConflictError, ContactNotFoundError, ContactService
from app.modules.identity.domain import SessionView

router = APIRouter(prefix="/admin/contacts", tags=["Contact administration"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope} for status in (401, 403, 404, 409, 422, 428, 503)
}


def _service(request: Request) -> ContactService:
    value = getattr(request.app.state, "contact_service", None)
    if not isinstance(value, ContactService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return value


def _summary(c: ContactSubmission) -> ContactSummaryData:
    return ContactSummaryData(
        id=c.id,
        name=c.name,
        email=c.email,
        subject=c.subject,
        state=c.state.value,
        created_at=c.created_at,
        version=c.version,
    )


def _detail(c: ContactSubmission) -> ContactDetailData:
    return ContactDetailData(
        **_summary(c).model_dump(),
        message=c.message,
        consented_at=c.consented_at,
        policy_version=c.policy_version,
        source=c.source,
        read_at=c.read_at,
        archived_at=c.archived_at,
        updated_at=c.updated_at,
    )


def _map(error: Exception) -> ApiError:
    if isinstance(error, ContactNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, ContactConflictError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, ContactValidationError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    return ApiError.from_code("INTERNAL_ERROR")


@router.get("", response_model=ListEnvelope[ContactSummaryData], responses=_RESPONSES)
async def list_contacts(
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
    state: ContactState | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ListEnvelope[ContactSummaryData]:
    pagination = PageRequest(page=page, page_size=page_size)
    items, total = await _service(request).list(
        state=state,
        created_from=created_from,
        created_to=created_to,
        offset=pagination.offset,
        limit=pagination.page_size,
        oldest_first=sort == "oldest",
    )
    set_private_no_store(response)
    return list_success(
        request, [_summary(i) for i in items], page_metadata(pagination, total_items=total)
    )


@router.get(
    "/{contact_id}", response_model=SuccessEnvelope[ContactDetailData], responses=_RESPONSES
)
async def get_contact(
    request: Request,
    response: Response,
    contact_id: UUID,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ContactDetailData]:
    try:
        item = await _service(request).get(contact_id)
    except ContactNotFoundError as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _detail(item))


@router.patch(
    "/{contact_id}/state", response_model=SuccessEnvelope[ContactDetailData], responses=_RESPONSES
)
async def transition_contact(
    request: Request,
    response: Response,
    contact_id: UUID,
    body: ContactTransitionRequest,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[ContactDetailData]:
    if if_match is None:
        raise ApiError.from_code("PRECONDITION_REQUIRED")
    version = parse_etag(if_match)
    try:
        item = await _service(request).transition(
            contact_id,
            ContactState(body.state),
            expected_version=version,
            actor_id=session.administrator_id,
            request_id=get_request_id(request),
        )
    except (ContactNotFoundError, ContactConflictError, ContactValidationError) as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _detail(item))


@router.delete(
    "/{contact_id}", response_model=SuccessEnvelope[ContactAcceptedData], responses=_RESPONSES
)
async def delete_contact(
    request: Request,
    response: Response,
    contact_id: UUID,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[ContactAcceptedData]:
    try:
        await _service(request).delete(
            contact_id,
            expected_version=(parse_etag(if_match) if if_match is not None else _missing_etag()),
            actor_id=session.administrator_id,
            request_id=get_request_id(request),
        )
    except (ContactNotFoundError, ContactConflictError) as error:
        raise _map(error) from error
    set_private_no_store(response)
    return success(request, ContactAcceptedData())


def _missing_etag() -> int:
    raise ApiError.from_code("PRECONDITION_REQUIRED")
