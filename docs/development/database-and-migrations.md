# Database and Migrations

## Readiness

`M0-T05` established the PostgreSQL-only async runtime and first Alembic
lineage. The active backend owns the exact supported revision and maintains one
linear head. A database is ready only when it is reachable and its
`alembic_version` value exactly matches that revision.

The M4 accepted head is `20260802_0005`. It descends directly from the M3 site-configuration head
and adds ordered skill categories and skills with normalized-slug, numeric-range, visibility,
version, foreign-key, and deferrable-order constraints. Demo content remains an explicit separate
operation.

## Accepted contract

- PostgreSQL is the R1 system of record.
- SQLAlchemy 2 persistence sits behind application-facing repository and unit-of-work boundaries.
- All schema changes use Alembic; unmanaged schema edits are prohibited.
- Migrations maintain one linear head unless the integration owner explicitly authorizes and reviews a merge revision.
- Repositories do not commit transactions. Transaction completion belongs to the unit-of-work/application boundary.
- Runtime startup does not run migrations automatically.
- Deployment migration credentials and runtime credentials are always separated. The runtime role does not own the database, schema, tables, sequences, or functions.
- Migration output and evidence must not expose database URLs, credentials, production data, or machine paths.

The [database model](../architecture/database-model.md) defines planned entities and invariants. The [architecture overview](../architecture/architecture.md) and accepted ADRs define boundaries; migrations are executable history and must stay aligned with both models and code.

## Runtime and transaction ownership

Set backend `APP_DATABASE_URL` to a secret-managed `postgresql+asyncpg` URL for
the non-owner runtime login. Inject a distinct migration-owner URL only into
Alembic and permission-reconciliation jobs. The application creates one shared
async engine and session factory, disposes the engine during lifespan shutdown,
and never runs Alembic during startup.
Application services open `SqlAlchemyUnitOfWork`, call `commit()` only after a
complete successful operation, and otherwise receive rollback on normal or
exceptional context exit. Repositories may flush but must never commit.

Readiness returns the existing safe `database` category for connection failure
and `migration` for a missing or mismatched revision. Responses and logs never
include the URL, credentials, driver errors, SQL, or revision internals.

## Migration protocol

Run migration commands as an explicit deployment step from the repository
root. The environment examples below assume `APP_DATABASE_URL` has already
been injected with migration-owner credentials without printing it:

```text
uv run --frozen alembic -c backend/alembic.ini heads
uv run --frozen alembic -c backend/alembic.ini current
uv run --frozen alembic -c backend/alembic.ini check
uv run --frozen alembic -c backend/alembic.ini upgrade head
```

For a new environment, provision the roles/database, run `upgrade head`, confirm
`heads` and `current` match, reconcile runtime permissions, run the runtime
permission check, then start or roll out the application. A revision mismatch
is fixed by stopping the rollout, inspecting `heads` and `current`, and applying
the reviewed forward migration; never stamp or edit `alembic_version` manually.

`uv run --frozen alembic -c backend/alembic.ini downgrade base` remains a
development/test rollback check run with migration-owner credentials.
Production rollback requires migration-specific analysis, a restore point, and
either an approved downgrade or forward recovery. Coordinate production
migration timing with the backup/restore owner and verify restoration
procedures before rollout.

For the local container topology, start PostgreSQL and explicitly run the profile-gated role initialization, migration, and permission reconciliation services before either application. The exact sequence, existing-volume path, and cleanup boundary are in [local containers](containers.md). Ordinary application startup invokes none of those mutating operations; it runs only a read-only runtime-permission gate.

## Database role and grant contract

The bootstrap cluster administrator is retained only for role provisioning and disaster recovery. The migration owner is `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS` and owns the application database, `public` schema, and migration-created objects. The runtime login has the same restricted role attributes, belongs to no roles, owns no objects, cannot create schemas/tables/temporary tables, and receives:

- `CONNECT` on the application database and `USAGE` on `public`;
- only `SELECT` on Alembic migration metadata;
- `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on ordinary current tables;
- only `SELECT` and `INSERT` on `audit_entry`;
- `USAGE` and `SELECT` on current sequences;
- no `TRUNCATE`, `REFERENCES`, `TRIGGER`, function execution, DDL, or role-management authority.

Grant reconciliation revokes before it grants and installs owner-scoped default privileges for future ordinary objects. It must be rerun after every migration so exceptional tables are explicitly narrowed. The runtime check fails closed when roles are privileged, ownership is wrong, migrations are absent, audit privileges are broader than allowed, or any current table lacks the expected CRUD/no-DDL shape.

## Test database isolation

Database tests require `TEST_DATABASE_URL` for a unique, empty, ephemeral
PostgreSQL 17 database. Never point it at a shared, development, staging, or
production database: migration fixtures downgrade that database to base. Tests
exercise empty upgrade, exact current/head inspection, schema contents,
downgrade, transaction commit/rollback, and readiness mismatch behavior.

## Change checklist

A database change requires task ownership, migration reservation, model/schema alignment, forward and failure-path tests, rollback or forward-recovery analysis, data backfill and lock-duration analysis where applicable, compatibility impact, and sanitized evidence. Never create a second migration head to bypass coordination.
