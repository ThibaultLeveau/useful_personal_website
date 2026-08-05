"""Database-backed public media eligibility for exact current owner state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.modules.media.domain import MediaOwnerType, MediaUsage, MediaUsageRole

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import TextClause

    from app.infrastructure.database.session import AsyncSessionFactory


@dataclass(frozen=True, slots=True)
class DatabasePublicMediaEligibility:
    """Recheck current public owner pointers instead of trusting stale usage flags."""

    session_factory: AsyncSessionFactory

    async def is_publicly_eligible(self, usage: MediaUsage) -> bool:
        """Return true only when the materialized use still matches a public owner."""
        if not usage.active or not usage.public:
            return False
        statement = self._statement(usage)
        if statement is None:
            return False
        async with self.session_factory() as session:
            return bool(
                await session.scalar(
                    statement,
                    {"asset_id": usage.asset_id, "owner_id": usage.owner_id},
                )
            )

    @staticmethod
    def _statement(usage: MediaUsage) -> TextClause | None:  # noqa: PLR0911
        if (
            usage.owner_type is MediaOwnerType.PROFILE
            and usage.role is MediaUsageRole.PROFILE_IMAGE
        ):
            return text(
                "SELECT EXISTS (SELECT 1 FROM profile "
                "WHERE id=:owner_id AND profile_image_id=:asset_id)"
            )
        if usage.owner_type is MediaOwnerType.WEBSITE_SETTINGS:
            if usage.role is MediaUsageRole.SITE_LOGO:
                return text(
                    "SELECT EXISTS (SELECT 1 FROM website_settings "
                    "WHERE id=:owner_id AND logo_media_id=:asset_id)"
                )
            if usage.role is MediaUsageRole.SITE_FAVICON:
                return text(
                    "SELECT EXISTS (SELECT 1 FROM website_settings "
                    "WHERE id=:owner_id AND favicon_media_id=:asset_id)"
                )
            if usage.role is MediaUsageRole.SITE_SOCIAL_IMAGE:
                return text(
                    "SELECT EXISTS (SELECT 1 FROM website_settings "
                    "WHERE id=:owner_id AND social_image_media_id=:asset_id)"
                )
            return None
        if usage.owner_type is MediaOwnerType.PROJECT_REVISION and usage.role in {
            MediaUsageRole.PROJECT_COVER,
            MediaUsageRole.PROJECT_SCREENSHOT,
        }:
            return text(
                "SELECT EXISTS (SELECT 1 FROM project "
                "WHERE published_revision_id=:owner_id AND visible IS TRUE "
                "AND deleted_at IS NULL AND publish_at IS NOT NULL AND publish_at <= now())"
            )
        if (
            usage.owner_type is MediaOwnerType.BLOG_POST_REVISION
            and usage.role is MediaUsageRole.BLOG_COVER
        ):
            return text(
                "SELECT EXISTS (SELECT 1 FROM post "
                "WHERE published_revision_id=:owner_id AND visible IS TRUE "
                "AND deleted_at IS NULL AND publish_at IS NOT NULL AND publish_at <= now())"
            )
        if (
            usage.owner_type is MediaOwnerType.PAGE_BLOCK
            and usage.role is MediaUsageRole.PAGE_PRIMARY
        ):
            return text(
                "SELECT EXISTS (SELECT 1 FROM page_block AS b "
                "JOIN page_revision AS r ON r.id=b.revision_id "
                "JOIN page AS p ON p.published_revision_id=r.id "
                "WHERE b.id=:owner_id AND b.visible IS TRUE "
                "AND CAST(b.config->>'media_id' AS uuid)=:asset_id "
                "AND p.visible IS TRUE AND p.deleted_at IS NULL "
                "AND p.publish_at IS NOT NULL AND p.publish_at <= now())"
            )
        return None
