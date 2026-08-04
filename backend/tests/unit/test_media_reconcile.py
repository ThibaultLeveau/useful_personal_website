"""Stable-cutoff and explicit-apply media reconciliation tests."""

# ruff: noqa: D103

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Self

import pytest

from app.modules.media.reconcile import (
    APPLY_CONFIRMATION,
    MediaReconciler,
    ReconciliationConfirmationError,
)
from app.modules.media.storage import StoredObject

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)


class _Repository:
    async def database_now(self) -> datetime:
        return NOW

    async def known_storage_keys(self) -> tuple[str, ...]:
        return ("variants/registered.webp", "variants/missing.webp")


class _UnitOfWork:
    def __init__(self) -> None:
        self.media = _Repository()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_arguments: object) -> None:
        return


class _Storage:
    def __init__(self) -> None:
        old = NOW - timedelta(hours=26)
        recent = NOW - timedelta(minutes=10)
        self.objects = {
            "variants/registered.webp": StoredObject("variants/registered.webp", 10, "a" * 64, old),
            "variants/orphan.webp": StoredObject("variants/orphan.webp", 10, "b" * 64, old),
            "variants/recent.webp": StoredObject("variants/recent.webp", 10, "c" * 64, recent),
            "quarantine/stale.bin": StoredObject("quarantine/stale.bin", 10, "d" * 64, old),
        }

    async def list_managed(
        self, prefix: str, *, cursor: str | None, limit: int
    ) -> tuple[tuple[StoredObject, ...], str | None]:
        del cursor, limit
        return tuple(item for key, item in self.objects.items() if key.startswith(prefix)), None

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)


@pytest.mark.asyncio
async def test_dry_run_reports_without_deleting_and_apply_is_stable_only() -> None:
    storage = _Storage()
    reconciler = MediaReconciler(_UnitOfWork, storage)  # type: ignore[arg-type]

    planned = await reconciler.run()
    assert planned.mode == "dry_run"
    assert planned.scanned_objects == 4
    assert planned.orphan_objects == 1
    assert planned.stale_quarantine_objects == 1
    assert planned.missing_registered_objects == 1
    assert planned.deleted_objects == 0
    assert len(storage.objects) == 4

    applied = await reconciler.run(apply=True, confirmation=APPLY_CONFIRMATION)
    assert applied.deleted_objects == 2
    assert "variants/recent.webp" in storage.objects
    assert "variants/registered.webp" in storage.objects


@pytest.mark.asyncio
async def test_apply_requires_exact_confirmation() -> None:
    with pytest.raises(ReconciliationConfirmationError):
        await MediaReconciler(_UnitOfWork, _Storage()).run(  # type: ignore[arg-type]
            apply=True, confirmation="yes"
        )
