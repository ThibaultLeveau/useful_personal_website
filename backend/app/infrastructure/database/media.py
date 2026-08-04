"""SQLAlchemy records and PostgreSQL repository for private image media."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy runtime annotation.
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - SQLAlchemy runtime annotation.

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.media.domain import (
    MAXIMUM_ALT_TEXT_LENGTH,
    MAXIMUM_CAPTION_LENGTH,
    MAXIMUM_DISPLAY_NAME_LENGTH,
    MediaAsset,
    MediaFormat,
    MediaOwnerType,
    MediaStateError,
    MediaStatus,
    MediaUsage,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
    MediaVariant,
    ProcessedImage,
    VariantPurpose,
    validate_media_use,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession


class MediaBase(DeclarativeBase):
    """SQLAlchemy registry owned by the media slice."""


class MediaAssetRecord(MediaBase):
    """Stable logical asset and private-original state."""

    __tablename__ = "media_asset"
    __table_args__ = (
        CheckConstraint(
            "status IN ('quarantined','processing','ready','failed','deleting','deleted')",
            name="media_asset_status_catalog",
        ),
        CheckConstraint(
            "detected_format IS NULL OR detected_format IN ('jpeg','png','webp')",
            name="media_asset_format_catalog",
        ),
        CheckConstraint("version > 0", name="media_asset_positive_version"),
        CheckConstraint(
            f"length(display_name) BETWEEN 1 AND {MAXIMUM_DISPLAY_NAME_LENGTH}",
            name="media_asset_display_name_bounds",
        ),
        CheckConstraint(
            "width IS NULL OR (width BETWEEN 1 AND 6000)",
            name="media_asset_width_bounds",
        ),
        CheckConstraint(
            "height IS NULL OR (height BETWEEN 1 AND 6000)",
            name="media_asset_height_bounds",
        ),
        CheckConstraint(
            "byte_size IS NULL OR (byte_size BETWEEN 1 AND 10485760)",
            name="media_asset_byte_size_bounds",
        ),
        CheckConstraint(
            "checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="media_asset_checksum_shape",
        ),
        CheckConstraint(
            "(status <> 'ready') OR "
            "(detected_format IS NOT NULL AND width IS NOT NULL AND height IS NOT NULL "
            "AND byte_size IS NOT NULL AND checksum_sha256 IS NOT NULL "
            "AND original_key IS NOT NULL AND quarantine_key IS NULL)",
            name="media_asset_ready_shape",
        ),
        CheckConstraint(
            "(status IN ('deleting','deleted')) = (deleted_at IS NOT NULL)",
            name="media_asset_tombstone_shape",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["administrator.id"],
            name="fk_media_asset_created_by_administrator",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_media_asset_admin_order", "created_at", "id"),
        Index("ix_media_asset_status_updated", "status", "updated_at", "id"),
        Index("ix_media_asset_checksum", "checksum_sha256"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(MAXIMUM_DISPLAY_NAME_LENGTH), nullable=False)
    detected_format: Mapped[str | None] = mapped_column(String(8))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int | None] = mapped_column(Integer)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    original_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    quarantine_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MediaVariantRecord(MediaBase):
    """Immutable registered stripped rendition."""

    __tablename__ = "media_variant"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('responsive_webp','responsive_fallback')",
            name="media_variant_purpose_catalog",
        ),
        CheckConstraint("format IN ('jpeg','png','webp')", name="media_variant_format_catalog"),
        CheckConstraint(
            "width BETWEEN 1 AND 6000 AND height BETWEEN 1 AND 6000",
            name="media_variant_dimension_bounds",
        ),
        CheckConstraint("byte_size BETWEEN 1 AND 10485760", name="media_variant_byte_size_bounds"),
        CheckConstraint("checksum_sha256 ~ '^[0-9a-f]{64}$'", name="media_variant_checksum_shape"),
        UniqueConstraint("asset_id", "purpose", "width", name="uq_media_variant_catalog"),
        UniqueConstraint("storage_key", name="uq_media_variant_storage_key"),
        Index("ix_media_variant_asset_width", "asset_id", "width", "purpose"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="RESTRICT"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(24), nullable=False)
    format: Mapped[str] = mapped_column(String(8), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MediaUsageRecord(MediaBase):
    """Materialized contextual usage owned by an accepted aggregate."""

    __tablename__ = "media_usage"
    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('profile','website_settings','project_revision',"
            "'blog_post_revision','page_block')",
            name="media_usage_owner_catalog",
        ),
        CheckConstraint(
            "role IN ('profile_image','site_logo','site_favicon','site_social_image',"
            "'project_cover','project_screenshot','blog_cover','page_primary')",
            name="media_usage_role_catalog",
        ),
        CheckConstraint(
            "purpose IN ('meaningful','decorative')", name="media_usage_purpose_catalog"
        ),
        CheckConstraint("position >= 0", name="media_usage_nonnegative_position"),
        CheckConstraint(
            "focal_x BETWEEN 0 AND 100 AND focal_y BETWEEN 0 AND 100",
            name="media_usage_focal_bounds",
        ),
        CheckConstraint(
            f"alt_text IS NULL OR length(alt_text) <= {MAXIMUM_ALT_TEXT_LENGTH}",
            name="media_usage_alt_bounds",
        ),
        CheckConstraint(
            f"caption IS NULL OR length(caption) BETWEEN 1 AND {MAXIMUM_CAPTION_LENGTH}",
            name="media_usage_caption_bounds",
        ),
        CheckConstraint(
            "(purpose = 'decorative' AND alt_text = '') OR "
            "(purpose = 'meaningful' AND length(alt_text) > 0)",
            name="media_usage_accessibility_shape",
        ),
        UniqueConstraint(
            "owner_type", "owner_id", "role", "position", name="uq_media_usage_owner_role_pos"
        ),
        Index("ix_media_usage_asset_active", "asset_id", "active", "public"),
        Index("ix_media_usage_owner", "owner_type", "owner_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="RESTRICT"), nullable=False
    )
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(MAXIMUM_ALT_TEXT_LENGTH))
    caption: Mapped[str | None] = mapped_column(String(MAXIMUM_CAPTION_LENGTH))
    focal_x: Mapped[int] = mapped_column(Integer, nullable=False)
    focal_y: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MediaRepository:
    """PostgreSQL repository with lifecycle and usage race protection."""

    def __init__(self, session: AsyncSession, *, id_factory: Callable[[], UUID]) -> None:
        """Bind one transaction-scoped session and opaque ID source."""
        self._session = session
        self._id_factory = id_factory

    async def database_now(self) -> datetime:
        """Use PostgreSQL time for all lifecycle decisions."""
        return (await self._session.execute(select(func.now()))).scalar_one()

    async def add(self, asset: MediaAsset) -> None:
        """Insert one initial non-ready logical asset."""
        self._session.add(self._asset_record(asset))
        await self._session.flush()

    async def get(self, asset_id: UUID, *, for_update: bool = False) -> MediaAsset | None:
        """Load one aggregate and its immutable renditions."""
        statement = select(MediaAssetRecord).where(MediaAssetRecord.id == asset_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return None if row is None else await self._asset(row)

    async def list(
        self, *, offset: int, limit: int, search: str | None = None
    ) -> tuple[tuple[MediaAsset, ...], int]:
        """List nondeleted administrator assets newest-first."""
        predicate = MediaAssetRecord.status != MediaStatus.DELETED.value
        if search:
            predicate &= MediaAssetRecord.display_name.icontains(search, autoescape=True)
        count = (
            await self._session.execute(
                select(func.count()).select_from(MediaAssetRecord).where(predicate)
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                select(MediaAssetRecord)
                .where(predicate)
                .order_by(MediaAssetRecord.created_at.desc(), MediaAssetRecord.id.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars()
        return tuple([await self._asset(row) for row in rows]), count

    async def set_processing(self, asset_id: UUID, *, now: datetime) -> None:
        """Lock and advance exactly quarantined content into processing."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status != MediaStatus.QUARANTINED.value:
            raise MediaStateError
        row.status = MediaStatus.PROCESSING.value
        row.updated_at = now
        row.version += 1
        await self._session.flush()

    async def set_ready(
        self,
        asset_id: UUID,
        *,
        image: ProcessedImage,
        original_key: str,
        variants: tuple[MediaVariant, ...],
        now: datetime,
    ) -> MediaAsset:
        """Commit ready only with the complete verified variant catalog."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status != MediaStatus.PROCESSING.value or not variants:
            raise MediaStateError
        row.status = MediaStatus.READY.value
        row.detected_format = image.detected_format.value
        row.width = image.width
        row.height = image.height
        row.byte_size = image.byte_size
        row.checksum_sha256 = image.checksum_sha256
        row.original_key = original_key
        row.quarantine_key = None
        row.failure_code = None
        row.updated_at = now
        row.version += 1
        self._session.add_all(self._variant_record(item) for item in variants)
        await self._session.flush()
        return await self._asset(row)

    async def set_failed(self, asset_id: UUID, *, failure_code: str, now: datetime) -> None:
        """Persist one stable non-ready failure for operator reconciliation."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status in {
            MediaStatus.READY.value,
            MediaStatus.DELETING.value,
            MediaStatus.DELETED.value,
        }:
            raise MediaStateError
        row.status = MediaStatus.FAILED.value
        row.failure_code = failure_code
        row.updated_at = now
        row.version += 1
        await self._session.flush()

    async def rename(
        self,
        asset_id: UUID,
        *,
        display_name: str,
        expected_version: int,
        now: datetime,
    ) -> MediaAsset:
        """Update display-only metadata under a row lock and version check."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status != MediaStatus.READY.value or row.version != expected_version:
            raise MediaStateError
        row.display_name = display_name
        row.updated_at = now
        row.version += 1
        await self._session.flush()
        return await self._asset(row)

    async def list_usage(self, asset_id: UUID) -> tuple[MediaUsage, ...]:
        """Return contextual use facts without owner content or storage details."""
        rows = (
            await self._session.execute(
                select(MediaUsageRecord)
                .where(MediaUsageRecord.asset_id == asset_id)
                .order_by(
                    MediaUsageRecord.owner_type,
                    MediaUsageRecord.owner_id,
                    MediaUsageRecord.role,
                    MediaUsageRecord.position,
                )
            )
        ).scalars()
        return tuple(self._usage(row) for row in rows)

    async def replace_owner_usages(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        usages: tuple[MediaUse, ...],
        now: datetime,
    ) -> None:
        """Rebuild one owner's complete canonical usage set transactionally."""
        parsed_owner = MediaOwnerType(owner_type)
        validated = tuple(validate_media_use(item) for item in usages)
        if any(
            item.owner_type is not parsed_owner or item.owner_id != owner_id for item in validated
        ):
            raise MediaStateError
        asset_ids = tuple(dict.fromkeys(item.asset_id for item in validated))
        if asset_ids:
            ready = set(
                (
                    await self._session.execute(
                        select(MediaAssetRecord.id).where(
                            MediaAssetRecord.id.in_(asset_ids),
                            MediaAssetRecord.status == MediaStatus.READY.value,
                            MediaAssetRecord.deleted_at.is_(None),
                        )
                    )
                ).scalars()
            )
            if ready != set(asset_ids):
                raise MediaStateError
        await self._session.execute(
            delete(MediaUsageRecord).where(
                MediaUsageRecord.owner_type == parsed_owner.value,
                MediaUsageRecord.owner_id == owner_id,
            )
        )
        self._session.add_all(self._usage_record(item, now=now) for item in validated)
        await self._session.flush()

    async def begin_delete(
        self, asset_id: UUID, *, expected_version: int, now: datetime
    ) -> MediaAsset:
        """Lock, reject active usage, and make content immediately nondeliverable."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status != MediaStatus.READY.value or row.version != expected_version:
            raise MediaStateError
        active_usage = (
            await self._session.execute(
                select(MediaUsageRecord.id)
                .where(MediaUsageRecord.asset_id == asset_id, MediaUsageRecord.active.is_(True))
                .with_for_update()
                .limit(1)
            )
        ).scalar_one_or_none()
        if active_usage is not None:
            raise MediaStateError
        row.status = MediaStatus.DELETING.value
        row.deleted_at = now
        row.updated_at = now
        row.version += 1
        await self._session.flush()
        return await self._asset(row)

    async def finish_delete(self, asset_id: UUID, *, now: datetime) -> None:
        """Finalize a tombstone after idempotent object cleanup."""
        row = await self._required_row(asset_id, for_update=True)
        if row.status not in {MediaStatus.DELETING.value, MediaStatus.DELETED.value}:
            raise MediaStateError
        row.status = MediaStatus.DELETED.value
        row.original_key = None
        row.quarantine_key = None
        row.updated_at = now
        row.version += 1
        await self._session.flush()

    async def known_storage_keys(self) -> tuple[str, ...]:
        """Return only managed keys registered by durable asset state."""
        asset_rows = await self._session.execute(
            select(MediaAssetRecord.original_key, MediaAssetRecord.quarantine_key).where(
                MediaAssetRecord.status != MediaStatus.DELETED.value
            )
        )
        variant_rows = await self._session.execute(select(MediaVariantRecord.storage_key))
        keys: list[str] = []
        for original_key, quarantine_key in asset_rows:
            if original_key is not None:
                keys.append(original_key)
            if quarantine_key is not None:
                keys.append(quarantine_key)
        keys.extend(variant_rows.scalars())
        return tuple(sorted(set(keys)))

    async def _required_row(self, asset_id: UUID, *, for_update: bool = False) -> MediaAssetRecord:
        statement = select(MediaAssetRecord).where(MediaAssetRecord.id == asset_id)
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).scalar_one_or_none()
        if row is None:
            raise MediaStateError
        return row

    async def _asset(self, row: MediaAssetRecord) -> MediaAsset:
        variants = (
            await self._session.execute(
                select(MediaVariantRecord)
                .where(MediaVariantRecord.asset_id == row.id)
                .order_by(
                    MediaVariantRecord.width,
                    MediaVariantRecord.purpose,
                    MediaVariantRecord.id,
                )
            )
        ).scalars()
        return MediaAsset(
            id=row.id,
            status=MediaStatus(row.status),
            display_name=row.display_name,
            detected_format=None
            if row.detected_format is None
            else MediaFormat(row.detected_format),
            width=row.width,
            height=row.height,
            byte_size=row.byte_size,
            checksum_sha256=row.checksum_sha256,
            original_key=row.original_key,
            quarantine_key=row.quarantine_key,
            variants=tuple(self._variant(item) for item in variants),
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version,
            failure_code=row.failure_code,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def _asset_record(value: MediaAsset) -> MediaAssetRecord:
        return MediaAssetRecord(
            id=value.id,
            status=value.status.value,
            display_name=value.display_name,
            detected_format=None if value.detected_format is None else value.detected_format.value,
            width=value.width,
            height=value.height,
            byte_size=value.byte_size,
            checksum_sha256=value.checksum_sha256,
            original_key=value.original_key,
            quarantine_key=value.quarantine_key,
            created_by=value.created_by,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=value.version,
            failure_code=value.failure_code,
            deleted_at=value.deleted_at,
        )

    @staticmethod
    def _variant_record(value: MediaVariant) -> MediaVariantRecord:
        return MediaVariantRecord(
            id=value.id,
            asset_id=value.asset_id,
            purpose=value.purpose.value,
            format=value.format.value,
            width=value.width,
            height=value.height,
            byte_size=value.byte_size,
            checksum_sha256=value.checksum_sha256,
            storage_key=value.storage_key,
            created_at=value.created_at,
        )

    @staticmethod
    def _variant(value: MediaVariantRecord) -> MediaVariant:
        return MediaVariant(
            id=value.id,
            asset_id=value.asset_id,
            purpose=VariantPurpose(value.purpose),
            format=MediaFormat(value.format),
            width=value.width,
            height=value.height,
            byte_size=value.byte_size,
            checksum_sha256=value.checksum_sha256,
            storage_key=value.storage_key,
            created_at=value.created_at,
        )

    def _usage_record(self, value: MediaUse, *, now: datetime) -> MediaUsageRecord:
        return MediaUsageRecord(
            id=self._id_factory(),
            asset_id=value.asset_id,
            owner_type=value.owner_type.value,
            owner_id=value.owner_id,
            role=value.role.value,
            position=value.position,
            purpose=value.purpose.value,
            alt_text=value.alt_text,
            caption=value.caption,
            focal_x=value.focal_x,
            focal_y=value.focal_y,
            active=value.active,
            public=value.public,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _usage(value: MediaUsageRecord) -> MediaUsage:
        return MediaUsage(
            id=value.id,
            asset_id=value.asset_id,
            owner_type=MediaOwnerType(value.owner_type),
            owner_id=value.owner_id,
            role=MediaUsageRole(value.role),
            position=value.position,
            purpose=MediaUsePurpose(value.purpose),
            alt_text=value.alt_text,
            caption=value.caption,
            focal_x=value.focal_x,
            focal_y=value.focal_y,
            active=value.active,
            public=value.public,
            created_at=value.created_at,
            updated_at=value.updated_at,
        )
