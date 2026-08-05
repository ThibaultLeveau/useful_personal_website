# M5-T01-M - Migration `20260802_0006`

## Outcome

Pass. `20260802_0006_experiences.py` is the only M5 revision, directly follows accepted `0005`, and
is both the sole Alembic head and the running database current revision.

The migration creates the stable aggregate, immutable revisions, ordered responsibilities,
achievements, technologies, revision-scoped skill relations, same-aggregate pointer constraints,
catalog/date/order checks, query indexes, and frozen-row protection triggers. It creates no worker,
scheduler, outbox, or unrelated feature table.

## Verification

Migration tests cover empty upgrade, upgrade from `0005` with representative site/skill data,
schema/model parity, deferrable pointer integrity, constraints and indexes, frozen parent/child/skill
mutation rejection, copy-on-write persistence, downgrade, transaction rollback, and separation of
migration/runtime permissions.

An isolated no-seed Compose project ran role initialization, every migration from `0001` through
`0006`, permission reconciliation/check, and both exact scanned application images. PostgreSQL,
backend, and frontend reached healthy; `/experience` returned 200 with zero API items. Neither demo
seed nor admin bootstrap ran. Teardown left zero project containers and zero project volumes.

One diagnostic attempt intentionally used production mode with an HTTP loopback trusted origin;
configuration correctly refused it. The corrected documented development-mode run passed without
weakening the guard.
