"""API token management and one-time secret contracts."""

# ruff: noqa: D101
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.api.v1.schemas import ApiModel
from app.modules.api_access.domain import ApiTokenScope


class ApiTokenCreateRequest(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    scopes: set[ApiTokenScope] = Field(min_length=1, max_length=6)
    expires_at: datetime | None = None
    confirm_no_expiry: bool = False


class ApiTokenRotateRequest(ApiModel):
    expires_at: datetime | None = None
    confirm_no_expiry: bool = False


class ApiTokenData(ApiModel):
    id: UUID
    public_id: str
    name: str
    display_suffix: str
    scopes: list[ApiTokenScope]
    status: Literal["active", "expired", "revoked"]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None
    rotated_from_id: UUID | None
    version: int


class ApiTokenSecretData(ApiModel):
    token: ApiTokenData
    plaintext_token: str = Field(min_length=74, max_length=74)


class ApiTokenScopeCatalogData(ApiModel):
    scopes: list[ApiTokenScope]
