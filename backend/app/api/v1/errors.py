"""Centralized safe exception-to-API-envelope mapping."""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.schemas import ErrorBody, ErrorEnvelope
from app.common.errors import ApiError, error_spec
from app.common.request_context import REQUEST_ID_HEADER, get_request_id

if TYPE_CHECKING:
    from fastapi import FastAPI, Request
    from pydantic import JsonValue

_HTTP_ERROR_CODES: dict[int, str] = {
    HTTPStatus.BAD_REQUEST: "BAD_REQUEST",
    HTTPStatus.UNAUTHORIZED: "AUTHENTICATION_REQUIRED",
    HTTPStatus.FORBIDDEN: "AUTHORIZATION_DENIED",
    HTTPStatus.NOT_FOUND: "NOT_FOUND",
    HTTPStatus.METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    HTTPStatus.CONFLICT: "RESOURCE_VERSION_CONFLICT",
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: "REQUEST_TOO_LARGE",
    HTTPStatus.UNSUPPORTED_MEDIA_TYPE: "UNSUPPORTED_MEDIA_TYPE",
    HTTPStatus.UNPROCESSABLE_ENTITY: "VALIDATION_FAILED",
    HTTPStatus.PRECONDITION_REQUIRED: "PRECONDITION_REQUIRED",
    HTTPStatus.TOO_MANY_REQUESTS: "RATE_LIMITED",
    HTTPStatus.SERVICE_UNAVAILABLE: "DEPENDENCY_UNAVAILABLE",
}
_SAFE_LOCATION_PART = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


def _error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, JsonValue] | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
            request_id=request_id,
        )
    )
    headers = {
        REQUEST_ID_HEADER: request_id,
        "Cache-Control": "private, no-store",
        "Pragma": "no-cache",
    }
    return JSONResponse(
        content=envelope.model_dump(mode="json"),
        headers=headers,
        status_code=status_code,
    )


async def handle_api_error(request: Request, exception: Exception) -> JSONResponse:
    """Map an explicitly safe application error."""
    error = cast("ApiError", exception)
    response = _error_response(
        request=request,
        status_code=error.status_code,
        code=error.code,
        message=error.message,
        details=error.details,
    )
    if error.retry_after_seconds is not None:
        response.headers["Retry-After"] = str(error.retry_after_seconds)
    return response


async def handle_validation_error(request: Request, exception: Exception) -> JSONResponse:
    """Map validation failures without reflecting untrusted values."""
    validation_error = cast("RequestValidationError", exception)
    if request.url.path.startswith("/api/v1/auth/") and any(
        error.get("type") == "missing"
        and tuple(str(part).casefold() for part in error.get("loc", ()))
        == ("header", "x-csrf-token")
        for error in validation_error.errors()
    ):
        return _error_response(
            request=request,
            status_code=HTTPStatus.FORBIDDEN,
            code="CSRF_INVALID",
            message="The CSRF token is invalid.",
        )
    fields: list[JsonValue] = []
    for error in validation_error.errors():
        location = error.get("loc", ())
        safe_location = [
            str(part)
            if isinstance(part, int)
            or (isinstance(part, str) and _SAFE_LOCATION_PART.fullmatch(part))
            else "*"
            for part in location
        ]
        path = ".".join(safe_location)
        fields.append(
            {
                "path": path,
                "code": str(error.get("type", "invalid")),
                "message": "Value is invalid.",
            }
        )
    return _error_response(
        request=request,
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="VALIDATION_FAILED",
        message="The request contains invalid fields.",
        details={"fields": fields},
    )


async def handle_http_error(request: Request, exception: Exception) -> JSONResponse:
    """Map framework HTTP errors to the stable public contract."""
    http_error = cast("StarletteHTTPException", exception)
    code = _HTTP_ERROR_CODES.get(http_error.status_code)
    if code is None:
        code = "INTERNAL_ERROR"
    spec = error_spec(code)
    return _error_response(
        request=request,
        status_code=spec.status_code,
        code=code,
        message=spec.message,
    )


async def handle_unexpected_error(request: Request, _exception: Exception) -> JSONResponse:
    """Return a correlation-safe internal error without implementation details."""
    return _error_response(
        request=request,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Install centralized handlers in most-specific-first order."""
    application.add_exception_handler(ApiError, handle_api_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(StarletteHTTPException, handle_http_error)
    application.add_exception_handler(Exception, handle_unexpected_error)
