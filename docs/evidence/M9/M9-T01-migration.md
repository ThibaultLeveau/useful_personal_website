# M9-T01-M sole migration evidence

- Revision: `20260802_0010` on `20260802_0009`; one head.
- Empty upgrade, upgrade from accepted M8, downgrade to M8, and re-upgrade passed on disposable PostgreSQL 17.
- Representative ready and quarantined assets proved ready-reference enforcement.
- Active usage proved database-level tombstone rejection with SQLSTATE `55000`.
- Existing provider data and frozen revision mechanisms remain intact; new revision-owned relations use the established frozen guards.
- `alembic check` reports no new upgrade operations.
