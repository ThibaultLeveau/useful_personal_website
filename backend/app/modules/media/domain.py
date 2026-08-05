"""Persistence-neutral media assets, variants, usages, and lifecycle rules."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

MAXIMUM_UPLOAD_BYTES = 10 * 1024 * 1024
MAXIMUM_IMAGE_DIMENSION = 6_000
MAXIMUM_IMAGE_PIXELS = 36_000_000
MAXIMUM_DISPLAY_NAME_LENGTH = 180
MAXIMUM_ALT_TEXT_LENGTH = 300
MAXIMUM_CAPTION_LENGTH = 500
MAXIMUM_FOCAL_PERCENT = 100
VARIANT_WIDTHS = (320, 640, 960, 1_440, 1_920)
MANAGED_KEY_PATTERN = re.compile(
    r"^(?:quarantine|originals)/[0-9a-f]{2}/[0-9a-f-]{36}/[a-z0-9._-]{1,80}$"
    r"|^variants/[0-9a-f]{2}/[0-9a-f-]{36}/[a-z0-9._-]{1,80}$"
)


class MediaStatus(StrEnum):
    """Durable states with no false-ready transition."""

    QUARANTINED = "quarantined"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class MediaFormat(StrEnum):
    """Decoder-approved image formats only."""

    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"

    @property
    def content_type(self) -> str:
        """Return the exact transport content type."""
        return {
            MediaFormat.JPEG: "image/jpeg",
            MediaFormat.PNG: "image/png",
            MediaFormat.WEBP: "image/webp",
        }[self]

    @property
    def extension(self) -> str:
        """Return one canonical safe extension."""
        return "jpg" if self is MediaFormat.JPEG else self.value


class VariantPurpose(StrEnum):
    """Closed delivery rendition purposes."""

    RESPONSIVE_WEBP = "responsive_webp"
    RESPONSIVE_FALLBACK = "responsive_fallback"


class MediaUsePurpose(StrEnum):
    """Contextual accessibility intent."""

    MEANINGFUL = "meaningful"
    DECORATIVE = "decorative"


class MediaOwnerType(StrEnum):
    """Accepted S1 owner aggregates only."""

    PROFILE = "profile"
    WEBSITE_SETTINGS = "website_settings"
    PROJECT_REVISION = "project_revision"
    BLOG_POST_REVISION = "blog_post_revision"
    PAGE_BLOCK = "page_block"


class MediaUsageRole(StrEnum):
    """Exact accepted owner roles; storage details never form a role."""

    PROFILE_IMAGE = "profile_image"
    SITE_LOGO = "site_logo"
    SITE_FAVICON = "site_favicon"
    SITE_SOCIAL_IMAGE = "site_social_image"
    PROJECT_COVER = "project_cover"
    PROJECT_SCREENSHOT = "project_screenshot"
    BLOG_COVER = "blog_cover"
    PAGE_PRIMARY = "page_primary"


ALLOWED_OWNER_ROLES = {
    MediaOwnerType.PROFILE: frozenset({MediaUsageRole.PROFILE_IMAGE}),
    MediaOwnerType.WEBSITE_SETTINGS: frozenset(
        {
            MediaUsageRole.SITE_LOGO,
            MediaUsageRole.SITE_FAVICON,
            MediaUsageRole.SITE_SOCIAL_IMAGE,
        }
    ),
    MediaOwnerType.PROJECT_REVISION: frozenset(
        {MediaUsageRole.PROJECT_COVER, MediaUsageRole.PROJECT_SCREENSHOT}
    ),
    MediaOwnerType.BLOG_POST_REVISION: frozenset({MediaUsageRole.BLOG_COVER}),
    MediaOwnerType.PAGE_BLOCK: frozenset({MediaUsageRole.PAGE_PRIMARY}),
}


class MediaValidationError(ValueError):
    """Stable field-addressable media rejection without reflected input."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain safe field and reason tokens only."""
        super().__init__("media input is invalid")
        self.path = path
        self.code = code


class MediaStateError(Exception):
    """An operation targeted an incompatible lifecycle state."""


@dataclass(frozen=True, slots=True)
class MediaVariant:
    """One immutable registered stripped rendition."""

    id: UUID
    asset_id: UUID
    purpose: VariantPurpose
    format: MediaFormat
    width: int
    height: int
    byte_size: int
    checksum_sha256: str
    storage_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class MediaAsset:
    """Stable logical asset with private original and immutable variants."""

    id: UUID
    status: MediaStatus
    display_name: str
    detected_format: MediaFormat | None
    width: int | None
    height: int | None
    byte_size: int | None
    checksum_sha256: str | None
    original_key: str | None
    quarantine_key: str | None
    variants: tuple[MediaVariant, ...]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    version: int
    failure_code: str | None = None
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MediaUse:
    """Canonical contextual reference supplied by an owner aggregate."""

    asset_id: UUID
    owner_type: MediaOwnerType
    owner_id: UUID
    role: MediaUsageRole
    position: int
    purpose: MediaUsePurpose
    alt_text: str | None
    caption: str | None
    focal_x: int = 50
    focal_y: int = 50
    active: bool = True
    public: bool = False


@dataclass(frozen=True, slots=True)
class MediaUsage(MediaUse):
    """Materialized use identity and timestamps owned by media persistence."""

    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ProcessedVariant:
    """Processor output bytes before private promotion."""

    purpose: VariantPurpose
    format: MediaFormat
    width: int
    height: int
    content: bytes
    checksum_sha256: str


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    """Validated source facts and stripped delivery renditions."""

    detected_format: MediaFormat
    width: int
    height: int
    byte_size: int
    checksum_sha256: str
    variants: tuple[ProcessedVariant, ...]


def safe_display_name(filename: str | None) -> str:
    """Return a bounded display label that can never influence a storage key."""
    if filename is None:
        return "Untitled image"
    leaf = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    normalized = unicodedata.normalize("NFC", leaf).strip()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cc", "Cf", "Cs"}
    )
    if not normalized:
        return "Untitled image"
    return normalized[:MAXIMUM_DISPLAY_NAME_LENGTH]


def validate_display_name(value: str) -> str:
    """Validate an administrator-edited display label."""
    if not value or value != value.strip() or len(value) > MAXIMUM_DISPLAY_NAME_LENGTH:
        raise MediaValidationError(path="display_name", code="invalid_text")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise MediaValidationError(path="display_name", code="unsafe_unicode")
    return unicodedata.normalize("NFC", value)


def validate_managed_key(value: str) -> str:
    """Reject traversal, provider prefixes, and every unregistered namespace."""
    if MANAGED_KEY_PATTERN.fullmatch(value) is None or ".." in value or "//" in value:
        raise MediaValidationError(path="storage_key", code="invalid_managed_key")
    return value


def validate_media_use(value: MediaUse) -> MediaUse:
    """Enforce contextual alt semantics and bounded presentation metadata."""
    if value.role not in ALLOWED_OWNER_ROLES[value.owner_type]:
        raise MediaValidationError(path="role", code="invalid_owner_role")
    if value.position < 0:
        raise MediaValidationError(path="position", code="invalid_position")
    if (
        not 0 <= value.focal_x <= MAXIMUM_FOCAL_PERCENT
        or not 0 <= value.focal_y <= MAXIMUM_FOCAL_PERCENT
    ):
        raise MediaValidationError(path="focal_point", code="invalid_focal_point")
    alt = value.alt_text
    if value.purpose is MediaUsePurpose.DECORATIVE:
        if alt not in {None, ""}:
            raise MediaValidationError(path="alt_text", code="decorative_alt_must_be_empty")
        alt = ""
    elif alt is None or not alt.strip() or alt != alt.strip():
        raise MediaValidationError(path="alt_text", code="meaningful_alt_required")
    if alt is not None and len(alt) > MAXIMUM_ALT_TEXT_LENGTH:
        raise MediaValidationError(path="alt_text", code="text_too_long")
    caption = value.caption
    if caption is not None and (
        not caption or caption != caption.strip() or len(caption) > MAXIMUM_CAPTION_LENGTH
    ):
        raise MediaValidationError(path="caption", code="invalid_text")
    return replace(value, alt_text=alt)


def require_ready(asset: MediaAsset) -> None:
    """Require a complete ready and nondeleted asset."""
    if (
        asset.status is not MediaStatus.READY
        or asset.deleted_at is not None
        or asset.original_key is None
        or not asset.variants
    ):
        raise MediaStateError


def select_variant(asset: MediaAsset, *, width: int, accepted_webp: bool) -> MediaVariant:
    """Select the smallest adequate registered variant without exposing keys."""
    require_ready(asset)
    if width < 1 or width > MAXIMUM_IMAGE_DIMENSION:
        raise MediaValidationError(path="width", code="invalid_dimension")
    purpose = (
        VariantPurpose.RESPONSIVE_WEBP if accepted_webp else VariantPurpose.RESPONSIVE_FALLBACK
    )
    candidates = sorted(
        (item for item in asset.variants if item.purpose is purpose), key=lambda item: item.width
    )
    if not candidates:
        raise MediaStateError
    return next((item for item in candidates if item.width >= width), candidates[-1])
