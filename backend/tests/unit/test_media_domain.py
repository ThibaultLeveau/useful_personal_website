"""Media domain policy and safe-key regression tests."""

# ruff: noqa: D103

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.modules.media.domain import (
    MediaAsset,
    MediaFormat,
    MediaOwnerType,
    MediaStateError,
    MediaStatus,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
    MediaValidationError,
    MediaVariant,
    VariantPurpose,
    safe_display_name,
    select_variant,
    validate_managed_key,
    validate_media_use,
)

ASSET_ID = UUID("0198a9f4-8260-7ab1-9123-123456789abc")
OWNER_ID = UUID("0198a9f4-8260-7ab1-9123-123456789abd")
ACTOR_ID = UUID("0198a9f4-8260-7ab1-9123-123456789abe")
NOW = datetime(2026, 8, 4, tzinfo=UTC)


def _variant(*, width: int, purpose: VariantPurpose, suffix: str) -> MediaVariant:
    return MediaVariant(
        id=UUID(f"0198a9f4-8260-7ab1-9123-123456789a{suffix}"),
        asset_id=ASSET_ID,
        purpose=purpose,
        format=(
            MediaFormat.WEBP if purpose is VariantPurpose.RESPONSIVE_WEBP else MediaFormat.JPEG
        ),
        width=width,
        height=width // 2,
        byte_size=128,
        checksum_sha256="a" * 64,
        storage_key=(
            f"variants/01/{ASSET_ID}/{purpose.value}-{width}."
            f"{'webp' if purpose is VariantPurpose.RESPONSIVE_WEBP else 'jpg'}"
        ),
        created_at=NOW,
    )


def _asset(status: MediaStatus = MediaStatus.READY) -> MediaAsset:
    return MediaAsset(
        id=ASSET_ID,
        status=status,
        display_name="Portrait.jpg",
        detected_format=MediaFormat.JPEG,
        width=1_000,
        height=500,
        byte_size=512,
        checksum_sha256="b" * 64,
        original_key=f"originals/01/{ASSET_ID}/source.jpg",
        quarantine_key=None,
        variants=(
            _variant(width=320, purpose=VariantPurpose.RESPONSIVE_WEBP, suffix="01"),
            _variant(width=640, purpose=VariantPurpose.RESPONSIVE_WEBP, suffix="02"),
            _variant(width=320, purpose=VariantPurpose.RESPONSIVE_FALLBACK, suffix="03"),
            _variant(width=640, purpose=VariantPurpose.RESPONSIVE_FALLBACK, suffix="04"),
        ),
        created_by=ACTOR_ID,
        created_at=NOW,
        updated_at=NOW,
        version=2,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../private/portrait.jpg", "portrait.jpg"),
        (r"C:\\fake\\portrait.png", "portrait.png"),
        ("\u202esecret.jpg", "secret.jpg"),
        (None, "Untitled image"),
    ],
)
def test_safe_display_name_is_leaf_only_and_non_authoritative(
    raw: str | None, expected: str
) -> None:
    assert safe_display_name(raw) == expected


@pytest.mark.parametrize(
    "key",
    [
        "../outside.jpg",
        "variants/01/not-a-uuid/item.webp",
        f"public/01/{ASSET_ID}/item.webp",
        f"variants/01/{ASSET_ID}/../item.webp",
        f"variants/01/{ASSET_ID}//item.webp",
    ],
)
def test_managed_key_rejects_traversal_and_unregistered_namespaces(key: str) -> None:
    with pytest.raises(MediaValidationError) as captured:
        validate_managed_key(key)
    assert captured.value.code == "invalid_managed_key"


def test_meaningful_use_requires_contextual_alt_text() -> None:
    value = MediaUse(
        asset_id=ASSET_ID,
        owner_type=MediaOwnerType.PROFILE,
        owner_id=OWNER_ID,
        role=MediaUsageRole.PROFILE_IMAGE,
        position=0,
        purpose=MediaUsePurpose.MEANINGFUL,
        alt_text=None,
        caption=None,
    )
    with pytest.raises(MediaValidationError) as captured:
        validate_media_use(value)
    assert captured.value.code == "meaningful_alt_required"


def test_decorative_use_normalizes_none_to_empty_alt() -> None:
    value = MediaUse(
        asset_id=ASSET_ID,
        owner_type=MediaOwnerType.PROFILE,
        owner_id=OWNER_ID,
        role=MediaUsageRole.PROFILE_IMAGE,
        position=0,
        purpose=MediaUsePurpose.DECORATIVE,
        alt_text=None,
        caption=None,
    )
    assert validate_media_use(value).alt_text == ""


def test_select_variant_prefers_smallest_adequate_registered_width() -> None:
    assert select_variant(_asset(), width=400, accepted_webp=True).width == 640
    assert (
        select_variant(_asset(), width=900, accepted_webp=False).purpose
        is VariantPurpose.RESPONSIVE_FALLBACK
    )


def test_nonready_asset_has_no_delivery_variant() -> None:
    with pytest.raises(MediaStateError):
        select_variant(_asset(MediaStatus.PROCESSING), width=320, accepted_webp=True)
