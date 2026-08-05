"""Authenticated blog post, taxonomy, preview, export, and publication API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from app.api.v1.auth import require_full_admin_session, require_unsafe_admin_session
from app.api.v1.blog_schemas import (
    BlogDeleteData,
    BlogOrderData,
    BlogOrderListData,
    BlogReorderRequest,
    BlogVisibilityRequest,
    PostCreateRequest,
    PostData,
    PostInput,
    PostPreviewData,
    PostRevisionData,
    PostSourceExportData,
    PublishPostRequest,
    ReschedulePostRequest,
    SafeRenderedContentData,
    TaxonomyCreateRequest,
    TaxonomyData,
    TaxonomyListData,
    TaxonomyUpdateRequest,
)
from app.api.v1.conventions import (
    list_success,
    map_common_error,
    map_idempotency_decision,
    set_private_no_store,
    set_resource_etag,
    success,
)
from app.api.v1.schemas import ErrorEnvelope, ListEnvelope, SuccessEnvelope
from app.common.domain.actors import ActorContext
from app.common.domain.query import (
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.blog.domain import (
    AdminPostQuery,
    AdminPostView,
    BlogValidationError,
    FrozenPostRevisionError,
    PostLifecycle,
    PostPointerIntegrityError,
    PostRevision,
    PostSnapshot,
    PostValues,
    Taxonomy,
    TaxonomyKind,
)
from app.modules.blog.service import (
    BlogIdempotencyRejectedError,
    BlogIntegrityError,
    BlogNotFoundError,
    BlogPublicationError,
    BlogRelationError,
    BlogService,
    BlogSlugConflictError,
    BlogTaxonomyUsageError,
    CreatePostCommand,
    CreateTaxonomyCommand,
    DeletePostCommand,
    DeleteTaxonomyCommand,
    PublishPostCommand,
    ReorderPostsCommand,
    ReorderTaxonomiesCommand,
    ReschedulePostCommand,
    SavePostDraftCommand,
    SetPostVisibilityCommand,
    UnpublishPostCommand,
    UpdateTaxonomyCommand,
)
from app.modules.identity.domain import SessionView  # noqa: TC001
from app.modules.media.domain import MediaStateError

if TYPE_CHECKING:
    from pydantic import BaseModel

router = APIRouter(prefix="/admin/blog", tags=["Blog administration"])
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
_UNSAFE_OPENAPI = {
    "parameters": [
        {
            "name": "Origin",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "format": "uri"},
        }
    ]
}
_CONCURRENT_OPENAPI = {
    "parameters": [
        *_UNSAFE_OPENAPI["parameters"],
        {
            "name": "If-Match",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "example": '"v1"'},
        },
    ]
}
_CATALOG = QueryCatalog(
    allowed_filters=frozenset({"lifecycle", "visible", "tag_id", "category_id", "search"}),
    allowed_sorts=frozenset({"position", "title", "publish_at", "updated_at", "id"}),
    default_sort=(SortTerm("position"),),
)
_MAXIMUM_SEARCH_LENGTH = 120
_DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
_LIST_OPENAPI = {
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "default": 1},
        },
        {
            "name": "page_size",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
        },
        {
            "name": "lifecycle",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "enum": [item.value for item in PostLifecycle]},
        },
        {"name": "visible", "in": "query", "required": False, "schema": {"type": "boolean"}},
        {
            "name": "tag_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {
            "name": "category_id",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "format": "uuid"},
        },
        {
            "name": "search",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "minLength": 1, "maxLength": 120},
        },
        {
            "name": "sort",
            "in": "query",
            "required": False,
            "schema": {
                "type": "string",
                "enum": [
                    "position",
                    "title",
                    "publish_at",
                    "updated_at",
                    "-position",
                    "-title",
                    "-publish_at",
                    "-updated_at",
                ],
                "default": "position",
            },
        },
    ]
}


@dataclass(frozen=True, slots=True)
class MutationHeaders:
    """Idempotency plus optional concurrency headers."""

    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceMutationHeaders:
    """Post ID plus retry and concurrency headers."""

    post_id: UUID
    if_match: str | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ResourceConcurrencyHeaders:
    """Resource ID plus required optimistic-concurrency input."""

    resource_id: UUID
    if_match: str | None


def mutation_headers(
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> MutationHeaders:
    """Collect retry and optional concurrency headers."""
    return MutationHeaders(request.headers.get("if-match"), idempotency_key)


def post_mutation_headers(
    post_id: UUID,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> ResourceMutationHeaders:
    """Collect post retry and concurrency headers."""
    return ResourceMutationHeaders(post_id, request.headers.get("if-match"), idempotency_key)


def post_concurrency_headers(post_id: UUID, request: Request) -> ResourceConcurrencyHeaders:
    """Collect post concurrency headers."""
    return ResourceConcurrencyHeaders(post_id, request.headers.get("if-match"))


def taxonomy_concurrency_headers(
    taxonomy_id: UUID,
    request: Request,
) -> ResourceConcurrencyHeaders:
    """Collect taxonomy concurrency headers."""
    return ResourceConcurrencyHeaders(taxonomy_id, request.headers.get("if-match"))


def _service(request: Request) -> BlogService:
    service = getattr(request.app.state, "blog_service", None)
    if not isinstance(service, BlogService):
        raise ApiError.from_code(_DEPENDENCY_UNAVAILABLE, details={"dependency": "database"})
    return service


def _actor(session: SessionView) -> ActorContext:
    return ActorContext.administrator(session.administrator_id)


def _values(payload: PostInput | PostCreateRequest) -> PostValues:
    return PostValues(
        title=payload.title,
        excerpt=payload.excerpt,
        source=payload.source,
        author_display=payload.author_display,
        reading_minutes=0,
        content_checksum="",
        content_policy_name="",
        content_policy_version="",
        tag_ids=tuple(payload.tag_ids),
        category_ids=tuple(payload.category_ids),
        related_post_ids=tuple(payload.related_post_ids),
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        canonical_url=payload.canonical_url,
        cover_media_id=payload.cover_media_id,
    )


def _revision_data(revision: PostRevision) -> PostRevisionData:
    values = revision.values
    return PostRevisionData(
        id=revision.id,
        revision_number=revision.revision_number,
        based_on_revision_id=revision.based_on_revision_id,
        reading_minutes=values.reading_minutes,
        content_checksum=values.content_checksum,
        content_policy_name=values.content_policy_name,
        content_policy_version=values.content_policy_version,
        frozen=revision.frozen,
        created_by=revision.created_by,
        created_at=revision.created_at,
        updated_at=revision.updated_at,
        title=values.title,
        excerpt=values.excerpt,
        source=values.source,
        author_display=values.author_display,
        tag_ids=list(values.tag_ids),
        category_ids=list(values.category_ids),
        related_post_ids=list(values.related_post_ids),
        seo_title=values.seo_title,
        seo_description=values.seo_description,
        canonical_url=values.canonical_url,
        cover_media_id=values.cover_media_id,
    )


def _data(view: AdminPostView) -> PostData:
    snapshot = view.snapshot
    post = snapshot.post
    return PostData(
        id=post.id,
        slug=post.slug,
        visible=post.visible,
        position=post.position,
        lifecycle=view.lifecycle,
        draft=_revision_data(snapshot.draft),
        published=_revision_data(snapshot.published) if snapshot.published else None,
        publish_at=post.publish_at,
        unpublished_at=post.unpublished_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        version=post.version,
        deleted_at=post.deleted_at,
    )


def _taxonomy_data(item: Taxonomy) -> TaxonomyData:
    return TaxonomyData(
        id=item.id,
        kind=item.kind,
        name=item.name,
        slug=item.slug,
        position=item.position,
        visible=item.visible,
        created_at=item.created_at,
        updated_at=item.updated_at,
        version=item.version,
        deleted_at=item.deleted_at,
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


def _map_error(error: Exception) -> ApiError:  # noqa: C901, PLR0911
    if isinstance(error, MediaStateError):
        return ApiError.from_code("RESOURCE_CONFLICT")
    if isinstance(error, BlogValidationError):
        return _validation(f"body.{error.path}", error.code)
    if isinstance(error, BlogRelationError):
        return _validation("body.relations", error.code)
    if isinstance(error, BlogSlugConflictError):
        return _validation("body.slug", "duplicate_slug")
    if isinstance(error, BlogNotFoundError):
        return ApiError.from_code("NOT_FOUND")
    if isinstance(error, BlogIdempotencyRejectedError):
        return map_idempotency_decision(error.decision)
    if isinstance(error, BlogPublicationError):
        return ApiError.from_code("RESOURCE_VERSION_CONFLICT", details={"reason": error.code})
    if isinstance(error, BlogTaxonomyUsageError):
        return ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"reason": "taxonomy_in_use", "usage_count": error.usage_count},
        )
    if isinstance(
        error,
        FrozenPostRevisionError | PostPointerIntegrityError | BlogIntegrityError,
    ):
        return ApiError.from_code(
            "RESOURCE_VERSION_CONFLICT",
            details={"reason": "immutable_or_invalid_revision"},
        )
    if isinstance(error, ValueError):
        return _validation("body.publish_at", "utc_required")
    return map_common_error(error)


def _boolean(value: str | None, *, path: str) -> bool | None:
    if value is None:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise QueryValidationError((QueryIssue(path=path, code="boolean"),))


def _enum[EnumT: StrEnum](
    value: str | None,
    enum_type: type[EnumT],
    *,
    path: str,
) -> EnumT | None:
    if value is None:
        return None
    try:
        return enum_type(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="unsupported_value"),)) from error


def _uuid(value: str | None, *, path: str) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise QueryValidationError((QueryIssue(path=path, code="uuid"),)) from error


def _query(request: Request) -> AdminPostQuery:
    parsed = parse_collection_query(list(request.query_params.multi_items()), catalog=_CATALOG)
    search = parsed.filters.get("search")
    if search is not None and (
        not search or search != search.strip() or len(search) > _MAXIMUM_SEARCH_LENGTH
    ):
        raise QueryValidationError((QueryIssue(path="query.search", code="invalid_text"),))
    selected_sort = parsed.sort[0]
    return AdminPostQuery(
        page=parsed.page,
        lifecycle=_enum(parsed.filters.get("lifecycle"), PostLifecycle, path="query.lifecycle"),
        visible=_boolean(parsed.filters.get("visible"), path="query.visible"),
        tag_id=_uuid(parsed.filters.get("tag_id"), path="query.tag_id"),
        category_id=_uuid(parsed.filters.get("category_id"), path="query.category_id"),
        search=search,
        sort=f"{'-' if selected_sort.descending else ''}{selected_sort.field}",
    )


async def _mutation_data(service: BlogService, snapshot: PostSnapshot) -> PostData:
    return _data(await service.admin_view(snapshot))


@router.get(
    "/posts",
    operation_id="admin_blog_posts_list",
    openapi_extra=_LIST_OPENAPI,
    response_model=ListEnvelope[PostData],
    responses=_RESPONSES,
)
async def posts_list(
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> ListEnvelope[PostData]:
    """List filtered administrator post snapshots."""
    try:
        page = await _service(request).list_admin_posts(_actor(session), _query(request))
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return list_success(request, [_data(item) for item in page.items], page.metadata)


@router.post(
    "/posts",
    operation_id="admin_blog_post_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_create(
    payload: PostCreateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[PostData]:
    """Create one stable route and revision-one draft."""
    service = _service(request)
    try:
        snapshot = await service.create_post(
            CreatePostCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
                slug=payload.slug,
                values=_values(payload),
                visible=payload.visible,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.post.version)
    return success(request, data)


@router.put(
    "/posts/actions/reorder",
    operation_id="admin_blog_posts_reorder",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[BlogOrderListData],
    responses=_RESPONSES,
)
async def posts_reorder(
    payload: BlogReorderRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[BlogOrderListData]:
    """Replace complete nondeleted post order."""
    try:
        ordered = await _service(request).reorder_posts(
            ReorderPostsCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                ordered_ids=tuple(payload.ordered_ids),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=ordered[0].version)
    return success(
        request,
        BlogOrderListData(
            items=[
                BlogOrderData(id=item.id, position=item.position, version=item.version)
                for item in ordered
            ]
        ),
    )


@router.get(
    "/posts/{post_id}",
    operation_id="admin_blog_post_get",
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_get(
    post_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[PostData]:
    """Return one complete administrator post."""
    try:
        view = await _service(request).get_admin_post(_actor(session), post_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=view.snapshot.post.version)
    return success(request, _data(view))


@router.put(
    "/posts/{post_id}",
    operation_id="admin_blog_post_draft_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_update(
    payload: PostInput,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(post_concurrency_headers)],
) -> SuccessEnvelope[PostData]:
    """Replace only the current mutable draft values."""
    service = _service(request)
    try:
        snapshot = await service.save_post_draft(
            SavePostDraftCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                post_id=headers.resource_id,
                if_match=headers.if_match,
                values=_values(payload),
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.post.version)
    return success(request, data)


@router.get(
    "/posts/{post_id}/preview",
    operation_id="admin_blog_post_preview",
    response_model=SuccessEnvelope[PostPreviewData],
    responses=_RESPONSES,
)
async def post_preview(
    post_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[PostPreviewData]:
    """Render the current draft through the private canonical policy."""
    try:
        preview = await _service(request).preview(_actor(session), post_id)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    content = preview.content.rendered
    return success(
        request,
        PostPreviewData(
            post_id=preview.post_id,
            title=preview.title,
            excerpt=preview.excerpt,
            author_display=preview.author_display,
            cover_media_id=preview.cover_media_id,
            content=SafeRenderedContentData(
                html=content.html,
                policy_name=content.policy_name,
                policy_version=content.policy_version,
                source_checksum=content.source_checksum,
            ),
            reading_minutes=preview.content.reading_minutes,
        ),
    )


@router.get(
    "/posts/{post_id}/source",
    operation_id="admin_blog_post_source_export",
    response_model=SuccessEnvelope[PostSourceExportData],
    responses={
        **_RESPONSES,
        int(HTTPStatus.OK): {
            "content": {"text/markdown": {"schema": {"type": "string"}}},
            "description": "Exact normalized CommonMark source.",
        },
    },
)
async def post_source_export(
    post_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
    accept: Annotated[str | None, Header(alias="Accept")] = None,
) -> Response | SuccessEnvelope[PostSourceExportData]:
    """Download exact normalized draft source without public cacheability."""
    try:
        exported = await _service(request).export_source(_actor(session), post_id)
    except Exception as error:
        raise _map_error(error) from error
    if accept is not None and "application/json" in accept.casefold():
        set_private_no_store(response)
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return success(
            request,
            PostSourceExportData(
                post_id=exported.post_id,
                source=exported.source,
                checksum=exported.checksum,
                policy_name=exported.policy_name,
                policy_version=exported.policy_version,
                reading_minutes=exported.reading_minutes,
                filename=exported.filename,
                content_type="text/markdown; charset=utf-8",
            ),
        )
    return Response(
        content=exported.source,
        media_type=exported.content_type,
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'attachment; filename="{exported.filename}"',
            "X-Content-Checksum": exported.checksum,
            "X-Content-Policy": f"{exported.policy_name}/{exported.policy_version}",
            "X-Reading-Minutes": str(exported.reading_minutes),
            "X-Robots-Tag": "noindex, nofollow",
        },
    )


@router.put(
    "/posts/{post_id}/visibility",
    operation_id="admin_blog_post_visibility_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_visibility_update(
    payload: BlogVisibilityRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(post_concurrency_headers)],
) -> SuccessEnvelope[PostData]:
    """Set visibility independently from publication."""
    service = _service(request)
    try:
        snapshot = await service.set_post_visibility(
            SetPostVisibilityCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                post_id=headers.resource_id,
                if_match=headers.if_match,
                visible=payload.visible,
            )
        )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.post.version)
    return success(request, data)


async def _lifecycle(  # noqa: PLR0913
    payload: PublishPostRequest | ReschedulePostRequest | None,
    request: Request,
    response: Response,
    session: SessionView,
    headers: ResourceMutationHeaders,
    *,
    action: str,
) -> SuccessEnvelope[PostData]:
    service = _service(request)
    canonical = _canonical(payload, headers.if_match)
    try:
        if action == "publish":
            snapshot = await service.publish_post(
                PublishPostCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    post_id=headers.post_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                    publish_at=(
                        payload.publish_at if isinstance(payload, PublishPostRequest) else None
                    ),
                )
            )
        elif action == "reschedule" and isinstance(payload, ReschedulePostRequest):
            snapshot = await service.reschedule_post(
                ReschedulePostCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    post_id=headers.post_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                    publish_at=payload.publish_at,
                )
            )
        else:
            snapshot = await service.unpublish_post(
                UnpublishPostCommand(
                    actor=_actor(session),
                    request_id=get_request_id(request),
                    post_id=headers.post_id,
                    if_match=headers.if_match,
                    idempotency_key=headers.idempotency_key,
                    canonical_payload=canonical,
                )
            )
        data = await _mutation_data(service, snapshot)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=snapshot.post.version)
    return success(request, data)


@router.put(
    "/posts/{post_id}/actions/publish",
    operation_id="admin_blog_post_publish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_publish(
    payload: PublishPostRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(post_mutation_headers)],
) -> SuccessEnvelope[PostData]:
    """Publish now or schedule one immutable revision."""
    return await _lifecycle(payload, request, response, session, headers, action="publish")


@router.put(
    "/posts/{post_id}/actions/reschedule",
    operation_id="admin_blog_post_reschedule",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_reschedule(
    payload: ReschedulePostRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceMutationHeaders, Depends(post_mutation_headers)],
) -> SuccessEnvelope[PostData]:
    """Change only post publication schedule metadata."""
    return await _lifecycle(payload, request, response, session, headers, action="reschedule")


@router.put(
    "/posts/{post_id}/actions/unpublish",
    operation_id="admin_blog_post_unpublish",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[PostData],
    responses=_RESPONSES,
)
async def post_unpublish(
    post_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[PostData]:
    """Remove public eligibility without deleting revision history."""
    return await _lifecycle(
        None,
        request,
        response,
        session,
        ResourceMutationHeaders(post_id, headers.if_match, headers.idempotency_key),
        action="unpublish",
    )


@router.delete(
    "/posts/{post_id}",
    operation_id="admin_blog_post_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[BlogDeleteData],
    responses=_RESPONSES,
)
async def post_delete(
    post_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(post_concurrency_headers)],
) -> SuccessEnvelope[BlogDeleteData]:
    """Soft-delete a post after optimistic-concurrency validation."""
    try:
        await _service(request).delete_post(
            DeletePostCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                post_id=post_id,
                if_match=headers.if_match,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, BlogDeleteData())


@router.get(
    "/taxonomies/{kind}",
    operation_id="admin_blog_taxonomies_list",
    response_model=SuccessEnvelope[TaxonomyListData],
    responses=_RESPONSES,
)
async def taxonomies_list(
    kind: TaxonomyKind,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_full_admin_session)],
) -> SuccessEnvelope[TaxonomyListData]:
    """List ordered tags or categories."""
    try:
        items = await _service(request).list_taxonomies(_actor(session), kind)
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, TaxonomyListData(items=[_taxonomy_data(item) for item in items]))


@router.post(
    "/taxonomies",
    operation_id="admin_blog_taxonomy_create",
    status_code=HTTPStatus.CREATED,
    openapi_extra=_UNSAFE_OPENAPI,
    response_model=SuccessEnvelope[TaxonomyData],
    responses=_RESPONSES,
)
async def taxonomy_create(
    payload: TaxonomyCreateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[TaxonomyData]:
    """Create one stable tag or category identity."""
    try:
        item = await _service(request).create_taxonomy(
            CreateTaxonomyCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, None),
                kind=payload.kind,
                name=payload.name,
                slug=payload.slug,
                visible=payload.visible,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _taxonomy_data(item))


@router.put(
    "/taxonomies/{taxonomy_id}",
    operation_id="admin_blog_taxonomy_update",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[TaxonomyData],
    responses=_RESPONSES,
)
async def taxonomy_update(
    payload: TaxonomyUpdateRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(taxonomy_concurrency_headers)],
) -> SuccessEnvelope[TaxonomyData]:
    """Update taxonomy presentation without changing stable kind."""
    try:
        item = await _service(request).update_taxonomy(
            UpdateTaxonomyCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                taxonomy_id=headers.resource_id,
                if_match=headers.if_match,
                name=payload.name,
                slug=payload.slug,
                visible=payload.visible,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=item.version)
    return success(request, _taxonomy_data(item))


@router.put(
    "/taxonomies/{kind}/actions/reorder",
    operation_id="admin_blog_taxonomies_reorder",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[BlogOrderListData],
    responses=_RESPONSES,
)
async def taxonomies_reorder(  # noqa: PLR0913
    kind: TaxonomyKind,
    payload: BlogReorderRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[MutationHeaders, Depends(mutation_headers)],
) -> SuccessEnvelope[BlogOrderListData]:
    """Replace one complete taxonomy order."""
    try:
        ordered = await _service(request).reorder_taxonomies(
            ReorderTaxonomiesCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                kind=kind,
                if_match=headers.if_match,
                idempotency_key=headers.idempotency_key,
                canonical_payload=_canonical(payload, headers.if_match),
                ordered_ids=tuple(payload.ordered_ids),
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    set_resource_etag(response, version=ordered[0].version)
    return success(
        request,
        BlogOrderListData(
            items=[
                BlogOrderData(id=item.id, position=item.position, version=item.version)
                for item in ordered
            ]
        ),
    )


@router.delete(
    "/taxonomies/{taxonomy_id}",
    operation_id="admin_blog_taxonomy_delete",
    openapi_extra=_CONCURRENT_OPENAPI,
    response_model=SuccessEnvelope[BlogDeleteData],
    responses=_RESPONSES,
)
async def taxonomy_delete(
    taxonomy_id: UUID,
    request: Request,
    response: Response,
    session: Annotated[SessionView, Depends(require_unsafe_admin_session)],
    headers: Annotated[ResourceConcurrencyHeaders, Depends(taxonomy_concurrency_headers)],
) -> SuccessEnvelope[BlogDeleteData]:
    """Soft-delete an unused taxonomy identity."""
    try:
        await _service(request).delete_taxonomy(
            DeleteTaxonomyCommand(
                actor=_actor(session),
                request_id=get_request_id(request),
                taxonomy_id=taxonomy_id,
                if_match=headers.if_match,
            )
        )
    except Exception as error:
        raise _map_error(error) from error
    set_private_no_store(response)
    return success(request, BlogDeleteData())
