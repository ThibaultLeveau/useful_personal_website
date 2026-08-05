"""Public same-origin delivery of authorized stripped media variants."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID  # noqa: TC003 - FastAPI resolves route types at runtime.

from fastapi import APIRouter, Path, Query, Request, Response

from app.api.v1.schemas import ErrorEnvelope
from app.common.errors import ApiError
from app.modules.media.service import MediaNotFoundError, MediaService

router = APIRouter(prefix="/media", tags=["Media"])
_NOT_FOUND = "NOT_FOUND"
_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "A public-effective stripped image rendition.",
        "content": {
            media_type: {"schema": {"type": "string", "format": "binary"}}
            for media_type in ("image/jpeg", "image/png", "image/webp")
        },
    },
    404: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
}


def _service(request: Request) -> MediaService:
    service = getattr(request.app.state, "media_service", None)
    if not isinstance(service, MediaService):
        raise ApiError.from_code(_NOT_FOUND)
    return service


@router.get("/{asset_id}/{width}", response_class=Response, responses=_RESPONSES)
async def get_public_media(
    asset_id: UUID,
    width: Annotated[int, Path(ge=1, le=6_000)],
    request: Request,
    representation: Annotated[str, Query(pattern="^(webp|fallback)$")] = "webp",
) -> Response:
    """Deliver only a public-effective registered rendition with not-found parity."""
    try:
        variant, content = await _service(request).public_variant(
            asset_id,
            width=width,
            accepted_webp=representation == "webp",
        )
    except (MediaNotFoundError, ValueError) as error:
        raise ApiError.from_code(_NOT_FOUND) from error
    return Response(
        content=content,
        media_type=variant.format.content_type,
        headers={
            "Cache-Control": "public, max-age=300, s-maxage=300",
            "Content-Length": str(len(content)),
            "X-Content-Type-Options": "nosniff",
        },
    )
