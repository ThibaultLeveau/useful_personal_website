"""Reviewed least-privilege external integration resources."""

# ruff: noqa: D103, EM101, FAST001
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.api.v1.admin_contacts import _detail as contact_detail_data
from app.api.v1.admin_contacts import _summary as contact_summary_data
from app.api.v1.admin_projects import _data as project_data
from app.api.v1.admin_projects import _map_error as map_project_error
from app.api.v1.admin_projects import _query as project_query
from app.api.v1.contact_schemas import ContactDetailData, ContactSummaryData
from app.api.v1.conventions import list_success, set_private_no_store, set_resource_etag, success
from app.api.v1.integration_auth import require_api_token
from app.api.v1.project_schemas import ProjectData
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import PageRequest, page_metadata
from app.common.errors import ApiError
from app.modules.api_access.domain import ApiTokenScope
from app.modules.contacts.domain import ContactState
from app.modules.contacts.service import ContactNotFoundError, ContactService
from app.modules.projects.service import ProjectsService

router = APIRouter(prefix="/integrations", tags=["External integrations"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope} for status in (401, 403, 404, 422, 429, 503)
}


def _projects(request: Request) -> ProjectsService:
    value = getattr(request.app.state, "projects_service", None)
    if not isinstance(value, ProjectsService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return value


def _contacts(request: Request) -> ContactService:
    value = getattr(request.app.state, "contact_service", None)
    if not isinstance(value, ContactService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return value


@router.get("/projects", response_model=ListEnvelope[ProjectData], responses=_RESPONSES)
async def integration_projects(
    request: Request,
    response: Response,
    actor: Annotated[ActorContext, Depends(require_api_token(ApiTokenScope.CONTENT_READ))],
) -> ListEnvelope[ProjectData]:
    try:
        page = await _projects(request).list_admin(actor, project_query(request))
    except Exception as error:
        raise map_project_error(error) from error
    set_private_no_store(response)
    return list_success(request, [project_data(item) for item in page.items], page.metadata)


@router.get(
    "/projects/{project_id}", response_model=SuccessEnvelope[ProjectData], responses=_RESPONSES
)
async def integration_project(
    request: Request,
    response: Response,
    project_id: UUID,
    actor: Annotated[ActorContext, Depends(require_api_token(ApiTokenScope.CONTENT_READ))],
) -> SuccessEnvelope[ProjectData]:
    try:
        view = await _projects(request).get_admin(actor, project_id)
    except Exception as error:
        raise map_project_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=view.snapshot.project.version)
    return success(request, project_data(view))


@router.get("/contacts", response_model=ListEnvelope[ContactSummaryData], responses=_RESPONSES)
async def integration_contacts(
    request: Request,
    response: Response,
    _actor: Annotated[ActorContext, Depends(require_api_token(ApiTokenScope.CONTACTS_READ))],
    state: ContactState | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ListEnvelope[ContactSummaryData]:
    pagination = PageRequest(page=page, page_size=page_size)
    items, total = await _contacts(request).list(
        state=state,
        created_from=None,
        created_to=None,
        offset=pagination.offset,
        limit=pagination.page_size,
        oldest_first=False,
    )
    set_private_no_store(response)
    return list_success(
        request,
        [contact_summary_data(item) for item in items],
        page_metadata(pagination, total_items=total),
    )


@router.get(
    "/contacts/{contact_id}",
    response_model=SuccessEnvelope[ContactDetailData],
    responses=_RESPONSES,
)
async def integration_contact(
    request: Request,
    response: Response,
    contact_id: UUID,
    _actor: Annotated[ActorContext, Depends(require_api_token(ApiTokenScope.CONTACTS_READ))],
) -> SuccessEnvelope[ContactDetailData]:
    try:
        item = await _contacts(request).get(contact_id)
    except ContactNotFoundError as error:
        raise ApiError.from_code("NOT_FOUND") from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, contact_detail_data(item))
