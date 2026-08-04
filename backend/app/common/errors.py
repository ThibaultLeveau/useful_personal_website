"""Safe application error contracts used by the transport boundary."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import JsonValue

MAXIMUM_ERROR_MESSAGE_LENGTH = 240


@dataclass(frozen=True, slots=True)
class ErrorSpec:
    """One stable public error code, status, and default safe message."""

    status_code: HTTPStatus
    message: str


ERROR_SPECS: dict[str, ErrorSpec] = {
    "BAD_REQUEST": ErrorSpec(HTTPStatus.BAD_REQUEST, "The request could not be completed."),
    "AUTHENTICATION_REQUIRED": ErrorSpec(
        HTTPStatus.UNAUTHORIZED,
        "Authentication is required.",
    ),
    "AUTHENTICATION_FAILED": ErrorSpec(
        HTTPStatus.UNAUTHORIZED,
        "The credentials are invalid.",
    ),
    "AUTHORIZATION_DENIED": ErrorSpec(
        HTTPStatus.FORBIDDEN,
        "The requested operation is not permitted.",
    ),
    "CSRF_INVALID": ErrorSpec(HTTPStatus.FORBIDDEN, "The CSRF token is invalid."),
    "ORIGIN_INVALID": ErrorSpec(
        HTTPStatus.FORBIDDEN,
        "The request origin is not trusted.",
    ),
    "PASSWORD_CHANGE_REQUIRED": ErrorSpec(
        HTTPStatus.FORBIDDEN,
        "The initial password must be changed before continuing.",
    ),
    "NOT_FOUND": ErrorSpec(HTTPStatus.NOT_FOUND, "The requested resource was not found."),
    "METHOD_NOT_ALLOWED": ErrorSpec(
        HTTPStatus.METHOD_NOT_ALLOWED,
        "The method is not allowed.",
    ),
    "RESOURCE_VERSION_CONFLICT": ErrorSpec(
        HTTPStatus.CONFLICT,
        "The resource changed after it was read.",
    ),
    "RESOURCE_CONFLICT": ErrorSpec(
        HTTPStatus.CONFLICT,
        "The requested operation conflicts with the current resource state.",
    ),
    "IDEMPOTENCY_CONFLICT": ErrorSpec(
        HTTPStatus.CONFLICT,
        "The idempotency key was already used for a different request.",
    ),
    "IDEMPOTENCY_IN_PROGRESS": ErrorSpec(
        HTTPStatus.CONFLICT,
        "A request with this idempotency key is already in progress.",
    ),
    "REQUEST_TOO_LARGE": ErrorSpec(
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        "The request is too large.",
    ),
    "UNSUPPORTED_MEDIA_TYPE": ErrorSpec(
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        "The request media type is not supported.",
    ),
    "VALIDATION_FAILED": ErrorSpec(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "The request contains invalid fields.",
    ),
    "PASSWORD_POLICY_INVALID": ErrorSpec(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "The new password does not meet the password policy.",
    ),
    "PRECONDITION_REQUIRED": ErrorSpec(
        HTTPStatus.PRECONDITION_REQUIRED,
        "A current If-Match resource version is required.",
    ),
    "RATE_LIMITED": ErrorSpec(
        HTTPStatus.TOO_MANY_REQUESTS,
        "Too many requests. Try again later.",
    ),
    "INTERNAL_ERROR": ErrorSpec(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "An unexpected error occurred.",
    ),
    "DEPENDENCY_UNAVAILABLE": ErrorSpec(
        HTTPStatus.SERVICE_UNAVAILABLE,
        "A required dependency is unavailable.",
    ),
}


def error_spec(code: str) -> ErrorSpec:
    """Resolve one registered code or reject an undocumented public error."""
    try:
        return ERROR_SPECS[code]
    except KeyError as error:
        msg = f"unregistered API error code: {code}"
        raise ValueError(msg) from error


class ApiError(Exception):
    """An explicitly safe error that can cross the HTTP transport boundary."""

    def __init__(
        self,
        *,
        status_code: HTTPStatus,
        code: str,
        message: str,
        details: dict[str, JsonValue] | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        """Initialize an HTTP-safe application error."""
        spec = error_spec(code)
        if status_code != spec.status_code:
            msg = f"API error {code} must use status {int(spec.status_code)}"
            raise ValueError(msg)
        if not message or len(message) > MAXIMUM_ERROR_MESSAGE_LENGTH:
            msg = "API error messages must be non-empty and bounded"
            raise ValueError(msg)
        if retry_after_seconds is not None and (
            code != "RATE_LIMITED"
            or isinstance(retry_after_seconds, bool)
            or retry_after_seconds < 1
        ):
            msg = "Retry-After is allowed only as a positive RATE_LIMITED value"
            raise ValueError(msg)
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after_seconds = retry_after_seconds

    @classmethod
    def from_code(
        cls,
        code: str,
        *,
        details: dict[str, JsonValue] | None = None,
        message: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> ApiError:
        """Build an error from the stable registry with an optional reviewed message."""
        spec = error_spec(code)
        return cls(
            status_code=spec.status_code,
            code=code,
            message=message or spec.message,
            details=details,
            retry_after_seconds=retry_after_seconds,
        )
