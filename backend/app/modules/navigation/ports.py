"""Inward-facing navigation/footer persistence ports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType

    from app.common.application.idempotency import IdempotencyStore
    from app.modules.audit.domain import AuditEntry
    from app.modules.navigation.domain import FooterTree, NavigationTree


class NavigationRepositoryPort(Protocol):
    """Complete navigation-tree persistence operations."""

    async def get(self, *, for_update: bool = False) -> NavigationTree:
        """Load the primary navigation tree."""
        ...

    async def replace(
        self,
        tree: NavigationTree,
        *,
        expected_version: int,
        now: datetime,
    ) -> NavigationTree:
        """Atomically replace every authorized node."""
        ...


class FooterRepositoryPort(Protocol):
    """Complete footer-tree persistence operations."""

    async def get(self, *, for_update: bool = False) -> FooterTree:
        """Load the footer aggregate."""
        ...

    async def replace(
        self,
        tree: FooterTree,
        *,
        expected_version: int,
        now: datetime,
    ) -> FooterTree:
        """Atomically replace every authorized column and link."""
        ...


class AuditPort(Protocol):
    """Insert-only audit dependency."""

    def append(self, entry: AuditEntry) -> None:
        """Stage one allow-listed fact."""
        ...


class NavigationUnitOfWork(Protocol):
    """One navigation or footer operation transaction."""

    navigation: NavigationRepositoryPort
    footer: FooterRepositoryPort
    audit: AuditPort
    idempotency: IdempotencyStore

    async def __aenter__(self) -> Self:
        """Open one transaction and bind repositories."""
        ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back unfinished work and release resources."""
        ...

    async def commit(self) -> None:
        """Commit the application operation."""
        ...


class NavigationUnitOfWorkFactory(Protocol):
    """Create a fresh navigation transaction."""

    def __call__(self) -> NavigationUnitOfWork:
        """Return a fresh unopened transaction."""
        ...
