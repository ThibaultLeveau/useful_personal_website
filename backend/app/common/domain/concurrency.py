"""Integer-version ETag and precondition rules shared by mutable resources."""

from __future__ import annotations

import re

_ETAG_PATTERN = re.compile(r'^"v(?P<version>[1-9][0-9]*)"$')


class PreconditionRequiredError(Exception):
    """Raised when a mutation omits the required ``If-Match`` header."""


class InvalidPreconditionError(Exception):
    """Raised when an ``If-Match`` value is not one supported strong ETag."""


class ResourceVersionConflictError(Exception):
    """Raised when the submitted version is not the current resource version."""

    def __init__(self, *, current_version: int, submitted_version: int) -> None:
        """Retain safe integer facts for a stable conflict projection."""
        super().__init__("the submitted resource version is stale")
        self.current_version = current_version
        self.submitted_version = submitted_version


def format_etag(version: int) -> str:
    """Format one positive integer version as a strong opaque ETag."""
    if isinstance(version, bool) or version < 1:
        msg = "resource versions must be positive integers"
        raise ValueError(msg)
    return f'"v{version}"'


def parse_etag(value: str) -> int:
    """Parse exactly one strong version ETag without accepting wildcard/list syntax."""
    match = _ETAG_PATTERN.fullmatch(value)
    if match is None:
        raise InvalidPreconditionError
    return int(match.group("version"))


def require_matching_version(if_match: str | None, *, current_version: int) -> int:
    """Require a valid ETag and reject stale mutations before application work."""
    if if_match is None:
        raise PreconditionRequiredError
    submitted_version = parse_etag(if_match)
    if submitted_version != current_version:
        raise ResourceVersionConflictError(
            current_version=current_version,
            submitted_version=submitted_version,
        )
    return submitted_version
