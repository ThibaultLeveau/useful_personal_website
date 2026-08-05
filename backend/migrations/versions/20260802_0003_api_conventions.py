"""Add digest-only API idempotency records.

Revision ID: 20260802_0003
Revises: 20260802_0002
Create Date: 2026-08-03 00:01:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0003"
down_revision: str | None = "20260802_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the M2 actor/route/key idempotency persistence boundary."""
    op.create_table(
        "idempotency_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_digest", sa.LargeBinary(length=32), nullable=False),
        sa.Column("route", sa.String(length=255), nullable=False),
        sa.Column("key_digest", sa.LargeBinary(length=32), nullable=False),
        sa.Column("request_fingerprint", sa.LargeBinary(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("result_code", sa.String(length=80), nullable=True),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("octet_length(actor_digest) = 32", name="actor_digest_length"),
        sa.CheckConstraint("octet_length(key_digest) = 32", name="key_digest_length"),
        sa.CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="request_fingerprint_length",
        ),
        sa.CheckConstraint(
            "actor_type IN ('public', 'administrator_session', 'api_token')",
            name="idempotency_actor_type_catalog",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed')",
            name="idempotency_status_catalog",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="idempotency_expiry_after_creation",
        ),
        sa.CheckConstraint(
            "(status = 'pending' AND completed_at IS NULL AND response_status IS NULL "
            "AND result_code IS NULL AND resource_type IS NULL AND resource_id IS NULL "
            "AND resource_version IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL "
            "AND response_status BETWEEN 200 AND 299 AND result_code IS NOT NULL "
            "AND ((resource_type IS NULL AND resource_id IS NULL AND resource_version IS NULL) "
            "OR (resource_type IS NOT NULL AND resource_id IS NOT NULL "
            "AND resource_version > 0)))",
            name="idempotency_outcome_shape",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_idempotency_record")),
        sa.UniqueConstraint(
            "actor_digest",
            "route",
            "key_digest",
            name="uq_idempotency_actor_route_key",
        ),
    )
    op.create_index(
        "ix_idempotency_expiry",
        "idempotency_record",
        ["expires_at", "id"],
    )
    op.create_index(
        "ix_idempotency_status_updated",
        "idempotency_record",
        ["status", "updated_at", "id"],
    )


def downgrade() -> None:
    """Remove only the M2 API idempotency boundary."""
    op.drop_index("ix_idempotency_status_updated", table_name="idempotency_record")
    op.drop_index("ix_idempotency_expiry", table_name="idempotency_record")
    op.drop_table("idempotency_record")
