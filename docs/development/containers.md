# Local Containers

## Scope and security model

`compose.yaml` provides the local, production-shaped topology: PostgreSQL 17.10 at the F0 digest, a FastAPI image, a Next.js image, a named private media volume, profile-gated one-shot database operations, and a read-only permission gate. Application images use exact runtime image digests, multi-stage dependency/build steps, UID/GID 10001, read-only root filesystems, bounded temporary filesystems, and `no-new-privileges`. PostgreSQL helper jobs use the same digest-pinned image, UID/GID 999, read-only filesystems, and bounded temporary filesystems.

Compose is a local orchestration aid, not the production TLS edge described by ADR-0012. Published application ports bind only to `127.0.0.1`; PostgreSQL has no host port. The `private` network is internal. Browser calls to `/api/v1` that reach the local Next.js container are rewritten to `http://backend:8000` through the server-only fallback proxy, so cookies and CSRF remain same-origin. Production deployments must inject secrets through the platform secret manager and configure the preferred same-origin TLS edge, backups, object storage, and reviewed trusted origins.

## Prepare configuration

Copy `.env.example` to ignored `.env`. Set three distinct role names and three distinct URL-safe random database passwords of at least 32 characters:

- `POSTGRES_USER` is the image-required bootstrap cluster administrator. It provisions roles only and is never injected into backend or migration containers.
- `POSTGRES_MIGRATION_USER` is a `NOSUPERUSER NOCREATEDB NOCREATEROLE` database/schema owner used only by Alembic and grant reconciliation.
- `POSTGRES_RUNTIME_USER` is a `NOSUPERUSER NOCREATEDB NOCREATEROLE` non-owner used only by the backend and permission gate.

Leave no required value blank. Development does not require the three application signing/digest secrets, but independent values of at least 32 random bytes are mandatory when `APP_ENVIRONMENT=production`.

The backend accepts only the private `APP_` variables documented in [configuration](configuration.md). Compose supplies the frontend runtime only the non-secret, server-only `UPW_API_UPSTREAM_ORIGIN`; it supplies no `NEXT_PUBLIC_*`, database credential, or application secret. The proxy matches exactly `/api/v1/:path*`, preserves the browser request method/body/cookies/Origin/CSRF headers and upstream `Set-Cookie` response, and performs no authorization decision. Other routes stay in Next.js.

## Build, migrate, and start

From the repository root:

```console
docker compose build backend frontend
docker compose up --detach postgres
docker compose --profile operations run --rm role-init
docker compose --profile operations run --rm migrate
docker compose --profile operations run --rm permissions
docker compose up --detach backend frontend
docker compose ps
```

`role-init` is idempotent and also runs automatically once when the PostgreSQL data directory is first initialized. Running it explicitly reconciles role attributes/passwords and supports existing-volume upgrades. `migrate` is the container equivalent of `uv run --frozen alembic -c backend/alembic.ini upgrade head`; it receives only migration-owner credentials. `permissions` runs after migration, resets current/default privileges, and verifies them by reconnecting as the runtime role.

Ordinary `docker compose up` never selects the `operations` profile and cannot run role repair, Alembic, bootstrap, or seed. The backend depends only on `permissions-check`, a read-only one-shot check using runtime credentials. If migration or permission reconciliation was skipped, that check fails and the backend does not start.

Backend liveness and readiness are available at `/api/v1/health/live` and `/api/v1/health/ready`. The backend health check uses readiness, so it remains unhealthy until PostgreSQL is reachable and the backend-supported revision is current. Frontend health checks `/` only after the backend is healthy.

## Existing named-volume upgrade

Initialization scripts do not rerun when `postgres-data` already exists. Preserve the volume and its backups, update `.env` with distinct bootstrap/migration/runtime values, and run the same explicit sequence:

```console
docker compose up --detach postgres
docker compose --profile operations run --rm role-init
docker compose --profile operations run --rm migrate
docker compose --profile operations run --rm permissions
docker compose up --detach backend frontend
```

`role-init` connects with the existing volume's working `POSTGRES_USER` credentials, creates or rotates the two least-privilege roles, reassigns objects owned by the bootstrap identity to the migration owner, and transfers database/public-schema ownership. If the original bootstrap username or password is no longer known, stop: restore access through an approved PostgreSQL operator procedure rather than deleting the volume or editing authentication files ad hoc. Back up before ownership changes.

After every future Alembic upgrade, rerun `permissions`. Default privileges make ordinary owner-created tables usable, but reconciliation is the reviewed point that narrows exceptional tables such as `audit_entry`. Do not start a new backend revision until this operation and its runtime check pass.

## Stop and clean up

Stop only this Compose project:

```console
docker compose down --remove-orphans
```

This preserves the `postgres-data` and `local-media` named volumes. Deleting them is destructive and outside the routine shutdown command. Back up database and media together before any intentional volume removal.

## Bootstrap and seed boundary

Administrator bootstrap and demo seed are explicit operator actions, never dependencies of PostgreSQL, migration, permission reconciliation, backend, or frontend startup. Startup and migration remain independent of both operations; seed must create no users or tokens and must refuse production.

After migration and permission reconciliation, follow [first administrator setup and sign-in](../user/first-login.md). The documented one-shot command overrides the backend container command, reads the initial credential through standard input, uses the non-owner runtime database identity, and refuses replay once any administrator exists.

To add fictional website settings, a public profile, navigation, and footer for local demonstration, run the separate operation explicitly:

```console
docker compose --profile operations run --rm seed-demo
```

The seed converges to the same content on repeat runs, runs in one transaction, creates no administrator, session, API token, credential, contact submission, media object, or analytics credential, and refuses when `APP_ENVIRONMENT=production`. It is never selected by ordinary startup.
