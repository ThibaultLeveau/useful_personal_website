"""Inward-facing media transaction, storage, processing, and owner ports."""

# Protocol signatures intentionally remain compact and adjacent.
# ruff: noqa: D102, D105

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.modules.audit.domain import AuditEntry
    from app.modules.media.domain import (
        MediaAsset,
        MediaUsage,
        MediaUse,
        MediaVariant,
        ProcessedImage,
    )


class StorageObjectPort(Protocol):
    """Safe bounded object facts."""

    @property
    def key(self) -> str: ...

    @property
    def byte_size(self) -> int: ...

    @property
    def checksum_sha256(self) -> str: ...

    @property
    def last_modified(self) -> datetime: ...


class MediaStoragePort(Protocol):
    """Private managed object operations with no SDK types crossing inward."""

    async def write_quarantine(
        self, key: str, chunks: AsyncIterator[bytes], *, maximum_bytes: int
    ) -> StorageObjectPort: ...
    async def put_immutable(
        self, key: str, content: bytes, *, checksum_sha256: str
    ) -> StorageObjectPort: ...
    async def promote(self, source_key: str, target_key: str) -> StorageObjectPort: ...
    async def read(self, key: str, *, maximum_bytes: int) -> bytes: ...
    async def stat(self, key: str) -> StorageObjectPort | None: ...
    async def delete(self, key: str) -> None: ...
    async def list_managed(
        self, prefix: str, *, cursor: str | None, limit: int
    ) -> tuple[tuple[StorageObjectPort, ...], str | None]: ...


class ImageProcessorPort(Protocol):
    """Bounded decoder/re-encoder boundary."""

    async def process(
        self, content: bytes, *, declared_content_type: str | None
    ) -> ProcessedImage: ...


class MediaRepositoryPort(Protocol):
    """Asset, variant, usage, and reconciliation persistence."""

    async def database_now(self) -> datetime: ...
    async def add(self, asset: MediaAsset) -> None: ...
    async def get(self, asset_id: UUID, *, for_update: bool = False) -> MediaAsset | None: ...
    async def list(
        self, *, offset: int, limit: int, search: str | None = None
    ) -> tuple[tuple[MediaAsset, ...], int]: ...
    async def set_processing(self, asset_id: UUID, *, now: datetime) -> None: ...
    async def set_ready(
        self,
        asset_id: UUID,
        *,
        image: ProcessedImage,
        original_key: str,
        variants: tuple[MediaVariant, ...],
        now: datetime,
    ) -> MediaAsset: ...
    async def set_failed(self, asset_id: UUID, *, failure_code: str, now: datetime) -> None: ...
    async def rename(
        self, asset_id: UUID, *, display_name: str, expected_version: int, now: datetime
    ) -> MediaAsset: ...
    async def list_usage(self, asset_id: UUID) -> tuple[MediaUsage, ...]: ...
    async def replace_owner_usages(
        self, *, owner_type: str, owner_id: UUID, usages: tuple[MediaUse, ...], now: datetime
    ) -> None: ...
    async def begin_delete(
        self, asset_id: UUID, *, expected_version: int, now: datetime
    ) -> MediaAsset: ...
    async def finish_delete(self, asset_id: UUID, *, now: datetime) -> None: ...
    async def known_storage_keys(self) -> tuple[str, ...]: ...


class MediaUnitOfWork(Protocol):
    """One atomic media database transaction."""

    media: MediaRepositoryPort
    idempotency: IdempotencyStore
    audit: AuditPort

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...


class MediaUnitOfWorkFactory(Protocol):
    """Create a fresh media transaction."""

    def __call__(self) -> MediaUnitOfWork: ...


class AuditPort(Protocol):
    """Insert-only controlled media audit dependency."""

    def append(self, entry: AuditEntry) -> None: ...


class PublicMediaEligibilityPort(Protocol):
    """Owner-controlled public-effective usage decision."""

    async def is_publicly_eligible(self, usage: MediaUsage) -> bool: ...
