"""UTC timestamp and opaque UUID helpers for public contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


def require_utc(value: datetime) -> datetime:
    """Require an aware UTC instant without silently guessing a timezone."""
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        msg = "timestamps must be timezone-aware UTC values"
        raise ValueError(msg)
    return value


def format_rfc3339(value: datetime) -> str:
    """Serialize a UTC instant using an explicit RFC 3339 ``Z`` suffix."""
    return require_utc(value).isoformat().replace("+00:00", "Z")


def new_opaque_id() -> UUID:
    """Create a random UUID whose value carries no database sequencing semantics."""
    return uuid4()


def parse_opaque_id(value: str) -> UUID:
    """Accept only the canonical hyphenated UUID representation."""
    try:
        parsed = UUID(value)
    except ValueError as error:
        msg = "identifier must be a canonical UUID"
        raise ValueError(msg) from error
    if str(parsed) != value.casefold():
        msg = "identifier must be a canonical UUID"
        raise ValueError(msg)
    return parsed
