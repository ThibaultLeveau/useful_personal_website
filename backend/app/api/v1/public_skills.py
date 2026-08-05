"""Unauthenticated visibility-enforced skills projection."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.v1.conventions import list_success, map_common_error
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope
from app.api.v1.skills_schemas import PublicSkillData
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.modules.skills.domain import PublicSkillQuery, SkillValidationError, normalize_slug
from app.modules.skills.service import SkillsService

router = APIRouter(prefix="/public", tags=["Public skills"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_QUERY_CATALOG = QueryCatalog(
    allowed_filters=frozenset({"category", "featured", "search"}),
    allowed_sorts=frozenset({"position", "name", "featured", "id"}),
    default_sort=(SortTerm("position"),),
)
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_MAXIMUM_SEARCH_LENGTH = 120
_PUBLIC_LIST_OPENAPI = {
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
            "name": "category",
            "in": "query",
            "required": False,
            "schema": {
                "type": "string",
                "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
                "maxLength": 80,
            },
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
            "description": "One allow-listed field, optionally prefixed with - for descending.",
        },
    ]
}


def _service(request: Request) -> SkillsService:
    service = getattr(request.app.state, "skills_service", None)
    if not isinstance(service, SkillsService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _parse_featured(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path="query.featured", code="boolean"),))


def _query(request: Request) -> PublicSkillQuery:
    query = parse_collection_query(
        list(request.query_params.multi_items()),
        catalog=_QUERY_CATALOG,
    )
    category = query.filters.get("category")
    if category is not None:
        try:
            normalized = normalize_slug(category, path="query.category")
        except SkillValidationError as error:
            raise QueryValidationError(
                (QueryIssue(path="query.category", code=error.code),)
            ) from error
        if normalized != category:
            raise QueryValidationError(
                (QueryIssue(path="query.category", code="normalized_slug_required"),)
            )
    search = query.filters.get("search")
    if search is not None and (
        search != search.strip() or not search or len(search) > _MAXIMUM_SEARCH_LENGTH
    ):
        raise QueryValidationError((QueryIssue(path="query.search", code="invalid_text"),))
    first_sort = query.sort[0]
    sort = f"{'-' if first_sort.descending else ''}{first_sort.field}"
    return PublicSkillQuery(
        page=query.page,
        category_slug=category,
        featured=_parse_featured(query.filters.get("featured")),
        search=search,
        sort=sort,
    )


def _set_public_cache(response: Response) -> None:
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    response.headers["Vary"] = "Accept-Encoding"


@router.get(
    "/skills",
    operation_id="public_skills_list",
    openapi_extra=_PUBLIC_LIST_OPENAPI,
    response_model=ListEnvelope[PublicSkillData],
    responses=_RESPONSES,
)
async def public_skills_list(
    request: Request,
    response: Response,
) -> ListEnvelope[PublicSkillData]:
    """Return only visible skills with public category context."""
    try:
        page, groups = await _service(request).public_list(_query(request))
    except QueryValidationError as error:
        raise map_common_error(error) from error
    categories = {skill.slug: group for group in groups for skill in group.skills}
    data = [
        PublicSkillData(
            name=skill.name,
            slug=skill.slug,
            category_name=categories[skill.slug].name,
            category_slug=categories[skill.slug].slug,
            category_description=categories[skill.slug].description,
            category_position=categories[skill.slug].position,
            description=skill.description,
            proficiency_label=skill.proficiency_label,
            proficiency_score=skill.proficiency_score,
            years_experience=skill.years_experience,
            icon_key=skill.icon_key,
            position=skill.position,
            featured=skill.featured,
        )
        for skill in page.items
    ]
    _set_public_cache(response)
    return list_success(request, data, page.metadata)
