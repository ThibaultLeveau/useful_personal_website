# Inspect system health

Signed-in administrators can open **Health** in the administration navigation at
`/admin/health`. The page exposes only a safe deployment summary; it is not a database console or a
substitute for private operator telemetry.

## Interpret the status

- **Operational** means the application responded, PostgreSQL was reachable, and the database
  revision matched this build.
- **Degraded** means the administration interface is running but database connectivity or migration
  compatibility needs operator attention.
- **Unavailable** means the browser could not obtain a current health response.
- **Unknown** means the response could not be safely interpreted.
- **Stale result** means the visible values came from the previous successful check because refresh
  failed. Do not treat them as current.

The page also shows when the result was checked and bounded build/commit labels. It never displays a
database host, connection string, SQL statement, credential, or internal revision value.

## Refresh and recover

Choose **Refresh status** to request a new result. Other navigation remains available while the
request is pending. If refresh fails, record the displayed request ID, confirm network access, and
retry. Operators can use that ID in sanitized application logs.

If the session has expired, protected health details and the signed-in shell are removed before the
session-expired screen appears. Sign in again; do not use Back as evidence that the old snapshot is
current. If an initial password change is still required, complete it before accessing health.

Deployment and monitoring details are in the [health API guide](../api/health.md).
