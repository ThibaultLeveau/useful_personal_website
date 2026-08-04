# Milestone 4 Dispatch

## Dispatcher status

This document prepares `M4-T01` through `M4-T03`. It does not release implementation, record acceptance, or authorize M5.

The repository currently contains active M1 identity work, prepared but unaccepted M3 site-configuration work, and active Infrastructure database-role/CI work. M4 remains blocked until Integration/root records the M3 acceptance decision and releases every required shared surface.

| Task     | Current state | Release condition                                                                                                               |
| -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `M4-T01` | Blocked       | M3 passes; one Alembic head is confirmed at `20260802_0004`; active M1/M3/Infrastructure reservations are released; B0-B2 pass. |
| `M4-T02` | Blocked       | `M4-T01` backend/API evidence passes and skills contract freeze K2 is recorded with a clean generated client.                   |
| `M4-T03` | Blocked       | `M4-T01` and `M4-T02` pass and frontend readiness freeze K3 is recorded.                                                        |

M4 maps to trace milestone `M08` and delivers the Skills vertical slice: category and skill administration, ordering/feature/visibility behavior, a public grouped/filterable skills view, contract generation, tests, documentation, and evidence. Experience/project relation targets remain later milestones and must not be faked.

## Strict dependency gates

### B0 - M1 provider and active-file clearance

Integration/root confirms that M1 identity/authentication is accepted and that the following are stable provider contracts: administrator actor, protected route/session behavior, CSRF/Origin, request redaction, controlled audit facts, and auth OpenAPI/generated types. M4 may consume these contracts but may not alter identity repositories, sessions, rate limits, auth cookies, forced-password behavior, or auth UI/E2E.

### B1 - M2 API contract baseline

M4 consumes the accepted M2 C3 contract without modification:

- `/api/v1` audience separation, envelopes, stable errors, request IDs, UTC/ID rules;
- page-number pagination, typed filter/sort allow-lists, deterministic `id` tie-breaker;
- actor authorization, `ETag`/`If-Match`, `428`, version conflict, and actor+route idempotency;
- same-origin generated-client wrapper, cookie/CSRF behavior, and safe `ApiError` translation;
- deterministic OpenAPI export/generation and v1 compatibility/change policy.

Any common-contract defect returns to M2 and must be re-evidenced there. M4 does not add raw transport, alternate envelope, local error shim, arbitrary filtering, or duplicate idempotency storage.

### B2 - M3 acceptance and site-shell baseline

Integration/root must record the separate M3 acceptance decision and prove:

- `M3-T01` through `M3-T03` pass their backend, public projection, generated-client, admin/public UI, E2E, security, accessibility, performance, and documentation gates;
- there is exactly one Alembic head at revision `20260802_0004` from `20260802_0004_site_configuration.py`;
- the public/admin shells, same-origin SSR boundary, cache invalidation, navigation, theme, and protected admin layout are released;
- the M3 OpenAPI/generated client regenerates twice with no diff and strictly compiles;
- the registered `/skills` public route and `/admin/skills` admin destination are available for the slice without placeholder content;
- no failed Must requirement, unresolved WCAG blocker, or confirmed Critical/High finding remains in the dependency baseline.

Only B2 releases the M4 skills domain lane. M3 C3/S3-style preparation without the separate M3 acceptance decision is insufficient.

## Active-file exclusions

### M1 identity files

M4 must not edit, move, delete, format, or regenerate:

- `backend/app/modules/identity/**`, M1-owned `backend/app/modules/audit/**`, `backend/app/infrastructure/rate_limit/**`, bootstrap/auth route/schema/test files, and `20260802_0002_identity_auth.py`;
- `frontend/src/features/auth/**`, auth/account routes, auth boundary/wrappers, protected-session tests, and auth E2E/evidence;
- auth-only changes in shared backend/frontend application shells unless Integration/root issues a separate sequential reservation.

### M3 site-configuration files

Until B2, M4 must not edit, move, delete, format, or regenerate:

- `backend/app/modules/{profile,settings,navigation}/**`, their admin/public routes/schemas/tests, and `20260802_0004_site_configuration.py`;
- M3 demo-seed implementation/evidence and its Infrastructure handoff files;
- `frontend/src/features/{profile,settings,navigation}/**`, `/about`, profile/settings/navigation/footer admin routes, public header/footer/layout, admin-shell changes, and M3 E2E/evidence/docs;
- the in-flight M3 `docs/api/openapi.json`, generated client, contract reports, traceability edits, and final M3 acceptance record.

After B2, these remain provider-owned. Skills integrates with the released public/admin shells through documented extension points and does not reach into site-configuration persistence or private projections.

### Infrastructure database-role and CI files

M4 lanes may run but must not edit:

- `backend/alembic.ini`, `backend/migrations/env.py`, shared migration templates/bootstrap, and Infrastructure-owned database-role/grant/provisioning scripts;
- `backend/app/infrastructure/database/**`, shared database-role/readiness/runtime/session/UoW files, and active role-isolation tests;
- `.env.example`, `compose.yaml`, both Dockerfiles, `infrastructure/**`, migration/runtime credential injection, and database operator documentation under active Infrastructure ownership;
- `.github/workflows/**`, `.pre-commit-config.yaml`, `Makefile`, `scripts/task.py`, scanner/dependency-audit/coverage configuration, and M0-T07/T08/T09 reports;
- root manifests/locks and all active Infrastructure evidence.

M4 may add only its reserved `0005` revision and dedicated `test_0005_skills*` migration files after B2. If a task/role/CI change is required, M4 supplies a command or requirement to the active Infrastructure owner; it does not patch the shared file or weaken a gate.

### Integration/root single-writer files

Only Integration/root may write `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator scripts or configuration, final cross-lane contract reports, traceability acceptance links, and the final M4 task/milestone decisions. Requirements, architecture, ADR, UX, and existing planning artifacts remain read-only unless separately dispatched.

## Owner-safe M4 lanes

| Stage                                | Owner                           | Exclusive write area                                                                                                                                                                                                                                                                                  | Gate and handoff                                                                                                                                                                 |
| ------------------------------------ | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M4-T01-D` skills domain/application | Backend Domain Agent            | Skills/category domain types, invariants, command/query DTOs, application ports/facades, stable domain errors, and focused unit/service tests under `backend/app/modules/skills/**`; `docs/evidence/M4/M4-T01-domain.md`. Explicitly excludes persistence/public-projection filenames reserved below. | Starts after B2. Records the candidate relation and ordering interfaces for K1. Does not write migration, API artifact, frontend, shared DB infrastructure, or final acceptance. |
| `M4-T01-R` skills persistence        | Backend Persistence Agent       | Dedicated skills ORM/repository adapter files and repository tests inside `backend/app/modules/skills/**`; `docs/evidence/M4/M4-T01-persistence.md`.                                                                                                                                                  | Starts after K1. Implements inward-facing ports only; repositories never commit. It does not edit migration or target experience/project modules.                                |
| `M4-T01-M` sole migration            | Backend Migration Agent         | `backend/migrations/versions/20260802_0005_skills.py`, dedicated skills migration fixtures/tests, and `docs/evidence/M4/M4-T01-migration.md`.                                                                                                                                                         | Starts after K1 and an Integration/root `0005` reservation. Serialized with model registration; no other M4 revision or merge head.                                              |
| `M4-T01-A` admin API                 | Backend API Agent               | Dedicated admin skill/category route and transport-schema modules, API tests, and `docs/evidence/M4/M4-T01-admin-api.md`.                                                                                                                                                                             | Starts after K1; may run beside R/M only in disjoint files. Uses application facades, M1 actor, and M2 API primitives; never imports repositories/ORM.                           |
| `M4-T01-P` public projection         | Backend Public Projection Agent | Dedicated skills public projection/query files, `/api/v1/public/skills` route/schema, cache/privacy/query tests, and `docs/evidence/M4/M4-T01-public-projection.md`.                                                                                                                                  | Starts after K1. Reads through the skills query facade only and submits executable Pydantic source for K2.                                                                       |
| `M4-T01-I` OpenAPI/client generation | Integration/root                | Cross-lane contract tests/reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, K2, and final T01 decision.                                                                                                                                           | Starts after D/R/M/A/P evidence. Integration/root is the sole artifact/generated-code writer; every other lane pauses those surfaces.                                            |
| `M4-T02-A` skills admin frontend     | Frontend Admin Agent            | `frontend/src/features/skills/admin/**`, `/admin/skills`, skills-specific admin components/stories/tests, feature wrappers, and `docs/evidence/M4/M4-T02-admin.md`.                                                                                                                                   | Starts after K2. Any shared admin-shell/navigation edit receives one separate sequential reservation after M3 release.                                                           |
| `M4-T02-P` skills public frontend    | Frontend Public Agent           | `frontend/src/features/skills/public/**`, `/skills`, public skill/category components/stories/tests, SSR/filter/cache code, and `docs/evidence/M4/M4-T02-public.md`.                                                                                                                                  | Starts after K2 and may run beside T02-A only in disjoint files. Initial public data is server-rendered through the generated wrapper.                                           |
| `M4-T03-I` integration/E2E/docs      | Integration/root                | Skills API/browser fixtures/specs, sanitized traces/screenshots/reports, user/API/developer docs, traceability evidence links, `docs/evidence/M4/M4-T03.md`, and the final M4 gate record.                                                                                                            | Starts after T01/T02 pass and K3. Behavioral defects return to their owning lane. It does not start M5 or mark M4 accepted without independent review.                           |

No two lanes edit the same file concurrently. `backend/app/modules/skills/__init__.py`, backend router/application composition, admin sidebar, public navigation, central API wrapper, and shared fixtures each receive one Integration/root-scheduled writer window if necessary. Backend owns executable Pydantic source; Integration/root alone exports and generates; frontend consumes only the K2 contract.

## Sole linear migration policy

M4 reserves exactly one revision:

```text
file: backend/migrations/versions/20260802_0005_skills.py
revision: 20260802_0005
down_revision: 20260802_0004
scope: skill_category, skill, category/skill order, visibility/featured constraints, observed indexes
```

The revision is created only after B2 proves `20260802_0004` is the accepted single head. It contains:

- flat skill categories with opaque UUID, normalized unique slug/name policy, optional description where the accepted domain contract permits it, deterministic position, timestamps, and version;
- skills with opaque UUID, normalized globally unique slug, name, category FK, description, proficiency label, optional score, nonnegative years, nullable safe icon representation, deterministic category-scoped position, featured, visible, timestamps, and version;
- database checks for score `0..100`, nonnegative finite years representation, required category, and boolean/default invariants;
- case-insensitive/normalized uniqueness plus scoped category/skill position constraints and only the indexes justified by admin/public queries;
- `ON DELETE RESTRICT` for a category containing skills; no silent cascade of administrator content;
- no experience, project, media, page/block, token, or fake target table and no dangling cross-module FK.

The icon field must not accept raw HTML/SVG, executable content, arbitrary CSS, storage keys, or unvalidated URLs. If the accepted contract uses an existing icon-family identifier, it is allow-listed; a media-backed icon remains nullable and is activated by the later media slice.

Migration evidence requires empty upgrade, upgrade from accepted `0004` with representative site data, current/head equality, one-head verification, schema/model comparison, constraints/indexes, category-delete restriction, uniqueness/concurrent insert, rollback/UoW, and runtime-vs-migration-role isolation. Production startup must not migrate or seed. A schema need discovered after K1 returns to the sole migration owner; parallel revisions and merge heads are prohibited.

## Skills domain and relation-facade contract

### Slugs, values, categories, visibility, and featured semantics

- Skill and category slugs use the accepted domain normalization: Unicode normalization to ASCII lowercase kebab case, `1..80` characters, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`, with normalized/case-insensitive uniqueness enforced in domain and PostgreSQL.
- A submitted slug either round-trips to the documented normalized value or receives a field-addressable validation error; invisible whitespace, confusables that cannot normalize safely, reserved/malformed separators, and concurrent duplicates do not create ambiguous rows.
- Proficiency score is optional; when present it is finite and inclusive `0..100`. Years of experience is finite and `>=0`; transport/database precision is explicit and values are not silently rounded or coerced.
- R1 categories are flat, ordered entities rather than an invented hierarchy. Category deletion while skills remain returns a stable in-use conflict; reassignment, if offered, is one explicit transactional command.
- Skill order is deterministic and scoped to category. Category order is deterministic globally. A bulk reorder contains the complete authorized ID set for its scope and atomically normalizes positions; duplicate, missing, foreign, stale, or cross-category IDs fail without partial writes.
- `featured` is presentation priority only and never implies public eligibility. Hidden skills may retain their admin featured flag, but public featured/group/list/filter projections require `visible=true`. A hidden category is not invented; an empty/no-visible-skills category is absent publicly.
- Create/edit/delete/category/reassign/reorder/feature/visibility commands create controlled audit facts in the same UoW. Audit/log metadata contains safe IDs and changed field names, never descriptions, request bodies, cookies, CSRF values, or hidden content values.

### Relations without fake target modules

Experience and project modules do not exist at M4 entry. M4 must not create placeholder modules, repositories, ORM tables, dangling FKs, mock production data, or a generic polymorphic relation store.

The real boundary is:

- Skills exposes an application `SkillReferenceFacade` that later experience/project modules use to validate opaque skill IDs and retrieve safe reference summaries; consumers never import the skills repository/ORM.
- Revision-owned experience/project relation rows are created by those target milestones, matching the accepted architecture that editorial relations live with their content revision.
- Associated projects/experiences on a public skill are reverse public projections supplied by the future target-module facades. Until a provider exists, the projection is a typed empty/unavailable state and cannot reveal hidden identifiers.
- Non-empty relation writes submitted before the provider contract exists are rejected with one documented stable capability-unavailable validation/domain error; they are never accepted and discarded.
- The M4 admin UI shows an explanatory disabled/unavailable relation section or omits the editor according to the frozen contract. It does not render a fake picker or claim a relation was saved.

M4 evidence verifies safe unavailable/empty behavior and the skills facade itself. The cross-module links portion of `AC-008` remains explicitly pending and receives appended evidence in M5/M6; M4 must not overclaim it.

## Admin/public API contract

### Admin capabilities

- Administrator-only category and skill list/get/create/update/delete operations use explicit DTO allow-lists; skill create/update cannot mass-assign ID, timestamps, actor, version, or relation state.
- Create and complete bulk reorder/reassign operations use M2's `Idempotency-Key` semantics when retryable. Mutable reads return version-derived `ETag`; update/delete/reassign/reorder/visibility/featured commands require `If-Match`, return `428` when absent and `409 RESOURCE_VERSION_CONFLICT` when stale.
- List endpoints use M2 pagination (`page=1`, `page_size=20`, max `100`) with exact totals. Minimum admin filters are documented for category, visible, featured, and normalized search; minimum sorts are position, name, created/updated time where applicable, always with deterministic `id` tie-breaker.
- Unsupported/duplicate filters/sorts, arbitrary `filter[...]`, SQL-like expressions, encoded operators, and unknown query fields return safe `422` errors and never become SQL identifiers.
- Admin responses are `private, no-store`; unsafe cookie methods require M1 session, exact trusted Origin, and CSRF. Application use cases re-check authorization rather than relying only on router guards.

### Public capabilities and hidden-data prevention

- `GET /api/v1/public/skills` returns only `visible=true` skills using a dedicated public schema, grouped/resolvable by visible categories, with documented category/featured/search filters and allow-listed sorts under M2 pagination.
- Supplying an admin cookie or bearer token to the public route cannot reveal hidden rows, admin-only fields, unavailable relation IDs, audit/version internals, or database order outside the public contract.
- Public featured results are a subset of visible results. Hiding/deleting/reordering/reassigning a skill invalidates the relevant public cache so reload and SSR no longer expose stale data.
- Hidden/deleted skills are absent from payload, HTML, RSC data, metadata, search/filter counts, category counts, featured panels, relation summaries, accessibility trees, logs, screenshots, and traces. Public not-found/filter behavior does not reveal their existence.
- Public queries use purpose-built projections/select loading, bound parameters, measured indexes, deterministic order, and bounded query counts; they never serialize ORM/admin models.

## Contract freeze points

### K1 - Skills domain/facade freeze

Integration/root records K1 only after T01-D passes focused review/tests. K1 freezes:

- skill/category field and value types, slug normalization, score/years validation, category-delete/reassign rules;
- flat category and category-scoped skill ordering, visibility/featured semantics, and stable domain errors;
- command/query DTOs, authorization/audit facts, concurrency/idempotency expectations;
- `SkillReferenceFacade` and the explicit unavailable reverse-relation behavior;
- persistence ports and the proposed `0005` schema contract.

K1 releases R/M/A/P. An incompatible domain/schema change stops downstream work and returns to T01-D before generation.

### K2 - Skills API and generated-client freeze

Integration/root records K2 only after T01-D/R/M/A/P pass and generation is clean. K2 freezes:

- stable admin category/skill CRUD, reorder/reassign/visibility/featured operation IDs and request/response/error envelopes;
- `GET /api/v1/public/skills`, public schema, pagination/filter/sort/group semantics, cache behavior, and hidden-data guarantees;
- session/CSRF and public no-auth security declarations, `ETag`/`If-Match`, idempotency, examples, and deprecation metadata;
- stable relation-unavailable error/state and additive future extension rule;
- deterministic generated TypeScript client and feature-wrapper boundary.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. K2 releases frontend. Breaking changes require CHG-002 and a new reviewed generation window; frontend must not compensate with raw fetch, duplicate transport types, `any`, or hand-edited generated code.

### K3 - Skills frontend readiness freeze

Integration/root records K3 only after both T02 lanes pass focused tests and browser review. K3 freezes:

- admin route, forms, categories, table/mobile cards, ordering controls, visibility/featured behavior, unavailable-relation UX, and async/conflict states;
- public `/skills` SSR, grouping/filtering/featured presentation, empty/no-result/error states, cache behavior, and hidden-data protections;
- sanitized fixture interfaces, accessible component behavior, responsive layout, and Signal Ledger visual treatment used by T03.

K3 releases T03. K3 is not acceptance.

## Frontend behavior contract

### Admin skills manager

- `/admin/skills` provides category management/filtering, paginated skill table at fitting widths and equivalent mobile cards below it, create/edit/delete, visibility/featured controls, and explicit bulk ordering.
- Forms use persistent labels, locally known validation on blur, server validation on submit, a focused linked error summary, retained input, textual dirty/saving/saved/failed state, and session-expiry cleanup.
- Conflict preserves local edits and offers reload/review/copy without overwrite. Destructive category/skill actions explain effects and restore focus to the next logical item/heading.
- Reorder works with pointer and keyboard and always offers Move up/down/to-position controls. It announces the moved item and position, preserves focus/scroll after server save, provides rollback/failure feedback, and is fully usable in mobile cards without drag.
- Visibility and featured are separate text-labeled controls/statuses. The UI never suggests featured means public. The relation section explains provider availability and never offers a nonfunctional/fake save.
- Initial/loading/success/empty/no-filter-result/validation/server/unauthorized/expired/offline/version-conflict states follow the accepted M3 shell contract; critical recovery is inline, not toast-only.

### Public skills view

- `/skills` is a Server Component for initial content and metadata, reading the same-origin public API through the generated feature wrapper. Filtering may use URL-backed server queries or a justified client island; the initial skill dataset is not client-only.
- Visible skills are grouped in deterministic category order, with featured treatment and optional filter/search that preserve shareable query state and accurate result counts. Hidden/empty categories do not render.
- Public content is API-backed and not hard-coded into components or demo fallbacks. Missing configuration/data renders an intentional empty state with relevant navigation, not invented skills, scores, clients, metrics, or relation links.
- Skill evidence uses semantic lists/headings and Signal Ledger labels, not progress bars that imply unsupported precision. A score, when public, has text context and is not communicated by color/width alone.
- Public cache invalidation makes admin create/edit/hide/delete/reorder/feature changes visible on reload without frontend source change or rebuild.

## Dispatch order

1. **Do not start M4 implementation now.** Complete B0-B2 and release active M1/M3/Infrastructure overlaps.
2. **After B2 - Backend `M4-T01-D`:** implement/review the skills domain, application contracts, errors, and relation facade candidate.
3. **After domain evidence - Integration/root:** record K1 and reserve sole revision `0005`.
4. **After K1 - Backend `M4-T01-R/M/A/P`:** persistence, migration, admin API, and public projection may run concurrently only in their disjoint files.
5. **After all T01 backend evidence - Integration/root `M4-T01-I`:** review contract/security/data evidence, export/generate twice, compile, and record K2.
6. **After K2 - Frontend `M4-T02-A/P`:** admin and public lanes may run concurrently only in disjoint feature/route/component files.
7. **After frontend evidence - Integration/root:** run focused SSR/privacy/accessibility/performance review and record K3.
8. **After K3 - Integration/root `M4-T03-I`:** execute full vertical integration, docs/reviews/evidence, and prepare the M4 gate record.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, record requested milestone `M4` plus trace alias `M08`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Logs, DB samples, API transcripts, screenshots, and traces are sanitized and contain no cookies, CSRF values, authorization headers, credentials, private/hidden content, production dumps, or machine-specific absolute paths.

### `M4-T01` backend/data/API evidence

Required mapping: `AC-008`, `AC-027`-`AC-030`, `AC-034`-`AC-040`; `F1-008`, `F2-004`, `API-001`-`API-006`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-006`-`NFR-008`, `NFR-011`, `NFR-014`-`NFR-018` applicable slice portions.

Evidence must include:

- unit/property tests for normalization/idempotence, malformed/confusable slug input, score absent/0/100 and below/above/nonfinite values, years zero/fractional/negative/nonfinite per frozen precision, visibility/featured truth table, category/order invariants, and stable errors;
- service/UoW tests for category and skill CRUD, delete-in-use, reassignment, complete bulk ordering, feature/visibility, audit coupling, rollback, deterministic clock/UUID, and relation provider unavailable/skills-facade behavior;
- PostgreSQL repository tests for normalized concurrent uniqueness, scoped positions, constraint races, bound parameters, transaction rollback, no repository commit, and bounded select loading;
- the complete `0005` migration evidence listed above, including role isolation and no second head;
- admin API tests for happy CRUD/category/order/feature/visibility plus absent/stale `If-Match`, idempotent replay/mismatch/concurrent duplicate, authorization/IDOR, mass assignment, CSRF/Origin, malformed input, safe not-found/conflict/internal errors, cache/no-store, and request-ID correlation;
- pagination traversal larger than one page with exact totals/no loss or duplication; accepted category/visible/featured/search filters and sorts; duplicate/unsupported/arbitrary-expression/SQL/filter injection negatives;
- public projection tests proving visible grouping/featured/filter behavior and exhaustive hidden/deleted/unavailable-relation absence even when credentials are supplied to the public route;
- audit/log/error/cache/trace inspection proving no hidden description/body, relation target ID, SQL, stack, credential, or private value disclosure;
- OpenAPI lint/reference/security/error/example/filter/sort/deprecation review, unique operation IDs, reviewed schema diff, generation twice with no diff, strict generated compile, and wrapper-boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest and meaningful coverage reports; generated TypeScript format/lint/type checks; no disabled test or unexplained warning.

An invalid score/years/slug write, duplicate normalized slug, order corruption/partial write, featured hidden leak, relation write silently discarded, fake target module/table, IDOR/mass-assignment/injection success, lost update, duplicate side effect, unsafe disclosure, generated drift, second migration head, failed Must requirement, or Critical/High finding blocks K1/K2.

### `M4-T02` frontend/admin/public evidence

Required mapping: `AC-008`, `AC-025`, `AC-031`-`AC-035`; `F1-002`-`F1-003`, `F1-008`, `F2-004`, `F2-019`, `NFR-001`-`NFR-010`, `SEC-004`-`SEC-005`, `SEC-009`.

Admin evidence must include:

- generated-wrapper/form tests for category/skill CRUD, normalized slug preview/server conflict, score/years boundaries, filters/pagination, visibility/featured, reorder/reassign, relation unavailable state, CSRF credentials, request IDs, and safe error mapping;
- component/story tests for desktop table and equivalent mobile cards, category navigation/filter, long content, default/hover/focus/disabled/loading/error/conflict/empty/no-result states, light/dark/high-contrast/reduced-motion, and narrow/zoom layouts;
- keyboard-only create/edit/delete/category/order/show-hide/feature flow; Move controls and announcements; focused error summary; dirty navigation protection; conflict draft preservation; expiry removal of protected state;
- axe with no unresolved blocker and manual keyboard/focus/screen-reader/200%-400% zoom/touch review at the required representative widths.

Public evidence must include:

- Server Component/wrapper tests and built HTML inspection proving API-backed initial content, correct grouping/order/featured/filter counts, meaningful JavaScript-disabled rendering, and no hard-coded business skill data or frontend DB/backend import;
- delayed/error/empty/no-result/page-beyond-last states and URL-backed filters with accessible result announcements/focus behavior;
- hidden/delete/cache invalidation tests across payload, RSC/HTML, metadata, accessibility tree, browser history/state, screenshots, and traces;
- semantic headings/lists, non-color score/proficiency meaning, readable long descriptions, 44 px targets, visible focus, and no invented relation links.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library, Storybook interaction/a11y, production build, and focused Playwright. Record Server/Client Component rationale, route JS/bundle delta, SSR/API request count, no unnecessary hydration/overfetch, public query plan/SQL count, and Lighthouse `/skills` profiles targeting performance >=90, accessibility >=95, SEO >=95 with measured variance disposition.

Broken keyboard/mobile reorder, stale privileged UI, raw fetch/generated bypass, client-only initial skills, hard-coded/fake relation content, hidden-data leak, unresolved WCAG blocker, or unexplained performance regression blocks K3/T02.

### `M4-T03` vertical-slice and M4 gate evidence

Required mapping: `AC-008`, `AC-025`, `AC-027`-`AC-040`, `AC-041`-`AC-043` applicable slice portions; `F1-008`, `F2-004`, `DOC-001`-`DOC-003`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-001`-`NFR-018` applicable slice portions.

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0005`. Fixtures are created through APIs/factories, not demo seed. It must prove:

- administrator creates/orders/edits/reassigns/features/hides/shows/deletes categories and skills at desktop and mobile widths using keyboard and pointer;
- normalized duplicate/malformed slug, score/years boundaries, category-in-use delete, invalid reorder set, missing/stale version, idempotency mismatch, unauthorized actor, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, and injection all fail safely without partial changes;
- public reload shows visible skills grouped/filtered/featured in deterministic order without rebuild, while hidden/deleted skills and empty categories disappear from API, SSR, metadata, caches, counts, accessibility tree, logs, traces, and screenshots;
- concurrent editors receive a conflict without silent overwrite and an idempotent retry commits one deterministic final order;
- relation provider absence is explained and safe, non-empty unavailable relation writes fail, no fake targets render, and the skills reference facade passes its consumer contract;
- full affected backend/frontend/contract/migration/E2E/build/scan commands pass, generated output remains clean, revision remains one head, and no Critical/High finding remains.

Documentation/evidence must include:

- user guide for categories, create/edit/delete, slug behavior, score/years, ordering, filtering, visibility/featured semantics, conflict recovery, and the staged relation limitation;
- API guide for admin/public skills, schemas/errors, auth/CSRF, pagination/filter/sort catalogs, cache, `ETag`/`If-Match`, idempotency, hidden-data policy, relation facade/unavailable behavior, and sanitized examples/cURL;
- developer guide for skills module/ports/facades, migration `0005`, repository/UoW, public SSR/cache invalidation, generated-client workflow, query/index decisions, and how M5/M6 consume `SkillReferenceFacade` without repository imports;
- sanitized screenshots at 320, 390, 768, 1024, 1440, and 1920 px for admin table/mobile cards/editor/reorder and public grouped/filter/empty states in light/dark, plus performance/query/bundle, accessibility, security/privacy, API, coverage, traceability, and independent-review reports.

M4 records the relation-target portion of `AC-008` as pending M5/M6 evidence; it does not mask the dependency or claim target links work before those modules exist. Passing lane evidence does not authorize M5 until Integration/root records the separate M4 acceptance decision.

The M4 gate remains blocked by any failed Must requirement, disabled/suppressed check, placeholder/mock production path, fake relation target, invalid invariant persistence, hidden-data leak, IDOR/mass-assignment/injection success, lost update/order corruption, generated drift, multiple migration heads, Infrastructure-file overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
