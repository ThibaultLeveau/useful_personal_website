"""Validation and one-way fingerprints for idempotent application commands."""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import JsonValue

    from app.common.domain.actors import ActorContext

_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{16,128}$")
_ROUTE_PATTERN = re.compile(r"^/api/v1/[A-Za-z0-9_./{}-]{1,238}$")


def validate_idempotency_key(value: str) -> str:
    """Accept a bounded opaque ASCII key safe for headers and diagnostics."""
    if _KEY_PATTERN.fullmatch(value) is None:
        msg = "idempotency keys must be 16-128 safe ASCII characters"
        raise ValueError(msg)
    return value


def validate_route_template(value: str) -> str:
    """Accept a canonical versioned route template without query material."""
    if _ROUTE_PATTERN.fullmatch(value) is None or "//" in value:
        msg = "idempotency routes must be canonical /api/v1 route templates"
        raise ValueError(msg)
    return value


def digest_actor(actor: ActorContext) -> bytes:
    """Digest the stable actor identity instead of storing it redundantly."""
    return hashlib.sha256(actor.storage_identity).digest()


def digest_idempotency_key(value: str) -> bytes:
    """Validate and digest a client key so raw material is never persisted."""
    return hashlib.sha256(validate_idempotency_key(value).encode()).digest()


def fingerprint_bytes(payload: bytes) -> bytes:
    """Fingerprint an already-canonical command representation."""
    return hashlib.sha256(payload).digest()


def fingerprint_json(payload: JsonValue) -> bytes:
    """Fingerprint a canonical JSON value with stable object-key ordering."""
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return fingerprint_bytes(encoded)
