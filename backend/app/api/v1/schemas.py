"""Baseline versioned response-envelope schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves this type at runtime.
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue


class ApiModel(BaseModel):
    """Base contract rejecting undeclared response properties."""

    model_config = ConfigDict(extra="forbid")


class ResponseMeta(ApiModel):
    """Metadata shared by successful API responses."""

    request_id: str


class PaginationData(ApiModel):
    """Exact page-number traversal metadata for every collection response."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_previous: bool
    has_next: bool


class ListResponseMeta(ResponseMeta):
    """Request correlation plus exact collection pagination facts."""

    pagination: PaginationData


class SuccessEnvelope[DataT: BaseModel](ApiModel):
    """Stable single-resource success envelope."""

    data: DataT
    meta: ResponseMeta


class ListEnvelope[DataT: BaseModel](ApiModel):
    """Stable list-resource success envelope."""

    data: list[DataT]
    meta: ListResponseMeta


class ValidationIssueData(ApiModel):
    """Typed, non-reflective validation issue returned to API consumers."""

    path: str
    code: str
    message: str


class ValidationErrorDetails(ApiModel):
    """Typed validation details cataloged by ``VALIDATION_FAILED``."""

    fields: list[ValidationIssueData]


class ErrorBody(ApiModel):
    """Stable safe API error payload."""

    code: str
    message: str
    details: dict[str, JsonValue]
    request_id: str


class ErrorEnvelope(ApiModel):
    """Stable top-level API error envelope."""

    error: ErrorBody


class LiveData(ApiModel):
    """Liveness response data."""

    status: Literal["ok"] = "ok"


class ReadyData(ApiModel):
    """Readiness response data."""

    status: Literal["ready"] = "ready"


class AdminHealthData(ApiModel):
    """Authenticated, disclosure-safe deployment and dependency summary."""

    status: Literal["operational", "degraded"]
    application_status: Literal["operational"]
    database_status: Literal["operational", "unavailable"]
    migration_status: Literal["current", "unavailable", "unknown"]
    build_version: str
    build_commit: str
    checked_at: datetime
