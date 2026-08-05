"""Authenticated professional experience CRUD, preview, and publication API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.conventions import (
    list_success,
    map_common_error,
    map_idempotency_decision,
    set_private_no_store,
    set_resource_etag,
    success,
)
from app.api.v1.experience_schemas import (
    DeleteExperienceData,
    ExperienceCreateRequest,
    ExperienceData,
    ExperienceInput,
    ExperienceOrderData,
    ExperienceOrderListData,
    ExperiencePreviewData,
    ExperienceRevisionData,
    PublishExperienceRequest,
    ReorderExperiencesRequest,
    RescheduleExperienceRequest,
    VisibilityRequest,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.actors import ActorContext
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.experiences.domain import (
    AdminExperienceQuery,
    AdminExperienceView,
    EmploymentType,
    ExperienceLifecycle,
    ExperienceRevision,
    ExperienceSnapshot,
    ExperienceValidationError,
    ExperienceValues,
    FrozenRevisionError,
    PointerIntegrityError,
    RemoteStatus,
)
from app.modules.experiences.service import (
    CreateExperienceCommand,
    DeleteExperienceCommand,
    ExperienceIdempotencyRejectedError,
    ExperienceNotFoundError,
    ExperiencePublicationError,
    ExperiencesService,
    PublishExperienceCommand,
    ReorderExperiencesCommand,
    RescheduleExperienceCommand,
    SaveExperienceDraftCommand,
    SetExperienceVisibilityCommand,
    UnpublishExperienceCommand,
)
from app.modules.identity.domain import SessionView  # noqa: TC001 - FastAPI annotation.
from app.modules.skills.service import SkillsNotFoundError

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Experiences"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.BAD_REQUEST): {"model": ErrorEnvelope},
    int(HTTPStatus.UNAUTHORIZED): {"model": ErrorEnvelope},
    int(HTTPStatus.FORBIDDEN): {"model": ErrorEnvelope},
    int(HTTPStatus.NOT_FOUND): {"model": ErrorEnvelope},
    int(HTTPStatus.CONFLICT): {"model": ErrorEnvelope},
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.PRECONDITION_REQUIRED): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_UNSAFE_OPENAPI = {
    "parameters": [
        {
            "name": "Origin",
            "in": "header",
            "required": True,
            "description": "Exact configured trusted HTTPS origin.",
            "schema": {"type": "string", "format": "uri"},
        }
    ]
}
_CONCURRENT_OPENAPI = {
    "parameters": [
        *_UNSAFE_OPENAPI["parameters"],
        {
            "name": "If-Match",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "example": '"v1"'},
        },
    ]
}
_ADMIN_QUERY_CATALOG = QueryCatalog(
    allowed_filters=frozenset(
        {
            "lifecycle",
            "visible",
            "current",
            "employment_type",
            "remote_status",
            "skill_id",
            "search",
        }
    ),
    allowed_sorts=frozenset(
        {"position", "company_name", "role_title", "start_date", "updated_at", "id"}
    ),
    default_sort=(SortTerm("position"),),
)
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_MAXIMUM_SEARCH_LENGTH = 120
_ADMIN_LIST_OPENAPI = {
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "default": 1},
        },
        {
            "name": "page_size",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
        },
        {
            "name": "lifecycle",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in ExperienceLifecycle]},
        },
        {
            "name": "visible",
            "in": "query",
            "required": False,
            "schema": {"type": "boolean"},
        },
        {
            "name": "current",
            "in": "query",
            "required": False,
            "schema": {"type": "boolean"},
        },
        {
            "name": "employment_type",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in EmploymentType]},
        },
        {
            "name": "remote_status",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in RemoteStatus]},
        },
        {
            "name": "skill_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {
            "name": "search",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "minLength": 1, "maxLength": 120},
        },
        {
            "name": "sort",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "default": "position"},
            "description": "One allow-listed field, optionally prefixed with - for descending.",
        },
    ]
}


@dataclass(frozen=True, slots=True)
class MutationHeaders:
    """Required idempotency plus optional concurrency headers."""

    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceMutationHeaders:
    """Resource identifier plus retry and concurrency headers."""

    experience_id: UUID
    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceConcurrencyHeaders:
    """Resource identifier plus required optimistic-concurrency input."""

    experience_id: UUID
    if_match: str | None


def mutation_headers(
    request: Request,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ],
) -> MutationHeaders:
    """Collect safe retry and concurrency headers."""
    return MutationHeaders(
        if_match=request.headers.get("if-match"),
        idempotency_key=idempotency_key,
    )


def resource_mutation_headers(
    experience_id: UUID,
    request: Request,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ],
) -> ResourceMutationHeaders:
    """Collect one resource identifier and its retry/concurrency headers."""
    return ResourceMutationHeaders(
        experience_id,
        request.headers.get("if-match"),
        idempotency_key,
    )


def resource_concurrency_headers(
    experience_id: UUID,
    request: Request,
) -> ResourceConcurrencyHeaders:
    """Collect one resource identifier and its concurrency header."""
    return ResourceConcurrencyHeaders(experience_id, request.headers.get("if-match"))


def _service(request: Request) -> ExperiencesService:
    service = getattr(request.app.state, "experiences_service", None)
    if not isinstance(service, ExperiencesService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _values(payload: ExperienceInput | ExperienceCreateRequest) -> ExperienceValues:
    return ExperienceValues(
        company_name=payload.company_name,
        company_url=payload.company_url,
        role_title=payload.role_title,
        employment_type=payload.employment_type,
        location=payload.location,
        remote_status=payload.remote_status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        current_position=payload.current_position,
        short_summary=payload.short_summary,
        detailed_description=payload.detailed_description,
        responsibilities=tuple(payload.responsibilities),
        achievements=tuple(payload.achievements),
        technologies=tuple(payload.technologies),
        skill_ids=tuple(payload.skill_ids),
    )


def _revision_data(revision: ExperienceRevision) -> ExperienceRevisionData:
    values = revision.values
    return ExperienceRevisionData(
        id=revision.id,
        revision_number=revision.revision_number,
        based_on_revision_id=revision.based_on_revision_id,
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
        responsibilities=list(values.responsibilities),
        achievements=list(values.achievements),
        technologies=list(values.technologies),
        skill_ids=list(values.skill_ids),
        frozen=revision.frozen,
        created_by=revision.created_by,
        created_at=revision.created_at,
        updated_at=revision.updated_at,
    )


def _data(view: AdminExperienceView) -> ExperienceData:
    snapshot = view.snapshot
    aggregate = snapshot.experience
    return ExperienceData(
        id=aggregate.id,
        visible=aggregate.visible,
        position=aggregate.position,
        lifecycle=view.lifecycle,
        draft=_revision_data(snapshot.draft),
        published=(_revision_data(snapshot.published) if snapshot.published is not None else None),
        publish_at=aggregate.publish_at,
        unpublished_at=aggregate.unpublished_at,
        created_at=aggregate.created_at,
        updated_at=aggregate.updated_at,
        version=aggregate.version,
        deleted_at=aggregate.deleted_at,
    )


def _canonical(payload: BaseModel, if_match: str | None) -> bytes:
    return json.dumps(
        {"if_match": if_match, "payload": payload.model_dump(mode="json")},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _validation(path: str, code: str) -> ApiError:
    return ApiError.from_code(
        "VALIDATION_FAILED",
        details={
            "fields": [
                {"path": path, "code": code, "message": "Value is invalid."},
            ]
        },
    )


def _map_error(error: Exception) -> ApiError:
    if isinstance(error, ExperienceValidationError):
        mapped = _validation(f"body.{error.path}", error.code)
    elif isinstance(error, SkillsNotFoundError):
        mapped = _validation("body.skill_ids", "unknown_reference")
    elif isinstance(error, ExperienceNotFoundError):
        mapped = ApiError.from_code("NOT_FOUND")
    elif isinstance(error, ExperienceIdempotencyRejectedError):
        mapped = map_idempotency_decision(error.decision)
    elif isinstance(error, ExperiencePublicationError):
        mapped = ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"reason": error.code},
        )
    elif isinstance(error, FrozenRevisionError | PointerIntegrityError):
        mapped = ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"reason": "immutable_revision"},
        )
    elif isinstance(error, ValueError):
        mapped = _validation("body.publish_at", "utc_required")
    else:
        mapped = map_common_error(error)
    return mapped


def _parse_bool(value: str | None, *, path: str) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path=path, code="boolean"),))


def _parse_enum[EnumT: StrEnum](
    value: str | None,
    enum_type: type[EnumT],
    *,
    path: str,
) -> EnumT | None:
    if value is None:
        return None
    try:
        return enum_type(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="unsupported_value"),)) from error


def _parse_uuid(value: str | None, *, path: str) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="uuid"),)) from error


def _admin_query(request: Request) -> AdminExperienceQuery:
    query = parse_collection_query(
        list(request.query_params.multi_items()),
        catalog=_ADMIN_QUERY_CATALOG,
    )
    search = query.filters.get("search")
    if search is not None and (
        search != search.strip() or not search or len(search) > _MAXIMUM_SEARCH_LENGTH
    ):
        raise QueryValidationError((QueryIssue(path="query.search", code="invalid_text"),))
    first_sort = query.sort[0]
    return AdminExperienceQuery(
        page=query.page,
        lifecycle=_parse_enum(
            query.filters.get("lifecycle"),
            ExperienceLifecycle,
            path="query.lifecycle",
        ),
        visible=_parse_bool(query.filters.get("visible"), path="query.visible"),
        current=_parse_bool(query.filters.get("current"), path="query.current"),
        employment_type=_parse_enum(
            query.filters.get("employment_type"),
            EmploymentType,
            path="query.employment_type",
        ),
        remote_status=_parse_enum(
            query.filters.get("remote_status"),
            RemoteStatus,
            path="query.remote_status",
        ),
        skill_id=_parse_uuid(query.filters.get("skill_id"), path="query.skill_id"),
        search=search,
        sort=f"{'-' if first_sort.descending else ''}{first_sort.field}",
    )


async def _mutation_data(
    service: ExperiencesService,
    snapshot: ExperienceSnapshot,
) -> ExperienceData:
    return _data(await service.admin_view(snapshot))


@router.get(
    "/experiences",
    operation_id="admin_experiences_list",
    openapi_extra=_ADMIN_LIST_OPENAPI,
    response_model=ListEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experiences_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> ListEnvelope[ExperienceData]:
    """List filtered administrator experience snapshots."""
    try:
        page = await _service(request).list_admin(_actor(session), _admin_query(request))
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return list_success(request, [_data(item) for item in page.items], page.metadata)


@router.post(
    "/experiences",
    operation_id="admin_experience_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_create(
    payload: ExperienceCreateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Create one mutable revision-one draft."""
    service = _service(request)
    try:
        snapshot = await service.create(
            CreateExperienceCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
                values=_values(payload),
                visible=payload.visible,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.put(
    "/experiences/actions/reorder",
    operation_id="admin_experiences_reorder",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceOrderListData],
    responses=_RESPONSES,
)
async def experiences_reorder(
    payload: ReorderExperiencesRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ExperienceOrderListData]:
    """Replace the complete nondeleted curated order."""
    try:
        ordered = await _service(request).reorder(
            ReorderExperiencesCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                ordered_ids=tuple(payload.ordered_ids),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=ordered[0].version)
    return success(
        request,
        ExperienceOrderListData(
            items=[
                ExperienceOrderData(id=item.id, position=item.position, version=item.version)
                for item in ordered
            ]
        ),
    )


@router.get(
    "/experiences/{experience_id}",
    operation_id="admin_experience_get",
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_get(
    experience_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ExperienceData]:
    """Return one complete administrator experience snapshot."""
    try:
        view = await _service(request).get_admin(_actor(session), experience_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=view.snapshot.experience.version)
    return success(request, _data(view))


@router.put(
    "/experiences/{experience_id}",
    operation_id="admin_experience_draft_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_update(
    payload: ExperienceInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Replace only the current mutable draft."""
    service = _service(request)
    try:
        snapshot = await service.save_draft(
            SaveExperienceDraftCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=headers.experience_id,
                if_match=headers.if_match,
                values=_values(payload),
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.get(
    "/experiences/{experience_id}/preview",
    operation_id="admin_experience_preview",
    response_model=SuccessEnvelope[ExperiencePreviewData],
    responses=_RESPONSES,
)
async def experience_preview(
    experience_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ExperiencePreviewData]:
    """Return a session-only no-store draft preview."""
    try:
        view = await _service(request).preview(_actor(session), experience_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    set_resource_etag(response, version=view.snapshot.experience.version)
    return success(request, ExperiencePreviewData(experience=_data(view)))


@router.put(
    "/experiences/{experience_id}/visibility",
    operation_id="admin_experience_visibility_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_visibility_update(
    payload: VisibilityRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Set visibility independently from publication lifecycle."""
    service = _service(request)
    try:
        snapshot = await service.set_visibility(
            SetExperienceVisibilityCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=headers.experience_id,
                if_match=headers.if_match,
                visible=payload.visible,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.put(
    "/experiences/{experience_id}/actions/publish",
    operation_id="admin_experience_publish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_publish(
    payload: PublishExperienceRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(resource_mutation_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Publish now or schedule through one immutable revision transition."""
    service = _service(request)
    try:
        snapshot = await service.publish(
            PublishExperienceCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=headers.experience_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                publish_at=payload.publish_at,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.put(
    "/experiences/{experience_id}/actions/reschedule",
    operation_id="admin_experience_reschedule",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_reschedule(
    payload: RescheduleExperienceRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(resource_mutation_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Change only publication schedule metadata."""
    service = _service(request)
    try:
        snapshot = await service.reschedule(
            RescheduleExperienceCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=headers.experience_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                publish_at=payload.publish_at,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.put(
    "/experiences/{experience_id}/actions/unpublish",
    operation_id="admin_experience_unpublish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ExperienceData],
    responses=_RESPONSES,
)
async def experience_unpublish(
    experience_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ExperienceData]:
    """Remove public eligibility without deleting revision history."""
    service = _service(request)
    try:
        canonical = json.dumps(
            {"if_match": headers.if_match, "payload": {}},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        snapshot = await service.unpublish(
            UnpublishExperienceCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=experience_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=canonical,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.experience.version)
    return success(request, data)


@router.delete(
    "/experiences/{experience_id}",
    operation_id="admin_experience_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[DeleteExperienceData],
    responses=_RESPONSES,
)
async def experience_delete(
    experience_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[DeleteExperienceData]:
    """Soft-delete as a confirmed action distinct from unpublish."""
    try:
        await _service(request).delete(
            DeleteExperienceCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                experience_id=experience_id,
                if_match=request.headers.get("if-match"),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, DeleteExperienceData())
