"""Unit coverage for digest-only M2 idempotency contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.common.application import (
    IDEMPOTENCY_RETENTION,
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain import ActorContext
from app.common.security import fingerprint_json, validate_idempotency_key

ADMIN_ID = UUID("00000000-0000-4000-8000-000000000211")
NOW = datetime(2026, 8, 3, 10, tzinfo=UTC)


def test_request_retains_only_fixed_length_digests_and_24_hour_expiry() -> None:
    """Raw key, actor, and payload values must not enter persistence contracts."""
    raw_key = "request-key-0000000000000001"
    raw_payload = b'{"private":"not-retained"}'
    request = IdempotencyRequest.create(
        actor=ActorContext.administrator(ADMIN_ID),
        route="/api/v1/admin/settings",
        key=raw_key,
        canonical_payload=raw_payload,
        requested_at=NOW,
    )

    assert len(request.actor_digest) == 32
    assert len(request.key_digest) == 32
    assert len(request.request_fingerprint) == 32
    assert request.expires_at - request.requested_at == IDEMPOTENCY_RETENTION
    assert raw_key not in repr(request)
    assert "not-retained" not in repr(request)


def test_canonical_json_fingerprint_is_order_independent_but_value_sensitive() -> None:
    """Equivalent object order replays while a different command conflicts."""
    left = fingerprint_json({"name": "Signal", "enabled": True})
    reordered = fingerprint_json({"enabled": True, "name": "Signal"})
    changed = fingerprint_json({"enabled": False, "name": "Signal"})

    assert left == reordered
    assert left != changed


def test_outcome_never_accepts_failure_or_partial_resource_metadata() -> None:
    """Replay state is a safe success reference, never an arbitrary body."""
    resource_id = UUID("00000000-0000-4000-8000-000000000212")
    outcome = IdempotencyOutcome(
        response_status=201,
        result_code="settings.updated",
        resource_type="settings",
        resource_id=resource_id,
        resource_version=2,
    )
    assert outcome.resource_id == resource_id
    with pytest.raises(ValueError, match="successful"):
        IdempotencyOutcome(response_status=500, result_code="failed")
    with pytest.raises(ValueError, match="all present"):
        IdempotencyOutcome(
            response_status=200,
            result_code="updated",
            resource_type="settings",
        )


def test_decision_shapes_are_unambiguous() -> None:
    """Acquired/replay/conflict states cannot carry contradictory fields."""
    record_id = UUID("00000000-0000-4000-8000-000000000213")
    outcome = IdempotencyOutcome(response_status=200, result_code="updated")
    assert (
        IdempotencyDecision(
            IdempotencyDecisionType.ACQUIRED,
            record_id=record_id,
        ).record_id
        == record_id
    )
    assert (
        IdempotencyDecision(
            IdempotencyDecisionType.REPLAY,
            record_id=record_id,
            outcome=outcome,
        ).outcome
        == outcome
    )
    with pytest.raises(ValueError, match="requires only"):
        IdempotencyDecision(IdempotencyDecisionType.ACQUIRED)
    with pytest.raises(ValueError, match="cannot expose"):
        IdempotencyDecision(
            IdempotencyDecisionType.PAYLOAD_CONFLICT,
            record_id=record_id,
        )


def test_key_route_and_retention_validation_fail_closed() -> None:
    """Whitespace, query strings, short keys, and custom retention are refused."""
    for key in ("short", "contains whitespace 0000", "unsafe/key/000000000"):
        with pytest.raises(ValueError, match="idempotency keys"):
            validate_idempotency_key(key)
    base = IdempotencyRequest.create(
        actor=ActorContext.administrator(ADMIN_ID),
        route="/api/v1/admin/settings",
        key="request-key-0000000000000002",
        canonical_payload=b"{}",
        requested_at=NOW,
    )
    with pytest.raises(ValueError, match="24-hour"):
        IdempotencyRequest(
            actor_type=base.actor_type,
            actor_digest=base.actor_digest,
            route=base.route,
            key_digest=base.key_digest,
            request_fingerprint=base.request_fingerprint,
            requested_at=NOW,
            expires_at=NOW + timedelta(hours=1),
        )
