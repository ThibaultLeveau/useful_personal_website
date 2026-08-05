"""Thin HTTP projections for shared API pagination, policy, and concurrency rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.api.v1.schemas import (
    ListEnvelope,
    ListResponseMeta,
    PaginationData,
    ResponseMeta,
    SuccessEnvelope,
)
from app.common.application.idempotency import IdempotencyDecisionType
from app.common.domain.concurrency import (
    InvalidPreconditionError,
    PreconditionRequiredError,
    ResourceVersionConflictError,
    format_etag,
)
from app.common.domain.query import QueryIssue, QueryValidationError
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.common.security.authorization import AuthorizationDeniedError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi import Request, Response
    from pydantic import BaseModel, JsonValue

    from app.common.application.idempotency import IdempotencyDecision
    from app.common.domain.pagination import PageMetadata


def validation_details(issues: Sequence[QueryIssue]) -> dict[str, JsonValue]:
    """Project safe common issues to the stable typed validation field list."""
    return {
        "fields": [
            {
                "path": issue.path,
                "code": issue.code,
                "message": "Value is invalid.",
            }
            for issue in issues
        ]
    }


def map_common_error(error: Exception) -> ApiError:
    """Map transport-neutral common exceptions to registered public errors."""
    if isinstance(error, AuthorizationDeniedError):
        return ApiError.from_code("AUTHORIZATION_DENIED")
    if isinstance(error, QueryValidationError):
        return ApiError.from_code(
            "VALIDATION_FAILED",
            details=validation_details(error.issues),
        )
    if isinstance(error, PreconditionRequiredError):
        return ApiError.from_code("PRECONDITION_REQUIRED")
    if isinstance(error, InvalidPreconditionError):
        return ApiError.from_code(
            "BAD_REQUEST",
            details={
                "fields": [
                    {
                        "path": "header.if-match",
                        "code": "invalid_etag",
                        "message": "Value is invalid.",
                    }
                ]
            },
        )
    if isinstance(error, ResourceVersionConflictError):
        return ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"current_version": error.current_version},
        )
    raise error


def map_idempotency_decision(decision: IdempotencyDecision) -> ApiError:
    """Map only non-success admission decisions to stable conflict codes."""
    if decision.decision is IdempotencyDecisionType.PAYLOAD_CONFLICT:
        return ApiError.from_code("IDEMPOTENCY_CONFLICT")
    if decision.decision is IdempotencyDecisionType.IN_PROGRESS:
        return ApiError.from_code("IDEMPOTENCY_IN_PROGRESS")
    msg = "successful idempotency decisions are not errors"
    raise ValueError(msg)


def success[DataT: BaseModel](request: Request, data: DataT) -> SuccessEnvelope[DataT]:
    """Create a correlated single-resource success envelope."""
    return SuccessEnvelope(data=data, meta=ResponseMeta(request_id=get_request_id(request)))


def list_success[DataT: BaseModel](
    request: Request,
    data: list[DataT],
    page: PageMetadata,
) -> ListEnvelope[DataT]:
    """Create a correlated collection envelope with exact pagination facts."""
    return ListEnvelope(
        data=data,
        meta=ListResponseMeta(
            request_id=get_request_id(request),
            pagination=PaginationData(
                page=page.page,
                page_size=page.page_size,
                total_items=page.total_items,
                total_pages=page.total_pages,
                has_previous=page.has_previous,
                has_next=page.has_next,
            ),
        ),
    )


def set_resource_etag(response: Response, *, version: int) -> None:
    """Attach the canonical strong version ETag to a resource response."""
    response.headers["ETag"] = format_etag(version)


def set_private_no_store(response: Response) -> None:
    """Prevent browser/shared caches from retaining administrator responses."""
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"


def set_no_store(response: Response) -> None:
    """Prevent operational responses from being reused as stale probe results."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
