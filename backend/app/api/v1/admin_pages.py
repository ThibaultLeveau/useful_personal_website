"""Authenticated configurable-page builder, preview, export, and lifecycle API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID  # noqa: TC003 - FastAPI resolves route types at runtime.

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.conventions import (
    list_success,
    map_common_error,
    map_idempotency_decision,
    set_private_no_store,
    set_resource_etag,
    success,
)
from app.api.v1.page_schemas import (
    BLOCK_DEFINITION_ADAPTER,
    AddBlockRequest,
    BlockData,
    BlockDefinition,
    BlockReorderRequest,
    BlockVisibilityRequest,
    PageCreateRequest,
    PageData,
    PageDeleteData,
    PageDuplicateRequest,
    PageExportData,
    PagePreviewData,
    PageRevisionData,
    PageUpdateRequest,
    PreviewBlockData,
    PublicationIssueData,
    PublishPageRequest,
    RegistryData,
    RegistryEntryData,
    ReschedulePageRequest,
    ResolvedReferenceData,
    UpdateBlockRequest,
    public_profile_data,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import PageRequest
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.identity.domain import SessionView  # noqa: TC001
from app.modules.media.domain import MediaStateError
from app.modules.pages.domain import (
    AdminPageView,
    FrozenPageRevisionError,
    PageBlock,
    PageBlockValues,
    PagePersistenceError,
    PageRevision,
    PageRevisionValues,
    PageSnapshot,
    PageValidationError,
    ResponsiveValues,
)
from app.modules.pages.registry import REGISTRY_MANIFEST, RegistryError
from app.modules.pages.service import (
    AddBlockCommand,
    BlockActionCommand,
    CreatePageCommand,
    DuplicateBlockCommand,
    DuplicatePageCommand,
    PageIdempotencyRejectedError,
    PageMutationCommand,
    PageNotFoundError,
    PagePublicationError,
    PageReferenceError,
    PageRouteConflictError,
    PageService,
    PublishPageCommand,
    ReorderBlocksCommand,
    ReschedulePageCommand,
    ResolvedReference,
    SavePageCommand,
    UnpublishPageCommand,
    UpdateBlockCommand,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin/pages", tags=["Page administration"])
_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorEnvelope}
    for status in (
        int(HTTPStatus.BAD_REQUEST),
        int(HTTPStatus.UNAUTHORIZED),
        int(HTTPStatus.FORBIDDEN),
        int(HTTPStatus.NOT_FOUND),
        int(HTTPStatus.CONFLICT),
        int(HTTPStatus.UNPROCESSABLE_ENTITY),
        int(HTTPStatus.PRECONDITION_REQUIRED),
        int(HTTPStatus.SERVICE_UNAVAILABLE),
    )
}
_ORIGIN = {
    "name": "Origin",
    "in": "header",
    "required": True,
    "schema": {"type": "string", "format": "uri"},
}
_IF_MATCH = {
    "name": "If-Match",
    "in": "header",
    "required": True,
    "schema": {"type": "string", "example": '"v1"'},
}
_UNSAFE_OPENAPI = {"parameters": [_ORIGIN]}
_CONCURRENT_OPENAPI = {"parameters": [_ORIGIN, _IF_MATCH]}
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class MutationHeaders:
    """Retry and optimistic-concurrency headers."""

    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceMutationHeaders:
    """Resource identity plus retry/concurrency headers."""

    page_id: UUID
    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceConcurrencyHeaders:
    """Resource identity plus required optimistic-concurrency input."""

    page_id: UUID
    if_match: str | None


def mutation_headers(
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> MutationHeaders:
    """Collect create retry and optional concurrency headers."""
    return MutationHeaders(request.headers.get("if-match"), idempotency_key)


def page_mutation_headers(
    page_id: UUID,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> ResourceMutationHeaders:
    """Collect page retry and concurrency headers."""
    return ResourceMutationHeaders(page_id, request.headers.get("if-match"), idempotency_key)


def page_concurrency_headers(page_id: UUID, request: Request) -> ResourceConcurrencyHeaders:
    """Collect page concurrency headers."""
    return ResourceConcurrencyHeaders(page_id, request.headers.get("if-match"))


def _service(request: Request) -> PageService:
    service = getattr(request.app.state, "page_service", None)
    if not isinstance(service, PageService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _page_values(payload: PageCreateRequest | PageUpdateRequest) -> PageRevisionValues:
    return PageRevisionValues(
        title=payload.title,
        description=payload.description,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        canonical_url=payload.canonical_url,
    )


def _block_values(definition: BlockDefinition) -> PageBlockValues:
    return PageBlockValues(
        block_type=definition.block_type,
        schema_version=definition.schema_version,
        visible=definition.visible,
        title=definition.title,
        subtitle=definition.subtitle,
        description=definition.description,
        theme=definition.theme,
        layout=definition.layout,
        responsive=ResponsiveValues(
            hide_on_small=definition.responsive.hide_on_small,
            hide_on_large=definition.responsive.hide_on_large,
            density=definition.responsive.density,
        ),
        config=definition.config.model_dump(mode="json", exclude_none=True),
    )


def _definition(block: PageBlock) -> BlockDefinition:
    values = block.values
    return BLOCK_DEFINITION_ADAPTER.validate_python(
        {
            "block_type": values.block_type.value,
            "schema_version": values.schema_version,
            "visible": values.visible,
            "title": values.title,
            "subtitle": values.subtitle,
            "description": values.description,
            "theme": values.theme.value,
            "layout": values.layout.value,
            "responsive": {
                "hide_on_small": values.responsive.hide_on_small,
                "hide_on_large": values.responsive.hide_on_large,
                "density": values.responsive.density,
            },
            "config": values.config,
        }
    )


def _block_data(block: PageBlock) -> BlockData:
    return BlockData(id=block.id, position=block.position, definition=_definition(block))


def _revision_data(revision: PageRevision) -> PageRevisionData:
    values = revision.values
    return PageRevisionData(
        id=revision.id,
        revision_number=revision.revision_number,
        based_on_revision_id=revision.based_on_revision_id,
        title=values.title,
        description=values.description,
        seo_title=values.seo_title,
        seo_description=values.seo_description,
        canonical_url=values.canonical_url,
        blocks=[_block_data(block) for block in revision.blocks],
        frozen=revision.frozen,
        created_at=revision.created_at,
        updated_at=revision.updated_at,
    )


def _data(view: AdminPageView) -> PageData:
    snapshot, page = view.snapshot, view.snapshot.page
    return PageData(
        id=page.id,
        route_kind=page.route_kind,
        slug=page.slug,
        visible=page.visible,
        navigation_visible=page.navigation_visible,
        position=page.position,
        lifecycle=view.lifecycle,
        draft=_revision_data(snapshot.draft),
        published=_revision_data(snapshot.published) if snapshot.published else None,
        publish_at=page.publish_at,
        unpublished_at=page.unpublished_at,
        created_at=page.created_at,
        updated_at=page.updated_at,
        version=page.version,
        deleted_at=page.deleted_at,
    )


def _reference_data(reference: ResolvedReference) -> ResolvedReferenceData:
    return ResolvedReferenceData(
        kind=reference.kind.value,
        target_id=reference.target_id,
        label=reference.label,
        href=reference.href,
        description=reference.description,
    )


def _canonical(payload: BaseModel | None, if_match: str | None) -> bytes:
    return json.dumps(
        {
            "if_match": if_match,
            "payload": payload.model_dump(mode="json") if payload is not None else {},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _validation(path: str, code: str) -> ApiError:
    return ApiError.from_code(
        "VALIDATION_FAILED",
        details={"fields": [{"path": path, "code": code, "message": "Value is invalid."}]},
    )


def _map_error(error: Exception) -> ApiError:  # noqa: PLR0911 - closed error catalog.
    try:
        return map_common_error(error)
    except Exception as common_error:
        if common_error is not error:
            raise
    if isinstance(error, (PageValidationError, RegistryError, PageReferenceError)):
        return _validation(error.path, error.code)
    if isinstance(error, PageRouteConflictError):
        return ApiError.from_code("RESOURCE_CONFLICT", details={"field": "slug"})
    if isinstance(error, MediaStateError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, PageNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, PagePublicationError):
        return ApiError.from_code(
            "RESOURCE_CONFLICT",
            details={
                "reason": error.code,
                "issues": [
                    {"block_id": str(item.block_id), "path": item.path, "code": item.code}
                    for item in error.issues
                ],
            },
        )
    if isinstance(error, PageIdempotencyRejectedError):
        return map_idempotency_decision(error.decision)
    if isinstance(error, (FrozenPageRevisionError, PagePersistenceError)):
        return ApiError.from_code("RESOURCE_CONFLICT")
    raise error


async def _mutation_data(
    service: PageService, actor: ActorContext, snapshot: PageSnapshot
) -> PageData:
    return _data(await service.admin_get(actor, snapshot.page.id))


@router.get(
    "/registry",
    operation_id="admin_pages_registry_get",
    response_model=SuccessEnvelope[RegistryData],
    responses=_RESPONSES,
)
async def registry_get(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[RegistryData]:
    """Return the exact frozen block palette manifest."""
    del session
    set_private_no_store(response)
    return success(
        request,
        RegistryData(
            entries=[RegistryEntryData.model_validate(item) for item in REGISTRY_MANIFEST]
        ),
    )


@router.get(
    "",
    operation_id="admin_pages_list",
    response_model=ListEnvelope[PageData],
    responses=_RESPONSES,
)
async def pages_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
    page: int = 1,
    page_size: int = 20,
) -> ListEnvelope[PageData]:
    """Return one bounded administrator page collection."""
    try:
        request_page = PageRequest(page=page, page_size=page_size)
        result = await _service(request).admin_list(_actor(session), request_page)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return list_success(request, [_data(view) for view in result.items], result.metadata)


@router.post(
    "",
    operation_id="admin_page_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_create(
    payload: PageCreateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Create one stable Home/custom page and empty draft."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.create(
            CreatePageCommand(
                actor=actor,
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
                route_kind=payload.route_kind,
                slug=payload.slug,
                values=_page_values(payload),
                visible=payload.visible,
                navigation_visible=payload.navigation_visible,
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.get(
    "/{page_id}",
    operation_id="admin_page_get",
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_get(
    page_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[PageData]:
    """Return one complete administrator page aggregate."""
    try:
        view = await _service(request).admin_get(_actor(session), page_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=view.snapshot.page.version)
    return success(request, _data(view))


@router.put(
    "/{page_id}",
    operation_id="admin_page_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_update(
    payload: PageUpdateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(page_concurrency_headers)],
) -> SuccessEnvelope[PageData]:
    """Replace mutable route metadata without changing live content."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.save(
            SavePageCommand(
                actor=actor,
                request_id=get_request_id(request),
                page_id=headers.page_id,
                if_match=headers.if_match,
                route_kind=payload.route_kind,
                slug=payload.slug,
                values=_page_values(payload),
                visible=payload.visible,
                navigation_visible=payload.navigation_visible,
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.post(
    "/{page_id}/duplicate",
    operation_id="admin_page_duplicate",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_duplicate(
    payload: PageDuplicateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Deep-copy one custom draft to a new stable route."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.duplicate(
            DuplicatePageCommand(
                actor=actor,
                request_id=get_request_id(request),
                source_page_id=headers.page_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                slug=payload.slug,
                title=payload.title,
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.post(
    "/{page_id}/blocks",
    operation_id="admin_page_block_add",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def block_add(
    payload: AddBlockRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Insert one strict current-version draft block."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.add_block(
            AddBlockCommand(
                actor=actor,
                request_id=get_request_id(request),
                page_id=headers.page_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                values=_block_values(payload.block),
                position=payload.position,
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.put(
    "/{page_id}/blocks/{block_id}",
    operation_id="admin_page_block_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def block_update(  # noqa: PLR0913, PLR0917 - FastAPI dependency shape.
    page_id: UUID,
    block_id: UUID,
    payload: UpdateBlockRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[PageData]:
    """Replace one draft block and regenerate its references."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.update_block(
            UpdateBlockCommand(
                actor=actor,
                request_id=get_request_id(request),
                page_id=page_id,
                block_id=block_id,
                if_match=request.headers.get("if-match"),
                values=_block_values(payload.block),
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


async def _block_action(  # noqa: PLR0913 - shared route projection inputs.
    *,
    action: str,
    page_id: UUID,
    block_id: UUID,
    request: Request,
    response: Response,
    session: SessionView,
    visible: bool | None = None,
) -> SuccessEnvelope[PageData]:
    actor, service = _actor(session), _service(request)
    command = BlockActionCommand(
        actor=actor,
        request_id=get_request_id(request),
        page_id=page_id,
        block_id=block_id,
        if_match=request.headers.get("if-match"),
    )
    try:
        if action == "visibility" and visible is not None:
            snapshot = await service.set_block_visibility(command, visible=visible)
        else:
            snapshot = await service.delete_block(command)
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.post(
    "/{page_id}/blocks/{block_id}/duplicate",
    operation_id="admin_page_block_duplicate",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def block_duplicate(  # noqa: PLR0913, PLR0917 - FastAPI dependency shape.
    page_id: UUID,
    block_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Deep-copy one draft block next to its source."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.duplicate_block(
            DuplicateBlockCommand(
                actor=actor,
                request_id=get_request_id(request),
                page_id=page_id,
                block_id=block_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(None, headers.if_match),
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.put(
    "/{page_id}/blocks/{block_id}/visibility",
    operation_id="admin_page_block_visibility_set",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def block_visibility(  # noqa: PLR0913, PLR0917 - FastAPI dependency shape.
    page_id: UUID,
    block_id: UUID,
    payload: BlockVisibilityRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[PageData]:
    """Hide or show one draft block."""
    return await _block_action(
        action="visibility",
        page_id=page_id,
        block_id=block_id,
        request=request,
        response=response,
        session=session,
        visible=payload.visible,
    )


@router.delete(
    "/{page_id}/blocks/{block_id}",
    operation_id="admin_page_block_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def block_delete(
    page_id: UUID,
    block_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[PageData]:
    """Delete one mutable block and reindex the draft."""
    return await _block_action(
        action="delete",
        page_id=page_id,
        block_id=block_id,
        request=request,
        response=response,
        session=session,
    )


@router.put(
    "/{page_id}/blocks/actions/reorder",
    operation_id="admin_page_blocks_reorder",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def blocks_reorder(
    payload: BlockReorderRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Replace the complete draft block order."""
    actor, service = _actor(session), _service(request)
    try:
        snapshot = await service.reorder_blocks(
            ReorderBlocksCommand(
                actor=actor,
                request_id=get_request_id(request),
                page_id=headers.page_id,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                ordered_ids=tuple(payload.ordered_ids),
            )
        )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.get(
    "/{page_id}/preview",
    operation_id="admin_page_preview",
    response_model=SuccessEnvelope[PagePreviewData],
    responses=_RESPONSES,
)
async def page_preview(
    page_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[PagePreviewData]:
    """Resolve the current draft through the canonical private renderer path."""
    actor, service = _actor(session), _service(request)
    try:
        preview = await service.preview(actor, page_id)
        page_data = _data(await service.admin_get(actor, page_id))
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return success(
        request,
        PagePreviewData(
            banner="Draft preview - not public",
            noindex=True,
            page=page_data,
            blocks=[
                PreviewBlockData(
                    id=item.block.id,
                    position=item.block.position,
                    definition=_definition(item.block),
                    references=[_reference_data(reference) for reference in item.references],
                    profile=public_profile_data(item.profile),
                )
                for item in preview.blocks
            ],
            issues=[
                PublicationIssueData(block_id=item.block_id, path=item.path, code=item.code)
                for item in preview.issues
            ],
        ),
    )


@router.get(
    "/{page_id}/export",
    operation_id="admin_page_export",
    response_model=SuccessEnvelope[PageExportData],
    responses=_RESPONSES,
)
async def page_export(
    page_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[PageExportData]:
    """Return a canonical validated non-persisting portability manifest."""
    try:
        exported = await _service(request).export(_actor(session), page_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return success(
        request,
        PageExportData(
            page_id=exported.page_id,
            manifest=exported.manifest,
            checksum=exported.checksum,
            filename=exported.filename,
        ),
    )


async def _lifecycle_action(  # noqa: PLR0913 - shared route projection inputs.
    *,
    action: str,
    payload: PublishPageRequest | ReschedulePageRequest | None,
    headers: ResourceMutationHeaders,
    request: Request,
    response: Response,
    session: SessionView,
) -> SuccessEnvelope[PageData]:
    actor, service = _actor(session), _service(request)
    try:
        if action == "publish":
            publish_payload = payload if isinstance(payload, PublishPageRequest) else None
            snapshot = await service.publish(
                PublishPageCommand(
                    actor=actor,
                    request_id=get_request_id(request),
                    page_id=headers.page_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=_canonical(payload, headers.if_match),
                    publish_at=publish_payload.publish_at if publish_payload else None,
                )
            )
        elif action == "reschedule" and isinstance(payload, ReschedulePageRequest):
            snapshot = await service.reschedule(
                ReschedulePageCommand(
                    actor=actor,
                    request_id=get_request_id(request),
                    page_id=headers.page_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=_canonical(payload, headers.if_match),
                    publish_at=payload.publish_at,
                )
            )
        else:
            snapshot = await service.unpublish(
                UnpublishPageCommand(
                    actor=actor,
                    request_id=get_request_id(request),
                    page_id=headers.page_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=_canonical(None, headers.if_match),
                )
            )
        data = await _mutation_data(service, actor, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.page.version)
    return success(request, data)


@router.put(
    "/{page_id}/publish",
    operation_id="admin_page_publish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_publish(
    payload: PublishPageRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Publish now or schedule using PostgreSQL time eligibility."""
    return await _lifecycle_action(
        action="publish",
        payload=payload,
        headers=headers,
        request=request,
        response=response,
        session=session,
    )


@router.put(
    "/{page_id}/reschedule",
    operation_id="admin_page_reschedule",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_reschedule(
    payload: ReschedulePageRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Replace only the absolute UTC publication instant."""
    return await _lifecycle_action(
        action="reschedule",
        payload=payload,
        headers=headers,
        request=request,
        response=response,
        session=session,
    )


@router.put(
    "/{page_id}/unpublish",
    operation_id="admin_page_unpublish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageData],
    responses=_RESPONSES,
)
async def page_unpublish(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(page_mutation_headers)],
) -> SuccessEnvelope[PageData]:
    """Immediately remove public eligibility while retaining revisions."""
    return await _lifecycle_action(
        action="unpublish",
        payload=None,
        headers=headers,
        request=request,
        response=response,
        session=session,
    )


@router.delete(
    "/{page_id}",
    operation_id="admin_page_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PageDeleteData],
    responses=_RESPONSES,
)
async def page_delete(
    page_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
) -> SuccessEnvelope[PageDeleteData]:
    """Soft-delete one custom page after explicit confirmation in the client."""
    try:
        await _service(request).delete(
            PageMutationCommand(
                _actor(session), get_request_id(request), page_id, request.headers.get("if-match")
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, PageDeleteData())
