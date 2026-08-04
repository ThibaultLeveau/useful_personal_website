"""Stable transport- and persistence-neutral common domain contracts."""

from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.concurrency import (
    InvalidPreconditionError,
    PreconditionRequiredError,
    ResourceVersionConflictError,
    format_etag,
    parse_etag,
    require_matching_version,
)
from app.common.domain.pagination import Page, PageMetadata, PageRequest, page_metadata
from app.common.domain.query import (
    CollectionQuery,
    QueryCatalog,
    QueryIssue,
    QueryValidationError,
    SortTerm,
    parse_collection_query,
)
from app.common.domain.temporal import (
    format_rfc3339,
    new_opaque_id,
    parse_opaque_id,
    require_utc,
)

__all__ = [
    "ActorContext",
    "ActorType",
    "CollectionQuery",
    "InvalidPreconditionError",
    "Page",
    "PageMetadata",
    "PageRequest",
    "PreconditionRequiredError",
    "QueryCatalog",
    "QueryIssue",
    "QueryValidationError",
    "ResourceVersionConflictError",
    "SortTerm",
    "format_etag",
    "format_rfc3339",
    "new_opaque_id",
    "page_metadata",
    "parse_collection_query",
    "parse_etag",
    "parse_opaque_id",
    "require_matching_version",
    "require_utc",
]
