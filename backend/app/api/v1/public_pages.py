"""Unauthenticated effective Home and custom-page projections."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.v1.conventions import list_success, map_common_error, success
from app.api.v1.page_schemas import (
    PUBLIC_BLOCK_DEFINITION_ADAPTER,
    PublicBlockDefinition,
    PublicPageBlockData,
    PublicPageData,
    PublicPageRouteData,
    ResolvedReferenceData,
    public_profile_data,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.pagination import PageRequest
from app.common.errors import ApiError
from app.modules.pages.domain import PageValidationError
from app.modules.pages.registry import BlockType
from app.modules.pages.service import PageNotFoundError, PageService, PublicPage, PublicPageBlock

router = APIRouter(prefix="/public/pages", tags=["Public pages"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(HTTPStatus.NOT_FOUND): {"model": ErrorEnvelope},
    int(HTTPStatus.UNPROCESSABLE_ENTITY): {"model": ErrorEnvelope},
    int(HTTPStatus.SERVICE_UNAVAILABLE): {"model": ErrorEnvelope},
}
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_NOT_FOUND = "NOT_FOUND"


def _service(request: Request) -> PageService:
    service = getattr(request.app.state, "page_service", None)
    if not isinstance(service, PageService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _definition(item: PublicPageBlock) -> PublicBlockDefinition:
    block = item.block
    values = block.values
    config: dict[str, object]
    if values.block_type is BlockType.RICH_TEXT:
        if item.rendered is None:
            raise PageNotFoundError
        config = {
            "content": {
                "html": item.rendered.html,
                "policy_name": item.rendered.policy_name,
                "policy_version": item.rendered.policy_version,
                "source_checksum": item.rendered.source_checksum,
            }
        }
    else:
        config = values.config
    return PUBLIC_BLOCK_DEFINITION_ADAPTER.validate_python(
        {
            "block_type": values.block_type.value,
            "schema_version": values.schema_version,
            "visible": True,
            "title": values.title,
            "subtitle": values.subtitle,
            "description": values.description,
            "theme": values.theme.value,
            "layout": values.layout.value,
            "responsive": {
                "hide_on_small": values.responsive.hide_on_small,
                "hide_on_large": values.responsive.hide_on_large,
                "density": values.responsive.density,
            },
            "config": config,
        }
    )


def _data(page: PublicPage) -> PublicPageData:
    return PublicPageData(
        id=page.id,
        route_kind=page.route_kind,
        slug=page.slug,
        title=page.title,
        description=page.description,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        canonical_path=page.canonical_path,
        canonical_url=page.canonical_url,
        published_at=page.published_at,
        blocks=[
            PublicPageBlockData(
                id=item.block.id,
                position=item.block.position,
                definition=_definition(item),
                references=[
                    ResolvedReferenceData(
                        kind=reference.kind.value,
                        target_id=reference.target_id,
                        label=reference.label,
                        href=reference.href,
                        description=reference.description,
                    )
                    for reference in item.references
                ],
                profile=public_profile_data(item.profile),
            )
            for item in page.blocks
        ],
    )


def _cache_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=0, must-revalidate"
    response.headers["Vary"] = "Accept-Encoding"


@router.get(
    "",
    operation_id="public_pages_list",
    response_model=ListEnvelope[PublicPageRouteData],
    responses=_RESPONSES,
)
async def public_pages_list(
    request: Request,
    response: Response,
    page: int = 1,
    page_size: int = 100,
) -> ListEnvelope[PublicPageRouteData]:
    """Return one bounded effective route list without page body or draft facts."""
    try:
        result = await _service(request).public_routes(PageRequest(page=page, page_size=page_size))
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return list_success(
        request,
        [
            PublicPageRouteData(
                id=item.id,
                canonical_path=item.canonical_path,
                title=item.title,
                published_at=item.published_at,
                updated_at=item.updated_at,
            )
            for item in result.items
        ],
        result.metadata,
    )


async def _projection(
    request: Request, response: Response, *, slug: str | None
) -> SuccessEnvelope[PublicPageData]:
    try:
        page = (
            await _service(request).public_home()
            if slug is None
            else await _service(request).public_custom(slug)
        )
    except (PageNotFoundError, PageValidationError) as error:
        raise ApiError.from_code(_NOT_FOUND) from error
    except Exception as error:
        raise map_common_error(error) from error
    _cache_headers(response)
    return success(request, _data(page))


@router.get(
    "/home",
    operation_id="public_page_home_get",
    response_model=SuccessEnvelope[PublicPageData],
    responses=_RESPONSES,
)
async def public_page_home_get(
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicPageData]:
    """Return only the effective singleton Home revision."""
    return await _projection(request, response, slug=None)


@router.get(
    "/{slug}",
    operation_id="public_page_custom_get",
    response_model=SuccessEnvelope[PublicPageData],
    responses=_RESPONSES,
)
async def public_page_custom_get(
    slug: str,
    request: Request,
    response: Response,
) -> SuccessEnvelope[PublicPageData]:
    """Return one effective custom page or indistinguishable not-found."""
    return await _projection(request, response, slug=slug)
