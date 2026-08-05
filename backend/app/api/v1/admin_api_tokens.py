"""Administrator-session-only API token lifecycle routes."""

# ruff: noqa: D103, EM101, FAST001, PLR0913, PLR0917
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from app.api.v1.api_token_schemas import (
    ApiTokenCreateRequest,
    ApiTokenData,
    ApiTokenRotateRequest,
    ApiTokenScopeCatalogData,
    ApiTokenSecretData,
)
from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.conventions import list_success, set_private_no_store, set_resource_etag, success
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.concurrency import parse_etag
from app.common.domain.pagination import PageRequest, page_metadata
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.api_access.domain import ApiTokenMetadata, ApiTokenScope, ApiTokenValidationError
from app.modules.api_access.service import (
    ApiTokenConflictError,
    ApiTokenNotFoundError,
    ApiTokenService,
)
from app.modules.identity.domain import SessionView

router = APIRouter(prefix="/admin/api-tokens", tags=["API token administration"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope} for status in (400, 401, 403, 404, 409, 422, 428, 503)
}


def _service(request: Request) -> ApiTokenService:
    value = getattr(request.app.state, "api_token_service", None)
    if not isinstance(value, ApiTokenService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return value


def _data(item: ApiTokenMetadata, now: datetime) -> ApiTokenData:
    return ApiTokenData(
        id=item.id,
        public_id=item.public_id,
        name=item.name,
        display_suffix=item.display_suffix,
        scopes=sorted(item.scopes, key=lambda x: x.value),
        status=item.status_at(now).value,
        created_at=item.created_at,
        expires_at=item.expires_at,
        last_used_at=item.last_used_at,
        revoked_at=item.revoked_at,
        revocation_reason=item.revocation_reason,
        rotated_from_id=item.rotated_from_id,
        version=item.version,
    )


def _map(error: Exception) -> ApiError:
    if isinstance(error, ApiTokenNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, ApiTokenConflictError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, ApiTokenValidationError):
        return ApiError.from_code(
            "VALIDATION_FAILED",
            details={
                "fields": [{"path": error.path, "code": error.code, "message": "Value is invalid."}]
            },
        )
    return ApiError.from_code("INTERNAL_ERROR")


@router.get(
    "/scopes", response_model=SuccessEnvelope[ApiTokenScopeCatalogData], responses=_RESPONSES
)
async def scope_catalog(
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ApiTokenScopeCatalogData]:
    set_private_no_store(response)
    return success(request, ApiTokenScopeCatalogData(scopes=list(ApiTokenScope)))


@router.post(
    "", status_code=201, response_model=SuccessEnvelope[ApiTokenSecretData], responses=_RESPONSES
)
async def create_token(
    request: Request,
    response: Response,
    body: ApiTokenCreateRequest,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[ApiTokenSecretData]:
    try:
        created = await _service(request).create(
            owner_id=session.administrator_id,
            name=body.name,
            scopes=frozenset(body.scopes),
            expires_at=body.expires_at,
            confirm_no_expiry=body.confirm_no_expiry,
            request_id=get_request_id(request),
        )
    except (ApiTokenValidationError, ApiTokenConflictError) as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=created.metadata.version)
    return success(
        request,
        ApiTokenSecretData(
            token=_data(created.metadata, created.metadata.created_at),
            plaintext_token=created.plaintext,
        ),
    )


@router.get("", response_model=ListEnvelope[ApiTokenData], responses=_RESPONSES)
async def list_tokens(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
    status: Literal["active", "expired", "revoked"] | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ListEnvelope[ApiTokenData]:
    pagination = PageRequest(page=page, page_size=page_size)
    items, total, now = await _service(request).list(
        owner_id=session.administrator_id,
        offset=pagination.offset,
        limit=pagination.page_size,
        status=status,
    )
    set_private_no_store(response)
    return list_success(
        request, [_data(item, now) for item in items], page_metadata(pagination, total_items=total)
    )


@router.get("/{token_id}", response_model=SuccessEnvelope[ApiTokenData], responses=_RESPONSES)
async def get_token(
    request: Request,
    response: Response,
    token_id: UUID,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[ApiTokenData]:
    try:
        item, now = await _service(request).get(token_id)
    except ApiTokenNotFoundError as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _data(item, now))


def _version(if_match: str | None) -> int:
    if if_match is None:
        raise ApiError.from_code("PRECONDITION_REQUIRED")
    return parse_etag(if_match)


@router.post(
    "/{token_id}/rotate",
    status_code=201,
    response_model=SuccessEnvelope[ApiTokenSecretData],
    responses=_RESPONSES,
)
async def rotate_token(
    request: Request,
    response: Response,
    token_id: UUID,
    body: ApiTokenRotateRequest,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[ApiTokenSecretData]:
    try:
        created = await _service(request).rotate(
            token_id,
            owner_id=session.administrator_id,
            expected_version=_version(if_match),
            expires_at=body.expires_at,
            confirm_no_expiry=body.confirm_no_expiry,
            request_id=get_request_id(request),
        )
    except (ApiTokenNotFoundError, ApiTokenConflictError, ApiTokenValidationError) as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=created.metadata.version)
    return success(
        request,
        ApiTokenSecretData(
            token=_data(created.metadata, created.metadata.created_at),
            plaintext_token=created.plaintext,
        ),
    )


@router.post(
    "/{token_id}/revoke", response_model=SuccessEnvelope[ApiTokenData], responses=_RESPONSES
)
async def revoke_token(
    request: Request,
    response: Response,
    token_id: UUID,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[ApiTokenData]:
    try:
        item = await _service(request).revoke(
            token_id,
            owner_id=session.administrator_id,
            expected_version=_version(if_match),
            request_id=get_request_id(request),
        )
    except (ApiTokenNotFoundError, ApiTokenConflictError) as error:
        raise _map(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _data(item, item.revoked_at or item.created_at))
