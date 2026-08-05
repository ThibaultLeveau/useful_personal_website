"""Add the least-privilege bounded audit-retention function.

Revision ID: 20260802_0013
Revises: 20260802_0012
Create Date: 2026-08-04 23:30:00+00:00
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260802_0013"
down_revision: str | None = "20260802_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Permit deletion only inside the non-public retention function."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_entry_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF TG_OP = 'DELETE'
               AND current_setting('upw.audit_retention', true) = 'enabled' THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'audit_entry is append-only' USING ERRCODE = '42501';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION purge_audit_entries_before(
            retention_cutoff timestamptz,
            maximum_rows integer
        )
        RETURNS integer
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
            deleted_rows integer;
        BEGIN
            IF retention_cutoff IS NULL OR maximum_rows < 1 OR maximum_rows > 1000 THEN
                RAISE EXCEPTION 'invalid audit retention arguments' USING ERRCODE = '22023';
            END IF;
            PERFORM set_config('upw.audit_retention', 'enabled', true);
            WITH victims AS (
                SELECT id
                FROM public.audit_entry
                WHERE occurred_at < retention_cutoff
                ORDER BY occurred_at, id
                LIMIT maximum_rows
                FOR UPDATE SKIP LOCKED
            )
            DELETE FROM public.audit_entry AS entry
            USING victims
            WHERE entry.id = victims.id;
            GET DIAGNOSTICS deleted_rows = ROW_COUNT;
            RETURN deleted_rows;
        END;
        $$
        """
    )
    op.execute(
        "REVOKE ALL ON FUNCTION purge_audit_entries_before(timestamptz, integer) FROM PUBLIC"
    )


def downgrade() -> None:
    """Remove the operator function and restore unconditional append-only enforcement."""
    op.execute("DROP FUNCTION purge_audit_entries_before(timestamptz, integer)")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_entry_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_entry is append-only' USING ERRCODE = '42501';
        END;
        $$
        """
    )
