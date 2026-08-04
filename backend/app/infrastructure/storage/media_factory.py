"""Fail-closed composition of the explicitly selected private media adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import MediaStorageKind, Settings
from app.infrastructure.storage.local_media import LocalMediaStorage
from app.infrastructure.storage.s3_media import S3MediaConfiguration, S3MediaStorage

if TYPE_CHECKING:
    from app.modules.media.ports import MediaStoragePort


def build_media_storage(settings: Settings) -> MediaStoragePort | None:
    """Compose only the selected adapter after settings validation succeeds."""
    if settings.media_storage_kind is None:
        return None
    if settings.media_storage_kind is MediaStorageKind.LOCAL:
        if settings.media_local_root is None:
            msg = "validated local media root is unavailable"
            raise RuntimeError(msg)
        return LocalMediaStorage(settings.media_local_root)
    endpoint = settings.media_s3_endpoint_url
    region = settings.media_s3_region
    bucket = settings.media_s3_bucket
    prefix = settings.media_s3_managed_prefix
    auth_source = settings.media_s3_auth_source
    encryption = settings.media_s3_encryption
    connect_timeout = settings.media_s3_connect_timeout_seconds
    read_timeout = settings.media_s3_read_timeout_seconds
    if (
        endpoint is None
        or region is None
        or bucket is None
        or prefix is None
        or auth_source is None
        or encryption is None
        or connect_timeout is None
        or read_timeout is None
    ):
        msg = "validated S3 media configuration is unavailable"
        raise RuntimeError(msg)
    return S3MediaStorage(
        S3MediaConfiguration(
            endpoint_url=endpoint,
            region=region,
            bucket=bucket,
            managed_prefix=prefix,
            auth_source=auth_source.value,
            encryption_mode=encryption.value,
            kms_key_id=settings.media_s3_kms_key_id,
            connect_timeout_seconds=connect_timeout,
            read_timeout_seconds=read_timeout,
        )
    )
