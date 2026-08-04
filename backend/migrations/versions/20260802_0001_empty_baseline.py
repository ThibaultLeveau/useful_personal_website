"""Establish the empty Milestone 0 migration baseline.

Revision ID: 20260802_0001
Revises: None
Create Date: 2026-08-02 00:00:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish lineage without speculative feature tables."""


def downgrade() -> None:
    """Return the empty baseline to Alembic base."""
