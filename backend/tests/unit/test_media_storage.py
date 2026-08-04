"""Secure local-storage and image-processing regression tests."""

# ruff: noqa: D103

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest
from botocore.exceptions import ClientError  # type: ignore[import-untyped]
from PIL import Image

from app.infrastructure.storage.image_processing import PillowImageProcessor
from app.infrastructure.storage.local_media import LocalMediaStorage
from app.infrastructure.storage.s3_media import S3MediaConfiguration, S3MediaStorage
from app.modules.media.domain import MediaFormat, MediaValidationError, VariantPurpose
from app.modules.media.storage import (
    MediaObjectExistsError,
    MediaObjectMissingError,
    MediaStorageError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

ASSET_ID = UUID("0198a9f4-8260-7ab1-9123-123456789abc")


class _Body:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self, maximum: int) -> bytes:
        return self._content[:maximum]

    def close(self) -> None:
        return


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, dict[str, str]]] = {}

    def put_object(self, **arguments: object) -> dict[str, object]:
        key = str(arguments["Key"])
        if key in self.objects:
            code = "PreconditionFailed"
            raise self._error(code, 412, "PutObject")
        self.objects[key] = (
            cast("bytes", arguments["Body"]),
            dict(cast("dict[str, str]", arguments["Metadata"])),
        )
        return {}

    def head_object(self, **arguments: object) -> dict[str, object]:
        key = str(arguments["Key"])
        if key not in self.objects:
            code = "NoSuchKey"
            raise self._error(code, 404, "HeadObject")
        content, metadata = self.objects[key]
        return {
            "ContentLength": len(content),
            "Metadata": metadata,
            "LastModified": datetime.now(UTC),
        }

    def get_object(self, **arguments: object) -> dict[str, object]:
        key = str(arguments["Key"])
        if key not in self.objects:
            code = "NoSuchKey"
            raise self._error(code, 404, "GetObject")
        content, _metadata = self.objects[key]
        return {"ContentLength": len(content), "Body": _Body(content)}

    def copy_object(self, **arguments: object) -> dict[str, object]:
        source = cast("dict[str, str]", arguments["CopySource"])["Key"]
        target = str(arguments["Key"])
        content, _metadata = self.objects[str(source)]
        self.objects[target] = (
            content,
            dict(cast("dict[str, str]", arguments["Metadata"])),
        )
        return {}

    def delete_object(self, **arguments: object) -> dict[str, object]:
        self.objects.pop(str(arguments["Key"]), None)
        return {}

    def list_objects_v2(self, **arguments: object) -> dict[str, object]:
        prefix = str(arguments["Prefix"])
        maximum = cast("int", arguments["MaxKeys"])
        keys = [key for key in sorted(self.objects) if key.startswith(prefix)][:maximum]
        return {
            "Contents": [{"Key": key, "Size": len(self.objects[key][0])} for key in keys],
            "IsTruncated": False,
        }

    @staticmethod
    def _error(code: str, status: int, operation: str) -> ClientError:
        return ClientError(
            {
                "Error": {"Code": code, "Message": "synthetic"},
                "ResponseMetadata": {"HTTPStatusCode": status},
            },
            operation,
        )


def _image_bytes(image_format: str, *, size: tuple[int, int] = (800, 400)) -> bytes:
    target = BytesIO()
    Image.new("RGB", size, (34, 78, 120)).save(target, format=image_format)
    return target.getvalue()


async def _chunks(content: bytes, size: int = 7) -> AsyncIterator[bytes]:
    for index in range(0, len(content), size):
        yield content[index : index + size]


@pytest.mark.asyncio
async def test_local_adapter_confines_and_promotes_private_objects(tmp_path: Path) -> None:
    storage = LocalMediaStorage((tmp_path / "media").resolve())
    source_key = f"quarantine/01/{ASSET_ID}/source.bin"
    target_key = f"originals/01/{ASSET_ID}/source.png"
    content = _image_bytes("PNG")

    written = await storage.write_quarantine(
        source_key, _chunks(content), maximum_bytes=len(content)
    )
    assert written.checksum_sha256 == hashlib.sha256(content).hexdigest()
    promoted = await storage.promote(source_key, target_key)
    assert promoted.checksum_sha256 == written.checksum_sha256
    assert await storage.stat(source_key) is None
    assert await storage.read(target_key, maximum_bytes=len(content)) == content


@pytest.mark.asyncio
async def test_local_adapter_removes_partial_over_limit_quarantine(tmp_path: Path) -> None:
    storage = LocalMediaStorage((tmp_path / "media").resolve())
    key = f"quarantine/01/{ASSET_ID}/source.bin"
    with pytest.raises(MediaStorageError):
        await storage.write_quarantine(key, _chunks(b"too large"), maximum_bytes=3)
    assert await storage.stat(key) is None


@pytest.mark.asyncio
async def test_local_adapter_refuses_immutable_variant_overwrite(tmp_path: Path) -> None:
    storage = LocalMediaStorage((tmp_path / "media").resolve())
    key = f"variants/01/{ASSET_ID}/responsive_webp-320.webp"
    content = b"safe rendition"
    checksum = hashlib.sha256(content).hexdigest()
    await storage.put_immutable(key, content, checksum_sha256=checksum)
    with pytest.raises(MediaObjectExistsError):
        await storage.put_immutable(key, content, checksum_sha256=checksum)


@pytest.mark.asyncio
async def test_processor_creates_only_stripped_closed_variants() -> None:
    processor = PillowImageProcessor()
    result = await processor.process(_image_bytes("JPEG"), declared_content_type="image/jpeg")
    assert result.detected_format is MediaFormat.JPEG
    assert {item.width for item in result.variants} == {320, 640}
    assert {item.purpose for item in result.variants} == {
        VariantPurpose.RESPONSIVE_WEBP,
        VariantPurpose.RESPONSIVE_FALLBACK,
    }
    for variant in result.variants:
        with Image.open(BytesIO(variant.content)) as decoded:
            assert not decoded.getexif()
            assert "icc_profile" not in decoded.info


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "declared", "code"),
    [
        (b"<svg><script>alert(1)</script></svg>", "image/svg+xml", "unsupported_format"),
        (_image_bytes("PNG") + b"<script>", "image/png", "invalid_container"),
        (_image_bytes("JPEG"), "image/png", "content_type_mismatch"),
    ],
)
async def test_processor_rejects_unsupported_polyglot_and_mismatch(
    content: bytes, declared: str, code: str
) -> None:
    with pytest.raises(MediaValidationError) as captured:
        await PillowImageProcessor().process(content, declared_content_type=declared)
    assert captured.value.code == code


def test_s3_configuration_rejects_http_and_incomplete_kms() -> None:
    base = S3MediaConfiguration(
        endpoint_url="http://object.example.test",
        region="eu-test-1",
        bucket="private-media-test",
        managed_prefix="upw/media/",
        auth_source="workload_identity",
        encryption_mode="AES256",
        kms_key_id=None,
        connect_timeout_seconds=2.0,
        read_timeout_seconds=5.0,
    )
    with pytest.raises(ValueError, match="invalid private S3 endpoint"):
        base.validate()
    with pytest.raises(ValueError, match="KMS key requirements"):
        replace(
            base,
            endpoint_url="https://object.example.test",
            encryption_mode="aws:kms",
        ).validate()


@pytest.mark.asyncio
async def test_s3_adapter_matches_private_immutable_object_contract() -> None:
    configuration = S3MediaConfiguration(
        endpoint_url="https://object.example.test",
        region="eu-test-1",
        bucket="private-media-test",
        managed_prefix="upw/media/",
        auth_source="workload_identity",
        encryption_mode="AES256",
        kms_key_id=None,
        connect_timeout_seconds=2.0,
        read_timeout_seconds=5.0,
    )
    client = _FakeS3Client()
    storage = S3MediaStorage(configuration, client=client)
    source = f"quarantine/01/{ASSET_ID}/source.bin"
    target = f"originals/01/{ASSET_ID}/source.png"
    content = _image_bytes("PNG")

    written = await storage.write_quarantine(source, _chunks(content), maximum_bytes=len(content))
    promoted = await storage.promote(source, target)
    assert promoted.checksum_sha256 == written.checksum_sha256
    assert await storage.stat(source) is None
    assert await storage.read(target, maximum_bytes=len(content)) == content
    objects, cursor = await storage.list_managed("originals/", cursor=None, limit=100)
    assert [item.key for item in objects] == [target]
    assert cursor is None
    await storage.delete(target)
    await storage.delete(target)
    assert await storage.stat(target) is None


def test_local_adapter_rejects_relative_and_linked_roots(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute"):
        LocalMediaStorage(Path("relative-media"))
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory links require additional privileges on this host")
    with pytest.raises(ValueError, match="must not be a link"):
        LocalMediaStorage(link)


async def test_local_adapter_closed_error_and_reconciliation_contracts(tmp_path: Path) -> None:
    storage = LocalMediaStorage((tmp_path / "media-errors").resolve())
    quarantine = f"quarantine/01/{ASSET_ID}/source.bin"
    original = f"originals/01/{ASSET_ID}/source.png"
    variant = f"variants/01/{ASSET_ID}/responsive_webp-320.webp"

    with pytest.raises(MediaStorageError):
        await storage.write_quarantine(quarantine, _chunks(b""), maximum_bytes=10)
    with pytest.raises(MediaStorageError):
        await storage.put_immutable(variant, b"content", checksum_sha256="0" * 64)
    with pytest.raises(MediaObjectMissingError):
        await storage.promote(quarantine, original)

    await storage.write_quarantine(quarantine, _chunks(b"source"), maximum_bytes=10)
    await storage.put_immutable(
        variant, b"variant", checksum_sha256=hashlib.sha256(b"variant").hexdigest()
    )
    with pytest.raises(MediaStorageError):
        await storage.read(variant, maximum_bytes=2)
    await storage.delete("variants/01/00000000-0000-7000-8000-000000000000/missing.webp")
    for prefix, limit in (("private/", 1), ("variants/", 0), ("variants/", 1001)):
        with pytest.raises(MediaStorageError):
            await storage.list_managed(prefix, cursor=None, limit=limit)
    first, cursor = await storage.list_managed("variants/", cursor=None, limit=1)
    assert len(first) == 1
    assert cursor is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"region": ""}, "region or bucket"),
        ({"managed_prefix": "INVALID"}, "managed S3 prefix"),
        ({"auth_source": "static-secret"}, "auth source"),
        ({"encryption_mode": "none"}, "encryption mode"),
        ({"connect_timeout_seconds": 0}, "timeouts must be positive"),
    ],
)
def test_s3_configuration_rejects_every_unsafe_dimension(
    changes: dict[str, object], message: str
) -> None:
    base = S3MediaConfiguration(
        endpoint_url="https://object.example.test",
        region="eu-test-1",
        bucket="private-media-test",
        managed_prefix="upw/media/",
        auth_source="environment",
        encryption_mode="AES256",
        kms_key_id=None,
        connect_timeout_seconds=2.0,
        read_timeout_seconds=5.0,
    )
    with pytest.raises(ValueError, match=message):
        replace(base, **changes).validate()  # type: ignore[arg-type]


async def test_s3_adapter_reports_missing_and_bounded_reads() -> None:
    configuration = S3MediaConfiguration(
        endpoint_url="https://object.example.test",
        region="eu-test-1",
        bucket="private-media-test",
        managed_prefix="upw/media/",
        auth_source="environment",
        encryption_mode="AES256",
        kms_key_id=None,
        connect_timeout_seconds=2.0,
        read_timeout_seconds=5.0,
    )
    client = _FakeS3Client()
    storage = S3MediaStorage(configuration, client=client)
    missing = f"variants/01/{ASSET_ID}/responsive_webp-320.webp"
    assert await storage.stat(missing) is None
    with pytest.raises(MediaObjectMissingError):
        await storage.read(missing, maximum_bytes=10)
    client.objects[f"upw/media/{missing}"] = (b"too large", {"sha256": "0" * 64})
    with pytest.raises(MediaStorageError):
        await storage.read(missing, maximum_bytes=2)
