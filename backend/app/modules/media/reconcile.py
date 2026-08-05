"""Stable-cutoff, dry-run-first media object reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.media.ports import MediaStoragePort, MediaUnitOfWorkFactory

STABLE_CUTOFF_GRACE = timedelta(hours=1)
STALE_QUARANTINE_AGE = timedelta(hours=24)
RECONCILIATION_BATCH_SIZE = 100
APPLY_CONFIRMATION = "delete-reviewed-media-orphans"


class ReconciliationConfirmationError(Exception):
    """Apply mode lacked the exact explicit confirmation token."""


@dataclass(frozen=True, slots=True)
class MediaReconciliationResult:
    """Sanitized count-only reconciliation outcome."""

    mode: str
    scanned_objects: int
    orphan_objects: int
    stale_quarantine_objects: int
    missing_registered_objects: int
    deleted_objects: int


class MediaReconciler:
    """Compare durable registrations with private objects under a stable cutoff."""

    def __init__(self, uow_factory: MediaUnitOfWorkFactory, storage: MediaStoragePort) -> None:
        """Bind transaction and provider-neutral storage boundaries."""
        self._uow_factory = uow_factory
        self._storage = storage

    async def run(
        self, *, apply: bool = False, confirmation: str | None = None
    ) -> MediaReconciliationResult:
        """Plan by default; delete only stable reviewed orphans under exact confirmation."""
        if apply and confirmation != APPLY_CONFIRMATION:
            raise ReconciliationConfirmationError
        async with self._uow_factory() as uow:
            now = await uow.media.database_now()
            registered = set(await uow.media.known_storage_keys())
        stable_cutoff = now - STABLE_CUTOFF_GRACE
        stale_quarantine_cutoff = now - STALE_QUARANTINE_AGE
        observed: set[str] = set()
        orphan_keys: list[str] = []
        stale_quarantine_keys: list[str] = []
        scanned = 0
        for prefix in ("quarantine/", "originals/", "variants/"):
            cursor: str | None = None
            while True:
                objects, cursor = await self._storage.list_managed(
                    prefix, cursor=cursor, limit=RECONCILIATION_BATCH_SIZE
                )
                scanned += len(objects)
                for item in objects:
                    observed.add(item.key)
                    if item.key in registered or item.last_modified > stable_cutoff:
                        continue
                    if (
                        item.key.startswith("quarantine/")
                        and item.last_modified <= stale_quarantine_cutoff
                    ):
                        stale_quarantine_keys.append(item.key)
                    else:
                        orphan_keys.append(item.key)
                if cursor is None:
                    break
        missing = sum(1 for key in registered if key not in observed)
        candidates = tuple(sorted({*orphan_keys, *stale_quarantine_keys}))
        deleted = 0
        if apply:
            for key in candidates:
                await self._storage.delete(key)
                deleted += 1
        return MediaReconciliationResult(
            mode="apply" if apply else "dry_run",
            scanned_objects=scanned,
            orphan_objects=len(orphan_keys),
            stale_quarantine_objects=len(stale_quarantine_keys),
            missing_registered_objects=missing,
            deleted_objects=deleted,
        )
