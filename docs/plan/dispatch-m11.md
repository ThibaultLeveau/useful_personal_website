# Milestone 11 Dispatch

## Dispatcher status

This document prepares `M11-T01` through `M11-T03`. It does not release implementation, record acceptance, authorize M12, or claim that M10 has passed.

M11 remains blocked until Integration/root records the separate M10 acceptance decision, confirms its accepted single database head, resolves every token/security/product decision below, and releases each shared/provider surface required by this dispatch.

| Task      | Current state | Release condition                                                                                                                                                  |
| --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `M11-T01` | Blocked       | M10 passes; one Alembic head is `20260802_0011`; gates T0-T2 pass; sole `0012` and disjoint token/provider/route owners are recorded.                              |
| `M11-T02` | Blocked       | T01 backend/security/API evidence passes; Integration/root records contract freeze T4 after deterministic OpenAPI/client generation.                               |
| `M11-T03` | Blocked       | T02 token-management UX passes and Integration/root records T5; the complete approved route-scope matrix and external-consumer fixtures are available for closure. |

M11 maps to trace milestone `M15`. It delivers the API-token vertical slice: administrator-session-only token management, one-time plaintext reveal, digest-only persistence, scoped bearer authentication for approved integration routes, safe lifecycle metadata, generated contracts, accessible management UX, external-consumer verification, and documentation. It does not add browser JWT authentication, token-authenticated admin pages, OAuth/OIDC, service accounts, multi-administrator RBAC, token export/import, bulk secrets, background cleanup, a second audit system, or M12 audit-viewer work.

## Blocking predecessor and owner decisions

### T0 - Separate M10 acceptance and shared-surface release

Before any M11 write, Integration/root must record:

- a separate accepted M10 gate with `M10-T01` through `M10-T03` evidence, no unresolved Critical/High finding, and no active M10 writer on a file M11 needs;
- exactly one Alembic head at `20260802_0011` from `20260802_0011_contacts.py`, with current/head equality in the accepted environment;
- clean OpenAPI export and deterministic generated-client regeneration at the M10 baseline;
- accepted M1/M2 provider contracts for administrator sessions, forced-password-change denial, actor context, CSRF/Origin, request IDs, safe errors, PostgreSQL rate limiting, minimal append-only audit, idempotency, pagination/filter/sort, `ETag`/`If-Match`, UoW, configuration validation, and same-origin transport;
- released application facades and exact current integration-route candidates for projects and contacts, plus the complete route/security catalog for every other required initial token scope;
- exact backend/frontend router, model, auth dependency, configuration, event catalog, central wrapper, admin navigation, command, docs, and E2E fixture files that require later serialized windows.

M11 consumes earlier capabilities through application facades. It does not reach into project/contact repositories, duplicate session/audit/rate/idempotency persistence, mutate prior migrations, or infer that planning evidence is predecessor acceptance.

### T1 - Scope catalog and least-privilege resolution

Product, API, Architecture, Security, and each capability owner must publish one authoritative route-to-scope matrix before token code starts.

There is a blocking source mismatch:

- the requested M11 target explicitly names `projects:write` and `contacts:read`;
- normative `F2-017`, `SPEC.md`, the database model, and the API architecture define the initial catalog as `content:read`, `content:write`, `media:read`, `media:write`, `contacts:read`, and `admin:read`;
- the accepted API architecture maps project mutation to `content:write`, not `projects:write`, while mapping `contacts:read` to contact list/detail and approved read/archive state changes but never hard deletion/export.

No lane may invent `projects:write` as an alias, silently replace `content:write`, narrow away other Must scopes, or grant both for convenience. The owners must either preserve the normative six-scope catalog or approve a CHG-002 change that updates requirement, database, API, migration, compatibility, documentation, and test impacts. The resulting matrix must specify for every `/api/v1/integrations/*` operation:

- one exact required scope or explicit all/any composition semantics; there are no wildcards, implication by string prefix, hidden superuser scope, or client-selected policy;
- resource/action authorization inside the application use case in addition to the route dependency;
- whether `contacts:read` state mutations remain approved despite the scope name, with contact hard delete always denied;
- the exact project read/write/publication/media-relation actions covered by the approved project scope and what remains denied;
- explicit denial of token create/list/rotate/revoke, password/bootstrap/session/security administration, browser-admin pages, contact hard delete/export, and any operation not present in the reviewed matrix;
- additive/deprecation behavior for future scope-catalog changes and how stored tokens with retired/unknown scopes fail closed.

T1 also records the single owner for the backend scope enum/database constraint, bearer-policy map, OpenAPI security declarations, generated documentation table, and parity fixture. Separate feature lanes cannot maintain competing copies.

### T2 - Secret, digest, expiry, rate, idempotency, and retention freeze

Security/Operations/API/Integration must resolve and record:

- the accepted token format `pp_live_<public_id>.<256-bit-secret>`, including public-selector and secret encodings/lengths, cryptographically secure generator, parser bounds, environment prefix policy, collision retries, and safe display suffix. Encoding is not guessed by implementers;
- digest semantics. The requested wording says “SHA-256 digest-only storage,” while ADR-0002, security architecture, task catalog, and risk mitigation require HMAC-SHA-256 with a deployment pepper and constant-time comparison. The accepted baseline is a SHA-256-family HMAC digest only—never plaintext or reversible ciphertext—but owners must explicitly resolve any demand for unkeyed SHA-256. No weaker direct hash or undocumented algorithm change is permitted;
- pepper/key identifier persistence, purpose separation, entropy/source, secret-manager ownership, fail-closed production validation, active/previous version lookup, rotation/re-authentication strategy, emergency mass revocation, backup/restore implications, and a runbook that does not expose values. Example/default/empty peppers are forbidden;
- optional expiry semantics already baselined as a 90-day UI default, maximum 365 days, and no-expiry only after explicit administrator confirmation: exact database-UTC boundary (`expires_at <= database_now` is denied), allowed precision, validation codes, and display timezone are frozen;
- strict token-name normalization/length/uniqueness, allowed scope combinations, maximum active/revoked token counts, list filters/sorts/page bounds, derived statuses, revoked-record retention/cleanup owner, and whether revocation reasons are stored from a fixed safe catalog;
- the separate PostgreSQL rate policies and safe subjects for token management, unknown/malformed bearer attempts, valid bearer use, and selector abuse. Exact limits, windows, `Retry-After`, atomic behavior, cleanup and load targets are owner decisions; no contact/login limits are reused by accident and no unbounded/no-limit production default is allowed;
- `last_used_at` semantics: which successfully authenticated/authorized requests update it, database-time source, write coalescing if any, concurrency monotonicity, failure behavior, and audit relationship. A performance shortcut cannot make displayed metadata false;
- idempotency for secret-bearing create and rotate. A one-time plaintext secret cannot be faithfully replayed after commit without retaining recoverable response material, while M2 expects safe retry semantics. Owners must select and document a secure contract—for example a safe completed-without-secret recovery requiring revoke/rotate—without storing plaintext/reversible secret or displaying it twice. Revoke replay/concurrency semantics are also frozen;
- controlled audit events and allow-listed metadata for create, authentication/use outcome, rotate, revoke, expiry denial and rate denial. Secret, full token, digest, pepper/key material, full Authorization header, idempotency material, and unnecessary request data are forbidden everywhere;
- public-selector enumeration and timing policy, including a constant-work/dummy-digest path for unknown selectors, constant-time digest comparison, generic invalid/expired/revoked/rotated response behavior, and safe operator diagnostics.

Missing production pepper/key configuration, an unresolved scope/digest/idempotency decision, indefinite unowned token-row retention, or a secret-bearing observability/evidence path blocks T2 and M11 acceptance.

## Scope reservations and exclusions

### Existing and active work is excluded

Until T0 and an explicit release, no M11 lane may edit, move, delete, format, or regenerate:

- `backend/app/modules/contacts/**`, contact security/rate/purge integrations, `backend/migrations/versions/20260802_0011_contacts.py`, M10 routes/configuration/tests/evidence, or M10 frontend/E2E files;
- any still-active M0-M10 migration, evidence, provider, shared router/auth dependency, wrapper, admin shell/navigation, infrastructure, CI, documentation, or generated-contract surface;
- `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator scripts, root manifests/locks, `.github/workflows/**`, `compose.yaml`, `.env.example`, deployment/secret configuration, scanner/coverage settings, or backup scripts except during a separately assigned Integration/Infrastructure window;
- requirements, architecture, ADR, UX, traceability, risk, milestone, task-catalog, and prior dispatch sources. Required corrections use owner-approved change control and are not folded into a token implementation lane.

M11 introduces no external identity provider, JWT/JWK library, Redis, worker, vault client, telemetry vendor, clipboard package, cryptographic primitive, or secret-scanning bypass without a separately approved current requirement and dependency/security review.

### Shared single-writer surfaces

Integration/root publishes an exact file manifest before fan-out. The sole migration, token ORM registration, scope catalog, bearer actor/auth dependency, route-to-scope registry, shared configuration/secret schema, rate/provider integration, audit event catalog, backend router composition, generated artifacts, central handwritten wrapper, admin route/navigation, E2E authorization matrix, and sanitized credential corpus each have one named writer window. Lanes submit contract proposals or use released ports; they never create shadow enums/policies or edit a shared file concurrently.

## Owner-safe M11 lanes

| Lane                                      | Owner                                  | Exclusive write area                                                                                                                                                                                                                                         | Boundary and handoff                                                                                                                                                                                           |
| ----------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M11-T01-D` token domain/application      | Backend API-Access Domain Agent        | New token lifecycle, secret-generation/digest ports, name/scope/expiry validation, create/list/rotate/revoke/authenticate use cases, DTOs/errors/events, and focused tests under `backend/app/modules/api_access/**`; `docs/evidence/M11/M11-T01-domain.md`. | Starts after T2. No ORM/migration/router/shared auth/config/generated/frontend files. Domain receives explicit actors/clock/random/digest ports and never logs a secret.                                       |
| `M11-T01-P` token persistence             | Backend API-Access Persistence Agent   | Dedicated token/scope ORM, repository/query adapter, digest lookup and PostgreSQL concurrency/query tests in Integration-reserved files; `docs/evidence/M11/M11-T01-persistence.md`.                                                                         | Starts after T3. Repositories never commit; admin list never selects digests. Reuses accepted UoW/audit/rate/idempotency providers.                                                                            |
| `M11-T01-M` sole migration                | Backend Migration Agent                | `backend/migrations/versions/20260802_0012_api_tokens.py`, migration fixtures/tests, and `docs/evidence/M11/M11-T01-migration.md`.                                                                                                                           | Starts after T3/root reservation. Sole `0012` writer; no mutation of `0001`-`0011`, merge head, duplicate identity/audit/rate/idempotency table, or production secret/data fixture.                            |
| `M11-T01-A` management/authentication API | Backend API-Access API Agent           | Dedicated administrator token-management and integration bearer schema/route/dependency modules plus API/security tests; `docs/evidence/M11/M11-T01-api.md`.                                                                                                 | Starts after T3. Calls application services only. Admin management uses session+CSRF/Origin; bearer authentication is limited to integration routes and never accepts query/cookie tokens.                     |
| `M11-T01-S` scope/actor integration       | Integration plus Capability Owners     | T1-approved scope/actor registry and exact project/contact/other integration-route adapters/tests in individually reserved owner files; `docs/evidence/M11/M11-T01-scope-matrix.md`.                                                                         | Serialized per shared/feature owner after T3. Uses application facades, not cross-module repositories. No owner widens another capability, invents a scope, or edits token internals.                          |
| `M11-T01-K` key/rate/audit provider       | Security plus Original Provider Owners | Only T2-approved changes to shared secret configuration, HMAC provider, rate policies, minimal audit producer/catalog, safe observability, and dedicated tests/evidence; `docs/evidence/M11/M11-T01-security.md`.                                            | Serialized after active providers release files. Infrastructure alone writes production secret/env/deployment surfaces in a separately approved window. No secret value enters repository evidence.            |
| `M11-T01-I` contract integration          | Integration/root                       | Sequential model/router/auth composition, reviewed OpenAPI diff, `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator reports, full scope parity review, T4, and final T01 decision.                                                          | Starts after D/P/M/A/S/K evidence. Integration/root alone exports/generates and writes shared composition; all other lanes pause those surfaces.                                                               |
| `M11-T02-F` token management frontend     | Frontend API-Token Agent               | `frontend/src/features/api-tokens/**`, released `/admin/api-tokens` route slot, token-specific handwritten wrapper/stories/tests, and `docs/evidence/M11/M11-T02-frontend.md`.                                                                               | Starts after T4. Uses generated types through accepted wrapper. No raw fetch, duplicate models, global secret state, storage persistence, analytics, or shared shell/navigation edit outside its named window. |
| `M11-T02-I` frontend/shared integration   | Integration/root                       | Sequential admin navigation/route/wrapper composition, secret-state/a11y/security review, T5, and final T02 decision.                                                                                                                                        | Runs after T02-F evidence. It does not regenerate outside its sole window, conceal UI defects, or claim M11 acceptance.                                                                                        |
| `M11-T03-I` security/E2E/docs             | Integration/root                       | Complete authorization-matrix/API/browser/consumer/security/load fixtures and reports, redacted docs/transcripts/screenshots, `docs/evidence/M11/M11-T03.md`, trace links, and final M11 gate preparation.                                                   | Starts after T5. Defects return to named owners. No M12 work or final acceptance without independent Security/API/Architecture/Operations/a11y review.                                                         |

No two lanes edit the same file concurrently. Backend owns executable FastAPI/Pydantic source; Integration/root alone exports and generates; frontend consumes only the T4 generated client through handwritten wrappers.

## Sole migration reservation

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0012_api_tokens.py
revision: 20260802_0012
down_revision: 20260802_0011
owner: M11-T01-M only
```

The revision adds only the T1-T3 accepted token persistence:

- `api_token`: opaque ID, unique public selector, administrator owner, normalized descriptive name, fixed-length SHA-256-family `secret_digest`, any required non-secret digest-key version identifier approved at T2, database-UTC created/expiry/last-used/revoked timestamps, fixed safe revocation reason if approved, nullable `rotated_from_id`, and integer version;
- `api_token_scope`: token foreign key plus one exact scope value from the T1 catalog, with composite uniqueness and database constraint/reference enforcement;
- unique/index support for selector and digest lookup, owner/name rules, active-expiry/list filters and stable sorts, scope joins, rotation predecessor uniqueness if T2 requires one successor, and least-privilege runtime grants.

It never stores the plaintext secret, full bearer token, reversible/encrypted secret, pepper/key value, Authorization header, response body, clipboard data, idempotency key/fingerprint, raw request, or arbitrary metadata JSON. Administrator list/detail queries must be structurally unable to select `secret_digest` through their projection.

The migration does not recreate administrator/session, rate-limit, idempotency, or audit tables and does not mutate accepted revisions. Evidence requires empty upgrade, upgrade from accepted `0011`, one head/current equality, schema-model/constraint/index/grant parity, representative active/expired/revoked/rotated/scope rows without real secrets, and the project-approved downgrade check. Production startup checks compatibility and never migrates or creates a token.

## Backend contract to freeze

### T3 - Token domain, bearer, and persistence contract

Integration/root records T3 after T01-D review/tests and T0-T2 decisions, before P/M/A/S/K fan-out. T3 freezes:

#### Secret creation and digest-only storage

- Create and rotate obtain 256 random secret bits from the approved cryptographic generator and construct the exact T2 token format. Public-selector collision retries are bounded; any generator/entropy failure aborts with no row or misleading success.
- The full token exists only in the successful create/rotate response object and the narrow application stack needed to construct it. That response is `Cache-Control: private, no-store`, never compressed/cached by an intermediary under the approved edge policy, and cannot be retrieved later.
- Before commit, only the accepted HMAC-SHA-256 digest and approved non-secret metadata enter persistence. Comparison is constant time after selector lookup; unknown, malformed, expired, revoked, rotated and wrong-secret paths perform the T2-approved generic work and return the same safe authentication class without revealing selector/state.
- No API, repository, admin projection, debug representation, exception, audit event, log, trace, metric, profile, SQL bind log, test snapshot, documentation example, screenshot, browser artifact, backup report, or support tool can recover or emit the secret, full token, digest, pepper, or Authorization value.

#### Administrator-only lifecycle

- Token create, list, detail if retained, rotate and revoke are available only to a fully authorized administrator cookie session that has completed forced password change. Unsafe operations require exact trusted Origin, signed CSRF and applicable rate/idempotency controls. Bearer tokens cannot manage tokens even if they hold `admin:read` or every content scope.
- Create accepts only the frozen normalized unique name, exact T1 scopes and optional expiry. UI/API defaulting to 90 days is explicit, expiry cannot exceed 365 days, and no-expiry requires a separate explicit confirmation fact; mass-assigned owner/status/digest/timestamps are rejected.
- List is bounded/paginated and returns only opaque ID, safe selector suffix, name, scopes, created/expiry/last-used/revoked metadata, derived status and version. It never returns digest, key version, full selector+secret, revocation internals, or secret-presence flags that imply retrieval.
- Rotate locks the active predecessor, validates its version and state, atomically revokes it and creates exactly one successor with a new selector/secret/digest/scopes/expiry according to the frozen policy. Concurrent rotations have one winner; rotate/revoke races cannot leave two active successors or resurrect access.
- Revoke is immediate, version guarded and irreversible. Concurrent/replayed revoke follows T2's safe idempotent/conflict contract. There is no reveal, reactivate, un-revoke, plaintext export, secret edit, hard delete, or ordinary-admin cleanup operation.
- Lifecycle audit participates in the same transaction. Events contain safe actor/resource/public suffix/scopes/expiry/status/request/outcome facts only as approved; no secret, digest, Authorization header, pepper, idempotency payload or unsafe free text.

#### Bearer authentication and least privilege

- Only `/api/v1/integrations/*` accepts `Authorization: Bearer <token>`. A token in query, form, JSON, URL fragment, cookie, WebSocket subprotocol, or alternate header is rejected. Admin/public/auth/health behavior is not elevated by a bearer credential.
- Exactly one syntactically valid Authorization credential is accepted. Missing credentials return the established `401 AUTHENTICATION_REQUIRED`; malformed/multiple/wrong/unknown/expired/revoked/rotated tokens return one non-enumerating `401 TOKEN_INVALID` with the standards-approved `WWW-Authenticate` behavior. A valid token lacking required scope returns `403 SCOPE_REQUIRED` without disclosing unrelated grants/resources.
- Successful parsing never logs headers or token fragments. The public selector is used only for bounded lookup and safe suffix/audit representation; digest comparison is constant time. Database outage/failure returns a safe unavailable/internal response and never fails open.
- Authentication produces an immutable token `ActorContext` containing only safe token ID/owner/scopes/expiry/request facts. Each route dependency and application use case independently enforces the exact T1 matrix. Repository access cannot bypass scope/resource rules, and confused-deputy calls cannot substitute an administrator actor.
- Expiry and revocation are checked on every request using database time/state. A request that authenticates concurrently with revoke/rotate follows the frozen transaction/authorization boundary; no request beginning after committed revocation can succeed. Connection pooling, caching, last-use writes and error fallback cannot extend validity.
- `contacts:read` permits only the T1-approved contact list/detail and state operations and never body export or hard deletion. The requested `projects:write` is enforced only if T1 approves and defines it; otherwise the normative `content:write` matrix applies. No string alias or union broadens access.
- Rate admission and last-use/audit updates follow T2. Failed bearer attempts cannot enumerate selectors or cause attacker-controlled high-cardinality metrics/audit values. Successful use never places a secret in an event.

## API and generated-client handoff

The executable contract submitted to `M11-T01-I` includes:

- administrator-session-only create/list/rotate/revoke operations, optional approved detail, exact validation/concurrency/idempotency/rate errors, private no-store headers, and a distinct one-time create/rotate response schema;
- a one-time secret property present only in successful first delivery, clearly documented as non-recoverable and excluded from later resource/list schemas and examples;
- bearer security scheme and T1-approved integration operations with exact per-operation scopes and safe `401/403/409/422/428/429/500/503` behavior;
- no token-management bearer security, no browser-admin bearer alternative, no full-secret example/default, and no generated-client logging/interceptor behavior that exposes Authorization.

Integration/root records T4 only after T01-D/P/M/A/S/K pass. It reviews schema/security/cache/idempotency/rate/concurrency semantics, unique stable operation IDs, response separation, every route-scope declaration and parity fixture; exports, validates/lints, generates, formats only as configured, strictly compiles, regenerates, and obtains no diff. Only Integration/root writes `docs/api/openapi.json` and `frontend/src/generated/api/**`.

T4 releases T02. Frontend cannot compensate with raw fetch, duplicate schemas, `any`, hand-built CSRF/idempotency, bearer storage, or generated-file edits.

## Frontend token-management contract

- `/admin/api-tokens` lists safe metadata with status text, allowed scope explanations, created/expiry/last-used times, pagination/filter/sort if T2 approves, create action, and explicit rotate/revoke actions. Empty/loading/no-results/offline/error/unauthorized/session-expired/version-conflict/rate-limited states are distinct and accessible.
- Create uses a unique descriptive name, least-privilege scope selection with plain-language capability/denial summaries, and expiry defaulted to 90 days. No-expiry requires a separate unchecked acknowledgment; review names high-impact scopes and states that tokens never manage tokens/passwords/sessions/bootstrap or hard-delete contacts.
- Create success opens a blocking one-time reveal dialog. It shows the plaintext only in a read-only selectable control with Copy, a plain-language cannot-recover warning, safe metadata, and an unchecked `I have stored this token` acknowledgment required before Close. Copy success is announced inline; copy failure leaves the value selectable. Download-as-text is disabled unless Security explicitly approves it at T2.
- Rotation requires confirmation explaining immediate predecessor revocation and the possibility that an interrupted one-time response cannot be recovered. Its success uses the same isolated reveal component. Revoke names only the token name/safe suffix and explains immediate integration impact; neither action is optimistic.
- The secret is kept only in the narrow reveal component's volatile state. It never enters URL/history, server-rendered markup, query cache, global state, Web Storage, IndexedDB, Cache Storage, service worker/offline queue, form defaults, clipboard history under application control, analytics, telemetry, console, error reporting, toast, notification, title, audit, or later list DOM.
- Acknowledged close, session expiry/logout, route change, component unmount, error boundary, revoke/rotate replacement, and browser lifecycle disposal clear all application-held secret references and protected caches. The app does not claim it can erase an operating-system clipboard; documentation tells the administrator to manage it safely without silently overwriting unrelated clipboard content.
- Back/forward cache and refresh cannot reveal or resubmit the secret response. After loss/close there is no Reveal action: the administrator must revoke or rotate according to the documented T2 recovery contract.
- Dialog focus is contained, starts at the heading or safe explanatory control, has a complete keyboard path, announces copy/errors without exposing the secret to accessible labels outside the control, and handles 200% text/400% zoom, touch, forced colors, reduced motion, and narrow screens without clipping the secret/actions.

Integration/root records T5 after T02-F/I pass generated-wrapper, component, Storybook, DOM/state-clearing, privacy, security, accessibility, responsive and built-app browser tests. T5 is readiness for T03, not M11 acceptance.

## Ordered dispatch

1. **Blocked - Integration/root:** record separate M10 acceptance, verify sole head `0011`, release active/shared files, and publish T0 route/file inventories.
2. **Blocked - Product/API/Architecture/Security/Operations/capability owners:** resolve T1 scope conflict/matrix and every T2 digest/key/rate/idempotency/expiry/name/last-use/retention decision.
3. **After T2 - `M11-T01-D`:** implement and review token domain/application contracts; Integration/root records T3.
4. **After T3 - Integration/root:** reserve sole `0012` on `0011` and publish exact disjoint P/M/A/S/K plus shared-writer windows.
5. **After T3 - `M11-T01-P/M/A/S/K`:** implement persistence, migration, API/bearer behavior, scope-owner routes, and provider integrations only in disjoint files with serialized shared windows.
6. **After T01 evidence - `M11-T01-I`:** integrate, review the full route matrix, export/generate twice, compile, and record T4.
7. **After T4 - `M11-T02-F/I`:** implement and integrate the accessible one-time-reveal management UX; record T5.
8. **After T5 - `M11-T03-I`:** certify complete token lifecycle/external-consumer/authorization/redaction/docs evidence and prepare the M11 gate record without releasing M12.

## Exact acceptance, security, quality, and evidence gates

All evidence follows `docs/plan/delivery-evidence-template.md`, maps M11 and trace M15, records commit/worktree/environment/tool versions/commands/results/defects/retests, and uses repository-relative artifact links. Every test secret is generated per test and remains redacted; no plaintext/full token, digest, pepper, Authorization header, cookie, private data, production value, or machine-specific path may enter evidence, screenshots, traces, videos, reports, snapshots, command lines, shell-history excerpts, or committed fixtures.

### `M11-T01` backend, persistence, security, API, and contract evidence

Evidence must include:

- deterministic random-source tests proving exact 256-bit secret input, format/parser bounds, public-selector collision retry/failure, generator failure rollback and large-sample uniqueness without printing values; statistical theater cannot replace construction/entropy-source review;
- cryptographic known-answer/negative tests for the T2-approved HMAC-SHA-256 digest, key version, purpose separation, constant-time comparison path, wrong/unknown/old key, malformed/unknown selector dummy work, rotation/mass-revocation runbook, fail-closed production config, and storage inspection proving no plaintext/reversible secret;
- name/scope/expiry validation for normalization/bounds/uniqueness, empty/unknown/duplicate/incompatible scopes, T1 catalog parity, default 90/max 365/no-expiry acknowledgment, database-time exact expiry boundary, and mass-assigned metadata rejection;
- domain/concurrency tests for create, first response only, list-safe projection, rotate atomic predecessor revocation/new successor, simultaneous rotate, rotate/revoke race, repeated/stale `If-Match`, revoke immediacy/replay, invalid-state denial, transaction/audit rollback, and T2 secret-bearing idempotency recovery with no second reveal or recoverable response storage;
- migration tests for empty/`0011` upgrade, one head/current equality, schema-model/constraint/index/grant parity, scope catalog, unique selector/digest/name/rotation rules, representative states, prior revision nonmutation, and no duplicate provider tables;
- repository/query tests for digest exclusion from list/detail, selector lookup bounds, active/expired/revoked/rotated predicates, deterministic page/filter/sort, concurrent last-use monotonicity/coalescing, no N+1, bound parameters, realistic query plans and load/write-contention targets;
- administrator API tests for session/forced-change/authz, CSRF/Origin/CORS, create/list/rotate/revoke, no-expiry confirmation, rate/idempotency/`ETag`/`If-Match`, IDOR/mass assignment/injection, safe pagination/filter/sort/errors/request IDs, private no-store headers, one-time response separation, and bearer denial on all management operations;
- bearer parser/auth tests for absent, scheme case/whitespace as standards require, duplicate/multiple headers, query/cookie/body alternatives, malformed/truncated/oversized tokens, invalid selector/secret, expired/revoked/rotated, key-version paths, DB/provider failure, `WWW-Authenticate`, non-enumerating/timing-safe outcomes, rate limits and no fail-open;
- a generated parity test enumerating every integration method/path against its route declaration, OpenAPI scopes and application-use-case check, covering each exact sufficient token, every individual under-scope token, extra unrelated scopes, unknown/retired scopes, missing/invalid token, cross-resource IDOR, and explicit forbidden admin/security/contact-delete operations;
- lifecycle/use audit and negative observability inspection across database, PostgreSQL bind/error logs, application/edge logs, audit, exception strings, traces/spans, metrics labels, profiler, analytics/error reporting, HTTP/RSC/HTML/cache, OpenAPI examples, test snapshots and backups for full token/secret/digest/pepper/Authorization absence;
- OpenAPI validation, unique operation IDs, exact security schemes/scopes, safe write-only response separation/examples/errors/idempotency/rates/concurrency/cache review, two deterministic generations/no diff, strict generated compile, and wrapper/interceptor secret-leak scan;
- Ruff format/lint, strict Mypy, full affected Pytest, meaningful backend overall and >=95% token security/critical-domain coverage evidence, architecture-boundary checks, dependency/container/secret scans, and no disabled/suppressed test or unexplained warning.

Any recoverable/stored/repeated secret, unkeyed digest without approved change, comparison/timing enumeration, weak/default pepper, bearer on admin routes, scope bypass/alias drift, missing use-case authorization, expired/revoked/rotated success, contact hard delete, non-atomic rotation/revoke, false last-use, secret-bearing audit/log/cache/evidence, generated drift, second migration head, or confirmed Critical/High finding blocks T3/T4 and T01.

### `M11-T02` frontend and accessibility evidence

Evidence must include:

- generated-wrapper/component tests for safe list metadata, name/scope/expiry validation, least-privilege explanations, 90-day default, max/stale date, no-expiry confirmation, review, pending/rate/error/conflict, and no bearer or raw transport in browser-management code;
- one-time reveal tests for create/rotate first delivery, read-only selection, Copy success announcement, permission/API/copy failure fallback, stored acknowledgment, Close disabled until acknowledgment, permanent close/refresh/back/lost-response behavior, no Reveal action, and documented revoke/rotate recovery;
- DOM/state inspection proving close/session expiry/logout/navigation/unmount/error clears the value and that secret/full token never reaches URL/history/query or global cache/storage/service-worker/offline queue/toast/title/analytics/telemetry/console/error boundary/later list;
- rotate/revoke confirmation and concurrency tests, including old token immediately invalid after successful rotation, stale version, interrupted response, focus placement/restoration, and safe suffix/name-only feedback;
- Storybook interaction, axe and manual keyboard/screen-reader tests for scope checkboxes/descriptions, expiry/no-expiry warning, review, modal focus containment, copy/status live regions, errors, table/mobile-card parity, pagination/filter/sort, touch targets, contrast/forced colors, reduced motion, 200% text and 400% zoom;
- Prettier, ESLint, strict TypeScript, affected Vitest/Testing Library/Storybook/Playwright, production build, >=80% meaningful critical token-form/business-utility coverage, bundle/render targets, and no generated edit/duplicate schema/raw fetch.

Evidence covers 320, 360, 390, 768, 1024, 1280, 1440 and 1920 px in relevant light/dark/system modes. Screenshots/traces show list, create, scope/expiry review, a fully redacted reveal dialog, copy success/failure, rotate/revoke, empty/error/rate/conflict/session-expiry states; capture is disabled or DOM values are deterministically redacted while plaintext is present. A screenshot, video, trace, accessibility tree dump, or report containing a full test token is a security failure, not evidence.

An inaccessible one-time flow, secret in a forbidden client sink/artifact, re-reveal after close, missing no-expiry warning, unclear least-privilege scopes, accidental optimistic rotation/revoke, stale protected state, unresolved WCAG blocker, or unexplained bundle/performance regression blocks T5/T02.

### `M11-T03` external-consumer, security, documentation, and M11 gate evidence

Integration/E2E uses built Next.js/FastAPI through the accepted edge and a fresh PostgreSQL database migrated through `0012`, isolated workers, synthetic content/contacts and ephemeral generated secrets that never enter artifacts. It must prove:

- J7: administrator creates a named least-privilege token with expiry, copies the secret once, acknowledges storage, closes it permanently, inspects safe metadata, rotates atomically, proves the old token denied, and revokes the successor so it is immediately denied;
- optional no-expiry creation requires explicit review; exact expiry boundary denies; lost create/rotate response follows T2 recovery without re-reveal, duplicate active successor or recoverable persisted response;
- a cURL-equivalent external consumer uses the approved project-write scope—`projects:write` only if T1 approved, otherwise the normative scope—and `contacts:read` against every allowed operation, while each missing/under-scoped/cross-resource/forbidden operation fails with the exact safe contract;
- complete matrix coverage for every accepted initial scope and integration route, including extra-scope non-escalation, unknown/retired values, token management/password/session/bootstrap/contact-delete denial, and matching route/OpenAPI/use-case policy catalogs;
- malformed/missing/multiple/query/cookie/body tokens, guessed selectors, brute force/rate boundaries, invalid/expired/revoked/rotated credentials, pepper versions, provider/database failures and concurrent revoke/use/rotate cannot enumerate, fail open, corrupt last-use, or leak values;
- DB/admin responses/logs/audit/traces/metrics/cache/URLs/history/analytics/error reports/OpenAPI/generated output/test reports/screenshots/repository/backup inspection finds no plaintext/full token, secret, digest, pepper/key material or Authorization header; stored rows contain only approved digest and safe metadata;
- query/auth/load performance meets T2 targets for selector lookup, last-use writes, rate buckets, list pagination and complete scope matrix; representative admin Lighthouse performance remains >=90 and accessibility >=95 unless measured owner dispositions exist, without relaxing security/a11y;
- full affected backend/frontend/migration/contract/E2E/build/security/accessibility/performance suites pass, generated output remains clean, `0012` is the sole head, and no active/shared writer overlap occurred.

Documentation/evidence must include:

- an administrator guide for naming, least-privilege scope choice, optional expiry/default/max/no-expiry risk, one-time copy/acknowledgment/loss recovery, metadata/last-use, rotate and revoke, with no secret screenshot;
- an API consumer guide for exact bearer header, base/version, every approved scope/route, safe `401/403/429` handling, expiry/rotation/revocation, pagination/filter/sort/errors/request IDs, generated-client and redacted environment-variable/cURL examples that never place tokens in command arguments, URLs or committed shell history;
- a developer/security guide for token format/parser, generator, HMAC-SHA-256 digest-only storage, constant-time/dummy work, selector handling, ActorContext, route/use-case scope enforcement, rate/idempotency/audit/redaction, concurrency/last-use, one-time response boundary and safe extension/change procedure;
- an operator guide for pepper/key ownership/injection/version rotation/emergency revocation, fail-closed startup/readiness, token/rate/idempotency retention cleanup, monitoring without credentials, backup/restore effects, incident response and secret-leak remediation;
- sanitized matrix, migration/storage inspection, query/load/timing reports, API/browser transcripts, coverage/scanner/a11y/performance results, responsive redacted screenshots, defect/retest links, and independent Security, API, Architecture, Operations and UX/a11y reviews.

Passing lane evidence does not authorize M12 until Integration/root records the separate M11 acceptance decision. The M11 gate remains blocked by open T1/T2 choices, unresolved `projects:write` versus normative scope catalog, unresolved SHA-256 versus accepted HMAC-SHA-256 semantics, insecure/default pepper or rotation, unresolved secret-response idempotency, incomplete route matrix, token management by bearer, scope/use-case bypass, recoverable/repeated/leaked secret, expired/revoked/rotated success, non-atomic lifecycle, incorrect last-use/rate behavior, generated drift, multiple migration heads, parallel migration/generated/scope/provider/shared writers, active earlier-milestone overlap, unsanitized evidence, failed Must requirement, missing independent retest, unresolved WCAG blocker, unexplained target regression, or any confirmed Critical/High finding.
