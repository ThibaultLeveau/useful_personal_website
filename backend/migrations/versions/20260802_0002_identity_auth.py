"""Add administrator authentication, rate limiting, and minimal audit.

Revision ID: 20260802_0002
Revises: 20260802_0001
Create Date: 2026-08-02 00:01:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0002"
down_revision: str | None = "20260802_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the complete M1 identity persistence boundary."""
    op.create_table(
        "administrator",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("email_normalized", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("length(email_normalized) > 3", name="email_normalized_nonempty"),
        sa.CheckConstraint("length(display_name) > 0", name="display_name_nonempty"),
        sa.CheckConstraint("version > 0", name="version_positive"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_administrator")),
        sa.UniqueConstraint("email_normalized", name=op.f("uq_administrator_email_normalized")),
    )
    op.create_index(
        "ix_administrator_active_lookup",
        "administrator",
        ["is_active", "id"],
        unique=False,
    )

    op.create_table(
        "admin_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("administrator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_digest", sa.LargeBinary(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=64), nullable=True),
        sa.Column("user_agent_digest", sa.LargeBinary(length=32), nullable=True),
        sa.Column("ip_pseudonym", sa.LargeBinary(length=32), nullable=True),
        sa.Column("rotated_from_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("octet_length(token_digest) = 32", name="token_digest_length"),
        sa.CheckConstraint(
            "absolute_expires_at > created_at AND idle_expires_at > created_at",
            name="expiry_after_creation",
        ),
        sa.CheckConstraint(
            "last_seen_at >= created_at AND last_seen_at <= absolute_expires_at",
            name="last_seen_bounds",
        ),
        sa.CheckConstraint(
            "idle_expires_at <= absolute_expires_at",
            name="idle_before_absolute_expiry",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revocation_reason IS NULL) OR "
            "(revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)",
            name="revocation_pair",
        ),
        sa.ForeignKeyConstraint(
            ["administrator_id"],
            ["administrator.id"],
            name=op.f("fk_admin_session_administrator_id_administrator"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["rotated_from_id"],
            ["admin_session.id"],
            name=op.f("fk_admin_session_rotated_from_id_admin_session"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_session")),
        sa.UniqueConstraint("token_digest", name=op.f("uq_admin_session_token_digest")),
    )
    op.create_index(
        "ix_admin_session_active_expiry",
        "admin_session",
        ["revoked_at", "idle_expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_session_administrator",
        "admin_session",
        ["administrator_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "rate_limit_bucket",
        sa.Column("policy", sa.String(length=64), nullable=False),
        sa.Column("subject_digest", sa.LargeBinary(length=32), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("count >= 0", name="count_nonnegative"),
        sa.CheckConstraint("octet_length(subject_digest) = 32", name="subject_digest_length"),
        sa.PrimaryKeyConstraint(
            "policy",
            "subject_digest",
            "window_started_at",
            name=op.f("pk_rate_limit_bucket"),
        ),
    )

    op.create_table(
        "audit_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_label_snapshot", sa.String(length=80), nullable=True),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("ip_pseudonym", sa.LargeBinary(length=32), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "actor_type IN ('administrator', 'anonymous', 'system')",
            name="actor_type_catalog",
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure', 'denied')",
            name="outcome_catalog",
        ),
        sa.CheckConstraint("jsonb_typeof(metadata) = 'object'", name="metadata_object"),
        sa.CheckConstraint("schema_version > 0", name="schema_version_positive"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_entry")),
    )
    op.create_index("ix_audit_entry_occurred", "audit_entry", ["occurred_at", "id"])
    op.create_index(
        "ix_audit_entry_event_time",
        "audit_entry",
        ["event_type", "occurred_at"],
    )
    op.create_index(
        "ix_audit_entry_actor_time",
        "audit_entry",
        ["actor_type", "actor_id", "occurred_at"],
    )
    op.create_index(
        "ix_audit_entry_resource_time",
        "audit_entry",
        ["resource_type", "resource_id", "occurred_at"],
    )
    op.create_index("ix_audit_entry_request_id", "audit_entry", ["request_id"])
    op.execute("REVOKE UPDATE, DELETE ON audit_entry FROM PUBLIC")
    op.execute(
        """
        CREATE FUNCTION prevent_audit_entry_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_entry is append-only' USING ERRCODE = '42501';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_entry_append_only
        BEFORE UPDATE OR DELETE ON audit_entry
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_entry_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_entry_no_truncate
        BEFORE TRUNCATE ON audit_entry
        FOR EACH STATEMENT EXECUTE FUNCTION prevent_audit_entry_mutation()
        """
    )


def downgrade() -> None:
    """Remove the M1 identity persistence boundary in dependency order."""
    op.execute("DROP TRIGGER audit_entry_no_truncate ON audit_entry")
    op.execute("DROP TRIGGER audit_entry_append_only ON audit_entry")
    op.execute("DROP FUNCTION prevent_audit_entry_mutation()")
    op.drop_index("ix_audit_entry_request_id", table_name="audit_entry")
    op.drop_index("ix_audit_entry_resource_time", table_name="audit_entry")
    op.drop_index("ix_audit_entry_actor_time", table_name="audit_entry")
    op.drop_index("ix_audit_entry_event_time", table_name="audit_entry")
    op.drop_index("ix_audit_entry_occurred", table_name="audit_entry")
    op.drop_table("audit_entry")
    op.drop_table("rate_limit_bucket")
    op.drop_index("ix_admin_session_administrator", table_name="admin_session")
    op.drop_index("ix_admin_session_active_expiry", table_name="admin_session")
    op.drop_table("admin_session")
    op.drop_index("ix_administrator_active_lookup", table_name="administrator")
    op.drop_table("administrator")
