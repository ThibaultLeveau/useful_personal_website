"""Safe administrator media library and delivery API schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves runtime field types.
from typing import Literal
from uuid import UUID  # noqa: TC003 - Pydantic resolves runtime field types.

from pydantic import Field

from app.api.v1.schemas import ApiModel
from app.modules.media.domain import (  # noqa: TC001 - Pydantic resolves enums at runtime.
    MediaFormat,
    MediaOwnerType,
    MediaStatus,
    MediaUsageRole,
    VariantPurpose,
)


class MediaVariantData(ApiModel):
    """Storage-neutral stripped rendition facts."""

    purpose: VariantPurpose
    format: MediaFormat
    width: int
    height: int
    byte_size: int
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    admin_url: str


class MediaAssetData(ApiModel):
    """Safe logical asset projection with no key/checksum/provider details."""

    id: UUID
    status: MediaStatus
    display_name: str
    detected_format: MediaFormat | None
    width: int | None
    height: int | None
    byte_size: int | None
    variants: list[MediaVariantData]
    version: int
    created_at: datetime
    updated_at: datetime


class MediaMetadataRequest(ApiModel):
    """Display-only logical asset metadata mutation."""

    display_name: str = Field(min_length=1, max_length=180)


class MediaUsageData(ApiModel):
    """Allow-listed usage location without draft content or contextual prose."""

    owner_type: MediaOwnerType
    owner_id: UUID
    role: MediaUsageRole
    position: int
    active: bool
    public: bool


class MediaUsageListData(ApiModel):
    """Bounded safe usage collection for one asset."""

    items: list[MediaUsageData]


class MediaDeleteData(ApiModel):
    """Confirmed tombstone result."""

    status: Literal["deleted"] = "deleted"
