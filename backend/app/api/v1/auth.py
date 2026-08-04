"""Thin versioned transport for administrator authentication."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Header, Request, Response, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyCookie

from app.api.v1.auth_schemas import (
    AuthActionData,
    ChangePasswordRequest,
    LoginRequest,
    SessionData,
)
from app.api.v1.schemas import ErrorBody, ErrorEnvelope, ResponseMeta, SuccessEnvelope
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.identity.domain import SessionIssue, SessionView
from app.modules.identity.security import PasswordPolicyError
from app.modules.identity.service import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    ChangePasswordCommand,
    CsrfValidationError,
    IdentityService,
    LoginCommand,
    PasswordChangeRequiredError,
    RateLimitedError,
)

if TYPE_CHECKING:
    from typing import Any

    from app.config import Settings

SESSION_COOKIE = "__Host-admin_session"
CSRF_COOKIE = "__Host-admin_csrf"
CSRF_HEADER = "X-CSRF-Token"
PRIVATE_NO_STORE = "private, no-store"

session_cookie = APIKeyCookie(
    name=SESSION_COOKIE,
    auto_error=False,
    scheme_name="AdminSessionCookie",
    description="Opaque digest-backed administrator browser session.",
)
router = APIRouter(prefix="/auth", tags=["Authentication"])

_AUTHENTICATION_RESPONSE = {"model": ErrorEnvelope, "description": "Authentication failed."}
_FORBIDDEN_RESPONSE = {
    "model": ErrorEnvelope,
    "description": "Origin, CSRF, or policy denied.",
}
_VALIDATION_RESPONSE = {
    "model": ErrorEnvelope,
    "description": "The request is invalid or violates password policy.",
}
_RATE_RESPONSE = {
    "model": ErrorEnvelope,
    "description": "Authentication is temporarily rate limited.",
}
_UNAVAILABLE_RESPONSE = {
    "model": ErrorEnvelope,
    "description": "Authentication persistence is unavailable.",
}
_LOGIN_RESPONSES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: {"model": ErrorEnvelope, "description": "Authentication failed."},
    HTTPStatus.FORBIDDEN: _FORBIDDEN_RESPONSE,
    HTTPStatus.UNPROCESSABLE_ENTITY: _VALIDATION_RESPONSE,
    HTTPStatus.TOO_MANY_REQUESTS: _RATE_RESPONSE,
    HTTPStatus.SERVICE_UNAVAILABLE: _UNAVAILABLE_RESPONSE,
}
_SESSION_RESPONSES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: _AUTHENTICATION_RESPONSE,
    HTTPStatus.SERVICE_UNAVAILABLE: _UNAVAILABLE_RESPONSE,
}
_UNSAFE_RESPONSES: dict[int | str, dict[str, Any]] = {
    HTTPStatus.UNAUTHORIZED: _AUTHENTICATION_RESPONSE,
    HTTPStatus.FORBIDDEN: _FORBIDDEN_RESPONSE,
    HTTPStatus.UNPROCESSABLE_ENTITY: _VALIDATION_RESPONSE,
    HTTPStatus.SERVICE_UNAVAILABLE: _UNAVAILABLE_RESPONSE,
}
_ORIGIN_PARAMETER = {
    "name": "Origin",
    "in": "header",
    "required": True,
    "description": "Exact configured trusted HTTPS origin.",
    "schema": {"type": "string", "format": "uri"},
}
_LOGIN_OPENAPI = {"parameters": [_ORIGIN_PARAMETER]}
_UNSAFE_OPENAPI = {
    "parameters": [_ORIGIN_PARAMETER],
}


def _service(request: Request) -> IdentityService:
    service = getattr(request.app.state, "identity_service", None)
    if not isinstance(service, IdentityService):
        raise ApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="DEPENDENCY_UNAVAILABLE",
            message="A required dependency is unavailable.",
            details={"dependency": "database"},
        )
    return service


def _require_origin(request: Request) -> None:
    settings: Settings = request.app.state.settings
    origin = request.headers.get("Origin")
    if origin is None or origin not in settings.trusted_origins:
        raise ApiError(
            status_code=HTTPStatus.FORBIDDEN,
            code="ORIGIN_INVALID",
            message="The request origin is not trusted.",
        )


def _require_secret(secret: str | None) -> str:
    if secret is None:
        raise ApiError(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
        )
    return secret


def _client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _session_data(view: SessionView) -> SessionData:
    return SessionData(
        administrator_id=view.administrator_id,
        display_name=view.display_name,
        must_change_password=view.must_change_password,
        idle_expires_at=view.idle_expires_at,
        absolute_expires_at=view.absolute_expires_at,
    )


def _success[DataT: SessionData | AuthActionData](
    request: Request,
    data: DataT,
) -> SuccessEnvelope[DataT]:
    return SuccessEnvelope(data=data, meta=ResponseMeta(request_id=get_request_id(request)))


def _private(response: Response) -> None:
    response.headers["Cache-Control"] = PRIVATE_NO_STORE
    response.headers["Pragma"] = "no-cache"


def _set_auth_cookies(response: Response, service: IdentityService, issue: SessionIssue) -> None:
    max_age = service.cookie_max_age_seconds(issue.view)
    response.set_cookie(
        SESSION_COOKIE,
        issue.secret,
        httponly=True,
        max_age=max_age,
        path="/",
        samesite="lax",
        secure=True,
    )
    _set_csrf_cookie(response, service.csrf_token(issue.view.session_id), max_age=max_age)


def _set_csrf_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        CSRF_COOKIE,
        token,
        httponly=False,
        max_age=max_age,
        path="/",
        samesite="lax",
        secure=True,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=True, httponly=False, samesite="lax")


def _rate_limited_response(request: Request, error: RateLimitedError) -> JSONResponse:
    request_id = get_request_id(request)
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code="RATE_LIMITED",
            message="Too many authentication attempts. Try again later.",
            details={"retry_after_seconds": error.retry_after_seconds},
            request_id=request_id,
        )
    )
    return JSONResponse(
        content=envelope.model_dump(mode="json"),
        headers={
            "Cache-Control": PRIVATE_NO_STORE,
            "Pragma": "no-cache",
            "Retry-After": str(error.retry_after_seconds),
            "X-Request-ID": request_id,
        },
        status_code=HTTPStatus.TOO_MANY_REQUESTS,
    )


def _map_identity_error(error: Exception) -> ApiError:
    if isinstance(error, AuthenticationRequiredError):
        return ApiError(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
        )
    if isinstance(error, AuthenticationFailedError):
        return ApiError(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message="The credentials are invalid.",
        )
    if isinstance(error, CsrfValidationError):
        return ApiError(
            status_code=HTTPStatus.FORBIDDEN,
            code="CSRF_INVALID",
            message="The CSRF token is invalid.",
        )
    if isinstance(error, PasswordChangeRequiredError):
        return ApiError(
            status_code=HTTPStatus.FORBIDDEN,
            code="PASSWORD_CHANGE_REQUIRED",
            message="The initial password must be changed before continuing.",
        )
    if isinstance(error, PasswordPolicyError):
        return ApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="PASSWORD_POLICY_INVALID",
            message=str(error),
            details={"fields": [{"path": "body.new_password", "code": "password_policy"}]},
        )
    raise error


@router.post(
    "/login",
    operation_id="auth_login",
    openapi_extra=_LOGIN_OPENAPI,
    response_model=SuccessEnvelope[SessionData],
    responses=_LOGIN_RESPONSES,
    summary="Create an opaque administrator session",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> SuccessEnvelope[SessionData] | JSONResponse:
    """Enforce Origin/rate policy and create secure session/CSRF cookies."""
    _require_origin(request)
    service = _service(request)
    try:
        issue = await service.login(
            LoginCommand(
                email=payload.email,
                password=payload.password,
                client_ip=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
                request_id=get_request_id(request),
            )
        )
    except RateLimitedError as error:
        return _rate_limited_response(request, error)
    except AuthenticationFailedError as error:
        raise _map_identity_error(error) from error
    _private(response)
    _set_auth_cookies(response, service, issue)
    return _success(request, _session_data(issue.view))


@router.get(
    "/session",
    operation_id="auth_session_get",
    response_model=SuccessEnvelope[SessionData],
    responses=_SESSION_RESPONSES,
    summary="Inspect the current administrator session",
)
async def session_get(
    request: Request,
    response: Response,
    secret: Annotated[str | None, Security(session_cookie)],
) -> SuccessEnvelope[SessionData]:
    """Inspect without sliding expiry or other GET-side mutation."""
    service = _service(request)
    try:
        view = await service.inspect_session(_require_secret(secret))
    except AuthenticationRequiredError as error:
        raise _map_identity_error(error) from error
    _private(response)
    return _success(request, _session_data(view))


@router.post(
    "/session/refresh",
    operation_id="auth_session_refresh",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[SessionData],
    responses=_UNSAFE_RESPONSES,
    summary="Slide the current session idle expiry",
)
async def session_refresh(
    request: Request,
    response: Response,
    secret: Annotated[str | None, Security(session_cookie)],
    csrf_header: Annotated[str, Header(alias=CSRF_HEADER)],
) -> SuccessEnvelope[SessionData]:
    """Refresh explicitly so safe GET requests remain mutation-free."""
    _require_origin(request)
    service = _service(request)
    try:
        view = await service.refresh_session(
            secret=_require_secret(secret),
            csrf_cookie=request.cookies.get(CSRF_COOKIE),
            csrf_header=csrf_header,
        )
    except (AuthenticationRequiredError, CsrfValidationError) as error:
        raise _map_identity_error(error) from error
    _private(response)
    _set_auth_cookies(response, service, SessionIssue(secret=_require_secret(secret), view=view))
    return _success(request, _session_data(view))


@router.post(
    "/password/change",
    operation_id="auth_password_change",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[SessionData],
    responses=_UNSAFE_RESPONSES,
    summary="Change the administrator password and rotate the session",
)
async def password_change(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    secret: Annotated[str | None, Security(session_cookie)],
    csrf_header: Annotated[str, Header(alias=CSRF_HEADER)],
) -> SuccessEnvelope[SessionData]:
    """Allow initial-password sessions while enforcing Origin and signed CSRF."""
    _require_origin(request)
    service = _service(request)
    try:
        issue = await service.change_password(
            ChangePasswordCommand(
                secret=_require_secret(secret),
                current_password=payload.current_password,
                new_password=payload.new_password,
                csrf_cookie=request.cookies.get(CSRF_COOKIE),
                csrf_header=csrf_header,
                request_id=get_request_id(request),
                client_ip=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
        )
    except (
        AuthenticationFailedError,
        AuthenticationRequiredError,
        CsrfValidationError,
        PasswordPolicyError,
    ) as error:
        raise _map_identity_error(error) from error
    _private(response)
    _set_auth_cookies(response, service, issue)
    return _success(request, _session_data(issue.view))


@router.post(
    "/logout",
    operation_id="auth_logout",
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[AuthActionData],
    responses=_UNSAFE_RESPONSES,
    summary="Revoke the current administrator session",
)
async def logout(
    request: Request,
    response: Response,
    secret: Annotated[str | None, Security(session_cookie)],
    csrf_header: Annotated[str, Header(alias=CSRF_HEADER)],
) -> SuccessEnvelope[AuthActionData]:
    """Revoke the digest-backed server session and clear both cookies."""
    _require_origin(request)
    service = _service(request)
    try:
        await service.logout(
            secret=_require_secret(secret),
            csrf_cookie=request.cookies.get(CSRF_COOKIE),
            csrf_header=csrf_header,
            request_id=get_request_id(request),
        )
    except (AuthenticationRequiredError, CsrfValidationError) as error:
        raise _map_identity_error(error) from error
    _private(response)
    _clear_auth_cookies(response)
    return _success(request, AuthActionData(status="logged_out"))


async def require_full_admin_session(
    request: Request,
    secret: Annotated[str | None, Security(session_cookie)],
) -> SessionView:
    """Reusable deny-by-default dependency for future ordinary admin routers."""
    service = _service(request)
    try:
        view = await service.inspect_session(_require_secret(secret))
        service.require_full_access(view)
    except (AuthenticationRequiredError, PasswordChangeRequiredError) as error:
        raise _map_identity_error(error) from error
    return view


async def require_unsafe_admin_session(
    request: Request,
    secret: Annotated[str | None, Security(session_cookie)],
    csrf_header: Annotated[str, Header(alias=CSRF_HEADER)],
) -> SessionView:
    """Require full admin access plus trusted Origin and session-bound CSRF."""
    _require_origin(request)
    service = _service(request)
    try:
        view = await service.inspect_session(_require_secret(secret))
        service.require_full_access(view)
        service.validate_csrf(
            view.session_id,
            request.cookies.get(CSRF_COOKIE),
            csrf_header,
        )
    except (
        AuthenticationRequiredError,
        CsrfValidationError,
        PasswordChangeRequiredError,
    ) as error:
        raise _map_identity_error(error) from error
    return view
