# M6-T01-M - Migration `20260802_0007`

## Outcome

Pass. `20260802_0007_projects.py` is the sole M6 revision, directly follows accepted `0006`, and
remains the single Alembic head/current candidate. It creates only project aggregate/revision,
ordered technology, revision-scoped provider relations, and related-project graph data.

Deferrable same-aggregate pointers, status/date/slug/URL/order checks, duplicate/self-edge guards,
provider foreign keys, query indexes, and frozen-row triggers reinforce the application contract.
There is no media/storage table, scheduler, worker, outbox, blog/page/contact/token schema, or
parallel migration.

## Verification

The 12-test migration suite passes in 82.63 s after the final index correction. It covers empty and
prior-head upgrades, representative provider data, current/head equality, one head, schema/model
parity, pointer ownership, frozen parent/child rejection, catalog/date/URL/order constraints,
provider relations, expression-index definition, deterministic offline SQL, and downgrade.

An isolated database was migrated linearly from `0001` through revised `0007`, populated with
10,000 aggregates, 20,000 revisions, 60,000 technologies, and 9,999 related edges, and analyzed for
representative plans. The final fresh Compose certification is recorded in `M6-T03.md`.
