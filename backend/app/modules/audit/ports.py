"""Audit query transaction ports."""

# ruff: noqa: D101, D102, D105

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from app.common.domain.pagination import PageRequest
    from app.modules.audit.domain import AuditEntry, AuditQuery


class AuditQueryRepositoryPort(Protocol):
    """Read-only persistence contract for the protected audit viewer."""

    async def list(
        self, query: AuditQuery, page: PageRequest
    ) -> tuple[tuple[AuditEntry, ...], int]: ...

    async def get(self, entry_id: UUID) -> AuditEntry | None: ...


class AuditQueryUnitOfWork(Protocol):
    audit: AuditQueryRepositoryPort

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


class AuditQueryUnitOfWorkFactory(Protocol):
    def __call__(self) -> AuditQueryUnitOfWork: ...
