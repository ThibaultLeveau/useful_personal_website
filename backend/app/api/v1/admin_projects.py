"""Authenticated project CRUD, preview, and publication API."""

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
from app.api.v1.project_schemas import (
    DeleteProjectData,
    FeaturedRequest,
    ProjectCreateRequest,
    ProjectData,
    ProjectInput,
    ProjectOrderData,
    ProjectOrderListData,
    ProjectPreviewData,
    ProjectRevisionData,
    PublishProjectRequest,
    ReorderProjectsRequest,
    RescheduleProjectRequest,
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
from app.modules.experiences.service import ExperienceNotFoundError
from app.modules.identity.domain import SessionView  # noqa: TC001
from app.modules.media.domain import MediaStateError
from app.modules.projects.domain import (
    AdminProjectQuery,
    AdminProjectView,
    FrozenProjectRevisionError,
    ProjectLifecycle,
    ProjectPointerIntegrityError,
    ProjectRevision,
    ProjectSnapshot,
    ProjectStatus,
    ProjectValidationError,
    ProjectValues,
)
from app.modules.projects.service import (
    CreateProjectCommand,
    DeleteProjectCommand,
    ProjectIdempotencyRejectedError,
    ProjectNotFoundError,
    ProjectPublicationError,
    ProjectRelationError,
    ProjectSlugConflictError,
    ProjectsService,
    PublishProjectCommand,
    ReorderProjectsCommand,
    RescheduleProjectCommand,
    SaveProjectDraftCommand,
    SetProjectFeaturedCommand,
    SetProjectVisibilityCommand,
    UnpublishProjectCommand,
)
from app.modules.skills.service import SkillsNotFoundError

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Projects"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope}
    for status in (
        int(HTTPStatus.BAD_REQUEST),
        int(HTTPStatus.UNAUTHORIZED),
        int(HTTPStatus.FORBIDDEN),
        int(HTTPStatus.NOT_FOUND),
        int(HTTPStatus.CONFLICT),
        int(HTTPStatus.UNPROCESSABLE_ENTITY),
        int(HTTPStatus.PRECONDITION_REQUIRED),
        int(HTTPStatus.SERVICE_UNAVAILABLE),
    )
}
_UNSAFE_OPENAPI = {
    "parameters": [
        {
            "name": "Origin",
            "in": "header",
            "required": True,
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
_CATALOG = QueryCatalog(
    allowed_filters=frozenset(
        {
            "lifecycle",
            "visible",
            "featured",
            "status",
            "skill_id",
            "experience_id",
            "search",
        }
    ),
    allowed_sorts=frozenset({"position", "name", "status", "start_date", "updated_at", "id"}),
    default_sort=(SortTerm("position"),),
)
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_MAXIMUM_SEARCH_LENGTH = 120
_LIST_OPENAPI = {
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
            "schema": {"type": "string", "enum": [item.value for item in ProjectLifecycle]},
        },
        {"name": "visible", "in": "query", "required": False, "schema": {"type": "boolean"}},
        {"name": "featured", "in": "query", "required": False, "schema": {"type": "boolean"}},
        {
            "name": "status",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in ProjectStatus]},
        },
        {
            "name": "skill_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {
            "name": "experience_id",
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
        },
    ]
}


@dataclass(frozen=True, slots=True)
class MutationHeaders:
    """Idempotency plus optional concurrency headers."""

    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceMutationHeaders:
    """Resource ID plus retry and concurrency headers."""

    project_id: UUID
    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceConcurrencyHeaders:
    """Resource ID plus required optimistic concurrency input."""

    project_id: UUID
    if_match: str | None


def mutation_headers(
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> MutationHeaders:
    """Collect retry and concurrency headers."""
    return MutationHeaders(request.headers.get("if-match"), idempotency_key)


def resource_mutation_headers(
    project_id: UUID,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> ResourceMutationHeaders:
    """Collect resource, retry, and concurrency headers."""
    return ResourceMutationHeaders(project_id, request.headers.get("if-match"), idempotency_key)


def resource_concurrency_headers(project_id: UUID, request: Request) -> ResourceConcurrencyHeaders:
    """Collect resource and concurrency headers."""
    return ResourceConcurrencyHeaders(project_id, request.headers.get("if-match"))


def _service(request: Request) -> ProjectsService:
    service = getattr(request.app.state, "projects_service", None)
    if not isinstance(service, ProjectsService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _values(payload: ProjectInput | ProjectCreateRequest) -> ProjectValues:
    return ProjectValues(
        name=payload.name,
        short_description=payload.short_description,
        full_description=payload.full_description,
        problem=payload.problem,
        solution=payload.solution,
        impact=payload.impact,
        owner_role=payload.owner_role,
        architecture=payload.architecture,
        technologies=tuple(payload.technologies),
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        repository_url=payload.repository_url,
        demo_url=payload.demo_url,
        skill_ids=tuple(payload.skill_ids),
        experience_ids=tuple(payload.experience_ids),
        related_project_ids=tuple(payload.related_project_ids),
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        canonical_url=payload.canonical_url,
        cover_media_id=payload.cover_media_id,
        screenshot_media_ids=tuple(payload.screenshot_media_ids),
    )


def _revision_data(revision: ProjectRevision) -> ProjectRevisionData:
    values = revision.values
    return ProjectRevisionData(
        id=revision.id,
        revision_number=revision.revision_number,
        based_on_revision_id=revision.based_on_revision_id,
        frozen=revision.frozen,
        created_by=revision.created_by,
        created_at=revision.created_at,
        updated_at=revision.updated_at,
        **ProjectInput(
            name=values.name,
            short_description=values.short_description,
            full_description=values.full_description,
            problem=values.problem,
            solution=values.solution,
            impact=values.impact,
            owner_role=values.owner_role,
            architecture=values.architecture,
            technologies=list(values.technologies),
            status=values.status,
            start_date=values.start_date,
            end_date=values.end_date,
            repository_url=values.repository_url,
            demo_url=values.demo_url,
            skill_ids=list(values.skill_ids),
            experience_ids=list(values.experience_ids),
            related_project_ids=list(values.related_project_ids),
            seo_title=values.seo_title,
            seo_description=values.seo_description,
            canonical_url=values.canonical_url,
            cover_media_id=values.cover_media_id,
            screenshot_media_ids=list(values.screenshot_media_ids),
        ).model_dump(),
    )


def _data(view: AdminProjectView) -> ProjectData:
    snapshot = view.snapshot
    aggregate = snapshot.project
    return ProjectData(
        id=aggregate.id,
        slug=aggregate.slug,
        visible=aggregate.visible,
        featured=aggregate.featured,
        position=aggregate.position,
        lifecycle=view.lifecycle,
        draft=_revision_data(snapshot.draft),
        published=_revision_data(snapshot.published) if snapshot.published else None,
        publish_at=aggregate.publish_at,
        unpublished_at=aggregate.unpublished_at,
        created_at=aggregate.created_at,
        updated_at=aggregate.updated_at,
        version=aggregate.version,
        deleted_at=aggregate.deleted_at,
    )


def _canonical(payload: BaseModel | None, if_match: str | None) -> bytes:
    return json.dumps(
        {
            "if_match": if_match,
            "payload": payload.model_dump(mode="json") if payload is not None else {},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _validation(path: str, code: str) -> ApiError:
    return ApiError.from_code(
        "VALIDATION_FAILED",
        details={"fields": [{"path": path, "code": code, "message": "Value is invalid."}]},
    )


def _map_error(error: Exception) -> ApiError:  # noqa: C901, PLR0911
    if isinstance(error, MediaStateError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, ProjectValidationError):
        return _validation(f"body.{error.path}", error.code)
    if isinstance(error, SkillsNotFoundError):
        return _validation("body.skill_ids", "unknown_reference")
    if isinstance(error, ExperienceNotFoundError):
        return _validation("body.experience_ids", "unknown_reference")
    if isinstance(error, ProjectRelationError):
        return _validation("body.related_project_ids", error.code)
    if isinstance(error, ProjectSlugConflictError):
        return _validation("body.slug", "duplicate_slug")
    if isinstance(error, ProjectNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, ProjectIdempotencyRejectedError):
        return map_idempotency_decision(error.decision)
    if isinstance(error, ProjectPublicationError):
        return ApiError.from_code("RESOURCE_VERSION_CONFLICT", details={"reason": error.code})
    if isinstance(error, FrozenProjectRevisionError | ProjectPointerIntegrityError):
        return ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT", details={"reason": "immutable_revision"}
        )
    if isinstance(error, ValueError):
        return _validation("body.publish_at", "utc_required")
    return map_common_error(error)


def _boolean(value: str | None, *, path: str) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path=path, code="boolean"),))


def _enum[EnumT: StrEnum](value: str | None, enum_type: type[EnumT], *, path: str) -> EnumT | None:
    if value is None:
        return None
    try:
        return enum_type(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="unsupported_value"),)) from error


def _uuid(value: str | None, *, path: str) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="uuid"),)) from error


def _query(request: Request) -> AdminProjectQuery:
    parsed = parse_collection_query(list(request.query_params.multi_items()), catalog=_CATALOG)
    search = parsed.filters.get("search")
    if search is not None and (
        not search or search != search.strip() or len(search) > _MAXIMUM_SEARCH_LENGTH
    ):
        raise QueryValidationError((QueryIssue(path="query.search", code="invalid_text"),))
    selected_sort = parsed.sort[0]
    return AdminProjectQuery(
        page=parsed.page,
        lifecycle=_enum(parsed.filters.get("lifecycle"), ProjectLifecycle, path="query.lifecycle"),
        visible=_boolean(parsed.filters.get("visible"), path="query.visible"),
        featured=_boolean(parsed.filters.get("featured"), path="query.featured"),
        status=_enum(parsed.filters.get("status"), ProjectStatus, path="query.status"),
        skill_id=_uuid(parsed.filters.get("skill_id"), path="query.skill_id"),
        experience_id=_uuid(parsed.filters.get("experience_id"), path="query.experience_id"),
        search=search,
        sort=f"{'-' if selected_sort.descending else ''}{selected_sort.field}",
    )


async def _mutation_data(service: ProjectsService, snapshot: ProjectSnapshot) -> ProjectData:
    return _data(await service.admin_view(snapshot))


@router.get(
    "/projects",
    operation_id="admin_projects_list",
    openapi_extra=_LIST_OPENAPI,
    response_model=ListEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def projects_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> ListEnvelope[ProjectData]:
    """List filtered administrator project snapshots."""
    try:
        page = await _service(request).list_admin(_actor(session), _query(request))
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return list_success(request, [_data(item) for item in page.items], page.metadata)


@router.post(
    "/projects",
    operation_id="admin_project_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_create(
    payload: ProjectCreateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Create one stable route and revision-one draft."""
    service = _service(request)
    try:
        snapshot = await service.create(
            CreateProjectCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
                slug=payload.slug,
                values=_values(payload),
                visible=payload.visible,
                featured=payload.featured,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.project.version)
    return success(request, data)


@router.put(
    "/projects/actions/reorder",
    operation_id="admin_projects_reorder",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectOrderListData],
    responses=_RESPONSES,
)
async def projects_reorder(
    payload: ReorderProjectsRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ProjectOrderListData]:
    """Replace complete nondeleted curated order."""
    try:
        ordered = await _service(request).reorder(
            ReorderProjectsCommand(
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
        ProjectOrderListData(
            items=[
                ProjectOrderData(id=item.id, position=item.position, version=item.version)
                for item in ordered
            ]
        ),
    )


@router.get(
    "/projects/{project_id}",
    operation_id="admin_project_get",
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_get(
    project_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ProjectData]:
    """Return one complete administrator project."""
    try:
        view = await _service(request).get_admin(_actor(session), project_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=view.snapshot.project.version)
    return success(request, _data(view))


@router.put(
    "/projects/{project_id}",
    operation_id="admin_project_draft_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_update(
    payload: ProjectInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Replace only current mutable draft values."""
    service = _service(request)
    try:
        snapshot = await service.save_draft(
            SaveProjectDraftCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                project_id=headers.project_id,
                if_match=headers.if_match,
                values=_values(payload),
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.project.version)
    return success(request, data)


@router.get(
    "/projects/{project_id}/preview",
    operation_id="admin_project_preview",
    response_model=SuccessEnvelope[ProjectPreviewData],
    responses=_RESPONSES,
)
async def project_preview(
    project_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ProjectPreviewData]:
    """Return a session-only no-store project draft preview."""
    try:
        view = await _service(request).preview(_actor(session), project_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    set_resource_etag(response, version=view.snapshot.project.version)
    return success(request, ProjectPreviewData(project=_data(view)))


async def _flag(
    payload: VisibilityRequest | FeaturedRequest,
    request: Request,
    response: Response,
    session: SessionView,
    headers: ResourceConcurrencyHeaders,
) -> SuccessEnvelope[ProjectData]:
    service = _service(request)
    try:
        if isinstance(payload, VisibilityRequest):
            snapshot = await service.set_visibility(
                SetProjectVisibilityCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    project_id=headers.project_id,
                    if_match=headers.if_match,
                    visible=payload.visible,
                )
            )
        else:
            snapshot = await service.set_featured(
                SetProjectFeaturedCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    project_id=headers.project_id,
                    if_match=headers.if_match,
                    featured=payload.featured,
                )
            )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.project.version)
    return success(request, data)


@router.put(
    "/projects/{project_id}/visibility",
    operation_id="admin_project_visibility_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_visibility_update(
    payload: VisibilityRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Set visibility independently from publication."""
    return await _flag(payload, request, response, session, headers)


@router.put(
    "/projects/{project_id}/featured",
    operation_id="admin_project_featured_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_featured_update(
    payload: FeaturedRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Set featured independently from public eligibility."""
    return await _flag(payload, request, response, session, headers)


async def _lifecycle(  # noqa: PLR0913
    payload: PublishProjectRequest | RescheduleProjectRequest | None,
    request: Request,
    response: Response,
    session: SessionView,
    headers: ResourceMutationHeaders,
    *,
    action: str,
) -> SuccessEnvelope[ProjectData]:
    service = _service(request)
    canonical = _canonical(payload, headers.if_match)
    try:
        if action == "publish":
            snapshot = await service.publish(
                PublishProjectCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    project_id=headers.project_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                    publish_at=payload.publish_at
                    if isinstance(payload, PublishProjectRequest)
                    else None,
                )
            )
        elif action == "reschedule" and isinstance(payload, RescheduleProjectRequest):
            snapshot = await service.reschedule(
                RescheduleProjectCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    project_id=headers.project_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                    publish_at=payload.publish_at,
                )
            )
        else:
            snapshot = await service.unpublish(
                UnpublishProjectCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    project_id=headers.project_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                )
            )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.project.version)
    return success(request, data)


@router.put(
    "/projects/{project_id}/actions/publish",
    operation_id="admin_project_publish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_publish(
    payload: PublishProjectRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(resource_mutation_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Publish now or schedule one immutable revision."""
    return await _lifecycle(payload, request, response, session, headers, action="publish")


@router.put(
    "/projects/{project_id}/actions/reschedule",
    operation_id="admin_project_reschedule",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_reschedule(
    payload: RescheduleProjectRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(resource_mutation_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Change only project publication schedule metadata."""
    return await _lifecycle(payload, request, response, session, headers, action="reschedule")


@router.put(
    "/projects/{project_id}/actions/unpublish",
    operation_id="admin_project_unpublish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[ProjectData],
    responses=_RESPONSES,
)
async def project_unpublish(
    project_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[ProjectData]:
    """Remove public eligibility without deleting revision history."""
    return await _lifecycle(
        None,
        request,
        response,
        session,
        ResourceMutationHeaders(project_id, headers.if_match, headers.idempotency_key),
        action="unpublish",
    )


@router.delete(
    "/projects/{project_id}",
    operation_id="admin_project_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[DeleteProjectData],
    responses=_RESPONSES,
)
async def project_delete(
    project_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(resource_concurrency_headers)],
) -> SuccessEnvelope[DeleteProjectData]:
    """Soft-delete a project after optimistic-concurrency validation."""
    try:
        await _service(request).delete(
            DeleteProjectCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                project_id=project_id,
                if_match=headers.if_match,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, DeleteProjectData())
