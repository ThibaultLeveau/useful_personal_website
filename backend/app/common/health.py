"""Readiness probe port and failure-isolating evaluation service."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ReadinessCategory(StrEnum):
    """Safe dependency categories permitted in readiness responses."""

    DATABASE = "database"
    MIGRATION = "migration"


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    """Safe aggregate result returned by a readiness probe."""

    ready: bool
    category: ReadinessCategory | None = None

    def __post_init__(self) -> None:
        """Keep successful and unavailable results structurally consistent."""
        if self.ready and self.category is not None:
            msg = "a ready result cannot contain an unavailable category"
            raise ValueError(msg)
        if not self.ready and self.category is None:
            msg = "an unavailable result requires a safe category"
            raise ValueError(msg)


class ReadinessProbe(Protocol):
    """Port implemented by the database/migration adapter in M0-T05."""

    async def check(self) -> ReadinessResult:
        """Return dependency readiness without exposing implementation details."""
        ...


class UnconfiguredReadinessProbe:
    """Fail closed until M0-T05 supplies the real database readiness adapter."""

    async def check(self) -> ReadinessResult:
        """Report the required database category as unavailable."""
        return ReadinessResult(ready=False, category=ReadinessCategory.DATABASE)


async def evaluate_readiness(probe: ReadinessProbe) -> ReadinessResult:
    """Convert every adapter failure to a safe unavailable category."""
    try:
        return await probe.check()
    except Exception:  # noqa: BLE001 - dependency adapters are an isolation boundary.
        return ReadinessResult(ready=False, category=ReadinessCategory.DATABASE)
