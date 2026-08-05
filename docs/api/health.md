# Health API

Health operations separate process liveness, traffic readiness, and the authenticated administrator
summary. They never return hostnames, ports, database URLs, SQL, environment dumps, credentials,
cookies, stack traces, exception classes, or raw Alembic revision values.

## `GET /api/v1/health/live`

Liveness answers only whether the application process can serve HTTP. It performs no database,
migration, or other dependency call—even when those dependencies are unavailable, timed out, or at
an incompatible revision.

```json
{
  "data": { "status": "ok" },
  "meta": { "request_id": "docs-request-id-0001" }
}
```

Success is `200` with `Cache-Control: no-store`. A platform should restart a process only when this
probe itself fails; database outages must not create a restart loop.

## `GET /api/v1/health/ready`

Readiness checks PostgreSQL connectivity and exact compatibility with the packaged Alembic head.
Current/reachable returns `200`:

```json
{
  "data": { "status": "ready" },
  "meta": { "request_id": "docs-request-id-0001" }
}
```

An outage, timeout, unconfigured dependency, or revision mismatch returns `503` with the standard
error envelope. Only a safe dependency category is exposed:

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "A required dependency is unavailable.",
    "details": { "status": "not_ready", "dependency": "database" },
    "request_id": "docs-request-id-0001"
  }
}
```

`dependency` is `database` for connectivity/timeout failures and `migration` for a reachable but
incompatible revision. Operators should remove the instance from traffic on `503`, diagnose via
private operational tooling, and never use the public response as a substitute for database logs.

## `GET /api/v1/admin/health`

This endpoint requires a full administrator browser session whose forced password change is
complete. It returns `private, no-store` safe aggregate data:

```json
{
  "data": {
    "status": "operational",
    "application_status": "operational",
    "database_status": "operational",
    "migration_status": "current",
    "build_version": "0.2.0",
    "build_commit": "unknown",
    "checked_at": "2026-08-03T09:00:00Z"
  },
  "meta": { "request_id": "docs-request-id-0001" }
}
```

`status` is `operational` or `degraded`. A migration mismatch reports an operational database and
unavailable migration; a connectivity failure reports unavailable database and unknown migration.
Build identifiers are bounded deployment labels, not environment data. Authentication failures use
the stable `401`/`403` errors before health details are evaluated.

The back-office page is `/admin/health`. Refresh disables only the refresh control. A failed refresh
retains the last result but marks it stale, presents a request ID and recovery guidance, and announces
the outcome through a polite live region. A `401` clears the snapshot and the administrator shell
before routing to the session-expired screen.

## Monitoring guidance

- Poll liveness and readiness separately; do not cache either response.
- Correlate incidents with `X-Request-ID`; never add secrets to the request ID.
- Use readiness for traffic admission and liveness for process restart decisions.
- Configure build version/commit from trusted deployment metadata. Never put a branch credential,
  URL, or secret in either field.
- The application checks compatibility but does not run migrations at startup. Apply migrations as
  the migration role, reconcile permissions, then admit traffic.
