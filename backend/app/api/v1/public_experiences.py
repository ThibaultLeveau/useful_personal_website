"""Unauthenticated effective-time professional experience projection."""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.v1.conventions import list_success, map_common_error
from app.api.v1.experience_schemas import (
    PublicExperienceData,
    PublicSkillReferenceData,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.modules.experiences.domain import (
    EmploymentType,
    PublicExperience,
    PublicExperienceQuery,
    RemoteStatus,
)
from app.modules.experiences.service import ExperiencesService

router = APIRouter(prefix="/public", tags=["Public experiences"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_QUERY_CATALOG = QueryCatalog(
    allowed_filters=frozenset({"current", "employment_type", "remote_status", "skill"}),
    allowed_sorts=frozenset({"chronology", "id"}),
    default_sort=(SortTerm("chronology"),),
)
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
_MAXIMUM_SLUG_LENGTH = 80
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
            "name": "skill",
            "in": "query",
            "required": False,
            "schema": {
                "type": "string",
                "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                "maxLength": 80,
            },
        },
        {
            "name": "sort",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "default": "chronology"},
            "description": "One allow-listed field, optionally prefixed with - for descending.",
        },
    ]
}


def _service(request: Request) -> ExperiencesService:
    service = getattr(request.app.state, "experiences_service", None)
    if not isinstance(service, ExperiencesService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path="query.current", code="boolean"),))


def _parse_employment(value: str | None) -> EmploymentType | None:
    if value is None:
        return None
    try:
        return EmploymentType(value)
    except ValueError as error:
        raise QueryValidationError(
            (QueryIssue(path="query.employment_type", code="unsupported_value"),)
        ) from error


def _parse_remote(value: str | None) -> RemoteStatus | None:
    if value is None:
        return None
    try:
        return RemoteStatus(value)
    except ValueError as error:
        raise QueryValidationError(
            (QueryIssue(path="query.remote_status", code="unsupported_value"),)
        ) from error


def _parse_skill(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) > _MAXIMUM_SLUG_LENGTH or re.fullmatch(_SLUG_PATTERN, value) is None:
        raise QueryValidationError((QueryIssue(path="query.skill", code="invalid_slug"),))
    return value


def _query(request: Request) -> PublicExperienceQuery:
    query = parse_collection_query(
        list(request.query_params.multi_items()),
        catalog=_QUERY_CATALOG,
    )
    first_sort = query.sort[0]
    return PublicExperienceQuery(
        page=query.page,
        current=_parse_bool(query.filters.get("current")),
        employment_type=_parse_employment(query.filters.get("employment_type")),
        remote_status=_parse_remote(query.filters.get("remote_status")),
        skill_slug=_parse_skill(query.filters.get("skill")),
        sort=f"{'-' if first_sort.descending else ''}{first_sort.field}",
    )


def _data(item: PublicExperience) -> PublicExperienceData:
    return PublicExperienceData(
        id=item.id,
        company_name=item.company_name,
        company_url=item.company_url,
        role_title=item.role_title,
        employment_type=item.employment_type,
        location=item.location,
        remote_status=item.remote_status,
        start_date=item.start_date,
        end_date=item.end_date,
        current_position=item.current_position,
        short_summary=item.short_summary,
        detailed_description=item.detailed_description,
        responsibilities=list(item.responsibilities),
        achievements=list(item.achievements),
        technologies=list(item.technologies),
        skills=[
            PublicSkillReferenceData(name=skill.name, slug=skill.slug) for skill in item.skills
        ],
    )


@router.get(
    "/experiences",
    operation_id="public_experiences_list",
    openapi_extra=_PUBLIC_LIST_OPENAPI,
    response_model=ListEnvelope[PublicExperienceData],
    responses=_RESPONSES,
)
async def public_experiences_list(
    request: Request,
    response: Response,
) -> ListEnvelope[PublicExperienceData]:
    """Return only visible, effective, frozen publications in timeline order."""
    try:
        page = await _service(request).public_list(_query(request))
    except Exception as error:
        raise map_common_error(error) from error
    # A zero shared-cache TTL cannot outlive the next scheduled database instant.
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=0, must-revalidate"
    response.headers["Vary"] = "Accept-Encoding"
    return list_success(request, [_data(item) for item in page.items], page.metadata)
