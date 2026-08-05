"""API token persistence and transaction ports."""

# ruff: noqa: D101, D102, D105
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.modules.api_access.domain import ApiTokenMetadata
    from app.modules.audit.domain import AuditEntry


class ApiTokenRepositoryPort(Protocol):
    async def database_now(self) -> datetime: ...
    async def add(
        self,
        *,
        metadata: ApiTokenMetadata,
        secret_digest: bytes,
        key_version: str,
        owner_id: UUID,
        display_suffix: str,
    ) -> None: ...
    async def list(
        self, *, owner_id: UUID, offset: int, limit: int, status: str | None
    ) -> tuple[tuple[ApiTokenMetadata, ...], int]: ...
    async def get_metadata(
        self, token_id: UUID, *, for_update: bool = False
    ) -> ApiTokenMetadata | None: ...
    async def find_auth(self, public_id: str) -> tuple[ApiTokenMetadata, bytes, str] | None: ...
    async def revoke(
        self, token_id: UUID, *, expected_version: int, now: datetime, reason: str
    ) -> None: ...
    async def touch_used(self, token_id: UUID, *, now: datetime) -> None: ...
    async def active_count(self, owner_id: UUID, *, now: datetime) -> int: ...
    async def name_exists(
        self, owner_id: UUID, name: str, *, exclude_id: UUID | None = None
    ) -> bool: ...


class AuditPort(Protocol):
    def append(self, entry: AuditEntry) -> None: ...


class ApiTokenRateLimitPort(Protocol):
    async def admit_api_token(
        self, subject_digest: bytes, now: datetime, *, valid: bool
    ) -> tuple[bool, int]: ...


class ApiTokenUnitOfWork(Protocol):
    tokens: ApiTokenRepositoryPort
    audit: AuditPort
    rate_limits: ApiTokenRateLimitPort

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...


class ApiTokenUnitOfWorkFactory(Protocol):
    def __call__(self) -> ApiTokenUnitOfWork: ...
