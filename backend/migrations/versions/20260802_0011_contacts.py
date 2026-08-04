"""Add private contact submissions.

Revision ID: 20260802_0011
Revises: 20260802_0010
Create Date: 2026-08-04 22:00:00+00:00
"""
# ruff: noqa: D103, E501

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence
revision: str = "20260802_0011"
down_revision: str | None = "20260802_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_submission",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("subject", sa.String(180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "state IN ('unread','read','archived')",
            name="ck_contact_submission_contact_state_catalog",
        ),
        sa.CheckConstraint("version > 0", name="ck_contact_submission_contact_positive_version"),
        sa.CheckConstraint(
            "(state = 'unread' AND read_at IS NULL AND archived_at IS NULL) OR (state = 'read' AND read_at IS NOT NULL AND archived_at IS NULL) OR (state = 'archived' AND read_at IS NOT NULL AND archived_at IS NOT NULL)",
            name="ck_contact_submission_contact_lifecycle_shape",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contact_submission"),
    )
    op.create_index("ix_contact_state_created", "contact_submission", ["state", "created_at", "id"])
    op.create_index("ix_contact_retention", "contact_submission", ["created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_contact_retention", table_name="contact_submission")
    op.drop_index("ix_contact_state_created", table_name="contact_submission")
    op.drop_table("contact_submission")
