"""API token scopes, metadata, and validation."""
# ruff: noqa: D101, D102, D103, D107, EM101

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

TOKEN_NAME_PATTERN = re.compile(r"^[\w][\w .:/-]{0,79}$", re.UNICODE)
MAXIMUM_TOKEN_LIFETIME = timedelta(days=365)


class ApiTokenScope(StrEnum):
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    MEDIA_READ = "media:read"
    MEDIA_WRITE = "media:write"
    CONTACTS_READ = "contacts:read"
    ADMIN_READ = "admin:read"


class ApiTokenStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ApiTokenValidationError(ValueError):
    def __init__(self, path: str, code: str) -> None:
        super().__init__("API token input is invalid")
        self.path = path
        self.code = code


@dataclass(frozen=True, slots=True)
class ApiTokenMetadata:
    id: UUID
    public_id: str
    name: str
    display_suffix: str
    scopes: frozenset[ApiTokenScope]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None
    rotated_from_id: UUID | None
    version: int

    def status_at(self, now: datetime) -> ApiTokenStatus:
        if self.revoked_at is not None:
            return ApiTokenStatus.REVOKED
        if self.expires_at is not None and self.expires_at <= now:
            return ApiTokenStatus.EXPIRED
        return ApiTokenStatus.ACTIVE


def normalize_token_name(value: str) -> str:
    normalized = " ".join(value.split())
    if TOKEN_NAME_PATTERN.fullmatch(normalized) is None:
        raise ApiTokenValidationError("name", "invalid_format")
    return normalized


def validate_expiry(expires_at: datetime | None, *, now: datetime, confirm_no_expiry: bool) -> None:
    if expires_at is None:
        if not confirm_no_expiry:
            raise ApiTokenValidationError("confirm_no_expiry", "required")
        return
    if expires_at <= now:
        raise ApiTokenValidationError("expires_at", "must_be_future")
    if expires_at - now > MAXIMUM_TOKEN_LIFETIME:
        raise ApiTokenValidationError("expires_at", "maximum_365_days")
