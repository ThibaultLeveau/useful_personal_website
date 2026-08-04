"""Unauthenticated effective-time project list and case-study detail."""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.api.v1.conventions import list_success, map_common_error, success
from app.api.v1.project_schemas import (
    PublicExperienceReferenceData,
    PublicProjectData,
    PublicProjectReferenceData,
    PublicSkillReferenceData,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.modules.projects.domain import ProjectStatus, PublicProject, PublicProjectQuery
from app.modules.projects.service import ProjectNotFoundError, ProjectsService

router = APIRouter(prefix="/public", tags=["Public projects"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.NOT_FOUND): {"model": ErrorEnvelope},
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_CATALOG = QueryCatalog(
    allowed_filters=frozenset(
        {"status", "technology", "skill", "experience_id", "featured", "search"}
    ),
    allowed_sorts=frozenset({"default", "start_date", "id"}),
    default_sort=(SortTerm("default"),),
)
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAXIMUM_SEARCH_LENGTH = 120
_MAXIMUM_SLUG_LENGTH = 80
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_NOT_FOUND = "NOT_FOUND"
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
            "name": "status",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in ProjectStatus]},
        },
        {
            "name": "technology",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "minLength": 1, "maxLength": 120},
        },
        {
            "name": "skill",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 80},
        },
        {
            "name": "experience_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {"name": "featured", "in": "query", "required": False, "schema": {"type": "boolean"}},
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
            "schema": {"type": "string", "default": "default"},
        },
    ]
}


def _service(request: Request) -> ProjectsService:
    service = getattr(request.app.state, "projects_service", None)
    if not isinstance(service, ProjectsService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _boolean(value: str | None, *, path: str) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path=path, code="boolean"),))


def _status(value: str | None) -> ProjectStatus | None:
    if value is None:
        return None
    try:
        return ProjectStatus(value)
    except ValueError as error:
        raise QueryValidationError(
            (QueryIssue(path="query.status", code="unsupported_value"),)
        ) from error


def _uuid(value: str | None, *, path: str) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="uuid"),)) from error


def _bounded(value: str | None, *, path: str, maximum: int) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > maximum:
        raise QueryValidationError((QueryIssue(path=path, code="invalid_text"),))
    return value


def _skill_slug(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) > _MAXIMUM_SLUG_LENGTH or _SLUG_PATTERN.fullmatch(value) is None:
        raise QueryValidationError((QueryIssue(path="query.skill", code="invalid_slug"),))
    return value


def _query(request: Request) -> PublicProjectQuery:
    parsed = parse_collection_query(list(request.query_params.multi_items()), catalog=_CATALOG)
    selected_sort = parsed.sort[0]
    return PublicProjectQuery(
        page=parsed.page,
        status=_status(parsed.filters.get("status")),
        technology=_bounded(parsed.filters.get("technology"), path="query.technology", maximum=120),
        skill_slug=_skill_slug(parsed.filters.get("skill")),
        experience_id=_uuid(parsed.filters.get("experience_id"), path="query.experience_id"),
        featured=_boolean(parsed.filters.get("featured"), path="query.featured"),
        search=_bounded(
            parsed.filters.get("search"), path="query.search", maximum=_MAXIMUM_SEARCH_LENGTH
        ),
        sort=f"{'-' if selected_sort.descending else ''}{selected_sort.field}",
    )


def _data(item: PublicProject) -> PublicProjectData:
    return PublicProjectData(
        id=item.id,
        slug=item.slug,
        name=item.name,
        short_description=item.short_description,
        full_description=item.full_description,
        problem=item.problem,
        solution=item.solution,
        impact=item.impact,
        owner_role=item.owner_role,
        architecture=item.architecture,
        technologies=list(item.technologies),
        status=item.status,
        start_date=item.start_date,
        end_date=item.end_date,
        repository_url=item.repository_url,
        demo_url=item.demo_url,
        featured=item.featured,
        seo_title=item.seo_title,
        seo_description=item.seo_description,
        canonical_url=item.canonical_url,
        cover_media_id=item.cover_media_id,
        screenshot_media_ids=list(item.screenshot_media_ids),
        skills=[
            PublicSkillReferenceData(name=value.name, slug=value.slug) for value in item.skills
        ],
        experiences=[
            PublicExperienceReferenceData(
                id=value.id, company_name=value.company_name, role_title=value.role_title
            )
            for value in item.experiences
        ],
        related_projects=[
            PublicProjectReferenceData(id=value.id, slug=value.slug, name=value.name)
            for value in item.related_projects
        ],
    )


def _cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=0, must-revalidate"
    response.headers["Vary"] = "Accept-Encoding"


@router.get(
    "/projects",
    operation_id="public_projects_list",
    openapi_extra=_LIST_OPENAPI,
    response_model=ListEnvelope[PublicProjectData],
    responses=_RESPONSES,
)
async def public_projects_list(
    request: Request, response: Response
) -> ListEnvelope[PublicProjectData]:
    """Return effective project publications in stable featured order."""
    try:
        page = await _service(request).public_list(_query(request))
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return list_success(request, [_data(item) for item in page.items], page.metadata)


@router.get(
    "/projects/{slug}",
    operation_id="public_projects_detail",
    response_model=SuccessEnvelope[PublicProjectData],
    responses=_RESPONSES,
)
async def public_projects_detail(
    slug: str, request: Request, response: Response
) -> SuccessEnvelope[PublicProjectData]:
    """Return one effective case study or indistinguishable not-found."""
    try:
        item = await _service(request).public_detail(slug)
    except ProjectNotFoundError as error:
        raise ApiError.from_code(_NOT_FOUND) from error
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return success(request, _data(item))
