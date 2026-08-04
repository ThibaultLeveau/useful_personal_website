# M0-T05 - Database Implementer Evidence

## Identity

- Milestone: M0
- Task: M0-T05
- Requirements: PostgreSQL persistence foundation, explicit migrations,
  transaction ownership, and database-backed readiness
- Implementer: Backend/database agent
- Date: 2026-08-02

## Delivery

- PostgreSQL-only SQLAlchemy async engine and session factory with hidden
  parameters, pool pre-ping, bounded pool configuration, and lifespan disposal.
- Transaction-owning `SqlAlchemyUnitOfWork`; only explicit `commit()` persists,
  while unfinished normal and exceptional exits roll back.
- Alembic async environment and one deterministic empty baseline revision:
  `20260802_0001`.
- Exact runtime revision compatibility check and safe readiness categories for
  connectivity and migration mismatch.
- No SQLite path, feature model, feature table, startup migration, or repository
  commit behavior was introduced.

## PostgreSQL migration proof

Validation used one uniquely named ephemeral PostgreSQL 17.10 container from
the frozen image digest
`postgres@sha256:4f736ae292687621d4dbe0d499ffd024a36bd2ee7d8ca6f2ccd4c800f047b394`.
The database, role, password, host port, and URL were synthetic and are omitted.

From an empty database:

- `alembic downgrade base` passed.
- `alembic upgrade head` passed.
- `alembic heads` returned exactly `20260802_0001 (head)`.
- `alembic current` returned exactly `20260802_0001 (head)`.
- `alembic check` returned `No new upgrade operations detected.`
- Schema inspection returned only `alembic_version`, whose value was
  `20260802_0001`.
- The exercised downgrade returned the revision row to base, and a subsequent
  upgrade restored the exact head.

## Validation

| Check | Result |
|---|---|
| Ruff lint | Pass; all checks |
| Ruff format | Pass; 45 files |
| Strict Mypy | Pass; 45 source files |
| Pytest, including isolated PostgreSQL | Pass; 38 tests |
| Branch coverage | Pass; 93.65% (threshold 85%) |
| Bandit application scan | Pass; zero findings and zero skipped issues |
| Git whitespace check | Pass |

The tests cover PostgreSQL-only configuration, secret-safe construction,
commit, explicit rollback, rollback on exception, rollback without commit,
healthy readiness, safe revision mismatch, default application wiring, one
linear head, empty-database upgrade/current/schema, downgrade, and deterministic
secret-free offline SQL.

## Handoff and freeze candidate F3

- Exact head: `20260802_0001`.
- Canonical Alembic config: `backend/alembic.ini`.
- Container/deployment integration must inject `APP_DATABASE_URL` and run
  `uv run --frozen alembic -c backend/alembic.ini upgrade head` as an explicit
  pre-start/deployment operation. Application startup must not apply migrations.
- The full PostgreSQL test gate must receive a unique empty database through
  `TEST_DATABASE_URL`.
- This implementer evidence is pending Integration/root acceptance and F3
  freeze.

## Cleanup

The uniquely named validation container was removed after the final checks, and
an exact-name lookup confirmed it was absent. No other container was changed.
