"""Request ID generation, validation, and request-state access."""

from __future__ import annotations

import re
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{15,127}$")


def create_request_id() -> str:
    """Generate an unguessable 128-bit request identifier."""
    return secrets.token_hex(16)


def select_request_id(candidate: str | None) -> str:
    """Accept a bounded edge ID or replace it with an unguessable value."""
    if candidate is not None and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return create_request_id()


def get_request_id(request: Request) -> str:
    """Read the middleware-assigned request ID with a safe fallback."""
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else create_request_id()
