"""Contact persistence transaction protocols."""
# ruff: noqa: D101, D102, D105, PLR0913

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from app.common.application.idempotency import IdempotencyStore
    from app.modules.audit.domain import AuditEntry
    from app.modules.contacts.domain import ContactState, ContactSubmission


class ContactRepositoryPort(Protocol):
    async def database_now(self) -> datetime: ...
    async def add(self, contact: ContactSubmission) -> None: ...
    async def get(
        self, contact_id: UUID, *, for_update: bool = False
    ) -> ContactSubmission | None: ...
    async def list(
        self,
        *,
        state: ContactState | None,
        created_from: datetime | None,
        created_to: datetime | None,
        offset: int,
        limit: int,
        oldest_first: bool,
    ) -> tuple[tuple[ContactSubmission, ...], int]: ...
    async def update(self, contact: ContactSubmission, *, expected_version: int) -> None: ...
    async def delete(self, contact_id: UUID, *, expected_version: int) -> None: ...
    async def purge(self, *, before: datetime, limit: int) -> int: ...


class ContactRateLimitPort(Protocol):
    async def admit_contact(self, subject_digest: bytes, now: datetime) -> tuple[bool, int]: ...


class AuditPort(Protocol):
    def append(self, entry: AuditEntry) -> None: ...


class ContactUnitOfWork(Protocol):
    contacts: ContactRepositoryPort
    rate_limits: ContactRateLimitPort
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


class ContactUnitOfWorkFactory(Protocol):
    def __call__(self) -> ContactUnitOfWork: ...
