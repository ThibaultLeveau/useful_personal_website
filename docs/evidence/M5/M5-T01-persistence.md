# M5-T01-R - Experience persistence

## Outcome

Pass. `ExperienceRepository` implements the inward-facing port with transaction-owned SQLAlchemy
sessions and no commits. Aggregate pointers are loaded with bounded revision/child/skill batches.
Draft replacement touches only a mutable draft. Publish freezes and points that revision, creates
the next editable copy, and advances the aggregate version in one unit of work.

## Database behavior

- PostgreSQL transaction time drives schedule effectiveness.
- Public reads require visible, nondeleted, published, due aggregates and a frozen pointed revision.
- Chronology is current first, start descending, end descending/null last, curated position, opaque
  ID. Optional current/employment/remote/skill filters are bound predicates.
- Revision children and skill relations have scoped deterministic positions and duplicate guards.
- Repository and migrated-database tests reject mutation/deletion of frozen revision data.
- The public-page regression test asserts at most seven SELECT statements, preventing relation N+1.

The representative browser dataset query used 15 shared-buffer hits and completed in 0.274 ms.
PostgreSQL chose sequential scans for the four-row aggregate table, which is appropriate at that
cardinality; partial effective-public and frozen-chronology indexes are present for larger sets.
See [performance evidence](performance/README.md).

Database, migration, concurrency, rollback, and integration tests are included in the passing
226-test/85.30%-coverage backend gate. No repository performs an implicit commit.
