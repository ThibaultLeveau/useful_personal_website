"""Authenticated skill/category CRUD, filtering, and ordering API."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.api.v1.skills_schemas import (
    DeleteData,
    ReorderRequest,
    SkillCategoryData,
    SkillCategoryInput,
    SkillCategoryListData,
    SkillData,
    SkillInput,
    SkillListData,
)
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
from app.modules.identity.domain import SessionView  # noqa: TC001 - FastAPI runtime annotation.
from app.modules.skills.domain import (
    AdminSkillQuery,
    CategoryInUseError,
    RelationProviderUnavailableError,
    Skill,
    SkillCategory,
    SkillCategoryValues,
    SkillsSlugConflictError,
    SkillValidationError,
    SkillValues,
)
from app.modules.skills.service import (
    CategoryCommand,
    DeleteCategoryCommand,
    DeleteSkillCommand,
    ReorderCommand,
    SkillCommand,
    SkillsIdempotencyRejectedError,
    SkillsNotFoundError,
    SkillsService,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Skills"])

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
_RETRYABLE_OPENAPI = {
    "parameters": [
        *_UNSAFE_OPENAPI["parameters"],
        {
            "name": "If-Match",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "example": '"v1"'},
        },
        {
            "name": "Idempotency-Key",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "minLength": 16, "maxLength": 128},
        },
    ]
}
_ADMIN_QUERY_CATALOG = QueryCatalog(
    allowed_filters=frozenset({"category_id", "visible", "featured", "search"}),
    allowed_sorts=frozenset({"position", "name", "created_at", "updated_at", "id"}),
    default_sort=(SortTerm("position"),),
)
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_BAD_REQUEST = "BAD_REQUEST"
_MAXIMUM_SEARCH_LENGTH = 120
_MINIMUM_IDEMPOTENCY_KEY_LENGTH = 16
_MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
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
            "name": "category_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {
            "name": "visible",
            "in": "query",
            "required": False,
            "schema": {"type": "boolean"},
        },
        {
            "name": "featured",
            "in": "query",
            "required": False,
            "schema": {"type": "boolean"},
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
            "description": (
                "Comma-separated allow-listed fields; prefix a field with - for descending."
            ),
        },
    ]
}


@dataclass(frozen=True, slots=True)
class MutationHeaders:
    """Optional concurrency plus required idempotency for retryable operations."""

    if_match: str | None
    idempotency_key: str


def mutation_headers(
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> MutationHeaders:
    """Collect safe retry/concurrency headers."""
    return MutationHeaders(if_match=if_match, idempotency_key=idempotency_key)


def _request_mutation_headers(request: Request) -> MutationHeaders:
    key = request.headers.get("idempotency-key", "")
    if not _MINIMUM_IDEMPOTENCY_KEY_LENGTH <= len(key) <= _MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
        raise ApiError.from_code(
            _BAD_REQUEST,
            details={"header": "idempotency-key"},
        )
    return MutationHeaders(if_match=request.headers.get("if-match"), idempotency_key=key)


def _service(request: Request) -> SkillsService:
    service = getattr(request.app.state, "skills_service", None)
    if not isinstance(service, SkillsService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _category_values(payload: SkillCategoryInput) -> SkillCategoryValues:
    return SkillCategoryValues(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
    )


def _skill_values(payload: SkillInput) -> SkillValues:
    SkillsService.reject_unavailable_relations(tuple(payload.associated_project_ids))
    SkillsService.reject_unavailable_relations(tuple(payload.associated_experience_ids))
    return SkillValues(
        name=payload.name,
        slug=payload.slug,
        category_id=payload.category_id,
        description=payload.description,
        proficiency_label=payload.proficiency_label,
        proficiency_score=payload.proficiency_score,
        years_experience=payload.years_experience,
        icon_key=payload.icon_key,
        featured=payload.featured,
        visible=payload.visible,
    )


def _category_data(category: SkillCategory) -> SkillCategoryData:
    return SkillCategoryData(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        position=category.position,
        created_at=category.created_at,
        updated_at=category.updated_at,
        version=category.version,
    )


def _skill_data(skill: Skill) -> SkillData:
    return SkillData(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        category_id=skill.category_id,
        description=skill.description,
        proficiency_label=skill.proficiency_label,
        proficiency_score=skill.proficiency_score,
        years_experience=skill.years_experience,
        icon_key=skill.icon_key,
        position=skill.position,
        featured=skill.featured,
        visible=skill.visible,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        version=skill.version,
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
    if isinstance(error, SkillValidationError):
        mapped = _validation(f"body.{error.path}", error.code)
    elif isinstance(error, SkillsSlugConflictError):
        mapped = _validation(f"body.{error.path}", "duplicate")
    elif isinstance(error, RelationProviderUnavailableError):
        mapped = _validation("body.associated_project_ids", "capability_unavailable")
    elif isinstance(error, SkillsNotFoundError):
        mapped = ApiError.from_code("NOT_FOUND")
    elif isinstance(error, CategoryInUseError):
        mapped = ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"reason": "category_in_use"},
        )
    elif isinstance(error, SkillsIdempotencyRejectedError):
        mapped = map_idempotency_decision(error.decision)
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


def _admin_query(request: Request) -> AdminSkillQuery:
    query = parse_collection_query(
        list(request.query_params.multi_items()),
        catalog=_ADMIN_QUERY_CATALOG,
    )
    category_id: UUID | None = None
    raw_category = query.filters.get("category_id")
    if raw_category is not None:
        try:
            category_id = UUID(raw_category)
        except ValueError as error:
            raise QueryValidationError(
                (QueryIssue(path="query.category_id", code="uuid"),)
            ) from error
    search = query.filters.get("search")
    if search is not None and (
        search != search.strip() or not search or len(search) > _MAXIMUM_SEARCH_LENGTH
    ):
        raise QueryValidationError((QueryIssue(path="query.search", code="invalid_text"),))
    first_sort = query.sort[0]
    sort = f"{'-' if first_sort.descending else ''}{first_sort.field}"
    return AdminSkillQuery(
        page=query.page,
        category_id=category_id,
        visible=_parse_bool(query.filters.get("visible"), path="query.visible"),
        featured=_parse_bool(query.filters.get("featured"), path="query.featured"),
        search=search,
        sort=sort,
    )


@router.get(
    "/skill-categories",
    operation_id="admin_skill_categories_list",
    response_model=SuccessEnvelope[SkillCategoryListData],
    responses=_RESPONSES,
)
async def categories_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[SkillCategoryListData]:
    """Return the complete deterministic category order."""
    categories = await _service(request).list_categories(_actor(session))
    set_private_no_store(response)
    if categories:
        set_resource_etag(response, version=categories[0].version)
    return success(
        request, SkillCategoryListData(items=[_category_data(item) for item in categories])
    )


@router.post(
    "/skill-categories",
    operation_id="admin_skill_category_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[SkillCategoryData],
    responses=_RESPONSES,
)
async def category_create(
    payload: SkillCategoryInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[SkillCategoryData]:
    """Create a normalized category at the end of the collection."""
    try:
        category = await _service(request).create_category(
            CategoryCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                values=_category_values(payload),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=category.version)
    return success(request, _category_data(category))


@router.get(
    "/skill-categories/{category_id}",
    operation_id="admin_skill_category_get",
    response_model=SuccessEnvelope[SkillCategoryData],
    responses=_RESPONSES,
)
async def category_get(
    category_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[SkillCategoryData]:
    """Return one administrator category."""
    try:
        category = await _service(request).get_category(_actor(session), category_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=category.version)
    return success(request, _category_data(category))


@router.put(
    "/skill-categories/{category_id}",
    operation_id="admin_skill_category_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[SkillCategoryData],
    responses=_RESPONSES,
)
async def category_update(
    category_id: UUID,
    payload: SkillCategoryInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[SkillCategoryData]:
    """Update one category with optimistic concurrency."""
    try:
        category = await _service(request).update_category(
            CategoryCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                values=_category_values(payload),
                category_id=category_id,
                if_match=request.headers.get("if-match"),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=category.version)
    return success(request, _category_data(category))


@router.delete(
    "/skill-categories/{category_id}",
    operation_id="admin_skill_category_delete",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[DeleteData],
    responses=_RESPONSES,
)
async def category_delete(
    category_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[DeleteData]:
    """Delete only an empty category."""
    try:
        await _service(request).delete_category(
            DeleteCategoryCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                category_id=category_id,
                if_match=if_match,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, DeleteData())


@router.put(
    "/skill-categories/actions/reorder",
    operation_id="admin_skill_categories_reorder",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[SkillCategoryListData],
    responses=_RESPONSES,
)
async def categories_reorder(
    payload: ReorderRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[SkillCategoryListData]:
    """Atomically replace the complete category order."""
    try:
        result = await _service(request).reorder(
            ReorderCommand(
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
    categories = [item for item in result if isinstance(item, SkillCategory)]
    set_private_no_store(response)
    set_resource_etag(response, version=categories[0].version)
    return success(
        request, SkillCategoryListData(items=[_category_data(item) for item in categories])
    )


@router.get(
    "/skills",
    operation_id="admin_skills_list",
    openapi_extra=_ADMIN_LIST_OPENAPI,
    response_model=ListEnvelope[SkillData],
    responses=_RESPONSES,
)
async def skills_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> ListEnvelope[SkillData]:
    """List exact filtered administrator skills with stable pagination."""
    try:
        page = await _service(request).list_skills(_actor(session), _admin_query(request))
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return list_success(request, [_skill_data(item) for item in page.items], page.metadata)


@router.post(
    "/skills",
    operation_id="admin_skill_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[SkillData],
    responses=_RESPONSES,
)
async def skill_create(
    payload: SkillInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[SkillData]:
    """Create a validated skill at the end of its category."""
    try:
        skill = await _service(request).create_skill(
            SkillCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                values=_skill_values(payload),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=skill.version)
    return success(request, _skill_data(skill))


@router.get(
    "/skills/{skill_id}",
    operation_id="admin_skill_get",
    response_model=SuccessEnvelope[SkillData],
    responses=_RESPONSES,
)
async def skill_get(
    skill_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[SkillData]:
    """Return one complete administrator skill."""
    try:
        skill = await _service(request).get_skill(_actor(session), skill_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=skill.version)
    return success(request, _skill_data(skill))


@router.put(
    "/skills/{skill_id}",
    operation_id="admin_skill_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[SkillData],
    responses=_RESPONSES,
)
async def skill_update(
    skill_id: UUID,
    payload: SkillInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[SkillData]:
    """Update, feature, hide, or reassign one skill."""
    try:
        skill = await _service(request).update_skill(
            SkillCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                values=_skill_values(payload),
                skill_id=skill_id,
                if_match=request.headers.get("if-match"),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=skill.version)
    return success(request, _skill_data(skill))


@router.delete(
    "/skills/{skill_id}",
    operation_id="admin_skill_delete",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[DeleteData],
    responses=_RESPONSES,
)
async def skill_delete(
    skill_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[DeleteData]:
    """Delete one skill and close its category order gap."""
    try:
        await _service(request).delete_skill(
            DeleteSkillCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                skill_id=skill_id,
                if_match=if_match,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, DeleteData())


@router.put(
    "/skill-categories/{category_id}/skills/reorder",
    operation_id="admin_category_skills_reorder",
    openapi_extra=_RETRYABLE_OPENAPI,
    response_model=SuccessEnvelope[SkillListData],
    responses=_RESPONSES,
)
async def skills_reorder(
    category_id: UUID,
    payload: ReorderRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[SkillListData]:
    """Atomically replace one category's complete skill order."""
    try:
        headers = _request_mutation_headers(request)
        result = await _service(request).reorder(
            ReorderCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                ordered_ids=tuple(payload.ordered_ids),
                category_id=category_id,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    skills = [item for item in result if isinstance(item, Skill)]
    set_private_no_store(response)
    set_resource_etag(response, version=skills[0].version)
    return success(request, SkillListData(items=[_skill_data(item) for item in skills]))
