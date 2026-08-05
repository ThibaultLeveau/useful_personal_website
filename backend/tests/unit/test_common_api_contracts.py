"""Unit coverage for stable M2 API value objects and security policies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from http import HTTPStatus
from uuid import UUID

import pytest

from app.api.v1.conventions import map_common_error, map_idempotency_decision
from app.common.application import IdempotencyDecision, IdempotencyDecisionType
from app.common.domain import (
    ActorContext,
    InvalidPreconditionError,
    PageRequest,
    PreconditionRequiredError,
    QueryCatalog,
    QueryValidationError,
    ResourceVersionConflictError,
    SortTerm,
    format_etag,
    format_rfc3339,
    page_metadata,
    parse_collection_query,
    parse_etag,
    parse_opaque_id,
    require_matching_version,
    require_utc,
)
from app.common.domain.actors import ActorType
from app.common.errors import ERROR_SPECS, ApiError, error_spec
from app.common.security import (
    AccessPolicy,
    AuthorizationDeniedError,
    require_authorized,
)

ADMIN_ID = UUID("00000000-0000-4000-8000-000000000201")
TOKEN_ID = UUID("00000000-0000-4000-8000-000000000202")


def test_actor_context_and_authorization_are_explicit_and_deny_by_default() -> None:
    """Public, session, and token actors must cross a use-case-owned policy."""
    public = ActorContext.public()
    administrator = ActorContext.administrator(ADMIN_ID)
    reader = ActorContext.token(TOKEN_ID, frozenset({"content:read"}))
    writer = ActorContext.token(TOKEN_ID, frozenset({"content:read", "content:write"}))
    policy = AccessPolicy(
        resource="content",
        action="update",
        allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION, ActorType.API_TOKEN}),
        required_token_scopes=frozenset({"content:write"}),
    )

    assert not policy.allows(public)
    assert policy.allows(administrator)
    assert not policy.allows(reader)
    assert policy.allows(writer)
    with pytest.raises(AuthorizationDeniedError):
        require_authorized(reader, policy)
    require_authorized(writer, policy)

    with pytest.raises(ValueError, match="public actor"):
        ActorContext(ActorType.PUBLIC, ADMIN_ID)
    with pytest.raises(ValueError, match="requires an opaque"):
        ActorContext(ActorType.API_TOKEN, None)


def test_etag_preconditions_use_one_strong_integer_version_contract() -> None:
    """Missing, malformed, and stale values remain distinct safe failures."""
    assert format_etag(7) == '"v7"'
    assert parse_etag('"v7"') == 7
    assert require_matching_version('"v7"', current_version=7) == 7

    with pytest.raises(PreconditionRequiredError):
        require_matching_version(None, current_version=7)
    for invalid in ('W/"v7"', '"7"', '"v0"', "*", '"v7", "v8"'):
        with pytest.raises(InvalidPreconditionError):
            parse_etag(invalid)
    with pytest.raises(ResourceVersionConflictError) as caught:
        require_matching_version('"v6"', current_version=7)
    assert caught.value.current_version == 7
    assert caught.value.submitted_version == 6


def test_page_metadata_covers_defaults_maximum_empty_and_beyond_last() -> None:
    """Page traversal metadata must remain exact at every boundary."""
    default = PageRequest()
    assert (default.page, default.page_size, default.offset) == (1, 20, 0)
    empty = page_metadata(default, total_items=0)
    assert empty.total_pages == 0
    assert not empty.has_previous
    assert not empty.has_next

    final = page_metadata(PageRequest(page=3, page_size=20), total_items=41)
    assert (final.total_pages, final.has_previous, final.has_next) == (3, True, False)
    beyond = page_metadata(PageRequest(page=4, page_size=20), total_items=41)
    assert (beyond.total_pages, beyond.has_previous, beyond.has_next) == (3, True, False)
    assert PageRequest(page=2, page_size=100).offset == 100
    with pytest.raises(ValueError, match="between 1 and 100"):
        PageRequest(page_size=101)


def test_allow_list_parser_adds_id_tie_breaker_and_rejects_unsafe_grammar() -> None:
    """Only exact catalog fields can become later repository mapping keys."""
    catalog = QueryCatalog(
        allowed_filters=frozenset({"status", "search"}),
        allowed_sorts=frozenset({"created_at", "name", "id"}),
        default_sort=(SortTerm("created_at", descending=True),),
    )
    parsed = parse_collection_query(
        [("page", "2"), ("page_size", "25"), ("status", "active"), ("sort", "name")],
        catalog=catalog,
    )
    assert parsed.page == PageRequest(page=2, page_size=25)
    assert parsed.filters == {"status": "active"}
    assert parsed.sort == (SortTerm("name"), SortTerm("id"))
    assert parse_collection_query([], catalog=catalog).sort == (
        SortTerm("created_at", descending=True),
        SortTerm("id"),
    )

    adversarial_queries = [
        [("status", "active"), ("status", "inactive")],
        [("filter[status]", "active")],
        [("sort", "name,name")],
        [("sort", "name desc;drop_table")],
        [("sort", "%2Did")],
        [("unknown_column", "value")],
        [("page_size", "101")],
        [("page", "1 OR 1=1")],
    ]
    for pairs in adversarial_queries:
        with pytest.raises(QueryValidationError) as caught:
            parse_collection_query(pairs, catalog=catalog)
        assert caught.value.issues
        assert "drop_table" not in repr(caught.value.issues)


def test_utc_and_opaque_identifier_helpers_never_guess_contract_values() -> None:
    """Timestamps require UTC and UUIDs require their canonical opaque form."""
    instant = datetime(2026, 8, 3, 9, 10, 11, tzinfo=UTC)
    assert require_utc(instant) is instant
    assert format_rfc3339(instant) == "2026-08-03T09:10:11Z"
    with pytest.raises(ValueError, match="UTC"):
        require_utc(instant.replace(tzinfo=None))
    identifier = "00000000-0000-4000-8000-000000000203"
    assert str(parse_opaque_id(identifier)) == identifier
    with pytest.raises(ValueError, match="canonical UUID"):
        parse_opaque_id(identifier.replace("-", ""))


def test_error_registry_has_stable_unique_status_and_safe_mapping() -> None:
    """Public errors must be registered and cannot silently change status."""
    assert len(ERROR_SPECS) == len(set(ERROR_SPECS))
    assert error_spec("PRECONDITION_REQUIRED").status_code is HTTPStatus.PRECONDITION_REQUIRED
    assert ApiError.from_code("NOT_FOUND").status_code is HTTPStatus.NOT_FOUND
    with pytest.raises(ValueError, match="unregistered"):
        ApiError.from_code("MADE_UP")
    with pytest.raises(ValueError, match="must use status"):
        ApiError(
            status_code=HTTPStatus.BAD_REQUEST,
            code="NOT_FOUND",
            message="The requested resource was not found.",
        )

    assert map_common_error(AuthorizationDeniedError()).code == "AUTHORIZATION_DENIED"
    assert map_common_error(PreconditionRequiredError()).code == "PRECONDITION_REQUIRED"
    assert map_common_error(InvalidPreconditionError()).code == "BAD_REQUEST"
    version_error = map_common_error(
        ResourceVersionConflictError(current_version=4, submitted_version=3)
    )
    assert version_error.code == "RESOURCE_VERSION_CONFLICT"
    assert version_error.details == {"current_version": 4}

    for decision_type, expected_code in (
        (IdempotencyDecisionType.PAYLOAD_CONFLICT, "IDEMPOTENCY_CONFLICT"),
        (IdempotencyDecisionType.IN_PROGRESS, "IDEMPOTENCY_IN_PROGRESS"),
    ):
        mapped = map_idempotency_decision(IdempotencyDecision(decision=decision_type))
        assert mapped.code == expected_code


def test_policy_rejects_malformed_capabilities_and_contradictory_scopes() -> None:
    """Policies cannot smuggle SQL-shaped or orphaned scope declarations."""
    with pytest.raises(ValueError, match="bounded capability"):
        AccessPolicy(
            resource="content;drop",
            action="read",
            allowed_actor_types=frozenset({ActorType.PUBLIC}),
        )
    with pytest.raises(ValueError, match="require the API-token"):
        AccessPolicy(
            resource="content",
            action="read",
            allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
            required_token_scopes=frozenset({"content:read"}),
        )


def test_page_request_rejects_boolean_and_negative_values() -> None:
    """Python bool values must not cross the integer API contract accidentally."""
    for page, page_size in ((True, 20), (0, 20), (1, False), (1, -1)):
        with pytest.raises(ValueError, match=r"positive|between"):
            PageRequest(page=page, page_size=page_size)


def test_non_utc_offset_is_rejected_even_when_timezone_aware() -> None:
    """An aware non-UTC offset is not silently normalized by the domain helper."""
    non_utc = datetime(2026, 8, 3, 10, tzinfo=timezone(timedelta(hours=2)))
    with pytest.raises(ValueError, match="UTC"):
        require_utc(non_utc)
