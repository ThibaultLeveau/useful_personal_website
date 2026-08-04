"""Operational health transport endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, cast

from fastapi import APIRouter, Depends, Request, Response

from app.api.v1.conventions import set_no_store
from app.api.v1.schemas import (
    ErrorEnvelope,
    LiveData,
    ReadyData,
    ResponseMeta,
    SuccessEnvelope,
)
from app.common.errors import ApiError
from app.common.health import ReadinessCategory, ReadinessProbe, evaluate_readiness
from app.common.request_context import get_request_id

if TYPE_CHECKING:
    from typing import Any

router = APIRouter(prefix="/health", tags=["health"])
_NO_STORE_HEADERS: dict[str, dict[str, Any]] = {
    "Cache-Control": {
        "description": "Operational probe responses are never reused from a cache.",
        "schema": {"type": "string", "example": "no-store"},
    },
    "Pragma": {
        "description": "Compatibility directive for older intermediaries.",
        "schema": {"type": "string", "example": "no-cache"},
    },
}


def get_readiness_probe(request: Request) -> ReadinessProbe:
    """Resolve the application-level readiness port from app state."""
    return cast("ReadinessProbe", request.app.state.readiness_probe)


@router.get(
    "/live",
    operation_id="health_live",
    response_model=SuccessEnvelope[LiveData],
    responses={
        HTTPStatus.OK: {"headers": _NO_STORE_HEADERS},
        HTTPStatus.INTERNAL_SERVER_ERROR: {
            "headers": _NO_STORE_HEADERS,
            "model": ErrorEnvelope,
        },
    },
    summary="Check process liveness",
)
async def health_live(request: Request, response: Response) -> SuccessEnvelope[LiveData]:
    """Report process responsiveness without calling dependencies."""
    set_no_store(response)
    return SuccessEnvelope(
        data=LiveData(),
        meta=ResponseMeta(request_id=get_request_id(request)),
    )


@router.get(
    "/ready",
    operation_id="health_ready",
    response_model=SuccessEnvelope[ReadyData],
    responses={
        HTTPStatus.SERVICE_UNAVAILABLE: {
            "description": "A required dependency is unavailable.",
            "headers": _NO_STORE_HEADERS,
            "model": ErrorEnvelope,
        },
        HTTPStatus.OK: {"headers": _NO_STORE_HEADERS},
        HTTPStatus.INTERNAL_SERVER_ERROR: {
            "headers": _NO_STORE_HEADERS,
            "model": ErrorEnvelope,
        },
    },
    summary="Check required dependency readiness",
)
async def health_ready(
    request: Request,
    response: Response,
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
) -> SuccessEnvelope[ReadyData]:
    """Report safe aggregate dependency readiness."""
    set_no_store(response)
    result = await evaluate_readiness(probe)
    if not result.ready:
        category = result.category or ReadinessCategory.DATABASE
        raise ApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="DEPENDENCY_UNAVAILABLE",
            message="A required dependency is unavailable.",
            details={"status": "not_ready", "dependency": category.value},
        )
    return SuccessEnvelope(
        data=ReadyData(),
        meta=ResponseMeta(request_id=get_request_id(request)),
    )
