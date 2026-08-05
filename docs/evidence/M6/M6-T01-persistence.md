# M6-T01-R - Project persistence and query behavior

## Outcome

Pass. `ProjectRepository` implements the project ports without importing skills/experience
persistence and never commits. The stable aggregate and complete revision-owned children round-trip
without loss. Publish freezes the draft and creates a distinct mutable copy atomically; migrated
triggers reject mutation/deletion of a frozen revision, technologies, skill/experience links, and
related-project edges.

PostgreSQL time controls public effectiveness. Slug reservation includes soft-deleted aggregates.
Reorder locks the complete requested set. The related-project graph uses a transaction-scoped
advisory lock and rejects direct/indirect cycles or an over-limit graph fail-closed.

## Query bounds and corrective loop

Public list loading is fixed at seven SELECT statements independent of relation count: page, exact
count, revisions, technologies, skills, experiences, and related projects. A regression assertion
records that bound. Detail and relation-summary plans use their dedicated indexes.

The first 10,000-project plan run found that case-insensitive technology filtering used
`lower(value)` against a plain-value index, scanning 60,000 rows. The sole M6 model/migration index
was corrected to `(lower(value), revision_id)`, a migrated-index assertion was added, and the plan
now selects the expression index. Execution fell from 239.550 ms to 114.658 ms on the synthetic
60,000-row technology set. The corrected migration suite and repository suite pass.

Full data-volume and plan details are in [performance/query-plans.md](performance/query-plans.md).

## Verification

- project repository: 3/3 PostgreSQL tests pass, including rollback/no-commit, copy-on-write,
  frozen trigger, database-time public eligibility, fixed SQL count, and graph cycles;
- complete migration lineage: 12/12 pass after the expression-index correction;
- Ruff format/check and strict Mypy pass the persistence and migration sources.

No N+1, repository commit, provider ORM reach-through, mutable publication, unbounded page, or
second migration head remains.
