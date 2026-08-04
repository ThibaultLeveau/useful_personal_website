"""Unauthenticated database-time-effective blog list and article detail."""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.v1.blog_schemas import (
    PublicPostData,
    PublicPostReferenceData,
    PublicTaxonomyData,
    SafeRenderedContentData,
)
from app.api.v1.conventions import list_success, map_common_error, success
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.modules.blog.domain import PublicPost, PublicPostQuery
from app.modules.blog.service import BlogIntegrityError, BlogNotFoundError, BlogService

router = APIRouter(prefix="/public/blog", tags=["Public blog"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.NOT_FOUND): {"model": ErrorEnvelope},
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_CATALOG = QueryCatalog(
    allowed_filters=frozenset({"tag", "category", "search"}),
    allowed_sorts=frozenset({"newest", "oldest", "title", "id"}),
    default_sort=(SortTerm("newest"),),
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
            "name": "tag",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 80},
        },
        {
            "name": "category",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 80},
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
            "schema": {
                "type": "string",
                "enum": ["newest", "oldest", "title"],
                "default": "newest",
            },
        },
    ]
}


def _service(request: Request) -> BlogService:
    service = getattr(request.app.state, "blog_service", None)
    if not isinstance(service, BlogService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _slug(value: str | None, *, path: str) -> str | None:
    if value is None:
        return None
    if len(value) > _MAXIMUM_SLUG_LENGTH or _SLUG_PATTERN.fullmatch(value) is None:
        raise QueryValidationError((QueryIssue(path=path, code="invalid_slug"),))
    return value


def _bounded(value: str | None, *, path: str) -> str | None:
    if value is None:
        return None
    if not value or value != value.strip() or len(value) > _MAXIMUM_SEARCH_LENGTH:
        raise QueryValidationError((QueryIssue(path=path, code="invalid_text"),))
    return value


def _query(request: Request) -> PublicPostQuery:
    parsed = parse_collection_query(list(request.query_params.multi_items()), catalog=_CATALOG)
    selected_sort = parsed.sort[0]
    if selected_sort.descending:
        raise QueryValidationError((QueryIssue(path="query.sort", code="unsupported_value"),))
    return PublicPostQuery(
        page=parsed.page,
        tag_slug=_slug(parsed.filters.get("tag"), path="query.tag"),
        category_slug=_slug(parsed.filters.get("category"), path="query.category"),
        search=_bounded(parsed.filters.get("search"), path="query.search"),
        sort=selected_sort.field,
    )


def _data(item: PublicPost) -> PublicPostData:
    return PublicPostData(
        id=item.id,
        slug=item.slug,
        title=item.title,
        excerpt=item.excerpt,
        author_display=item.author_display,
        content=SafeRenderedContentData(
            html=item.rendered.html,
            policy_name=item.rendered.policy_name,
            policy_version=item.rendered.policy_version,
            source_checksum=item.rendered.source_checksum,
        ),
        reading_minutes=item.reading_minutes,
        published_at=item.published_at,
        seo_title=item.seo_title,
        seo_description=item.seo_description,
        canonical_url=item.canonical_url,
        cover_media_id=item.cover_media_id,
        tags=[
            PublicTaxonomyData(id=value.id, name=value.name, slug=value.slug) for value in item.tags
        ],
        categories=[
            PublicTaxonomyData(id=value.id, name=value.name, slug=value.slug)
            for value in item.categories
        ],
        related_posts=[
            PublicPostReferenceData(
                id=value.id,
                slug=value.slug,
                title=value.title,
                excerpt=value.excerpt,
            )
            for value in item.related_posts
        ],
    )


def _cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=0, must-revalidate"
    response.headers["Vary"] = "Accept-Encoding"


@router.get(
    "/posts",
    operation_id="public_blog_posts_list",
    openapi_extra=_LIST_OPENAPI,
    response_model=ListEnvelope[PublicPostData],
    responses=_RESPONSES,
)
async def public_blog_posts_list(
    request: Request,
    response: Response,
) -> ListEnvelope[PublicPostData]:
    """Return effective articles with exact public-only pagination."""
    try:
        page = await _service(request).public_list(_query(request))
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return list_success(request, [_data(item) for item in page.items], page.metadata)


@router.get(
    "/posts/{slug}",
    operation_id="public_blog_post_detail",
    response_model=SuccessEnvelope[PublicPostData],
    responses=_RESPONSES,
)
async def public_blog_post_detail(
    slug: str,
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicPostData]:
    """Return one effective safe-rendered article or indistinguishable not-found."""
    try:
        item = await _service(request).public_detail(slug)
    except BlogNotFoundError as error:
        raise ApiError.from_code(_NOT_FOUND) from error
    except BlogIntegrityError as error:
        raise ApiError.from_code(
            _DEPENDENCY_UNAVAILABLE, details={"dependency": "content"}
        ) from error
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return success(request, _data(item))
