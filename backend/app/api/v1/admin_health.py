"""Authenticated administrator health transport."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.v1.auth import require_full_admin_session
from app.api.v1.conventions import set_private_no_store, success
from app.api.v1.health import get_readiness_probe
from app.api.v1.schemas import AdminHealthData, ErrorEnvelope, SuccessEnvelope
from app.common.health import ReadinessCategory, ReadinessProbe, evaluate_readiness
from app.modules.identity.domain import (
    SessionView,  # noqa: TC001 - FastAPI resolves dependency annotations.
)

if TYPE_CHECKING:
    from typing import Any, Literal

    from app.config import Settings

router = APIRouter(prefix="/admin/health", tags=["Administrator health"])

_PRIVATE_NO_STORE_HEADERS: dict[str, dict[str, Any]] = {
    "Cache-Control": {
        "description": "Protected health responses are private and never stored.",
        "schema": {"type": "string", "example": "private, no-store"},
    },
    "Pragma": {
        "description": "Compatibility directive for older intermediaries.",
        "schema": {"type": "string", "example": "no-cache"},
    },
}

_RESPONSES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.OK: {"headers": _PRIVATE_NO_STORE_HEADERS},
    HTTPStatus.UNAUTHORIZED: {
        "headers": _PRIVATE_NO_STORE_HEADERS,
        "model": ErrorEnvelope,
        "description": "An active administrator session is required.",
    },
    HTTPStatus.FORBIDDEN: {
        "headers": _PRIVATE_NO_STORE_HEADERS,
        "model": ErrorEnvelope,
        "description": "The administrator must complete the required password change.",
    },
    HTTPStatus.SERVICE_UNAVAILABLE: {
        "headers": _PRIVATE_NO_STORE_HEADERS,
        "model": ErrorEnvelope,
        "description": "Authentication persistence is unavailable.",
    },
    HTTPStatus.INTERNAL_SERVER_ERROR: {
        "headers": _PRIVATE_NO_STORE_HEADERS,
        "model": ErrorEnvelope,
    },
}


@router.get(
    "",
    operation_id="admin_health_get",
    response_model=SuccessEnvelope[AdminHealthData],
    responses=_RESPONSES,
    summary="Inspect safe application and dependency health",
)
async def admin_health_get(
    request: Request,
    response: Response,
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[AdminHealthData]:
    """Return an authenticated aggregate without infrastructure internals."""
    del session
    result = await evaluate_readiness(probe)
    settings: Settings = request.app.state.settings
    if result.ready:
        status: Literal["operational", "degraded"] = "operational"
        database_status: Literal["operational", "unavailable"] = "operational"
        migration_status: Literal["current", "unavailable", "unknown"] = "current"
    elif result.category is ReadinessCategory.MIGRATION:
        status = "degraded"
        database_status = "operational"
        migration_status = "unavailable"
    else:
        status = "degraded"
        database_status = "unavailable"
        migration_status = "unknown"

    set_private_no_store(response)
    return success(
        request,
        AdminHealthData(
            status=status,
            application_status="operational",
            database_status=database_status,
            migration_status=migration_status,
            build_version=settings.build_version,
            build_commit=settings.build_commit,
            checked_at=datetime.now(UTC),
        ),
    )
