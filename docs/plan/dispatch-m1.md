# Milestone 1 Dispatch

## Dependency status

M0 evidence records T01-T06 as Pass. T07's environment/container portion passes, but T07 remains Blocked on real bootstrap and demo seed. T08 has no acceptance record and Infrastructure is actively implementing CI.

- `M1-T01` is dispatch-ready as the approved bridge that implements real identity bootstrap and closes only the bootstrap half of M0-T07.
- Demo seed remains later and separate. M1 creates no demo content, credential, or API token and does not mark T07/M0 complete.
- `M1-T02` waits for the backend auth contract and regenerated client.
- `M1-T03` waits for passing T01 and T02 evidence.

Infrastructure retains exclusive ownership of `.github/workflows/**`, `.pre-commit-config.yaml`, `Makefile`, `scripts/task.py`, scanner/coverage configuration, T08 reports, and T08 evidence. M1 may run but must not edit these files. Integration/root must coordinate any root `pyproject.toml`/`uv.lock` Argon2 update after confirming it does not overlap T08; Backend does not edit root manifests or locks.

## Reservations

| Owner | Exclusive M1 area |
|---|---|
| Backend Agent | `backend/app/modules/identity/**`, minimal `backend/app/modules/audit/**`, `backend/app/infrastructure/rate_limit/**`, `backend/app/commands/bootstrap_admin.py`, auth router/dependencies/schemas under `backend/app/api/v1/**`, auth-only changes to router/config/main, identity/auth tests, and `docs/evidence/M1/M1-T01-backend.md`. |
| Backend Agent — migration | Sole revision `backend/migrations/versions/20260802_0002_identity_auth.py` with `down_revision = "20260802_0001"`; administrator, session, rate-limit, and minimal audit persistence only. No other M1 revision or merge head until T01 closes. |
| Integration/root — contract | Sole writer of `docs/api/openapi.json`, generator/export/validator scripts if required, `frontend/src/generated/api/**`, contract-refresh evidence, and final M1 acceptance records. |
| Frontend Agent | After client freeze: `frontend/src/features/auth/**`; admin login/change-password/session-expired/account routes; protected changes to admin layout/page and `components/admin/admin-shell.*`; handwritten auth wrappers/tests under `frontend/src/lib/api/**`; one selected Next auth request boundary (`proxy.ts` or `middleware.ts`, not both); frontend auth evidence. |
| Integration/root — E2E | After T01/T02: `frontend/e2e/auth*.spec.ts`, auth-only E2E fixtures, adversarial reports/traces/screenshots, bootstrap/first-login and auth API docs, traceability updates, final M1 gate. |

Backend owns executable Pydantic source; Integration/root alone exports and generates; Frontend never edits generated files. Infrastructure owns Docker/Compose/environment/CI files. Existing architecture, requirements, UX, and planning sources are read-only.

## Backend-first contract freeze

### B1 — auth API contract

Backend first submits passing contract tests for:

- `/api/v1/auth/*` paths/methods and stable operation IDs;
- explicit envelopes, session state including `must_change_password`, safe `401/403/422/429` errors and `Retry-After`;
- login/logout/session/CSRF/password-change semantics;
- `__Host-admin_session`, signed double-submit `__Host-admin_csrf` plus `X-CSRF-Token`, trusted Origin, and `private, no-store` behavior;
- CLI-only idempotent bootstrap and server-side denial of ordinary admin access until password change.

Integration/root records B1 only after migrated-PostgreSQL API smoke and OpenAPI convention tests pass. Later contract changes require root coordination and regeneration.

### B2 — generated auth client

After B1, Integration/root performs the only OpenAPI/client refresh. B2 requires deterministic no-diff regeneration, unique operation IDs, complete security/error declarations, strict client compile, wrapper/boundary tests, and unchanged health contracts. B2 releases T02.

## Ordered assignments

1. **Start now — Backend Agent, `M1-T01`:** implement administrator/session/rate-limit/minimal-audit backend, explicit bootstrap, revision `20260802_0002`, API, and tests within the reservations above.
2. **After B1 — Integration/root:** refresh and verify OpenAPI/generated client; record B2. This may run while Backend finishes noncontract security verification.
3. **After B2 — Frontend Agent, `M1-T02`:** implement login, forced password change, session-expired/account, and protected shell against frozen generated types. It may run while Backend finishes T01, but cannot close before T01 passes.
4. **After T01/T02 pass — Integration/root, `M1-T03`:** own real browser/API lifecycle, adversarial validation, docs, traceability, and M1 acceptance.

Safe parallelism is file-disjoint: Backend identity may run now beside Infrastructure CI; after B2 Backend verification and Frontend auth may run together. Frontend work before B2 and M1 edits to CI/task-runner/scanner files are prohibited.

## Blocking acceptance/security gates

| Task | Required evidence before release |
|---|---|
| T01 | One Alembic head `20260802_0002`; empty/current/prior-baseline migration tests; bootstrap idempotency/replay refusal/no startup action; Argon2id benchmark and hash inspection; digest-only 256-bit sessions; cookie/expiry/rotation/revocation; non-enumerating login and PostgreSQL rate limits; CSRF/Origin/authz/mass-assignment/injection negatives; append-only audit and DB/log redaction; Ruff, strict Mypy, Bandit, backend tests, and reviewed OpenAPI diff. |
| T02 | Strict TS/lint/build; component/form/story/axe tests for loading/error/unauthorized/expired/success; safe return path; password manager/paste/reveal; focused forced-change flow; protected cache/state/DOM clearing; no session secret in JS storage; mobile/desktop browser evidence. |
| T03/M1 | Real bootstrap -> login -> forced change -> protected shell -> logout/expiry/password revocation plus replay, invalid login, brute-force, forged/missing CSRF, untrusted Origin, headers/CORS/cache and DB/log/audit inspection; first-login docs; AC-015-AC-017, auth portion AC-024, AC-025, AC-032-AC-033, AC-039, and AC-041 mapped to durable evidence. |

Confirmed Critical/High findings, a second migration head, default/takeover bootstrap, recoverable password/session secret, enumeration, CSRF/Origin bypass, ordinary access during forced change, missing audit/redaction, generated-client drift, stale protected UI, or weakened CI/security gates block downstream dispatch.
