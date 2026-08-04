# M5 security certification

The exact M5 backend and frontend images were scanned by pinned
`aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`
with vulnerability and secret scanners at High/Critical blocking severity. Both reports contain
zero High, zero Critical, and zero secrets.

Bandit 1.9.4 scanned 13,167 backend lines with zero findings. `pip-audit` against a frozen `uv`
export and `pnpm audit --prod --audit-level high` reported no known vulnerabilities. Temporary
dependency-export material was removed in the command's `finally` block.

Application negative tests cover full-session authorization, forced-password restriction,
CSRF/origin, IDOR, mass assignment, SQL/query allow-lists, safe URL schemes, stale preconditions,
idempotency conflicts, and safe error envelopes. Public DTO and rendered-DOM inspection found no
draft/revision/creator/version/schedule/deletion fields or hidden skill. Preview is private,
no-store, and non-indexable. No scanner suppression or threshold reduction was added.

Raw machine-readable reports: [backend](trivy-backend.json) and [frontend](trivy-frontend.json).
