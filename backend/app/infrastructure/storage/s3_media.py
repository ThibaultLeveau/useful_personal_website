"""Strict private S3-compatible media adapter with injected provider configuration."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from app.modules.media.domain import validate_managed_key
from app.modules.media.storage import (
    MediaObjectExistsError,
    MediaObjectMissingError,
    MediaObjectTooLargeError,
    MediaStorageError,
    StoredObject,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_PREFIX_PATTERN = re.compile(r"^[a-z0-9][a-z0-9/-]{0,63}/$")
MAXIMUM_LIST_PAGE = 1_000


@dataclass(frozen=True, slots=True)
class S3MediaConfiguration:
    """Explicit production-owned S3-compatible requirements."""

    endpoint_url: str
    region: str
    bucket: str
    managed_prefix: str
    auth_source: str
    encryption_mode: str
    kms_key_id: str | None
    connect_timeout_seconds: float
    read_timeout_seconds: float

    def validate(self) -> None:
        """Fail closed without inventing provider, security, or identity defaults."""
        endpoint = urlsplit(self.endpoint_url)
        if (
            endpoint.scheme != "https"
            or not endpoint.hostname
            or endpoint.username is not None
            or endpoint.password is not None
            or endpoint.query
            or endpoint.fragment
        ):
            message = "invalid private S3 endpoint"
            raise ValueError(message)
        if not self.region or not _BUCKET_PATTERN.fullmatch(self.bucket):
            message = "invalid S3 region or bucket"
            raise ValueError(message)
        if not _PREFIX_PATTERN.fullmatch(self.managed_prefix):
            message = "invalid managed S3 prefix"
            raise ValueError(message)
        if self.auth_source not in {"workload_identity", "environment"}:
            message = "invalid S3 auth source"
            raise ValueError(message)
        if self.encryption_mode not in {"AES256", "aws:kms"}:
            message = "invalid S3 encryption mode"
            raise ValueError(message)
        if (self.encryption_mode == "aws:kms") != bool(self.kms_key_id):
            message = "KMS key requirements are incomplete"
            raise ValueError(message)
        if self.connect_timeout_seconds <= 0 or self.read_timeout_seconds <= 0:
            message = "S3 timeouts must be positive"
            raise ValueError(message)


class S3MediaStorage:
    """Private bucket adapter; browser-facing credentials and public ACLs are absent."""

    def __init__(
        self, configuration: S3MediaConfiguration, *, client: object | None = None
    ) -> None:
        """Validate explicit configuration and build a bounded SDK client."""
        configuration.validate()
        self._configuration = configuration
        self._client = client or boto3.client(
            "s3",
            endpoint_url=configuration.endpoint_url,
            region_name=configuration.region,
            config=Config(
                connect_timeout=configuration.connect_timeout_seconds,
                read_timeout=configuration.read_timeout_seconds,
                retries={"max_attempts": 3, "mode": "adaptive"},
                signature_version="s3v4",
            ),
        )

    async def write_quarantine(
        self, key: str, chunks: AsyncIterator[bytes], *, maximum_bytes: int
    ) -> StoredObject:
        """Buffer only the bounded request and conditionally create a private object."""
        self._qualified_key(key, required_namespace="quarantine")
        content = BytesIO()
        digest = hashlib.sha256()
        size = 0
        async for chunk in chunks:
            if not chunk:
                continue
            size += len(chunk)
            if size > maximum_bytes:
                raise MediaObjectTooLargeError
            digest.update(chunk)
            content.write(chunk)
        if size == 0:
            raise MediaStorageError
        checksum = digest.hexdigest()
        await self._put(key, content.getvalue(), checksum)
        return StoredObject(key, size, checksum, datetime.now(UTC))

    async def put_immutable(
        self, key: str, content: bytes, *, checksum_sha256: str
    ) -> StoredObject:
        """Conditionally create a checksum-bound private rendition."""
        self._qualified_key(key, required_namespace="variants")
        if hashlib.sha256(content).hexdigest() != checksum_sha256:
            raise MediaStorageError
        await self._put(key, content, checksum_sha256)
        return StoredObject(key, len(content), checksum_sha256, datetime.now(UTC))

    async def promote(self, source_key: str, target_key: str) -> StoredObject:
        """Copy quarantine to an immutable private original and remove the source."""
        source = self._qualified_key(source_key, required_namespace="quarantine")
        target = self._qualified_key(target_key, required_namespace="originals")
        if await self.stat(target_key) is not None:
            raise MediaObjectExistsError
        source_facts = await self.stat(source_key)
        if source_facts is None:
            raise MediaObjectMissingError
        arguments = {
            "Bucket": self._configuration.bucket,
            "Key": target,
            "CopySource": {"Bucket": self._configuration.bucket, "Key": source},
            "MetadataDirective": "REPLACE",
            "Metadata": {"sha256": source_facts.checksum_sha256},
            **self._encryption_arguments(),
        }
        await self._call("copy_object", **arguments)
        promoted = await self.stat(target_key)
        if promoted is None or promoted.checksum_sha256 != source_facts.checksum_sha256:
            await self.delete(target_key)
            raise MediaStorageError
        await self.delete(source_key)
        return promoted

    async def read(self, key: str, *, maximum_bytes: int) -> bytes:
        """Read one exact managed object with a response-size cap."""
        response = await self._call(
            "get_object", Bucket=self._configuration.bucket, Key=self._qualified_key(key)
        )
        declared = int(response.get("ContentLength", maximum_bytes + 1))
        if declared > maximum_bytes:
            raise MediaStorageError
        try:
            content = await asyncio.to_thread(response["Body"].read, maximum_bytes + 1)
        finally:
            await asyncio.to_thread(response["Body"].close)
        if len(content) > maximum_bytes:
            raise MediaStorageError
        return bytes(content)

    async def stat(self, key: str) -> StoredObject | None:
        """Return checksum metadata for one managed object."""
        try:
            response = await self._call(
                "head_object", Bucket=self._configuration.bucket, Key=self._qualified_key(key)
            )
        except MediaObjectMissingError:
            return None
        checksum = str(response.get("Metadata", {}).get("sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise MediaStorageError
        modified = response.get("LastModified")
        if not isinstance(modified, datetime):
            raise MediaStorageError
        return StoredObject(key, int(response["ContentLength"]), checksum, modified)

    async def delete(self, key: str) -> None:
        """Idempotently delete one exact managed object."""
        await self._call(
            "delete_object", Bucket=self._configuration.bucket, Key=self._qualified_key(key)
        )

    async def list_managed(
        self, prefix: str, *, cursor: str | None, limit: int
    ) -> tuple[tuple[StoredObject, ...], str | None]:
        """List one closed managed namespace page for reconciliation."""
        if (
            prefix not in {"quarantine/", "originals/", "variants/"}
            or not 1 <= limit <= MAXIMUM_LIST_PAGE
        ):
            raise MediaStorageError
        arguments: dict[str, object] = {
            "Bucket": self._configuration.bucket,
            "Prefix": f"{self._configuration.managed_prefix}{prefix}",
            "MaxKeys": limit,
        }
        if cursor is not None:
            arguments["ContinuationToken"] = cursor
        response = await self._call("list_objects_v2", **arguments)
        objects: list[StoredObject] = []
        for item in response.get("Contents", []):
            qualified = str(item["Key"])
            key = qualified.removeprefix(self._configuration.managed_prefix)
            facts = await self.stat(key)
            if facts is not None:
                objects.append(facts)
        next_cursor = (
            str(response["NextContinuationToken"])
            if response.get("IsTruncated") and response.get("NextContinuationToken")
            else None
        )
        return tuple(objects), next_cursor

    async def _put(self, key: str, content: bytes, checksum: str) -> None:
        arguments = {
            "Bucket": self._configuration.bucket,
            "Key": self._qualified_key(key),
            "Body": content,
            "ContentLength": len(content),
            "ChecksumSHA256": base64.b64encode(bytes.fromhex(checksum)).decode("ascii"),
            "Metadata": {"sha256": checksum},
            "IfNoneMatch": "*",
            **self._encryption_arguments(),
        }
        await self._call("put_object", **arguments)

    def _qualified_key(self, key: str, *, required_namespace: str | None = None) -> str:
        validate_managed_key(key)
        if required_namespace is not None and not key.startswith(f"{required_namespace}/"):
            raise MediaStorageError
        return f"{self._configuration.managed_prefix}{key}"

    def _encryption_arguments(self) -> dict[str, str]:
        arguments = {"ServerSideEncryption": self._configuration.encryption_mode}
        if self._configuration.kms_key_id is not None:
            arguments["SSEKMSKeyId"] = self._configuration.kms_key_id
        return arguments

    async def _call(self, operation: str, **arguments: object) -> dict[str, Any]:
        try:
            result = await asyncio.to_thread(
                cast("Any", getattr(self._client, operation)), **arguments
            )
        except ClientError as error:
            status = int(error.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0))
            code = str(error.response.get("Error", {}).get("Code", ""))
            if status == HTTPStatus.NOT_FOUND or code in {"NoSuchKey", "NotFound"}:
                raise MediaObjectMissingError from error
            if status == HTTPStatus.PRECONDITION_FAILED or code in {
                "PreconditionFailed",
                "ConditionalRequestConflict",
            }:
                raise MediaObjectExistsError from error
            raise MediaStorageError from error
        except BotoCoreError as error:
            raise MediaStorageError from error
        if not isinstance(result, dict):
            raise MediaStorageError
        return result
