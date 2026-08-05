# M8-T01 persistence evidence

## Record

- Date: 2026-08-04.
- Executor: Integration/root.
- Migration: `20260802_0009_pages_blocks.py`, sole head on `20260802_0008`.
- Test database: disposable PostgreSQL 17 container on a loopback-only non-default port; credentials were generated at runtime and were not logged or committed.

## Persistence contract

The page slice owns stable page identities, immutable-capable revisions, ordered blocks, and normalized config-derived references. Database constraints enforce the Home singleton, case-insensitive retained custom slugs, reserved routes, positive versions, pointer ownership, distinct draft/live pointers, the exact 19-kind catalog, bounded JSON objects, closed presentation tokens, contiguous application-managed positions, normalized reference kinds/roles, and child ownership.

Publishing freezes the selected revision and copies a new independent draft. PostgreSQL triggers reject update/delete of frozen revisions and insert/update/delete of their block/reference descendants. Scheduling uses database time and needs no worker. Page and revision pointer foreign keys are deferred only to support the reviewed aggregate creation/copy sequence.

The repository now uses positive scratch positions above the current maximum, so add, duplicate, delete, and complete reorder cannot violate the non-negative or unique-position constraints mid-transaction. New revisions are explicitly flushed before child blocks. Administrator listing uses SQL `LIMIT`/`OFFSET` plus an exact count. Internal page references resolve with one bounded set query rather than per-reference aggregate loads.

## Verification

The migration tests upgrade the accepted `0008` state to `0009`, preserve earlier providers, reject invalid catalog/shape/order data, verify sole-head behavior, and exercise every frozen parent/child mutation direction. Fresh upgrade, downgrade, and re-upgrade succeeded. The focused migration suite passed 2 tests.

The full page integration scenarios passed against the migrated runtime role and exercised create/replay, strict block insertion, staged media, preview, export, positive-position delete/reorder, publication copy-on-write, live/draft isolation, public projection, deep page copy, block-copy replay, unpublish replay, CSRF/authentication, missing/stale preconditions, and privacy-safe 404 behavior.

## Decision

M8-T01 persistence is accepted for G4. Migration `0009` remains the only M8 schema revision and the only Alembic head.
