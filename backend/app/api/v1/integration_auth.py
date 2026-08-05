"""Bearer authentication restricted to reviewed integration routes."""

# ruff: noqa: D103, EM101
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.domain.actors import ActorContext
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.api_access.domain import ApiTokenScope
from app.modules.api_access.service import (
    ApiTokenAuthenticationError,
    ApiTokenRateLimitedError,
    ApiTokenService,
)

_bearer = HTTPBearer(
    auto_error=False, scheme_name="ApiTokenBearer", description="Scoped opaque integration token"
)


def _service(request: Request) -> ApiTokenService:
    value = getattr(request.app.state, "api_token_service", None)
    if not isinstance(value, ApiTokenService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return value


def require_api_token(*scopes: ApiTokenScope) -> Callable[..., object]:
    required = frozenset(scopes)

    async def dependency(
        request: Request,
        response: Response,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    ) -> ActorContext:
        if credentials is None or credentials.scheme.casefold() != "bearer":
            raise ApiError.from_code("AUTHENTICATION_FAILED")
        try:
            return await _service(request).authenticate(
                credentials.credentials,
                required_scopes=required,
                request_id=get_request_id(request),
            )
        except ApiTokenRateLimitedError as error:
            response.headers["Retry-After"] = str(error.retry_after)
            raise ApiError.from_code("RATE_LIMITED") from error
        except ApiTokenAuthenticationError as error:
            raise ApiError.from_code("AUTHENTICATION_FAILED") from error

    return dependency
