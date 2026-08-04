# Milestone 2 Dispatch

## Dispatcher status

This document prepares `M2-T01` through `M2-T03` for dispatch. It does not release implementation, record a task as passing, or accept Milestone 2.

The current repository contains active M1 identity/authentication work and active M0 CI work. There is no M1 acceptance bundle yet. Therefore every M2 task remains blocked until the dependency gates below have durable evidence and Integration/root explicitly releases the relevant reservation.

| Task     | Current state | Release condition                                                                                                        |
| -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `M2-T01` | Blocked       | Gates G0-G2 pass and the M1/M0 shared-file reservations are released.                                                    |
| `M2-T02` | Blocked       | `M2-T01` passes, contract freeze C1 is recorded, and its backend, generation, and frontend stages are released in order. |
| `M2-T03` | Blocked       | `M2-T01` and `M2-T02` pass and contract freeze C2 is recorded.                                                           |

Milestone 2 maps to trace milestone `M05`. Its goal is to stabilize the common API contract used by later feature slices; it does not authorize profile/settings, content, media, contact, API-token, or audit-viewer feature work.

## Dependency gates from M1 and M0

### G0 - Foundation and reservation release

Integration/root must confirm all of the following before any M2 write:

- M0 foundation records required by M1 remain passing and the active `M0-T08` CI assignment has either passed or explicitly released its files;
- the canonical local/CI commands run without M2 weakening, suppressing, or editing a gate;
- root manifests and locks are stable, or any required dependency change has a separately coordinated Integration/root assignment;
- the committed OpenAPI artifact and generated client have no unexplained drift before the M2 baseline is taken.

M2 agents may run the existing CI/task-runner commands while G0 is pending, but may not edit their definitions.

### G1 - M1 identity and data gate

The final M1 record must show `M1-T01` through `M1-T03` passing, including:

- explicit one-time bootstrap, login, forced password change, session inspection, logout, expiry, password revocation, CSRF/Origin, brute-force, and protected-route browser/API evidence;
- non-enumerating authentication, digest-only sessions, Argon2id policy, audit/redaction, and no unresolved Critical/High finding;
- exactly one Alembic head at `20260802_0002` (file `20260802_0002_identity_auth.py`) with empty/current/prior-baseline migration evidence;
- accepted auth Pydantic schemas, operation IDs, security declarations, errors, cookies/cache behavior, and a deterministic generated auth client;
- the M1 frontend no longer has stale protected state and its auth wrapper/boundary tests pass.

M2 may reuse M1's actor/session facade and rate-limit port. It must not reach into identity repositories/ORM types, replace the auth error contract, or duplicate auth/session/rate-limit/audit persistence.

### G2 - M1 contract baseline

Integration/root snapshots the post-M1 baseline and records:

- clean OpenAPI export, schema lint, unique operation IDs, deterministic regeneration, and strict generated-client compile;
- the set of stable M1 auth error codes and security schemes that M2 must preserve;
- one backend architecture-boundary pass proving `api -> application -> domain` and module-to-module access through application facades;
- passing full affected backend/frontend tests and the same-origin built-app auth smoke.

Only G2 releases `M2-T01`. A contract discrepancy is corrected and re-evidenced in M1; M2 must not conceal it with a compatibility shim.

## Reservations and excluded active files

### Files excluded while M1 identity/authentication is active

M2 must not edit, move, delete, format, or regenerate any of the following until Integration/root closes M1 and releases the reservation:

- `backend/app/modules/identity/**`;
- the M1-owned minimal `backend/app/modules/audit/**` and `backend/app/infrastructure/rate_limit/**`;
- `backend/app/commands/bootstrap_admin.py` and bootstrap wrappers;
- auth routers, dependencies, schemas, tests, and auth-only changes to `backend/app/api/v1/router.py`, `backend/app/config.py`, and `backend/app/main.py`;
- `backend/migrations/versions/20260802_0002_identity_auth.py` and all M1 migration fixtures/evidence;
- `frontend/src/features/auth/**`, login/change-password/session-expired/account routes, protected admin layout/page, and `frontend/src/components/admin/admin-shell.*`;
- M1-owned changes under `frontend/src/lib/api/**`, and the selected `frontend/src/proxy.ts` or `frontend/src/middleware.ts` boundary;
- `frontend/e2e/auth*.spec.ts`, auth fixtures, M1 reports, M1 documentation, and `docs/evidence/M1/**`;
- the in-flight M1 versions of `docs/api/openapi.json` and `frontend/src/generated/api/**`.

After G2, M2 treats identity, session, CSRF, rate-limit, and minimal-audit behavior as provider contracts. Any required change is routed back to the M1 owner and reviewed by Integration/root; it is not absorbed into an M2 common helper.

### Files excluded while M0 CI is active

M2 may consume but must not edit:

- `.github/workflows/**`;
- `.pre-commit-config.yaml`;
- `Makefile` and `scripts/task.py`;
- scanner, dependency-audit, coverage, and CI report configuration;
- `docs/evidence/M0/M0-T08*` and the final M0 CI acceptance record;
- root `pyproject.toml`, `uv.lock`, `package.json`, `pnpm-lock.yaml`, and other root toolchain manifests/locks.

If an M2 check is missing from CI, its command and evidence are supplied to the active CI owner. An M2 agent does not patch the workflow or lower a threshold. Requirements, architecture, ADR, UX, and existing planning sources remain read-only unless a separate correction is dispatched.

## Owner-safe M2 lanes

| Stage                                  | Owner                              | Exclusive write area                                                                                                                                                                                                                                                                | Exclusions and handoff                                                                                                                                                                                                                                                                                |
| -------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M2-T01-B` common backend              | Backend Agent                      | New/changed API-convention code under `backend/app/common/{domain,application,security}/**`; request-context/observability middleware and API dependencies/schemas needed only for common conventions; common backend unit/integration tests; `docs/evidence/M2/M2-T01-backend.md`. | Starts only after G2. Does not edit identity/audit/rate-limit internals, OpenAPI artifact, generated code, frontend, CI, or final acceptance records. Shared `backend/app/api/v1/{router,schemas,errors}.py` and `backend/app/main.py` are a single sequential Backend window after M1 releases them. |
| `M2-T01-M` migration                   | Backend Agent, same T01 assignment | Sole M2 revision `backend/migrations/versions/20260802_0003_api_conventions.py`, idempotency persistence adapter/model, and its migration/repository tests.                                                                                                                         | Starts only after M1's `0002` is accepted as the sole head. Scope is actor+route idempotency records and necessary constraints/indexes only.                                                                                                                                                          |
| `M2-T01-I` contract integration        | Integration/root                   | Contract tests/reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, and the T01 contract-refresh/final acceptance record.                                                                                                                                             | Runs after Backend submits executable Pydantic source and passing tests. Integration/root is the only generator writer. Records C1; does not implement Backend behavior or frontend feature UI.                                                                                                       |
| `M2-T02-B` health backend              | Backend Agent                      | `backend/app/modules/health/**`, `backend/app/api/v1/health.py`, health-specific tests, and `docs/evidence/M2/M2-T02-backend.md`; read-only use of the existing DB revision probe.                                                                                                  | Starts after C1. Does not add a migration, alter auth, expose infrastructure details, or edit generated/frontend files. Submits the executable health contract before frontend work.                                                                                                                  |
| `M2-T02-I` health contract integration | Integration/root                   | Health OpenAPI review/export, generated-client regeneration, generated compile/no-diff reports, and freeze C2.                                                                                                                                                                      | Begins only after the health backend contract passes. This is a sequential writer window; Backend and Frontend do not touch artifact/generated files.                                                                                                                                                 |
| `M2-T02-F` health frontend             | Frontend Agent                     | Handwritten health/client changes under `frontend/src/lib/api/**`, `frontend/src/features/health/**`, a health route owned after the M1 admin-shell release, component/stories/tests, and `docs/evidence/M2/M2-T02-frontend.md`.                                                    | Starts only after C2. Consumes generated types; never edits generated output. Any shared admin-shell change requires an explicit post-M1 reservation from Integration/root.                                                                                                                           |
| `M2-T03-I` certification               | Integration/root                   | M2 contract/E2E fixtures and tests, common API/health documentation, scope/error/filter catalogs, sanitized reports, `docs/evidence/M2/M2-T03.md`, final M2 acceptance record, and traceability evidence links.                                                                     | Starts after T01/T02 pass. It may correct integration-only defects; behavioral defects return to their owning lane. It does not start M3 or mark M2 accepted without independent review.                                                                                                              |

No two lanes edit the same file concurrently. Backend owns executable Pydantic source; Integration/root owns exported and generated contracts; Frontend owns handwritten consumption only after the corresponding generated freeze.

## Sole migration policy

`M2-T01-M` is the sole migration assignment for Milestone 2. The planned revision is:

```text
revision: 20260802_0003
down_revision: 20260802_0002
scope: idempotency records, actor+route/key uniqueness, expiry and operational indexes
```

The revision is created only after G1 confirms `20260802_0002` is the accepted single head. It must not duplicate identity, session, rate-limit, or audit tables. Idempotency retention is 24 hours; persisted records must not unnecessarily retain private response bodies or secrets.

No M2-T02 migration is planned. Readiness compares the runtime database revision with the packaged Alembic head through the existing probe. If T02 uncovers a genuine schema requirement, work stops at C1 and Integration/root either returns the change to the still-open T01 migration owner or dispatches one explicitly named forward revision after T01 closes. Parallel revisions and merge heads are prohibited.

Migration acceptance requires empty-database upgrade, upgrade from accepted `0002`, current/head equality, schema/model comparison, constraint/index inspection, representative idempotency data behavior, downgrade only where the project migration policy requires it, and one-head verification. Production startup must not run migrations.

## OpenAPI and generated-client single-writer policy

Backend agents author and test the executable FastAPI/Pydantic contract: request/response types, operation IDs, envelopes, errors, examples, cache headers, and security declarations. They do not edit the committed OpenAPI artifact.

Integration/root alone may write:

- `docs/api/openapi.json`;
- `frontend/src/generated/api/**`;
- generator/export/validator configuration or scripts, if a separately reviewed change is necessary;
- schema snapshots, generator reports, and final cross-lane contract evidence.

Frontend imports generated types only through handwritten wrappers and never patches generated code. Each regeneration uses the pinned standard generator and must be deterministic: export, validate/lint, generate, format only as configured, strict compile, regenerate again, and produce no diff. Backend contract changes and their generated output land in the same Integration/root window.

## Contract freeze points

### C1 - Common API conventions freeze

Integration/root records C1 after `M2-T01-B/M` pass and the first M2 regeneration is clean. C1 freezes:

- `/api/v1` namespace and audience separation;
- single/list success and error envelope shapes and request-ID correlation;
- stable error/status mapping and typed validation details;
- page-number pagination (`page=1`, `page_size=20`, maximum `100`, totals and beyond-last behavior);
- allow-listed filter/sort grammar, duplicate/unsupported-field rejection, and deterministic `id` tie-breaker;
- RFC 3339 UTC timestamps, calendar dates, `snake_case`, and opaque UUID semantics;
- public/session/token actor-context interfaces and explicit use-case authorization boundary;
- integer version/ETag behavior, required `If-Match`, `428 PRECONDITION_REQUIRED`, and `409 RESOURCE_VERSION_CONFLICT`;
- actor+route idempotency semantics, 24-hour retention, replay/conflict behavior, and safe persistence;
- M1 auth/security declarations and error codes unchanged.

C1 releases the health backend lane. A later incompatible change requires an explicit CHG-002 record with implementation, migration, generation, consumer, test, and acceptance impact; it is not silently folded into T02.

### C2 - Health and handwritten-client freeze

Integration/root records C2 after the T02 backend contract passes and regeneration is clean. C2 freezes:

- `GET /api/v1/health/live` as process-only with no dependency calls;
- `GET /api/v1/health/ready` as PostgreSQL connectivity plus migration-compatibility readiness, returning safe `200 ready` or documented `503 not_ready` behavior;
- authenticated admin health as safe aggregate/build information with `private, no-store` and no host, SQL, environment, credential, or stack detail;
- generated health operation IDs, response/error schemas, examples, and security declarations;
- same-origin wrapper defaults, cookie credentials, CSRF on unsafe cookie-authenticated methods, request-ID forwarding/correlation, injected fetch, and safe typed `ApiError` translation without raw-body leakage.

C2 releases the frontend health lane. Any generated-contract defect returns to Backend plus Integration/root; Frontend must not compensate with `any`, duplicate transport types, or raw fetch calls.

### C3 - M2 feature-fan-out certificate

`M2-T03-I` may record C3 only after all acceptance evidence below passes. C3 is the reviewed v1 baseline for M3 and later feature teams: additive compatible changes are allowed through the same source/export/generation workflow; removals or semantic breaks require deprecation plus CHG-002/new-version review.

C3 is not itself acceptance. Integration/root separately records the M2 gate after independent API, security, quality, documentation, and evidence review.

## Dispatch order

1. **Do not start M2 implementation now.** Integration/root completes G0-G2 and releases M1/M0 reservations.
2. **After G2 - Backend `M2-T01-B/M`:** implement and verify common conventions plus the sole migration.
3. **After Backend T01 evidence - Integration/root `M2-T01-I`:** export, lint, regenerate, compile, review, and record C1.
4. **After C1 - Backend `M2-T02-B`:** implement the health contract and dependency-failure tests.
5. **After health contract evidence - Integration/root `M2-T02-I`:** perform the sole health contract refresh and record C2.
6. **After C2 - Frontend `M2-T02-F`:** finish handwritten transport behavior and the accessible admin health experience.
7. **After T01/T02 pass - Integration/root `M2-T03-I`:** run certification, consumer walkthrough, docs/security/API reviews, and prepare the M2 gate record.

Backend noncontract verification may continue while Integration/root performs a regeneration only when the files are disjoint. Frontend may not begin from an uncommitted schema or anticipated generated types.

## Exact acceptance, security, and quality evidence

All evidence follows `docs/plan/delivery-evidence-template.md`, records both `M2` and `M05`, uses repository-relative artifact links, and contains date, executor, environment, commit/worktree identity, tool versions, exact command/protocol, result, and defects/retests. Logs, API transcripts, screenshots, traces, and database samples must be sanitized; they must not contain cookies, CSRF values, authorization headers, passwords, private data, stack traces, production dumps, or machine-specific absolute paths.

### `M2-T01` release evidence

Required requirement mapping: `AC-027`-`AC-030`, `AC-035`; `API-001`-`API-006`, `SEC-004`, `SEC-006`; relevant `NFR-007`-`NFR-008`, `NFR-014`-`NFR-016` evidence.

Backend and data evidence must include:

- unit/property tests for envelope serialization, stable error registry, request-ID validation/replacement/correlation, ISO/UTC and opaque-ID rules;
- PostgreSQL integration tests for default/max/invalid/beyond-last pagination, exact total metadata, traversal without loss/duplication, and deterministic `id` tie-breaking;
- allow-list tests for supported filters and `sort=field,-other_field`, with safe `422` rejection of duplicate/unsupported fields, arbitrary `filter[...]`, SQL fragments, encoded operators, and column-name interpolation attempts;
- representative `400/401/403/404/409/422/428/429/500/503` mapping tests covering validation, absent/expired auth, unauthorized/IDOR, hidden not-found, conflict, precondition, rate limit with `Retry-After`, and internal failure; every error has a stable code, safe object `details`, and correlated request ID, with no stack/SQL/class/secret/existence leak;
- actor-context tests for public, administrator session, and token-shaped actors at the common policy boundary, including explicit resource/action authorization, mass-assignment rejection, and no repository/ORM reach-through;
- ETag/`If-Match` tests for success, missing precondition, stale version, concurrent update, and delete/action behavior;
- idempotency tests for actor+route+key scope, 24-hour expiry, same-request replay, mismatched-payload conflict, concurrent duplicate execution exactly once, and stored-record/log redaction;
- the sole migration evidence listed above, architecture-boundary results, query/constraint inspection, and no obvious N+1 or unindexed operational predicate in changed paths.

Contract, frontend, and flow evidence must include:

- OpenAPI validation, unique stable operation IDs, explicit success/error schemas, examples, security declarations, filters/sorts, deprecation metadata, and a reviewed schema diff;
- deterministic generated-client no-diff logs, strict TypeScript compile, typed success/error-mapper wrapper tests, and a scan proving imports of generated transport stay inside the approved wrapper boundary;
- a real PostgreSQL API flow that traverses a multi-page representative collection and triggers validation, authorization, conflict, rate-limit, and internal-safe errors while correlating `X-Request-ID` with envelope metadata/error data;
- Ruff format/lint, strict Mypy, full affected Pytest suites and coverage reports; Prettier, ESLint, strict TypeScript, affected Vitest/build checks; no disabled test or new unexplained warning.

Any SQL interpolation, IDOR/mass-assignment success, existence disclosure, stack/body/secret leak, incorrect retry semantics, duplicate side effect, generated drift, second migration head, or Critical/High finding blocks C1.

### `M2-T02` release evidence

Required requirement mapping: `AC-026`-`AC-030`, plus the applicable UI state/accessibility portions of `AC-025`, `AC-032`, and `AC-033`; `API-002`, `API-006`-`API-007`, `F2-020`, `SEC-004`-`SEC-005`, `SEC-009`.

Backend/contract evidence must include:

- liveness with PostgreSQL healthy, unreachable, and revision-mismatched, proving identical process-only success and no dependency call;
- readiness with healthy PostgreSQL/current revision (`200 ready`), database outage, timeout, and revision mismatch (`503 not_ready`) using safe typed dependency categories and correlated request IDs;
- authenticated admin-health success plus unauthenticated/expired-session denial, exact `private, no-store`, and safe build/aggregate fields;
- negative disclosure inspection across response, headers, structured logs, trace, and screenshot for hostnames, ports, connection strings, SQL, environment dumps, credentials, cookies, stack traces, exception classes, and raw migration internals;
- preserved restrictive CORS, auth/CSRF behavior where applicable, OpenAPI security declarations/examples/errors, deterministic regeneration, generated compile, and no diff.

Frontend and browser evidence must include:

- wrapper tests for typed live/ready/admin-health success; documented non-2xx envelopes; malformed/non-JSON responses; same-origin base path; cookie credentials; CSRF on unsafe session requests; request-ID forwarding; injected fetch; and no raw response/body/cause leak from `ApiError`;
- health component/story tests for `Operational`, `Degraded`, `Unavailable`, and `Unknown`, last-checked time, stale retained result, loading/error/unauthorized/offline states, and request-ID/docs recovery guidance;
- manual refresh disabling only its control, retaining previous status as stale, and announcing completion through a polite live region;
- keyboard/focus, semantic headings/status, text-plus-color status, 320/1440 and 400% reflow, light/dark/system, reduced-motion, and automated axe evidence with no unresolved blocker;
- real built-app Playwright flows for healthy admin health, database outage/recovery, unauthorized/expired session, and operational probes, with sanitized traces/screenshots.

Ruff/Mypy/Pytest and Prettier/ESLint/strict-TypeScript/Vitest/Storybook/build/full affected E2E must pass. A dependency call from liveness, false-ready revision mismatch, privileged admin-health access, sensitive disclosure, stale privileged DOM after expiry, inaccessible state, raw fetch bypass, or generated drift blocks C2/T02.

### `M2-T03` certification and M2 gate evidence

Required mapping: `AC-026`-`AC-030`, `AC-035`, `AC-037`, `AC-039`, `AC-042` API-conventions subset, and `AC-045`; `API-001`-`API-007`, `DOC-002`, `CHG-002`. `AC-042` remains release-level and is not claimed fully verified until the later API-token consumer workflow exists.

Certification must include:

- a full schema/conventions suite over representative success, single, list, validation, authentication, authorization, hidden not-found, conflict, precondition, rate-limit, internal failure, live, ready, and admin-health operations;
- deterministic OpenAPI export/generation twice with no diff, standard generator logs, strict generated-client compile, operation-ID uniqueness, reference resolution, and wrapper-boundary scan;
- a same-origin consumer walkthrough against built Next.js/FastAPI and fresh migrated PostgreSQL covering base/version discovery, health, request IDs, pagination, allow-listed filter/sort, safe errors/rates, ETag/`If-Match`, idempotency, and authentication/security declarations;
- API documentation for base URL/version/OpenAPI access, audience/auth model, envelopes, dates/IDs, pagination, filter/sort catalogs, status/error catalog, request IDs, rate limits, concurrency, idempotency, cache behavior, health, examples/cURL, and additive/deprecation/change policy;
- reviewed route/security and error/filter catalogs; restrictive CORS/cache/error-disclosure review; dependency and secret/privacy scans; no unresolved Critical/High issue;
- all affected backend/frontend/contract/migration/E2E suites, production frontend build, backend startup, coverage reports with target disposition, and CI command parity without editing active CI definitions;
- independent API, security, architecture, documentation, and evidence review; each finding linked to an AC/requirement, corrected by its owner, and independently retested;
- final evidence links added to traceability without changing stable IDs or prematurely marking later token/full-documentation work verified.

The M2 gate remains blocked by any failed Must requirement, weakened/suppressed check, unexplained generated diff, undocumented breaking change, multiple Alembic heads, placeholder/mock production path, unsanitized evidence, missing independent retest, or confirmed Critical/High finding. Passing individual task evidence does not authorize M3 until Integration/root records the separate M2 acceptance decision.
