"""Add digest-only scoped API access tokens.

Revision ID: 20260802_0012
Revises: 20260802_0011
Create Date: 2026-08-04 23:00:00+00:00
"""

# ruff: noqa: D103, E501
from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence
revision: str = "20260802_0012"
down_revision: str | None = "20260802_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_token",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_id", sa.String(22), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("display_suffix", sa.String(6), nullable=False),
        sa.Column("secret_digest", sa.LargeBinary(32), nullable=False),
        sa.Column("digest_key_version", sa.String(40), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(32), nullable=True),
        sa.Column("rotated_from_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "octet_length(secret_digest)=32", name="ck_api_token_api_token_digest_length"
        ),
        sa.CheckConstraint("version>0", name="ck_api_token_api_token_positive_version"),
        sa.CheckConstraint(
            "expires_at IS NULL OR expires_at>created_at",
            name="ck_api_token_api_token_expiry_after_creation",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL)=(revocation_reason IS NULL)",
            name="ck_api_token_api_token_revocation_shape",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["administrator.id"],
            name="fk_api_token_owner_id_administrator",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["rotated_from_id"],
            ["api_token.id"],
            name="fk_api_token_rotated_from_id_api_token",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_api_token"),
        sa.UniqueConstraint("public_id", name="uq_api_token_public_id"),
        sa.UniqueConstraint("rotated_from_id", name="uq_api_token_rotated_from_id"),
    )
    op.create_index("ix_api_token_owner_created", "api_token", ["owner_id", "created_at", "id"])
    op.create_index(
        "ix_api_token_active_expiry", "api_token", ["owner_id", "revoked_at", "expires_at", "id"]
    )
    op.create_table(
        "api_token_scope",
        sa.Column("token_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.CheckConstraint(
            "scope IN ('content:read','content:write','media:read','media:write','contacts:read','admin:read')",
            name="ck_api_token_scope_api_token_scope_catalog",
        ),
        sa.ForeignKeyConstraint(
            ["token_id"],
            ["api_token.id"],
            name="fk_api_token_scope_token_id_api_token",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token_id", "scope", name="pk_api_token_scope"),
    )


def downgrade() -> None:
    op.drop_table("api_token_scope")
    op.drop_index("ix_api_token_active_expiry", table_name="api_token")
    op.drop_index("ix_api_token_owner_created", table_name="api_token")
    op.drop_table("api_token")
