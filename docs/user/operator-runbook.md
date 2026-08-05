# Operator runbook

This is the day-to-day entry point for a self-hosted Useful Personal Website instance. It links to
the detailed authorities instead of duplicating security-sensitive procedures. Complete the
production decisions in the [owner decision register](../evidence/M13/owner-decisions.md) before
serving public traffic; the local Compose topology is production-shaped but is not a TLS edge or a
production backup service.

## Install and start

1. Copy `.env.example` to the ignored `.env` file and replace every required blank. Use distinct,
   URL-safe database credentials and independent application keys. Review the complete
   [configuration contract](../development/configuration.md).
2. From the repository root, build, initialize roles, migrate, reconcile permissions, and start:

   ```console
   docker compose build backend frontend
   docker compose up --detach postgres
   docker compose --profile operations run --rm role-init
   docker compose --profile operations run --rm migrate
   docker compose --profile operations run --rm permissions
   docker compose up --detach backend frontend
   docker compose ps
   ```

3. Confirm `/api/v1/health/live`, `/api/v1/health/ready`, and `/` return HTTP 200. Readiness must
   remain closed when PostgreSQL, the migration revision, permissions, or required dependencies are
   invalid.
4. Follow [first administrator setup](first-login.md). Bootstrap is one-shot, reads the temporary
   password from standard input, and must be completed before the first sign-in.

Routine shutdown uses `docker compose down --remove-orphans`; it preserves the `postgres-data` and
`local-media` volumes. Never add `--volumes` to routine shutdown.

## Operate content

Use the focused guides for [site configuration](site-configuration.md), [skills](skills.md),
[experience](experiences.md), [projects](projects.md), [blog](blog.md), [configurable pages and
blocks](pages.md), and [media](media.md). Private operational workflows are documented for the
[contact inbox](contact-inbox.md), [API tokens](api-tokens.md), [audit log](audit.md), and [system
health](system-health.md).

Publish only reviewed revisions. Preview content before publication, keep hidden/draft content out
of public navigation, give every meaningful image contextual alternative text, and revoke API
tokens that are no longer required. Token secrets appear once and must go directly into the
approved secret manager.

## Upgrade an existing installation

Preserve and back up both named data stores before changing images or ownership. Do not recreate an
existing PostgreSQL volume to make initialization scripts rerun. With the existing volume and its
working bootstrap identity available, update the source and `.env`, then run:

```console
docker compose build backend frontend
docker compose up --detach postgres
docker compose --profile operations run --rm role-init
docker compose --profile operations run --rm migrate
docker compose --profile operations run --rm permissions
docker compose up --detach backend frontend
docker compose ps
```

After every migration, permission reconciliation is mandatory. Stop the rollout if migration or
permission checks fail; never edit or stamp `alembic_version` manually. The full ownership and
existing-volume rules are in the [container runbook](../development/containers.md) and [migration
protocol](../development/database-and-migrations.md).

## Backup and recovery

A valid recovery point is coordinated: it contains a PostgreSQL backup and the corresponding
private media/object snapshot from one recorded cutoff. Protect both with the approved encryption,
retention, access, and deletion policy. A database-only or media-only copy is incomplete.

Restore into an isolated environment first. Apply the expected migration, reconcile runtime
permissions, run media reconciliation in dry-run mode, compare ready asset and rendition
checksums/counts, inspect usage pointers, sample authenticated and eligible public delivery, and
only then start application traffic. The exact validated local proof and its limits are recorded in
the [M14 restore drill](../evidence/M14/restore-drill.md); provider, schedule, RPO/RTO, key owner, and
incident owner remain deployment-specific decisions. See [media operations](media-operations.md)
for the reconciliation safety boundary.

## Troubleshooting and escalation

- If readiness fails, inspect the safe dependency category and request ID, then verify PostgreSQL,
  the exact Alembic head, permission reconciliation, media configuration, and the same-origin API
  route. Do not bypass readiness.
- If sign-in or CSRF fails, verify the exact public origin, proxy forwarding of `Origin`, cookies,
  `X-CSRF-Token`, and `Set-Cookie`, and the administrator guide. Do not disable origin or CSRF
  checks.
- If media reconciliation reports missing, corrupt, orphaned, or uncertain objects, stop automatic
  deletion and escalate with sanitized counts and opaque identifiers only.
- If a migration, restore, security scan, or accessibility acceptance gate fails, keep the prior
  release serving and record the finding. Do not waive a release blocker silently.

Logs, tickets, and evidence must never contain passwords, database URLs, cookies, CSRF values, API
token plaintext, contact bodies, private filenames, object keys, signed URLs, or production dumps.
