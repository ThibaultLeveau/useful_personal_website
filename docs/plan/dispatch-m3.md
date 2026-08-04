# Milestone 3 Dispatch

## Dispatcher status

This document prepares `M3-T01` through `M3-T03`. It does not release implementation, accept a task, close M0 work, or authorize M4.

The repository currently contains active M1 identity/authentication work, prepared but unreleased M2 API-convention work, and active M0 CI reservations. M3 is therefore blocked. Integration/root may release an M3 lane only after the named dependency and file reservations below have durable evidence.

| Task     | Current state | Release condition                                                                                                                 |
| -------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `M3-T01` | Blocked       | M2 C3 and the separate M2 gate pass; one Alembic head is confirmed at `20260802_0003`; active M1/M2/CI shared files are released. |
| `M3-T02` | Blocked       | `M3-T01` backend/public contracts pass and M3 contract freeze S2 is recorded with a clean generated client.                       |
| `M3-T03` | Blocked       | `M3-T01` and `M3-T02` pass and S3 is recorded.                                                                                    |

Milestone 3 maps to trace milestones `M06` and `M07`. Its scope is profile, website settings, navigation/footer, their public-safe projections, and the corresponding public/admin experience. It does not authorize skills or later content slices, media upload/library behavior, custom pages, analytics script injection, API-token management, or speculative AI behavior.

## Strict dependency gates

### D0 - M1 and active-reservation clearance

Before any M3 write, Integration/root confirms:

- the M1 gate has durable passing evidence for identity, session, CSRF/Origin, bootstrap, protected admin shell, audit/redaction, auth OpenAPI, and browser lifecycle;
- M1-owned identity, auth route, admin-shell, auth wrapper, `20260802_0002`, and auth E2E files are released;
- active M0 CI/task-runner/scanner files are either accepted or remain under their current owner with a no-write reservation for M3;
- root manifests/locks are stable and no M3 dependency change is implied.

M3 consumes identity through its application actor/session facade. It does not edit identity repositories, session storage, rate-limit storage, auth cookies, CSRF semantics, or the forced-password boundary.

### D1 - M2 C3 and M2 acceptance

M2 C3 is a strict prerequisite, but C3 alone is not enough. Integration/root must also record the separate M2 acceptance decision and provide a baseline proving:

- common envelopes, errors, request IDs, actor context, `ETag`/`If-Match`, idempotency, health, and v1 compatibility rules pass their contract/security suites;
- the committed OpenAPI artifact and generated client regenerate twice with no diff and compile strictly;
- there is exactly one Alembic head at revision `20260802_0003` from file `20260802_0003_api_conventions.py`;
- M2 health, handwritten client, and feature-fan-out evidence have no unresolved Critical/High finding or failed Must requirement;
- Integration/root has released the M2 common/backend/health/generated/client/E2E reservations needed by M3.

Any M2 discrepancy is corrected and re-evidenced in M2. M3 must not fork the common error, concurrency, idempotency, request-ID, health, auth, or generated-client contracts.

### D2 - M3 baseline review

After D1, Integration/root records the M3 starting baseline:

- one clean backend architecture-boundary run;
- full affected backend/frontend tests and production frontend build;
- clean schema export/generation and generated-import boundary scan;
- current public/admin shell screenshots at 320 and 1440 px in light/dark themes;
- the exact registered internal-route catalog available to navigation validation;
- no unexplained working-tree overlap in any M3-owned path.

Only D2 releases the first M3 backend/migration lane.

## Active-file exclusions

### M1 files excluded until D0

M3 must not edit, move, delete, format, or regenerate:

- `backend/app/modules/identity/**`, M1-owned `backend/app/modules/audit/**`, and `backend/app/infrastructure/rate_limit/**`;
- `backend/app/commands/bootstrap_admin.py`, auth routers/dependencies/schemas/tests, auth-only `backend/app/{config,main}.py`, and `backend/migrations/versions/20260802_0002_identity_auth.py`;
- `frontend/src/features/auth/**`, login/change-password/session-expired/account routes, the protected admin layout/page, `frontend/src/components/admin/admin-shell.*`, auth wrapper/boundary files, and auth E2E;
- `docs/evidence/M1/**` and in-flight M1 API/generated-client artifacts.

### M2 files excluded until D1

M3 must not edit, move, delete, format, or regenerate:

- M2-owned `backend/app/common/{domain,application,security}/**`, request-context/observability/API-convention seams, idempotency persistence, and their tests;
- `backend/migrations/versions/20260802_0003_api_conventions.py`;
- `backend/app/modules/health/**`, `backend/app/api/v1/health.py`, and health tests;
- M2-owned `frontend/src/lib/api/**`, `frontend/src/features/health/**`, admin-health routes/components/tests, and M2 E2E/contract fixtures;
- `docs/evidence/M2/**`, M2 API/security/catalog reports, and the M2 acceptance record;
- the in-flight M2 versions of `docs/api/openapi.json` and `frontend/src/generated/api/**`.

After D1, M3 treats these as provider contracts. A common-contract defect returns to its M2 owner; M3 does not add compatibility shims, raw fetch paths, `any` transport types, or duplicate request/auth/error logic.

### M0 CI and Integration/root files excluded throughout M3

M3 lanes may run but must not edit:

- `.github/workflows/**`, `.pre-commit-config.yaml`, `Makefile`, and `scripts/task.py`;
- Compose/Docker/environment files, scanner/dependency-audit/coverage configuration, and M0-T07/T08 reports;
- root manifests and locks;
- requirements, architecture, ADR, UX, and existing planning sources;
- `docs/api/openapi.json`, generator/export/validator scripts/config, and `frontend/src/generated/api/**`, which remain Integration/root-only.

The demo-seed handoff below explicitly returns command wiring and CI changes to Infrastructure; it does not grant an M3 agent access to these files.

## Owner-safe M3 lanes

| Stage                                | Owner                                          | Exclusive write area                                                                                                                                                                                                                                                    | Gate and handoff                                                                                                                                                                                                                   |
| ------------------------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M3-T01-B` domain/admin backend      | Backend Agent                                  | `backend/app/modules/{profile,settings,navigation}/**` except the reserved public-projection filenames; admin route modules/schemas dedicated to profile/settings/navigation/footer; focused domain/service/repository/API tests; `docs/evidence/M3/M3-T01-backend.md`. | Starts after D2. Owns invariants, singleton commands, admin authorization, audit facts, transactions, concurrency, and idempotency. Does not write migration, OpenAPI artifact, generated code, frontend, CI, or final acceptance. |
| `M3-T01-M` sole migration            | Backend Migration Agent, serialized with T01-B | `backend/migrations/versions/20260802_0004_site_configuration.py`, the new tables/model registration needed by this revision, migration fixtures/tests, and `docs/evidence/M3/M3-T01-migration.md`.                                                                     | Starts only after Integration/root reserves `0004` on accepted `0003`. No other M3 revision or merge head. Schema-model changes are coordinated with T01-B, never concurrent in the same file.                                     |
| `M3-T01-P` backend public projection | Backend Public Projection Agent                | Explicit public projection/query files inside the three modules; dedicated `/api/v1/public` route/schema modules for site/profile/navigation; public privacy/cache/query tests; `docs/evidence/M3/M3-T01-public-projection.md`.                                         | Starts after S1. May call module application facades only, never repositories/ORM from routes. Public/admin schemas remain distinct. Submits executable Pydantic source to Integration/root.                                       |
| `M3-T01-I` API generation            | Integration/root                               | Cross-lane contract tests/reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, schema/generator evidence, S2, and final T01 acceptance record.                                                                                                            | Starts after T01-B/M/P evidence. Integration/root is the sole OpenAPI/generated-client writer. No backend or frontend lane touches artifact/generated files during this window.                                                    |
| `M3-T02-A` admin frontend            | Frontend Admin Agent                           | `frontend/src/features/{profile,settings,navigation}/**`; `/admin/profile`, `/admin/settings`, `/admin/navigation`, `/admin/footer`; dedicated forms/components/stories/tests; `docs/evidence/M3/M3-T02-admin.md`.                                                      | Starts after S2. Uses generated types through feature wrappers. Any one-time edit to the released admin shell is separately reserved and serialized by Integration/root.                                                           |
| `M3-T02-P` public SSR frontend       | Frontend Public Agent                          | `/about`; public layout/header/footer and dedicated public profile/site/navigation feature code; SSR/cache/metadata tests, stories where appropriate, and `docs/evidence/M3/M3-T02-public.md`.                                                                          | Starts after S2 and may run beside T02-A only when files are disjoint. Server Components perform initial public reads; client islands are limited to real interaction such as theme and the mobile drawer.                         |
| `M3-SD` demo-seed backend handoff    | Backend Agent, after T01 domain freeze         | `backend/app/commands/seed_demo.py`, seed-only tests, and `docs/evidence/M0/M0-T07-seed-demo.md`.                                                                                                                                                                       | Starts after S1 and uses the accepted M3 application facades/UoW. Delivers an internal command to Integration/root and Infrastructure; it does not edit wrappers, Compose, task runner, CI, or M0 acceptance records.              |
| `M3-T03-I` vertical integration/E2E  | Integration/root                               | M3 E2E/API fixtures/specs, sanitized screenshots/traces/reports, profile/settings/navigation/footer API and user/developer docs, traceability evidence links, `docs/evidence/M3/M3-T03.md`, and the final M3 gate record.                                               | Starts after T01/T02 pass and S3. Behavioral defects return to the owning lane. Integration/root does not start M4 or mark M3 accepted without independent review.                                                                 |

No two lanes edit the same file concurrently. Backend owns executable Pydantic source; Integration/root alone exports/generates; frontend lanes consume only the S2 generated contract. Shared public layout, admin shell, central API wrapper, router composition, and application composition each receive one explicit sequential writer window if a change is required.

## Sole linear migration policy

M3 reserves exactly one revision:

```text
file: backend/migrations/versions/20260802_0004_site_configuration.py
revision: 20260802_0004
down_revision: 20260802_0003
scope: profile, website_settings, navigation_menu/item, footer/column/item, constraints and observed indexes
```

The revision is created only after D1 proves `20260802_0003` is the accepted single head. It includes:

- singleton profile and website-settings persistence with timestamps and integer optimistic versions;
- explicit public-field selection state for profile data rather than omission-based privacy;
- relational navigation/footer nodes, bounded parent relationships, visibility, target, and scoped integer order;
- unique sibling/column positions and the constraints/indexes required by accepted query/update paths;
- no identity/session/token/rate-limit/audit duplication, no content tables from M4+, and no secret-setting columns.

Profile image, logo, favicon, and social-image values are media-backed concepts, but the media capability is not delivered until M9. M3 must not create a fake upload/storage path, accept arbitrary storage keys, or substitute unvalidated public URLs. These values remain nullable/unset in M3 and are omitted from demo seed; their media-reference/FK activation is owned by the later media slice. M3 evidence must state this staged field limitation and must not claim `AC-014` or `AC-019`.

Migration evidence requires empty-database upgrade, upgrade from accepted `0003` with representative data, current/head equality, one-head verification, schema/model comparison, constraint/index inspection, rollback/UoW behavior, singleton-race behavior, and production-startup proof that no migration or seed runs automatically. A schema need found after S1 stops downstream work and returns to the sole migration owner; parallel revisions and merge heads are prohibited.

## Backend and public-projection contract

### Profile

- Admin schemas cover all SPEC profile fields and an explicit public/private decision for each potentially sensitive field.
- Public projection is constructed from an allow-list, not by serializing the admin model and dropping fields afterward.
- Email, contact preferences, location, availability, resume, social values, and biographies are absent unless explicitly approved for public display; absence means the JSON property, SSR markup, metadata, cache, log, trace, and live region do not contain the value.
- Profile is a singleton created/updated through an application command; route handlers do not contain policy or persistence logic.

### Website settings

- Website settings are a singleton covering site identity, title/description defaults, IETF locale, IANA timezone, theme policy, public contact/social values, SEO defaults, public availability, and allow-listed public analytics identifiers.
- Deployment secrets, analytics credentials, arbitrary scripts/HTML, private keys, database/storage identifiers, cookies, headers, and unbounded provider configuration are not fields and are rejected as extra/mass-assigned input.
- A public analytics value is an identifier only for an explicitly allow-listed provider/format. It does not authorize script injection; executable analytics integration requires a later reviewed CSP/privacy implementation.
- Admin responses are `private, no-store`; public projections expose only deliberate public fields and may use bounded cache semantics from M2.

### Navigation and footer

- Navigation depth is at most two levels; a parent belongs to the same menu; self-parent, orphan, duplicate child, cross-menu parent, and every direct/indirect cycle are rejected before write.
- Sibling/column order is unique and normalized to a complete deterministic integer sequence in one transaction. Bulk reorder/replace requires the complete authorized ID set; missing, duplicate, foreign, or stale IDs fail without partial writes.
- Internal links are canonical root-relative paths resolving to the registered core-route catalog or, later, a published-page facade. M3 does not query page tables that do not yet exist.
- General external links allow `https` only. Explicit contact fields may allow normalized `mailto`/`tel`. `javascript:`, `data:`, protocol-relative URLs, credentials, fragments/control-character tricks, malformed URLs, and unsafe targets are rejected.
- New-window external links render with `noopener noreferrer`; hidden/invalid destinations never enter public navigation, footer, sitemap inputs, or accessibility trees.
- Footer columns/links, social/legal links, copyright, visibility, and ordering use the same link policy; empty columns have an explicit validation or omission rule.

### Authorization, concurrency, idempotency, and audit

- Public queries are unauthenticated and cannot become draft/private views when cookies or bearer credentials are supplied.
- Every admin command requires the M1 administrator actor, trusted Origin and CSRF on unsafe cookie requests, DTO allow-lists, and application-level resource/action authorization.
- Profile, settings, menu, footer, and mutable child resources return version-derived `ETag`; mutation requires `If-Match`, returns M2's `428` when absent and `409 RESOURCE_VERSION_CONFLICT` when stale, and never silently overwrites.
- Retriable full-tree replace/reorder commands use M2's actor+route `Idempotency-Key` contract. Same key/same request replays safely; payload mismatch conflicts; concurrent duplicates commit once; failures leave no partial order.
- Profile/settings/navigation/footer changes create controlled audit facts in the same UoW with safe actor/resource/request metadata. Audit data and structured logs contain no private field values, URLs with credentials, analytics values, bodies, cookies, or secrets.

## SSR, cache, and no-secret frontend rules

- `/about`, the public header/footer, public shell identity, default metadata, and navigation initial state are rendered by Next.js Server Components from `/api/v1/public` through the approved same-origin generated-client wrapper. Frontend code never accesses PostgreSQL or imports backend modules.
- Public business content is not hard-coded into components, build-time constants, demo-only branches, or fallback copy. Missing configuration renders an intentional unavailable/empty state, not invented biography, legal copy, statistics, links, or testimonials.
- The server-rendered HTML contains the allowed public values and remains meaningful with client JavaScript disabled. Hydration is reserved for theme selection, mobile drawer interaction, and other genuine client behavior.
- Admin mutation invalidates/revalidates the affected public data/path tags so a reload shows the new public value without a source edit or frontend rebuild. Bounded public caching must not retain a removed/private field. Admin/auth data remains `private, no-store` and never shares a public cache key.
- No private environment value or website-setting secret is exposed through `NEXT_PUBLIC_*`, RSC payloads, HTML, metadata, source maps, client bundles, browser storage, logs, traces, or screenshots.
- Metadata uses public site/profile projections only. Missing owner-supplied values degrade safely; the UI does not invent legal/SEO claims or load arbitrary analytics code.

## Contract freeze points

### S1 - M3 domain/data freeze

Integration/root records S1 only after T01-B/M pass. S1 freezes:

- aggregate ownership, singleton semantics, explicit public-field policy, and audit facts;
- table/column/constraint/index contract at sole revision `0004`;
- profile/settings value catalogs and validation rules, including no-secret analytics handling;
- navigation/footer depth, link, cycle, parent, visibility, target, and deterministic-order rules;
- version/ETag, `If-Match`, and idempotent full-tree update semantics;
- application facades used by the public projection and demo seed.

S1 releases T01-P and M3-SD. An incompatible change stops downstream work and returns to the T01 owner before generation.

### S2 - Public/admin API and generated-client freeze

Integration/root records S2 only after T01-P plus complete backend contract tests pass and regeneration is clean. S2 freezes:

- stable operation IDs and explicit single/error envelopes for admin profile/settings/navigation/footer;
- `GET /api/v1/public/site`, `/api/v1/public/profile`, and `/api/v1/public/navigation` public-only schemas;
- admin session/CSRF security declarations, public no-auth declarations, cache headers, `ETag`/`If-Match`, idempotency, validation/error examples, and deprecation metadata;
- distinct admin/public schemas with no private/default-secret fields in the public generated types;
- deterministic generated TypeScript client and approved feature-wrapper boundary.

S2 releases both frontend lanes. Breaking changes require CHG-002 and a new reviewed generation window; frontend must not compensate locally.

### S3 - Rendered frontend readiness freeze

Integration/root records S3 only after T02-A/P pass focused tests and browser review. S3 freezes:

- public SSR/header/footer/about data and cache invalidation behavior;
- admin profile/settings/navigation/footer routes, form/state behavior, and responsive reorder alternative;
- public mobile drawer/theme/current-route behavior and the M0 design-token/component contract;
- sanitized fixture interfaces used by final E2E.

S3 releases T03. S3 is not M3 acceptance.

## Demo-seed handoff for M0-T07/T08

M3 is the first milestone with durable non-secret public content tables, so it supplies the missing internal `seed-demo` implementation without expanding M3 feature scope.

The `M3-SD` command must:

- be explicit, noninteractive, deterministic, idempotent, and transactionally use the accepted profile/settings/navigation application facades;
- create only clearly fictional, non-sensitive demo profile/site/navigation/footer content supported by M3; create no administrator, credential, password, session, CSRF value, API token, contact, private biography/contact value, media object, secret setting, or analytics credential;
- refuse production before any write, perform no startup/migration side effect, and leave existing administrator/auth state untouched;
- converge repeated runs without duplicate navigation/footer nodes and report only safe aggregate counts/IDs;
- be absent from E2E/test fixture setup: tests create isolated data through factories/APIs and do not depend on `seed-demo`.

Handoff order:

1. Backend delivers the internal command, focused unit/PostgreSQL/idempotency/production-refusal/redaction tests, and sanitized evidence.
2. Integration/root independently reviews the command against S1, runs seed with no administrator row present, runs it twice, inspects resulting tables/logs, and records the accepted internal command name only if evidence passes.
3. Infrastructure alone wires the accepted command into `scripts/task.py`, `Makefile`, Compose operations profile, and operator docs as required by the existing M0-T07 reservation.
4. The active M0-T08 owner alone adds/updates command-parity and seed-without-admin CI smoke without weakening other gates.
5. Integration/root reruns M0-T07/T08 acceptance and decides whether those tasks close. M3 agents do not edit or mark M0 evidence accepted.

Any production write, credential/token creation, private content, dependency on bootstrap, implicit startup action, duplicate seed rows, leaked value, or M3-agent edit to infrastructure/CI files blocks the handoff.

## Dispatch order

1. **Do not start M3 implementation now.** Complete D0-D2; require M2 C3 plus the separate M2 acceptance record.
2. **After D2 - Backend `M3-T01-B/M`:** implement the three domain modules, admin commands/API, and sole `0004` migration.
3. **After T01-B/M evidence - Integration/root:** review and record S1.
4. **After S1 - Backend `M3-T01-P` and `M3-SD`:** public projection and demo seed may run in parallel only in disjoint files.
5. **After all T01 backend evidence - Integration/root `M3-T01-I`:** export, lint, regenerate twice, compile, review, and record S2.
6. **After S2 - Frontend `M3-T02-A/P`:** admin and public lanes may run concurrently only in disjoint routes/features/components.
7. **After frontend evidence - Integration/root:** review SSR/privacy/accessibility/performance and record S3.
8. **After S3 - Integration/root `M3-T03-I`:** execute the full admin-to-public flow, documentation/reviews, and prepare the M3 gate record.
9. **Separately after seed acceptance - Infrastructure/M0 CI owners:** wire and validate seed, then return M0-T07/T08 to Integration/root.

## Exact acceptance, security, performance, and documentation evidence

All records follow `docs/plan/delivery-evidence-template.md`, record requested milestone `M3` plus trace aliases `M06/M07`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, artifact link, finding, correction, and independent retest. Evidence uses repository-relative paths and never stores cookies, CSRF values, authorization headers, credentials, private profile/contact data, analytics values, full external URLs with sensitive query data, production dumps, or machine-specific absolute paths.

### `M3-T01` backend/public-contract evidence

Required mapping: `AC-007`, `AC-021`, `AC-022`, applicable `AC-027`-`AC-030`, `AC-035`-`AC-036`, `AC-039`-`AC-040`; `F1-007`, `F2-003`, `F2-014`-`F2-015`, `API-001`-`API-006`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-006`-`NFR-008`, `NFR-011`.

Evidence must include:

- domain/service/repository tests for singleton create/update/race behavior, every profile/settings field and boundary value, IETF locale and IANA timezone validation, explicit public-field decisions, and rollback/audit coupling;
- public/admin schema-difference and serialization tests proving private/unapproved values are absent rather than null/redacted, including payload, metadata, cache, structured log, trace, and error inspection;
- settings mass-assignment and secret-like input tests for credentials, keys, scripts/HTML, unknown analytics providers/fields, storage/database identifiers, unsafe URLs, and extra fields;
- navigation/footer property and integration tests for max depth two, direct/indirect cycles, orphan/cross-menu/self parent, duplicate/missing/foreign IDs, empty/duplicate/gapped order, atomic normalization, visibility, and safe target behavior;
- URL tests for valid registered internal, normalized contact, and HTTPS external links plus encoded/case/whitespace/control-character, `javascript:`, `data:`, protocol-relative, credential, malformed, unsafe-target, and unpublished/unknown internal destination negatives;
- authorization/IDOR/mass-assignment, CSRF/Origin, safe not-found, request-ID/error, no-store admin, cacheable public, `ETag`/`If-Match` absent/stale/concurrent, idempotent replay/payload-mismatch/concurrent duplicate, and rollback-no-partial-order API tests;
- migration evidence listed above and query-plan/SQL-count evidence with representative menu/footer trees proving bounded queries, deterministic order, no obvious N+1, and appropriate observed indexes;
- OpenAPI schema/security/error/example/deprecation review, unique operation IDs, deterministic export/generation twice with no diff, strict generated compile, wrapper-boundary scan, and reviewed contract diff;
- Ruff format/lint, strict Mypy, full affected Pytest and coverage reports; generated TypeScript/Prettier/ESLint/strict type checks; no disabled test or unexplained new warning.

Confirmed private/secret disclosure, an accepted unsafe link, cycle/depth/order corruption, lost update, duplicate side effect, partial tree write, direct repository/ORM reach-through, second migration head, generated drift, failed Must requirement, or Critical/High finding blocks S1/S2.

### `M3-T02` frontend/admin/public evidence

Required mapping: `AC-003`, `AC-007`, `AC-021`-`AC-022`, `AC-025`, `AC-031`-`AC-035`; `F1-002`-`F1-004`, `F1-007`, `F2-003`, `F2-014`-`F2-015`, `F2-019`, `NFR-001`-`NFR-010`, `SEC-004`-`SEC-005`, `SEC-009`.

Admin evidence must include:

- generated-wrapper/form tests for profile public/private preview, settings validation/no-secret errors, navigation tree and footer editors, server field-path mapping, CSRF credentials, request IDs, and safe error text;
- initial/loading/success/empty/validation/server/unauthorized/expired/offline/conflict states; protected DOM/cache removal on expiry; dirty status and `Stay`, `Leave without saving`, valid `Save and continue` navigation protection;
- version-conflict behavior preserving local edits and offering reload/review/copy without overwrite;
- pointer and keyboard reorder with Move up/down/to-position alternatives, deterministic announcements, focus/scroll preservation, and an equivalent narrow mobile list rather than drag-only interaction;
- persistent labels, focused linked error summary, 44 px targets, visible unclipped focus, semantic tree/list/form structure, status not conveyed by color, reduced motion, and no critical toast-only feedback.

Public SSR evidence must include:

- Server Component tests and built-page inspection proving public profile/site/navigation/footer data comes from the public API wrapper, is present in initial HTML/metadata, works with JavaScript disabled, and has no direct DB/backend import or hard-coded business-content fallback;
- cache invalidation tests proving an admin update/removal appears on public reload without rebuild and removed/private values are absent from cached HTML/RSC payload/metadata;
- desktop primary navigation and below-`lg` modal drawer containing every visible destination, current route with `aria-current`, safe external target/rel, theme control, focus trap, Escape/close, scroll lock, and focus restoration;
- missing optional field/image, unconfigured profile/site, invalidated destination, public API failure, and designed not-found/error behavior without invented content or private leakage;
- responsive/manual evidence at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px plus 400% zoom, light/dark/system, forced-colors where practical, and reduced motion; axe plus keyboard and representative screen-reader review.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library, Storybook interaction/a11y, production build, and focused Playwright. Record Server/Client Component and bundle analysis showing no avoidable client conversion; route JS and bundle delta; SSR/API request counts; layout-shift/asset behavior; and Lighthouse profiles for `/about` plus the public shell targeting performance >=90, accessibility >=95, SEO >=95 with variances explicitly dispositioned.

Hard-coded public biography/settings/nav, client-only initial content, stale private cache, secret in bundle/storage/HTML, broken keyboard drawer/reorder, unresolved WCAG blocker, unexplained target regression, raw fetch/generated bypass, or stale generated types blocks S3/T02.

### `M3-T03` vertical-flow and M3 gate evidence

Required mapping: `AC-002`-`AC-003`, `AC-007`, `AC-021`-`AC-022`, `AC-025`, `AC-027`-`AC-035`, `AC-037`-`AC-043` applicable slice portions; `F1-002`-`F1-004`, `F1-007`, `F2-003`, `F2-014`-`F2-015`, `F2-019`, `DOC-001`-`DOC-003`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-001`-`NFR-018` applicable slice portions.

Integration/E2E must use built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0004`, with isolated API-created fixtures rather than demo seed. It must prove:

- authenticated administrator edits profile public/private fields, site identity/locale/timezone/theme/SEO/public analytics identifier, navigation nesting/order/visibility/targets, and footer columns/legal/social/copyright;
- invalid secret-like settings, unsafe URLs, unknown internal destinations, cycle/depth/order violations, missing/stale `If-Match`, forged/missing CSRF, untrusted Origin, unauthorized actor, IDOR/mass assignment, and idempotency mismatch all fail safely without partial writes;
- a second concurrent admin view receives a conflict and cannot silently overwrite; retry/idempotent reorder produces one final deterministic tree;
- public reload, hard navigation, and JavaScript-disabled request show the changed profile/brand/navigation/footer/metadata server-rendered without code change or rebuild; hidden/removed/private values disappear from payload, HTML, metadata, RSC/cache, accessibility tree, logs, screenshots, and traces;
- desktop/mobile keyboard navigation, drawer focus restoration, current-route state, themes across revisit, admin dirty/error/conflict/reorder flows, and responsive layouts meet the documented UX contract;
- regenerated client remains clean, migration remains one head, full affected backend/frontend/contract/migration/E2E/build/scan commands pass, and no Critical/High finding remains.

Documentation evidence must include:

- user walkthroughs for profile privacy flags, site identity/defaults/locale/timezone/theme/SEO/public analytics identifiers, navigation nesting/order/visibility/targets, footer/legal/social configuration, conflict recovery, and the staged media-field limitation;
- API documentation with public/admin endpoints, schemas, auth/CSRF, cache, public/privacy projection, errors, `ETag`/`If-Match`, idempotency, link/tree/order rules, and sanitized examples/cURL;
- developer documentation for module/facade boundaries, public SSR/data/cache invalidation, generated-client workflow, migration `0004`, link registry extension, no-secret settings model, and demo-seed separation;
- sanitized cross-device Signal Ledger screenshots, performance/bundle/query reports, accessibility protocol/results, security/privacy review, API review, traceability links, and independent reviewer sign-off.

Media-backed image fields remain staged until M9 and are explicitly recorded rather than masked by a fake implementation. Later release-level portions of documentation/SEO/media acceptance remain planned and are not overclaimed by M3.

The M3 gate remains blocked by any failed Must requirement, weakened/suppressed check, placeholder/mock production path, hard-coded business content, public/private projection leak, secret-capable setting, unsafe link/tree corruption, lost update, generated drift, multiple migration heads, incomplete demo-seed separation, unsanitized evidence, missing independent retest, unresolved WCAG blocker, or confirmed Critical/High finding. Passing lane evidence does not authorize M4 until Integration/root records the separate M3 acceptance decision.
