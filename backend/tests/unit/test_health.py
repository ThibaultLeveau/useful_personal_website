"""Tests for readiness result invariants and failure isolation."""

from __future__ import annotations

import pytest

from app.common.health import (
    ReadinessCategory,
    ReadinessResult,
    evaluate_readiness,
)


class ExplodingProbe:
    """Probe fixture that raises a sensitive implementation exception."""

    async def check(self) -> ReadinessResult:
        """Raise instead of returning a readiness result."""
        msg = "postgresql://app:private-password@internal-db/portfolio"
        raise RuntimeError(msg)


def test_readiness_result_enforces_consistent_state() -> None:
    """A result cannot be both ready and unavailable or neither."""
    with pytest.raises(ValueError, match="ready result"):
        ReadinessResult(ready=True, category=ReadinessCategory.DATABASE)
    with pytest.raises(ValueError, match="requires a safe category"):
        ReadinessResult(ready=False)


async def test_probe_failure_is_mapped_to_safe_database_category() -> None:
    """Adapter exceptions should never escape the readiness application service."""
    result = await evaluate_readiness(ExplodingProbe())

    assert result == ReadinessResult(
        ready=False,
        category=ReadinessCategory.DATABASE,
    )
