"""Explicit private-media adapter composition tests."""

# ruff: noqa: D103

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from app.config import MediaStorageKind, Settings
from app.infrastructure.storage import media_factory
from app.infrastructure.storage.local_media import LocalMediaStorage
from app.infrastructure.storage.media_factory import build_media_storage


def _settings(**changes: object) -> Settings:
    values = {
        "media_storage_kind": None,
        "media_local_root": None,
        "media_s3_endpoint_url": None,
        "media_s3_region": None,
        "media_s3_bucket": None,
        "media_s3_managed_prefix": None,
        "media_s3_auth_source": None,
        "media_s3_encryption": None,
        "media_s3_connect_timeout_seconds": None,
        "media_s3_read_timeout_seconds": None,
        "media_s3_kms_key_id": None,
        **changes,
    }
    return cast("Settings", SimpleNamespace(**values))


def test_media_factory_is_disabled_without_explicit_selection() -> None:
    assert build_media_storage(_settings()) is None


def test_media_factory_composes_local_adapter(tmp_path: Path) -> None:
    storage = build_media_storage(
        _settings(media_storage_kind=MediaStorageKind.LOCAL, media_local_root=tmp_path)
    )
    assert isinstance(storage, LocalMediaStorage)


def test_media_factory_rejects_incomplete_adapter_configuration() -> None:
    with pytest.raises(RuntimeError, match="local media root"):
        build_media_storage(_settings(media_storage_kind=MediaStorageKind.LOCAL))
    with pytest.raises(RuntimeError, match="S3 media configuration"):
        build_media_storage(_settings(media_storage_kind=MediaStorageKind.S3_COMPATIBLE))


def test_media_factory_composes_s3_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    auth = SimpleNamespace(value="environment")
    encryption = SimpleNamespace(value="AES256")
    captured: list[object] = []

    class _S3Storage:
        def __init__(self, configuration: object) -> None:
            captured.append(configuration)

    monkeypatch.setattr(media_factory, "S3MediaStorage", _S3Storage)
    storage = build_media_storage(
        _settings(
            media_storage_kind=MediaStorageKind.S3_COMPATIBLE,
            media_s3_endpoint_url="https://objects.example.test",
            media_s3_region="eu-west-3",
            media_s3_bucket="portfolio-private",
            media_s3_managed_prefix="managed/",
            media_s3_auth_source=auth,
            media_s3_encryption=encryption,
            media_s3_connect_timeout_seconds=3.0,
            media_s3_read_timeout_seconds=10.0,
        )
    )
    assert storage is not None
    assert len(captured) == 1
