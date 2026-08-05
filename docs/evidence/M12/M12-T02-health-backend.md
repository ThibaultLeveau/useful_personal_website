# M12 safe health backend

Date: 2026-08-04

The accepted M2 process-only liveness and bounded PostgreSQL/migration readiness probes remain unchanged. The authenticated administrator aggregate reports only application/database/migration categories, build version/commit, and server observation time. Database failure, migration mismatch, probe exception/timeout, authentication, cache, and disclosure tests remain in the full backend suite. No hostname, endpoint, credential, revision identifier, SQL, pool detail, exception, or operational control is exposed.
