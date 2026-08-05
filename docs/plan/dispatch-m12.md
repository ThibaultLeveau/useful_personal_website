# Milestone 12 Dispatch

## Dispatcher status

This document prepares `M12-T01` through `M12-T03`. It does not release implementation,
record acceptance, authorize M13, or treat the M11 planning document as proof that M11 passed.

| Task      | Current state | Release condition                                                                                                                           |
| --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `M12-T01` | Blocked       | Integration/root separately accepts M11, confirms its sole database head and released contracts, and records T0-T3 below.                   |
| `M12-T02` | Blocked       | T01 catalog/query/retention and health backend evidence passes; Integration/root records the deterministic contract freeze at T5.           |
| `M12-T03` | Blocked       | T02 audit/health UX passes at T6 and the complete event-family, degraded-health, retention, security, and documentation fixtures are ready. |

M12 maps to trace milestone `M16`. Its authorized outcome is a complete, append-only and
redacted audit catalog with bounded administrator inspection; the already specified liveness and
readiness probes plus an authenticated safe build/status view; an operator-only, dry-run-capable
400-day audit-retention command; accessible audit and health screens; generated contracts; and
operational evidence. It does not create a generic operations console, log viewer, metrics product,
backup UI, environment/configuration browser, database console, restart/deploy/migrate controls,
worker, scheduler, or a second audit store.

## Blocking predecessor and owner decisions

### T0 - Separate M11 acceptance and shared-surface release

Before any M12 implementation write, Integration/root must record:

- a separate accepted M11 gate covering `M11-T01` through `M11-T03`, with no unresolved
  Critical/High defect and no active M11 writer on a file M12 needs;
- exactly one Alembic head from the accepted M11 implementation. The M11 dispatch reserves
  `20260802_0012` in `20260802_0012_api_tokens.py`; M12 must verify that this is the actual accepted
  head rather than infer it from the plan;
- clean current/head equality, empty-database migration, OpenAPI validation, and deterministic
  generated-client regeneration at the accepted M11 commit;
- the accepted M11 route-to-scope matrix, especially the disposition of `admin:read`, and released
  administrator-session, API-token actor, CSRF/Origin, request-ID, safe-error, rate-limit,
  pagination/filter/sort, UoW, minimal-audit, and cache-control providers;
- a producer inventory for every implemented M3-M11 mutation, with the exact owning module and
  current audit event identifier, and released M2 liveness/readiness/build configuration contracts;
- an exact file manifest for shared routers, model registration, audit catalog, configuration,
  admin navigation, wrapper, generated client, E2E fixtures, and documentation surfaces that need
  serialized ownership.

M12 consumes earlier modules through their application services and audit port. It does not reach
into feature repositories, duplicate actor/request/UoW providers, rewrite prior migrations, or
reinterpret an unaccepted predecessor branch.

### T1 - Event catalog, metadata, and producer-coverage freeze

Security, Architecture, API, Operations, Integration/root, and every producer owner must publish one
machine-readable event coverage matrix before audit implementation starts. It must reconcile the
accepted identifiers already emitted by M1-M11 with these required semantic families:

- successful and failed authentication, logout, password change, and administrator security
  actions;
- API-token creation and revocation, plus any rotation/use/denial events already required by the
  accepted M11 contract;
- content creation, modification, and deletion for every implemented content aggregate;
- publication-state changes and website-settings changes;
- media deletion; and
- contact lifecycle/permanent deletion and any other earlier operation that its accepted milestone
  explicitly made auditable.

The matrix owns exact event identifiers; actor and resource types; success/failure outcome values;
metadata schema version; allowed metadata keys, types, bounds, and null behavior; producer location;
transaction behavior; and one positive and one redaction assertion per event. No lane invents a
parallel enum, renames an emitted event silently, accepts arbitrary JSON, or marks coverage complete
because a generic audit helper was called.

Every entry contains a UTC occurrence time and the correlated request ID when a request exists.
Operator/system events use a documented operation/run correlation identifier when no HTTP request
exists; they must not forge an HTTP request ID. Actor/resource identifiers and safe labels are
stable enough for attribution but may not expose administrator email, contact identity, content
bodies, storage keys, or token selectors beyond an already approved safe public identifier.

The forbidden-field corpus is global and fail-closed: passwords and password-derived material,
token secrets/digests/peppers, full or partial authentication headers, cookies/CSRF/idempotency
secrets, contact email/name/message/body, raw IP addresses, private draft/content bodies, raw upload
bytes/EXIF, SQL, hostnames, connection strings, environment dumps, stack traces, and unnecessary
personal data cannot enter audit metadata, logs, API responses, UI state, traces, screenshots, or
evidence. A keyed-HMAC IP pseudonym is allowed only where the accepted privacy policy and metadata
schema require it; it is never a raw-IP substitute chosen by a feature lane.

### T2 - Query, access, export, health, and operations freeze

Product, API, Security, Operations, and Integration/root must freeze the read contracts before
backend routes begin:

- the administrator audit list and durable detail paths, operation IDs, envelopes, exact safe
  projection, not-found policy, and cookie-session authorization;
- filters for event, safe actor, safe resource, outcome, UTC date interval, and exact request ID,
  including value/length bounds and half-open/inclusive date semantics;
- page-number pagination (`page=1`, `page_size=20`, maximum `100`) and the default deterministic
  order `(occurred_at DESC, id DESC)`. Any additional sort is denied unless explicitly allow-listed
  with an `id` tie-breaker; arbitrary expressions, metadata JSON search, substring scans, and raw
  column names are never accepted;
- whether the accepted M11 `admin:read` matrix contains separate integration audit/health routes.
  Browser `/admin/*` routes always require the administrator session and never accept bearer tokens;
  no integration route is inferred merely from the scope name;
- the authenticated admin-health path and safe schema: liveness/readiness concepts, safe aggregate
  status, build version, commit, and request correlation. Owners must map backend states to the UX
  labels `Operational`, `Degraded`, `Unavailable`, and `Unknown`, and decide whether `last_checked`
  is server observation time or client refresh time;
- exact probe timeouts/failure isolation and which required dependency categories may be named
  safely. Public liveness remains process-only; public readiness checks PostgreSQL reachability and
  migration compatibility without revealing a revision, hostname, credential, SQL, or exception;
- audit retention cutoff/time source, batch size/ordering, concurrency/retry semantics, dry-run
  output, execute confirmation, separate operator identity, least-privilege database credential,
  aggregate audit event, failure/partial-progress behavior, backup guidance, and deployment runbook;
  and
- owner/legal acceptance or release disposition of the ADR-0008 defaults: 400-day audit retention
  and the jurisdiction-specific policy caveat.

Admin auth, audit, and admin-health responses are `Cache-Control: private, no-store`; logout/session
expiry clears their client cache and protected DOM. Operational public probes are also non-cacheable
so a proxy cannot serve a stale readiness decision. All M12 web routes are read-only. If a later
owner-approved web mutation is added, cookie authentication requires the accepted CSRF token and
trusted-Origin policy; retention execution remains operator CLI-only in R1.

#### Blocking export and system-capability mismatch

The pasted master scope mentions “Data import and export,” but `F2-018`, `AC-024`, the M12 task
catalog, API architecture, and UX inventory specify audit list/detail/filtering, not audit export.
`assumptions-and-scope.md` leaves audit export expectations open, while ADR-0008 says to add
tamper-evident export only for a real compliance requirement. Therefore M12 has no audit-export
endpoint, button, file format, signing scheme, or evidence lane. An export request blocks and
requires CHG-002 updates covering requirements/AC, fields/redaction, authorization, volume limits,
streaming, formula injection, retention/tamper evidence, audit-of-export, API/UX, and tests before a
new dispatch.

Likewise “system administration” authorizes only the safe health/build view and documented operator
retention command in current sources. Any request for runtime logs, metrics, configuration values,
dependency addresses/versions, queues, sessions, filesystem/storage inspection, backups/restores,
deploy/restart/migration controls, or arbitrary commands is an owner blocker, not an implementation
detail. No production internals may be added to public health output.

### T3 - Query-plan/schema decision and conditional migration reservation

The Database, Security, Operations, and Integration owners inspect the accepted `audit_entry` schema,
runtime/operator grants, retention needs, and `EXPLAIN (ANALYZE, BUFFERS)` evidence using
representative volume and every T2 filter/order combination. Existing architecture already specifies
indexes for occurrence, event/time, actor/time, resource/time, request ID, plus no `updated_at` and no
application update/delete permission; indexes are not duplicated speculatively.

T3 must record exactly one of these outcomes in
`docs/evidence/M12/M12-T01-schema-decision.md`:

1. **No migration.** Existing accepted M11-head schema, indexes, constraints, and grants satisfy the
   frozen query/append-only/retention contracts. No `0013` file is created, current/head remains the
   accepted M11 head, and query-plan plus permission evidence proves the decision.
2. **One migration required.** Integration/root reserves the sole next revision on the actual
   accepted M11 head. If T0 confirms `20260802_0012`, the reservation is exactly:

   ```text
   file: backend/migrations/versions/20260802_0013_audit_system.py
   revision: 20260802_0013
   down_revision: 20260802_0012
   owner: M12-T01-R only
   ```

   It may add only evidence-required audit indexes/constraints or runtime/operator grants. It may
   not add a second audit table, mutable audit fields, health tables, exported payload storage,
   production data, or unrelated cleanup. If the accepted M11 head differs, all work remains blocked
   until Integration/root republishes the exact single successor; no lane guesses a revision or
   creates a merge head.

No migration writer starts before this signed decision. A health/build view and a CLI command alone
do not justify schema changes.

## Scope reservations and single-writer surfaces

Until T0 and an explicit release, no M12 lane may edit, move, delete, format, or regenerate active or
accepted M0-M11 implementation/evidence, any migration through the accepted M11 head, or prior
dispatch/requirements/architecture/ADR/UX sources. Corrections to normative sources use CHG-002 and
their owning lane.

Integration/root publishes an exact file manifest before fan-out. The event catalog/redaction
registry, producer integrations, audit ORM/repository, conditional migration, retention credential
and command registration, health configuration/provider, backend router composition, OpenAPI file,
generated client, central wrapper, admin navigation, E2E fixtures, operator docs, and evidence index
each have one named writer window. A lane may propose a contract but may not create shadow schemas,
enums, request-context implementations, health probes, or audit sinks.

M12 adds no exporter, telemetry vendor, search engine, data warehouse, cryptographic ledger, Redis,
worker, scheduler, queue, polling library, table/grid dependency, chart library, or infrastructure
service without a separately approved current requirement and dependency/security review.

## Owner-safe M12 lanes

| Lane                                    | Owner                                                                                    | Exclusive write area                                                                                                                                                                                            | Boundary and handoff                                                                                                                                                                                                 |
| --------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M12-T01-C` catalog/redaction           | Backend Audit Domain + Security                                                          | Audit event catalog, metadata validators/versioning, safe actor/resource projection, redaction corpus, coverage validator, focused unit tests, `docs/evidence/M12/M12-T01-catalog.md`.                          | Starts after T1. No feature producers, ORM/migration/routes, export, frontend, or shared request-context edits. Publishes the single catalog contract.                                                               |
| `M12-T01-P` producer closure            | Original M3-M11 Capability Owners, coordinated by Integration                            | Only T1-proven gaps in individually reserved feature application-service producer files and focused producer tests; `docs/evidence/M12/M12-T01-producers.md`.                                                   | Serialized per owning module after C. Producers pass safe facts to the existing audit port in the same UoW where feasible; failed-auth uses its accepted short transaction. No repository commits or broad refactor. |
| `M12-T01-Q` audit query API             | Backend Audit Query/API Agent                                                            | Audit query application service, repository projection, admin list/detail schemas/routes, filter/sort/pagination/auth/cache tests, `docs/evidence/M12/M12-T01-query.md`.                                        | Starts after T1-T3. Read-only application services, bound parameters, safe projection, no metadata search/N+1. There is deliberately no export writer.                                                               |
| `M12-T01-R` retention/database          | Backend Operations + Database Agent                                                      | Dry-run/execute retention application command and CLI, operator-credential adapter, PostgreSQL permission/query-plan tests, conditional sole migration and its tests, `docs/evidence/M12/M12-T01-retention.md`. | Starts after T2 and the T3 decision. CLI-only deletion in stable bounded batches; runtime application role keeps no update/delete grant. No web purge endpoint or background scheduler.                              |
| `M12-T02-HB` safe health backend        | Backend Health + Operations Agent                                                        | Authenticated safe admin-health query/schema/route and released M2 probe adapters/config tests; `docs/evidence/M12/M12-T02-health-backend.md`.                                                                  | Starts after T2. Reuses M2 probes with bounded timeouts; does not broaden public output or reveal infrastructure. No mutation, audit query, frontend, or deployment control.                                         |
| `M12-T01-I` backend integration         | Integration/root                                                                         | Sequential catalog/producer/query/retention/health model and router composition, affected full backend suites, T4 decision.                                                                                     | Runs after C/P/Q/R/HB evidence. Integration/root alone edits shared registration/router/provider files; defects return to named owners.                                                                              |
| `M12-T01-G` contract generation         | Integration/root Contract Agent                                                          | Reviewed OpenAPI diff, `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator validation/no-diff report, `docs/evidence/M12/M12-T01-contract.md`, T5.                                              | Runs alone after T4 with all other contract writers paused. Backend source is authoritative; generated output is never hand-edited.                                                                                  |
| `M12-T02-AF` audit frontend             | Frontend Audit Agent                                                                     | `frontend/src/features/audit/**`, released `/admin/audit` route slot, audit-specific wrapper/stories/tests, `docs/evidence/M12/M12-T02-audit-frontend.md`.                                                      | Starts after T5. Uses generated types through the accepted wrapper; no raw fetch, export control, duplicate schemas, shared nav edit, or sensitive analytics/cache.                                                  |
| `M12-T02-HF` health frontend            | Frontend Health Agent                                                                    | `frontend/src/features/health/**`, released `/admin/health` route slot, health-specific wrapper/stories/tests, `docs/evidence/M12/M12-T02-health-frontend.md`.                                                  | Starts after T5 and is file-disjoint from AF. Preserves a prior result only as visibly stale during refresh; session expiry removes it. No infrastructure details or operations controls.                            |
| `M12-T02-I` frontend/shared integration | Integration/root                                                                         | Serialized admin navigation/route/wrapper composition, protected-cache review, dashboard health-summary integration only if its exact existing slot is released, T6.                                            | Runs after AF/HF. One writer owns shared shell/navigation/wrapper files. It does not regenerate contracts or conceal failed accessibility/state evidence.                                                            |
| `M12-T03-S` security/E2E/docs           | Integration/root with independent Security, Operations, API, and Accessibility reviewers | Full event/health/retention/API/browser/security/load fixtures; user/API/operator/troubleshooting docs; sanitized screenshots/traces; `docs/evidence/M12/M12-T03.md`; final M12 gate preparation.               | Starts after T6. It may repair only explicitly reserved test/docs files; product defects return to the owning lane. It cannot accept M12 or begin M13.                                                               |

Backend owns executable FastAPI/Pydantic/CLI source. Integration/root alone exports OpenAPI and
generates the client. Frontend owns feature rendering. Infrastructure/Operations alone provisions a
retention credential or deployment metadata input during a separately named window; no secret value
is committed or captured as evidence.

## Frozen implementation contracts

### Append-only audit and correlation

- Audit is a security record, not a debug log. There is no create/update/delete admin API and no UI
  edit/delete action.
- Runtime application roles receive only the accepted `INSERT`/`SELECT` capabilities and cannot
  update or delete. Purge deletion requires the separately authorized operator path.
- A successful business mutation and its audit record commit or roll back in one PostgreSQL UoW
  where feasible. Repositories and audit adapters never commit independently. Expected rejected
  mutations record only the T1-approved safe failure events; failures cannot leak attempted payloads.
- Request IDs flow from the edge/request context through producer and response. Query/detail responses
  retain response request correlation in the standard envelope while displaying the audited event's
  own request ID as data; the two are never conflated.
- Metadata is schema-versioned and validated against the event's allow-list before persistence and
  again on projection. Unknown event/schema combinations fail closed and surface a safe operator
  diagnostic, not raw JSON.

### Audit list/detail

- The list uses the standard envelope and total metadata, maximum page size `100`, deterministic
  occurrence/ID order, typed allow-listed filters, and bounded database work. Unsupported, duplicate,
  malformed, overlong, or arbitrary filter/sort input returns the documented safe validation error.
- Actor/resource filters use exact normalized typed fields frozen at T2; no fuzzy personal-data
  search. Date parsing is RFC 3339 UTC and no browser-local ambiguity reaches the backend.
- Detail exposes only fields in the T1/T2 safe projection. A redaction/absence explanation is
  explicit in UI copy, but the system never stores a forbidden value merely to display `[redacted]`.
- The query is administrator-session protected and `private, no-store`. Unauthorized/expired access
  returns the shared non-enumerating contract and leaves no protected client cache or DOM.

### Retention command

- Default retention is 400 days, subject to the owner/legal release disposition. Cutoff is computed
  once from the accepted clock/database-time policy and reused throughout the run.
- Dry run is non-mutating and reports only safe cutoff and aggregate candidate counts. Execute
  requires explicit operator intent and deletes in stable, bounded, retry-safe batches.
- The command refuses the ordinary runtime credential for deletion, provides a non-zero exit on
  unsafe configuration/partial failure, and is idempotent on rerun. Its audit record contains safe
  aggregate counts and run correlation only, never deleted metadata.
- Backup implications, scheduling by an external platform cron if desired, permissions, monitoring,
  recovery limitations, and jurisdiction validation are documented. M12 does not embed a scheduler.

### Health and application metadata

- `/api/v1/health/live` remains a process-only `{status: "ok"}` probe with no dependency call.
- `/api/v1/health/ready` returns `200 ready` only when PostgreSQL is reachable and migration-compatible;
  otherwise it returns `503 not_ready` with a safe category and standard request correlation.
- Authenticated admin health may add only the T2-approved build version, commit, aggregate statuses,
  and observation context. It never returns hostnames, ports, IPs, connection/storage URLs,
  credentials, configuration/environment dumps, migration identifiers/history, SQL, pool internals,
  filesystem paths, dependency exception text, or stack traces.
- Probe failure is bounded and isolated. Liveness stays healthy during database failure; readiness and
  the admin view communicate the safe degraded state. Health is observation only and cannot restart,
  repair, migrate, purge, or reconfigure anything.

### Frontend, accessibility, and performance

- `/admin/audit` supports event/actor/resource/outcome/date/request-ID filters, active removable
  filter chips, list counts, pagination, safe durable detail, empty/no-match/loading/server-error/
  unauthorized states, and explicit safe-metadata/redaction explanation.
- At a container width below `960px`, the audit table has an equivalent labeled record-card view;
  genuinely wide technical data may scroll only with a visible hint and retained primary context.
- `/admin/health` shows text plus icon status, separate application/database readiness concepts,
  safe build version, last checked, refresh, stale/unknown, and safe failure guidance with request ID
  and documentation path. Manual refresh disables only Refresh, keeps the prior result visibly stale,
  and announces completion.
- Initial rendering never flashes protected or stale data. Logout/session expiry clears feature and
  query caches, removes detail DOM, announces expiry, and follows the accepted safe return-path flow.
- Keyboard, focus, landmarks/headings, labels, `aria-sort`, live announcements, contrast, touch
  targets, 400% zoom, light/dark/system, and reduced motion meet WCAG 2.2 AA evidence. Status never
  relies on color. Audit/card content remains usable at 320, 360, 390, 768, 1024, 1280, 1440, and
  1920 px.
- Query-plan evidence covers all frequent predicates and proves no obvious N+1 path. Frontend review
  records generated-client and feature bundle impact and avoids client polling or unnecessary
  JavaScript; refresh is explicit unless an owner-approved bounded policy exists.

## Ordered dispatch and handoffs

1. **T0:** Integration/root records separate M11 acceptance, actual sole head, released provider and
   file manifests, and current baseline command results.
2. **T1:** owners freeze the event/metadata/producer matrix and forbidden-field corpus.
3. **T2:** owners freeze query/auth/filter/health/retention contracts and record “no export/general
   operations capability” unless CHG-002 supersedes the sources.
4. **T3:** Database/Security/Operations record the no-migration decision or the sole successor
   reservation based on query-plan/grant evidence.
5. **Catalog and backend fan-out:** C publishes the catalog; then P, Q, R, and HB work in disjoint
   files and named shared-provider windows.
6. **T4:** Integration/root composes backend surfaces, runs affected full suites, and accepts or
   rejects T01 backend readiness.
7. **T5:** the Contract Agent alone exports, reviews, validates, and regenerates to a clean no-diff
   state; Integration/root freezes the generated client.
8. **Frontend fan-out:** AF and HF work in disjoint feature/route slots, then T02-I serializes shared
   navigation/wrapper/dashboard integration.
9. **T6:** Integration/root records audit/health UX, cache-clearing, accessibility, responsive, and
   performance evidence.
10. **T03:** Security/E2E/docs triggers the complete accepted event matrix, database-down health,
    retention dry-run/execute/permissions, and final documentation walkthrough; independent owners
    review the gate bundle.
11. **Acceptance:** Integration/root records a separate M12 decision only after all gates below pass.
    M13 receives no files or contracts before that record.

## Exact acceptance, test, and evidence gates

### `M12-T01` backend/audit/retention/health gate

Planned focused test files (or T0-recorded exact equivalents) are:

- `backend/tests/unit/audit/test_event_catalog.py`
- `backend/tests/unit/audit/test_metadata_redaction.py`
- `backend/tests/service/audit/test_producer_coverage.py`
- `backend/tests/integration/audit/test_audit_api.py`
- `backend/tests/integration/audit/test_audit_permissions.py`
- `backend/tests/integration/operations/test_audit_retention.py`
- `backend/tests/integration/health/test_admin_health_api.py`
- `backend/tests/migrations/test_m12_audit_system.py` only when T3 reserves a migration

Run the focused files with PostgreSQL, then the complete backend gate:

```text
python -m uv run --frozen pytest <T0-recorded M12 focused test paths>
python scripts/task.py backend-check
```

Required evidence:

- `M12-T01-catalog.md`: every T1 row maps event ID -> producer test -> safe metadata schema and has
  zero uncovered required family;
- `M12-T01-producers.md`: atomicity/rollback and request/actor/resource/outcome correlation results
  for every repaired producer;
- `M12-T01-query.md`: authz, envelopes, detail, empty/out-of-range pages, deterministic tie handling,
  all filter combinations, unsupported/duplicate/injection inputs, `private, no-store`, no N+1, and
  representative query plans/latencies;
- `M12-T01-retention.md`: dry-run no-change diff, stable cutoff/batches, execute/idempotent rerun,
  runtime-role delete/update denial, operator-only delete, failure recovery, and aggregate safe audit;
- `M12-T01-schema-decision.md`: explicit no-migration proof or sole migration lineage, upgrade from
  empty/prior head, current=head, expected indexes/constraints/grants, and no extra head; and
- `M12-T02-health-backend.md`: live/ready/admin status matrix including database unavailable,
  migration-incompatible and probe-timeout cases, safe output snapshot, authz, cache, and latency.

Raw database inspection and a seeded sentinel corpus must prove that password/token/header/cookie/
contact body/email/raw-IP/private-content/SQL/hostname/stack-trace values are absent from rows, logs,
responses, CLI output, and reports. Append-only and coverage/security-critical backend code reaches
the project critical target of at least 95%; overall backend remains at least 85%. AC-024, AC-026,
AC-029, AC-030, AC-034, AC-036, and SEC-009 must pass.

### T5 contract-generation gate

With only the Contract Agent writing generated surfaces:

```text
python scripts/task.py api-generate
python scripts/task.py api-check
git diff --exit-code -- docs/api/openapi.json frontend/src/generated/api
```

The reviewed diff must contain the T2-approved audit list/detail and admin-health operations only,
with unique stable operation IDs, administrator security declarations, typed bounds/envelopes/errors,
filters/sorts/pagination/examples, and no export or mutation operation. A second generation is clean;
generated TypeScript compiles in the frontend typecheck; no handwritten generated edit remains.

### `M12-T02` frontend gate

Planned feature evidence covers:

- audit table/card/filter/detail, all async states, deterministic pagination, keyboard/`aria-sort`,
  explicit safe redaction copy, narrow/long values, session expiry, and protected-cache removal;
- health operational/degraded/unavailable/unknown, refresh/stale/failure, safe build metadata,
  request-ID/docs guidance, and database-down behavior; and
- Storybook interaction/axe plus browser-assisted checks at every required width, 400% zoom,
  light/dark/system, reduced motion, forced colors, keyboard, and representative screen-reader flow.

Run the recorded exact feature paths, then full frontend gates:

```text
pnpm --dir frontend exec vitest run <T0-recorded audit/health test paths>
pnpm --dir frontend lint
pnpm --dir frontend typecheck
pnpm --dir frontend test:coverage
pnpm --dir frontend storybook:build
pnpm --dir frontend build
```

`docs/evidence/M12/M12-T02-audit-frontend.md` and
`docs/evidence/M12/M12-T02-health-frontend.md` identify fixtures, assertions, viewport/theme/AT matrix,
sanitized screenshots, traces, bundle result, findings, fixes, and retests. Critical audit/health
frontend code meets at least 80% meaningful coverage. AC-024 through AC-026 and AC-032 through
AC-034 must pass with no protected-content flash or stale data after session loss.

### `M12-T03` security/E2E/documentation gate

The dedicated built-app/PostgreSQL spec is
`frontend/e2e/audit-health-retention.spec.ts` (or the exact T0 manifest successor) and runs through
the same-origin edge:

```text
pnpm --dir frontend exec playwright test e2e/audit-health-retention.spec.ts
python scripts/task.py verify
```

It must trigger every row in the T1 event matrix, including representative auth, content,
publication, settings, token, contact, media, and security outcomes; traverse multi-page/filter/detail
audit results with duplicate timestamps; correlate request IDs; prove forbidden fields absent; deny
anonymous/expired/under-authorized access; clear browser state on session expiry; observe healthy and
database-unavailable probes/admin health; and exercise retention dry-run, ordinary-role denial,
operator execution, bounded batches, and idempotent rerun. Synthetic credentials/contact data are
never copied into screenshots, traces, or reports.

`docs/evidence/M12/M12-T03.md` links the immutable commit, environment, PostgreSQL version, migration
head/no-migration decision, command transcripts, event coverage matrix, permission report, OpenAPI
no-diff proof, frontend/accessibility matrix, security sentinel scan, query plans, sanitized browser
artifacts, and defect/retest ledger. User/API/operator/developer documentation covers audit meaning and
filters, safe health interpretation, request-ID troubleshooting, 400-day policy caveat, dry-run and
execute permissions, backup/recovery implications, and explicitly states that audit export and web
operations controls are unavailable. AC-024, AC-026, and AC-039 through AC-043 must pass.

## Final blockers and non-acceptance conditions

M12 cannot be accepted while any of the following remains:

- M11 lacks a separate acceptance record, has more than one head, or its actual head/released
  contracts differ from T0 without a republished dispatch decision;
- a required event family lacks an exact producer test, safe versioned metadata schema, actor/
  resource/outcome/request correlation, or atomicity decision;
- a password, secret, digest, header/cookie, contact body/email, raw IP, private content body,
  hostname/connection string, SQL, stack trace, or unnecessary personal datum appears in audit,
  logs, health, browser state, artifacts, or documentation;
- runtime roles can update/delete audit, retention is reachable from the web/runtime credential,
  dry run mutates, deletion is unbounded, or the 400-day/legal policy has no release disposition;
- pagination/filter/sort is arbitrary, unbounded, nondeterministic, unsupported input is ignored, or
  query evidence shows an unresolved N+1/full-scan/performance defect;
- public health exposes production internals, liveness depends on PostgreSQL, readiness reports ready
  during database/migration incompatibility, or admin health is unauthenticated/cacheable;
- an audit export/general system operation is implemented without the required CHG-002 contract;
- generated artifacts differ after regeneration, authorization/security declarations are wrong, or
  a frontend uses raw fetch/handwritten duplicate contract;
- protected content survives logout/session expiry, required async/responsive/accessibility states
  fail, coverage targets are missed without disposition, or any Critical/High finding remains; or
- evidence is stale, incomplete, non-reproducible, secret-bearing, or acceptance relies on skipped,
  suppressed, placeholder, retry-masked, or meaningless tests.

Only Integration/root records the final M12 acceptance decision and releases M13.
