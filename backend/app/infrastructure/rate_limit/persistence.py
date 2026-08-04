"""Atomic PostgreSQL rate-limit buckets for authentication."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, LargeBinary, String, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.identity.ports import RateLimitDecision

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

LOGIN_POLICY = "admin_login"
LOGIN_FAILURE_LIMIT = 5
LOGIN_WINDOW_MINUTES = 15
MAXIMUM_BLOCK_SECONDS = 3_600
CONTACT_SHORT_POLICY = "contact_submit_15m"
CONTACT_DAILY_POLICY = "contact_submit_day"
INTEGRATION_UNKNOWN_POLICY = "api_token_unknown_15m"
INTEGRATION_VALID_POLICY = "api_token_valid_15m"


class RateLimitBase(DeclarativeBase):
    """Rate-limit-only SQLAlchemy registry."""


class RateLimitBucketRecord(RateLimitBase):
    """Keyed-pseudonym rate bucket."""

    __tablename__ = "rate_limit_bucket"

    policy: Mapped[str] = mapped_column(String(64), primary_key=True)
    subject_digest: Mapped[bytes] = mapped_column(LargeBinary(32), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def login_window_start(now: datetime) -> datetime:
    """Place an instant in a deterministic 15-minute UTC bucket."""
    minute = now.minute - (now.minute % LOGIN_WINDOW_MINUTES)
    return now.replace(minute=minute, second=0, microsecond=0)


class RateLimitRepository:
    """Atomic bucket operations without transaction ownership."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned transaction session."""
        self._session = session

    async def check_login(self, subject_digest: bytes, now: datetime) -> RateLimitDecision:
        """Carry any active block across fixed-window boundaries."""
        result = await self._session.execute(
            select(func.max(RateLimitBucketRecord.blocked_until)).where(
                RateLimitBucketRecord.policy == LOGIN_POLICY,
                RateLimitBucketRecord.subject_digest == subject_digest,
                RateLimitBucketRecord.blocked_until > now,
            )
        )
        blocked_until = result.scalar_one_or_none()
        if blocked_until is None or blocked_until <= now:
            return RateLimitDecision(retry_after_seconds=0)
        retry = max(1, int((blocked_until - now).total_seconds()))
        return RateLimitDecision(retry_after_seconds=retry)

    async def record_login_failure(
        self,
        subject_digest: bytes,
        now: datetime,
    ) -> RateLimitDecision:
        """Atomically increment a failure bucket and apply progressive blocking."""
        window_started_at = login_window_start(now)
        statement = (
            insert(RateLimitBucketRecord)
            .values(
                policy=LOGIN_POLICY,
                subject_digest=subject_digest,
                window_started_at=window_started_at,
                count=1,
                blocked_until=None,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=(
                    RateLimitBucketRecord.policy,
                    RateLimitBucketRecord.subject_digest,
                    RateLimitBucketRecord.window_started_at,
                ),
                set_={
                    "count": RateLimitBucketRecord.count + 1,
                    "updated_at": now,
                },
            )
            .returning(RateLimitBucketRecord.count)
        )
        count = (await self._session.execute(statement)).scalar_one()
        if count < LOGIN_FAILURE_LIMIT:
            return RateLimitDecision(retry_after_seconds=0)

        block_seconds = min(2 ** (count - LOGIN_FAILURE_LIMIT) * 60, MAXIMUM_BLOCK_SECONDS)
        blocked_until = now + timedelta(seconds=block_seconds)
        await self._session.execute(
            update(RateLimitBucketRecord)
            .where(
                RateLimitBucketRecord.policy == LOGIN_POLICY,
                RateLimitBucketRecord.subject_digest == subject_digest,
                RateLimitBucketRecord.window_started_at == window_started_at,
            )
            .values(blocked_until=blocked_until, updated_at=now)
        )
        return RateLimitDecision(retry_after_seconds=block_seconds)

    async def clear_login_failures(self, subject_digest: bytes) -> None:
        """Reset the pseudonymous subject after successful authentication."""
        await self._session.execute(
            delete(RateLimitBucketRecord).where(
                RateLimitBucketRecord.policy == LOGIN_POLICY,
                RateLimitBucketRecord.subject_digest == subject_digest,
            )
        )

    async def admit_contact(self, subject_digest: bytes, now: datetime) -> tuple[bool, int]:
        """Atomically consume both public-contact quotas without persisting raw IP data."""
        windows = (
            (
                CONTACT_SHORT_POLICY,
                now.replace(minute=now.minute - now.minute % 15, second=0, microsecond=0),
                5,
                900,
            ),
            (
                CONTACT_DAILY_POLICY,
                now.replace(hour=0, minute=0, second=0, microsecond=0),
                20,
                86400,
            ),
        )
        retry = 0
        for policy, started, limit, seconds in windows:
            count = (
                await self._session.execute(
                    insert(RateLimitBucketRecord)
                    .values(
                        policy=policy,
                        subject_digest=subject_digest,
                        window_started_at=started,
                        count=1,
                        blocked_until=None,
                        updated_at=now,
                    )
                    .on_conflict_do_update(
                        index_elements=(
                            RateLimitBucketRecord.policy,
                            RateLimitBucketRecord.subject_digest,
                            RateLimitBucketRecord.window_started_at,
                        ),
                        set_={"count": RateLimitBucketRecord.count + 1, "updated_at": now},
                    )
                    .returning(RateLimitBucketRecord.count)
                )
            ).scalar_one()
            if count > limit:
                retry = max(
                    retry,
                    1,
                    int((started + timedelta(seconds=seconds) - now).total_seconds()),
                )
        return retry == 0, retry

    async def admit_api_token(
        self, subject_digest: bytes, now: datetime, *, valid: bool
    ) -> tuple[bool, int]:
        """Consume a token-specific fixed-window budget."""
        started = now.replace(minute=now.minute - now.minute % 15, second=0, microsecond=0)
        policy = INTEGRATION_VALID_POLICY if valid else INTEGRATION_UNKNOWN_POLICY
        limit = 600 if valid else 30
        count = (
            await self._session.execute(
                insert(RateLimitBucketRecord)
                .values(
                    policy=policy,
                    subject_digest=subject_digest,
                    window_started_at=started,
                    count=1,
                    blocked_until=None,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=(
                        RateLimitBucketRecord.policy,
                        RateLimitBucketRecord.subject_digest,
                        RateLimitBucketRecord.window_started_at,
                    ),
                    set_={"count": RateLimitBucketRecord.count + 1, "updated_at": now},
                )
                .returning(RateLimitBucketRecord.count)
            )
        ).scalar_one()
        retry = max(1, int((started + timedelta(minutes=15) - now).total_seconds()))
        return count <= limit, 0 if count <= limit else retry
