"""Authenticated secure image upload and media-library API."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast
from uuid import UUID  # noqa: TC003 - FastAPI resolves route types at runtime.

from fastapi import APIRouter, Depends, File, Header, Query, Request, Response, UploadFile

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.conventions import (
    list_success,
    map_common_error,
    set_private_no_store,
    set_resource_etag,
    success,
)
from app.api.v1.media_schemas import (
    MediaAssetData,
    MediaDeleteData,
    MediaMetadataRequest,
    MediaUsageData,
    MediaUsageListData,
    MediaVariantData,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.concurrency import require_matching_version
from app.common.domain.pagination import PageRequest, page_metadata
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.identity.domain import SessionView  # noqa: TC001
from app.modules.media.domain import MediaAsset, MediaValidationError
from app.modules.media.service import (
    MediaConflictError,
    MediaIdempotencyRejectedError,
    MediaNotFoundError,
    MediaService,
    MediaUploadCommand,
    MediaUploadError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.modules.media.domain import MediaUsage, MediaVariant

router = APIRouter(prefix="/admin/media", tags=["Media"])
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_RESPONSES: dict[int | str, dict[str, Any]] = {
    int(status): {"model": ErrorEnvelope}
    for status in (
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.CONFLICT,
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        HTTPStatus.PRECONDITION_REQUIRED,
        HTTPStatus.SERVICE_UNAVAILABLE,
    )
}
_IMAGE_SUCCESS = {
    "description": "A stripped registered image rendition.",
    "content": {
        media_type: {"schema": {"type": "string", "format": "binary"}}
        for media_type in ("image/jpeg", "image/png", "image/webp")
    },
}
_IMAGE_RESPONSES: dict[int | str, dict[str, Any]] = {**_RESPONSES, 200: _IMAGE_SUCCESS}


def _service(request: Request) -> MediaService:
    service = getattr(request.app.state, "media_service", None)
    if not isinstance(service, MediaService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "media_storage"})
    return service


async def _upload_chunks(upload: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await upload.read(1024 * 1024):
        yield chunk


def _variant_data(asset_id: UUID, variant: MediaVariant) -> MediaVariantData:
    representation = "webp" if variant.format.value == "webp" else "fallback"
    return MediaVariantData(
        purpose=variant.purpose,
        format=variant.format,
        width=variant.width,
        height=variant.height,
        byte_size=variant.byte_size,
        content_type=cast(
            "Literal['image/jpeg', 'image/png', 'image/webp']",
            variant.format.content_type,
        ),
        admin_url=(
            f"/api/v1/admin/media/{asset_id}/content"
            f"?width={variant.width}&representation={representation}"
        ),
    )


def _asset_data(asset: MediaAsset) -> MediaAssetData:
    return MediaAssetData(
        id=asset.id,
        status=asset.status,
        display_name=asset.display_name,
        detected_format=asset.detected_format,
        width=asset.width,
        height=asset.height,
        byte_size=asset.byte_size,
        variants=[_variant_data(asset.id, item) for item in asset.variants],
        version=asset.version,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _usage_data(usage: MediaUsage) -> MediaUsageData:
    return MediaUsageData(
        owner_type=usage.owner_type,
        owner_id=usage.owner_id,
        role=usage.role,
        position=usage.position,
        active=usage.active,
        public=usage.public,
    )


def _map_error(error: Exception) -> ApiError:  # noqa: PLR0911
    if isinstance(error, MediaNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, MediaConflictError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, MediaIdempotencyRejectedError):
        if error.decision.value == "payload_conflict":
            return ApiError.from_code("IDEMPOTENCY_CONFLICT")
        return ApiError.from_code("IDEMPOTENCY_IN_PROGRESS")
    if isinstance(error, MediaValidationError):
        return ApiError.from_code(
            "VALIDATION_FAILED",
            details={
                "fields": [{"path": error.path, "code": error.code, "message": "Value is invalid."}]
            },
        )
    if isinstance(error, MediaUploadError):
        if error.code == "invalid_size":
            return ApiError.from_code("REQUEST_TOO_LARGE")
        if error.code in {
            "unsupported_format",
            "content_type_mismatch",
            "invalid_container",
            "decode_failed",
            "invalid_image_sequence",
        }:
            return ApiError.from_code("UNSUPPORTED_MEDIA_TYPE")
        return ApiError.from_code(
            "VALIDATION_FAILED",
            details={
                "fields": [{"path": "file", "code": error.code, "message": "Value is invalid."}]
            },
        )
    return map_common_error(error)


@router.post(
    "",
    response_model=SuccessEnvelope[MediaAssetData],
    responses=_RESPONSES,
    status_code=HTTPStatus.CREATED,
)
async def upload_media(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="JPEG, PNG, or WebP; at most 10 MiB")],
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> SuccessEnvelope[MediaAssetData]:
    """Stream one image into private quarantine and return only after ready verification."""
    try:
        asset = await _service(request).upload(
            MediaUploadCommand(
                chunks=_upload_chunks(file),
                filename=file.filename,
                declared_content_type=file.content_type,
                actor_id=session.administrator_id,
                idempotency_key=idempotency_key,
                request_id=get_request_id(request),
            )
        )
    except (
        MediaIdempotencyRejectedError,
        MediaUploadError,
        MediaValidationError,
    ) as error:
        raise _map_error(error) from error
    finally:
        await file.close()
    set_private_no_store(response)
    set_resource_etag(response, version=asset.version)
    return success(request, _asset_data(asset))


@router.get(
    "",
    response_model=ListEnvelope[MediaAssetData],
    responses=_RESPONSES,
)
async def list_media(
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
) -> ListEnvelope[MediaAssetData]:
    """List the private media library with exact pagination."""
    pagination = PageRequest(page, page_size)
    assets, total = await _service(request).list(
        offset=pagination.offset, limit=pagination.page_size, search=search
    )
    set_private_no_store(response)
    return list_success(
        request,
        [_asset_data(item) for item in assets],
        page_metadata(pagination, total_items=total),
    )


@router.get(
    "/{asset_id}",
    response_model=SuccessEnvelope[MediaAssetData],
    responses=_RESPONSES,
)
async def get_media(
    asset_id: UUID,
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[MediaAssetData]:
    """Return one authorized media-library item."""
    try:
        asset = await _service(request).get(asset_id)
    except MediaNotFoundError as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=asset.version)
    return success(request, _asset_data(asset))


@router.patch(
    "/{asset_id}",
    response_model=SuccessEnvelope[MediaAssetData],
    responses=_RESPONSES,
)
async def update_media(  # noqa: PLR0913
    asset_id: UUID,
    payload: MediaMetadataRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[MediaAssetData]:
    """Rename one logical asset under strong optimistic concurrency."""
    service = _service(request)
    try:
        current = await service.get(asset_id)
        version = require_matching_version(if_match, current_version=current.version)
        asset = await service.rename(
            asset_id,
            display_name=payload.display_name,
            expected_version=version,
            actor_id=session.administrator_id,
            request_id=get_request_id(request),
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=asset.version)
    return success(request, _asset_data(asset))


@router.delete(
    "/{asset_id}",
    response_model=SuccessEnvelope[MediaDeleteData],
    responses=_RESPONSES,
)
async def delete_media(
    asset_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> SuccessEnvelope[MediaDeleteData]:
    """Tombstone one unused asset before idempotent object removal."""
    service = _service(request)
    try:
        current = await service.get(asset_id)
        version = require_matching_version(if_match, current_version=current.version)
        await service.delete(
            asset_id,
            expected_version=version,
            actor_id=session.administrator_id,
            request_id=get_request_id(request),
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, MediaDeleteData())


@router.get(
    "/{asset_id}/usage",
    response_model=SuccessEnvelope[MediaUsageListData],
    responses=_RESPONSES,
)
async def get_media_usage(
    asset_id: UUID,
    request: Request,
    response: Response,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[MediaUsageListData]:
    """Return allow-listed active and inactive owner locations."""
    try:
        usages = await _service(request).usage(asset_id)
    except MediaNotFoundError as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, MediaUsageListData(items=[_usage_data(item) for item in usages]))


@router.get("/{asset_id}/content", responses=_IMAGE_RESPONSES, response_class=Response)
async def get_admin_media_content(
    asset_id: UUID,
    request: Request,
    _session: Annotated[SessionView, Depends(require_full_admin_session)],
    width: Annotated[int, Query(ge=1, le=6_000)] = 960,
    representation: Literal["webp", "fallback"] = "webp",
) -> Response:
    """Return one stripped rendition; raw uploaded bytes are never served."""
    try:
        variant, content = await _service(request).admin_variant(
            asset_id, width=width, accepted_webp=representation == "webp"
        )
    except MediaNotFoundError as error:
        raise _map_error(error) from error
    return Response(
        content=content,
        media_type=variant.format.content_type,
        headers={
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "Content-Length": str(len(content)),
            "X-Content-Type-Options": "nosniff",
        },
    )
