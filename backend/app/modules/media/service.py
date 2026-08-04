"""Application orchestration for secure media ingestion and lifecycle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.common.application.idempotency import (
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain.actors import ActorContext
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7
from app.modules.media.domain import (
    MAXIMUM_UPLOAD_BYTES,
    MediaAsset,
    MediaStateError,
    MediaStatus,
    MediaUsage,
    MediaValidationError,
    MediaVariant,
    ProcessedImage,
    safe_display_name,
    select_variant,
    validate_display_name,
)
from app.modules.media.storage import MediaObjectTooLargeError

MAXIMUM_MEDIA_PAGE_SIZE = 100

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable
    from datetime import datetime
    from uuid import UUID

    from app.modules.media.ports import (
        ImageProcessorPort,
        MediaStoragePort,
        MediaUnitOfWork,
        MediaUnitOfWorkFactory,
        PublicMediaEligibilityPort,
    )


class MediaNotFoundError(Exception):
    """An asset is absent or deliberately indistinguishable from absent."""


class MediaConflictError(Exception):
    """A version, lifecycle, or active-usage conflict blocked mutation."""


class MediaUploadError(Exception):
    """A controlled upload failure with a stable non-reflective reason."""

    def __init__(self, code: str) -> None:
        """Retain one stable non-reflective reason token."""
        super().__init__("media upload failed")
        self.code = code


class MediaIdempotencyRejectedError(Exception):
    """An upload command was not newly admitted or safely replayable."""

    def __init__(self, decision: IdempotencyDecisionType) -> None:
        """Retain only the closed idempotency decision token."""
        super().__init__("media idempotency admission rejected")
        self.decision = decision


@dataclass(frozen=True, slots=True)
class MediaUploadCommand:
    """Bounded streamed upload facts; filename is display-only."""

    chunks: AsyncIterator[bytes]
    filename: str | None
    declared_content_type: str | None
    actor_id: UUID
    idempotency_key: str
    request_id: str


class MediaService:
    """Coordinate DB state and private object effects with visible compensation."""

    def __init__(
        self,
        uow_factory: MediaUnitOfWorkFactory,
        storage: MediaStoragePort,
        processor: ImageProcessorPort,
        eligibility: PublicMediaEligibilityPort,
        *,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind replaceable media dependencies and an opaque ID source."""
        self._uow_factory = uow_factory
        self._storage = storage
        self._processor = processor
        self._eligibility = eligibility
        self._id_factory = id_factory

    async def upload(  # noqa: PLR0915 - staged effects require explicit compensation.
        self, command: MediaUploadCommand
    ) -> MediaAsset:
        """Quarantine, decode, re-encode, promote, verify, and only then mark ready."""
        asset_id = self._id_factory()
        shard = asset_id.hex[:2]
        quarantine_key = f"quarantine/{shard}/{asset_id}/source.bin"
        try:
            quarantined = await self._storage.write_quarantine(
                quarantine_key,
                command.chunks,
                maximum_bytes=MAXIMUM_UPLOAD_BYTES,
            )
        except MediaObjectTooLargeError as error:
            code = "invalid_size"
            raise MediaUploadError(code) from error
        except Exception as error:
            code = "quarantine_write_failed"
            raise MediaUploadError(code) from error

        now = await self._database_now()
        asset = MediaAsset(
            id=asset_id,
            status=MediaStatus.QUARANTINED,
            display_name=safe_display_name(command.filename),
            detected_format=None,
            width=None,
            height=None,
            byte_size=quarantined.byte_size,
            checksum_sha256=quarantined.checksum_sha256,
            original_key=None,
            quarantine_key=quarantine_key,
            variants=(),
            created_by=command.actor_id,
            created_at=now,
            updated_at=now,
            version=1,
        )
        actor = ActorContext.administrator(command.actor_id)
        canonical_payload = json.dumps(
            {
                "checksum_sha256": quarantined.checksum_sha256,
                "declared_content_type": command.declared_content_type,
                "display_name": asset.display_name,
                "byte_size": quarantined.byte_size,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        async with self._uow_factory() as uow:
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=actor,
                    route="/api/v1/admin/media",
                    key=command.idempotency_key,
                    canonical_payload=canonical_payload,
                    requested_at=now,
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                outcome = decision.outcome
                replay = (
                    None
                    if outcome is None or outcome.resource_id is None
                    else await uow.media.get(outcome.resource_id)
                )
                if replay is None or replay.status is not MediaStatus.READY:
                    raise MediaIdempotencyRejectedError(decision.decision)
                await self._storage.delete(quarantine_key)
                return replay
            if decision.decision is not IdempotencyDecisionType.ACQUIRED:
                await self._storage.delete(quarantine_key)
                raise MediaIdempotencyRejectedError(decision.decision)
            if decision.record_id is None:
                raise MediaIdempotencyRejectedError(decision.decision)
            idempotency_record_id = decision.record_id
            await uow.media.add(asset)
            self._audit(
                uow,
                event_type="media.upload.accepted",
                actor_id=command.actor_id,
                resource_id=asset_id,
                request_id=command.request_id,
                occurred_at=now,
                outcome=AuditOutcome.SUCCESS,
                metadata={"byte_size": quarantined.byte_size, "status": "quarantined"},
            )
            await uow.commit()

        try:
            async with self._uow_factory() as uow:
                await uow.media.set_processing(
                    asset_id,
                    now=await uow.media.database_now(),
                )
                await uow.commit()
            source = await self._storage.read(
                quarantine_key,
                maximum_bytes=MAXIMUM_UPLOAD_BYTES,
            )
            image = await self._processor.process(
                source,
                declared_content_type=command.declared_content_type,
            )
            original_key = f"originals/{shard}/{asset_id}/source.{image.detected_format.extension}"
            promoted = await self._storage.promote(quarantine_key, original_key)
            if promoted.checksum_sha256 != image.checksum_sha256:
                self._raise_integrity_error("original_integrity_failed")
            variants = await self._store_variants(asset_id, image, now=now)
            await self._verify_ready_objects(original_key, image, variants)
            async with self._uow_factory() as uow:
                ready = await uow.media.set_ready(
                    asset_id,
                    image=image,
                    original_key=original_key,
                    variants=variants,
                    now=await uow.media.database_now(),
                )
                await uow.idempotency.complete(
                    idempotency_record_id,
                    IdempotencyOutcome(
                        response_status=201,
                        result_code="media.uploaded",
                        resource_type="media_asset",
                        resource_id=ready.id,
                        resource_version=ready.version,
                    ),
                    completed_at=await uow.media.database_now(),
                )
                self._audit(
                    uow,
                    event_type="media.upload.ready",
                    actor_id=command.actor_id,
                    resource_id=ready.id,
                    request_id=command.request_id,
                    occurred_at=ready.updated_at,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={
                        "format": image.detected_format.value,
                        "width": image.width,
                        "height": image.height,
                        "byte_size": image.byte_size,
                        "variant_count": len(variants),
                    },
                )
                await uow.commit()
            return ready  # noqa: TRY300 - success follows the final committed transaction.
        except Exception as error:
            await self._record_failure(
                asset_id,
                error,
                actor_id=command.actor_id,
                request_id=command.request_id,
            )
            if isinstance(error, MediaUploadError):
                raise
            code = getattr(error, "code", "processing_failed")
            raise MediaUploadError(str(code)) from error

    async def get(self, asset_id: UUID) -> MediaAsset:
        """Return one administrator-authorized asset projection."""
        async with self._uow_factory() as uow:
            asset = await uow.media.get(asset_id)
        if asset is None or asset.status is MediaStatus.DELETED:
            raise MediaNotFoundError
        return asset

    async def list(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
    ) -> tuple[tuple[MediaAsset, ...], int]:
        """List safe asset facts within a bounded page."""
        if offset < 0 or limit < 1 or limit > MAXIMUM_MEDIA_PAGE_SIZE:
            raise MediaValidationError(path="pagination", code="invalid_pagination")
        async with self._uow_factory() as uow:
            return await uow.media.list(offset=offset, limit=limit, search=search)

    async def rename(
        self,
        asset_id: UUID,
        *,
        display_name: str,
        expected_version: int,
        actor_id: UUID,
        request_id: str,
    ) -> MediaAsset:
        """Update display-only metadata under optimistic concurrency."""
        value = validate_display_name(display_name)
        try:
            async with self._uow_factory() as uow:
                asset = await uow.media.rename(
                    asset_id,
                    display_name=value,
                    expected_version=expected_version,
                    now=await uow.media.database_now(),
                )
                self._audit(
                    uow,
                    event_type="media.metadata.updated",
                    actor_id=actor_id,
                    resource_id=asset.id,
                    request_id=request_id,
                    occurred_at=asset.updated_at,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={"version": asset.version, "fields": "display_name"},
                )
                await uow.commit()
                return asset
        except MediaStateError as error:
            raise MediaConflictError from error

    async def delete(
        self,
        asset_id: UUID,
        *,
        expected_version: int,
        actor_id: UUID,
        request_id: str,
    ) -> None:
        """Tombstone only unused content, then remove managed objects idempotently."""
        try:
            async with self._uow_factory() as uow:
                asset = await uow.media.begin_delete(
                    asset_id,
                    expected_version=expected_version,
                    now=await uow.media.database_now(),
                )
                self._audit(
                    uow,
                    event_type="media.delete.requested",
                    actor_id=actor_id,
                    resource_id=asset.id,
                    request_id=request_id,
                    occurred_at=asset.updated_at,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={"version": asset.version},
                )
                await uow.commit()
        except MediaStateError as error:
            raise MediaConflictError from error

        keys = (
            *(item.storage_key for item in asset.variants),
            *((asset.original_key,) if asset.original_key else ()),
            *((asset.quarantine_key,) if asset.quarantine_key else ()),
        )
        for key in keys:
            await self._storage.delete(key)
        async with self._uow_factory() as uow:
            completed_at = await uow.media.database_now()
            await uow.media.finish_delete(asset_id, now=completed_at)
            self._audit(
                uow,
                event_type="media.delete.completed",
                actor_id=actor_id,
                resource_id=asset_id,
                request_id=request_id,
                occurred_at=completed_at,
                outcome=AuditOutcome.SUCCESS,
                metadata={"object_count": len(asset.variants) + 1},
            )
            await uow.commit()

    async def public_variant(
        self,
        asset_id: UUID,
        *,
        width: int,
        accepted_webp: bool,
    ) -> tuple[MediaVariant, bytes]:
        """Authorize through active public owner usage before reading a variant."""
        async with self._uow_factory() as uow:
            asset = await uow.media.get(asset_id)
            usages = await uow.media.list_usage(asset_id)
        eligible = False
        for usage in usages:
            if not usage.active:
                continue
            if not usage.public:
                continue
            if not await self._eligibility.is_publicly_eligible(usage):
                continue
            eligible = True
            break
        if asset is None or not eligible:
            raise MediaNotFoundError
        try:
            variant = select_variant(asset, width=width, accepted_webp=accepted_webp)
        except MediaStateError as error:
            raise MediaNotFoundError from error
        content = await self._storage.read(
            variant.storage_key,
            maximum_bytes=MAXIMUM_UPLOAD_BYTES,
        )
        return variant, content

    async def admin_variant(
        self,
        asset_id: UUID,
        *,
        width: int,
        accepted_webp: bool,
    ) -> tuple[MediaVariant, bytes]:
        """Read a stripped rendition for an already-authorized administrator."""
        asset = await self.get(asset_id)
        try:
            variant = select_variant(asset, width=width, accepted_webp=accepted_webp)
        except MediaStateError as error:
            raise MediaNotFoundError from error
        content = await self._storage.read(
            variant.storage_key,
            maximum_bytes=MAXIMUM_UPLOAD_BYTES,
        )
        return variant, content

    async def usage(self, asset_id: UUID) -> tuple[MediaUsage, ...]:
        """Return authorized safe usage facts for one visible asset."""
        await self.get(asset_id)
        async with self._uow_factory() as uow:
            return await uow.media.list_usage(asset_id)

    async def _database_now(self) -> datetime:
        async with self._uow_factory() as uow:
            return await uow.media.database_now()

    async def _store_variants(
        self,
        asset_id: UUID,
        image: ProcessedImage,
        *,
        now: datetime,
    ) -> tuple[MediaVariant, ...]:
        result = []
        shard = asset_id.hex[:2]
        for item in image.variants:
            variant_id = self._id_factory()
            key = (
                f"variants/{shard}/{asset_id}/"
                f"{item.purpose.value}-{item.width}.{item.format.extension}"
            )
            stored = await self._storage.put_immutable(
                key,
                item.content,
                checksum_sha256=item.checksum_sha256,
            )
            if stored.checksum_sha256 != item.checksum_sha256:
                self._raise_integrity_error("variant_integrity_failed")
            result.append(
                MediaVariant(
                    id=variant_id,
                    asset_id=asset_id,
                    purpose=item.purpose,
                    format=item.format,
                    width=item.width,
                    height=item.height,
                    byte_size=len(item.content),
                    checksum_sha256=item.checksum_sha256,
                    storage_key=key,
                    created_at=now,
                )
            )
        return tuple(result)

    async def _verify_ready_objects(
        self,
        original_key: str,
        image: ProcessedImage,
        variants: tuple[MediaVariant, ...],
    ) -> None:
        original = await self._storage.stat(original_key)
        if original is None or original.checksum_sha256 != image.checksum_sha256:
            self._raise_integrity_error("original_integrity_failed")
        for variant in variants:
            stored = await self._storage.stat(variant.storage_key)
            if stored is None or stored.checksum_sha256 != variant.checksum_sha256:
                self._raise_integrity_error("variant_integrity_failed")

    async def _record_failure(
        self,
        asset_id: UUID,
        error: Exception,
        *,
        actor_id: UUID,
        request_id: str,
    ) -> None:
        code = getattr(error, "code", "processing_failed")
        try:
            async with self._uow_factory() as uow:
                await uow.media.set_failed(
                    asset_id,
                    failure_code=str(code)[:64],
                    now=await uow.media.database_now(),
                )
                occurred_at = await uow.media.database_now()
                self._audit(
                    uow,
                    event_type="media.upload.failed",
                    actor_id=actor_id,
                    resource_id=asset_id,
                    request_id=request_id,
                    occurred_at=occurred_at,
                    outcome=AuditOutcome.FAILURE,
                    metadata={"reason": str(code)[:64]},
                )
                await uow.commit()
        except Exception:  # noqa: BLE001 - failure recording must not mask the primary error.
            return

    @staticmethod
    def _raise_integrity_error(code: str) -> None:
        raise MediaUploadError(code)

    def _audit(  # noqa: PLR0913 - safe audit facts are explicit.
        self,
        uow: MediaUnitOfWork,
        *,
        event_type: str,
        actor_id: UUID,
        resource_id: UUID,
        request_id: str,
        occurred_at: datetime,
        outcome: AuditOutcome,
        metadata: dict[str, str | int | bool | None],
    ) -> None:
        uow.audit.append(
            AuditEntry(
                id=self._id_factory(),
                event_type=event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=actor_id,
                actor_label_snapshot=None,
                resource_type="media_asset",
                resource_id=resource_id,
                request_id=request_id,
                occurred_at=occurred_at,
                outcome=outcome,
                ip_pseudonym=None,
                metadata=metadata,
                schema_version=1,
            )
        )


class MaterializedPublicMediaEligibility:
    """Trust only validated, transactionally materialized public owner usages."""

    async def is_publicly_eligible(self, usage: MediaUsage) -> bool:
        """Accept an active public use after its owner-role pair has been validated."""
        return usage.active and usage.public
