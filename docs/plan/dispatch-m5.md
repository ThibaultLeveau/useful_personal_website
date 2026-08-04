# Milestone 5 Dispatch

## Dispatcher status

This document prepares `M5-T01` through `M5-T03`. It does not release implementation, record acceptance, or authorize M6.

The repository contains active M1 identity work, prepared but unaccepted M3/M4 work, and active Infrastructure database-role/CI reservations. M5 remains blocked until Integration/root records the separate M4 acceptance decision and releases every required shared surface.

| Task     | Current state | Release condition                                                                                                                  |
| -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `M5-T01` | Blocked       | M4 passes; one Alembic head is confirmed at `20260802_0005`; active M1/M3/M4/Infrastructure reservations are released; E0-E2 pass. |
| `M5-T02` | Blocked       | `M5-T01` backend/API evidence passes and experience contract freeze L2 is recorded with a clean generated client.                  |
| `M5-T03` | Blocked       | `M5-T01` and `M5-T02` pass and frontend readiness freeze L3 is recorded.                                                           |

M5 maps to trace milestone `M09` and delivers the Professional Experiences vertical slice: revision-safe administration, skill relations, preview/publication lifecycle, public semantic timeline/list, contract generation, tests, documentation, and evidence. It does not authorize projects, media, blog, pages, workers/schedulers, or speculative AI behavior.

## Strict dependency gates

### E0 - M1/M2 provider baseline

Integration/root confirms accepted provider contracts for:

- M1 administrator actor, session/protected-route behavior, CSRF/Origin, forced-password restriction, redaction, and controlled audit facts;
- M2 envelopes/errors/request IDs, pagination/filter/sort, actor authorization, `ETag`/`If-Match`, idempotency, health, same-origin handwritten wrapper, and v1 compatibility;
- deterministic OpenAPI export/generated-client generation with no unexplained drift.

M5 consumes these contracts and does not change identity/session/rate-limit/auth, common API middleware, idempotency persistence, health, central error semantics, or generated transport behavior.

### E1 - M3 site-shell/timezone baseline

The separate M3 acceptance decision must prove that the public/admin shells, site settings, IANA timezone, navigation, theme, public SSR/cache invalidation, and protected admin layout pass their gates. M5 reads the configured timezone through the released settings application/public facade. It never queries settings tables directly or stores employment calendar dates as timestamps.

### E2 - M4 acceptance and skills-facade baseline

Integration/root must record the separate M4 acceptance decision and prove:

- `M4-T01` through `M4-T03` pass backend, migration, API, generated-client, admin/public UI, security, accessibility, performance, documentation, and vertical E2E gates;
- there is exactly one Alembic head at revision `20260802_0005` from `20260802_0005_skills.py`;
- `SkillReferenceFacade` is accepted, application-facing, and tested for existing/deleted/visible/hidden skill references without repository/ORM leakage;
- the M4 OpenAPI/generated client regenerates twice with no diff and strictly compiles;
- the released public/admin shells have real `/experience` and `/admin/experiences` extension points without placeholder business content;
- no failed Must requirement, unresolved WCAG blocker, unexplained generated drift, or confirmed Critical/High finding remains.

Only E2 releases the experience domain lane. M4 relation behavior that is merely prepared or pending without the separate acceptance record is insufficient.

## Active-file exclusions

### M1 identity/authentication files

M5 must not edit, move, delete, format, or regenerate identity, session, rate-limit, bootstrap/auth routes/schemas/tests, auth UI/boundary/E2E, `20260802_0002_identity_auth.py`, or M1 evidence. Shared auth/application-shell changes require a separate sequential Integration/root reservation.

### M3 site-configuration files

M5 must not edit profile/settings/navigation modules, their routes/projections/tests, `20260802_0004_site_configuration.py`, demo-seed code/evidence, site/admin shell implementation, public header/footer/about, M3 routes/features/E2E/docs, or M3 acceptance evidence. M5 uses settings/timezone and shells only through released facades/components.

### M4 skills files

Until E2, M5 must not edit, move, delete, format, or regenerate:

- `backend/app/modules/skills/**`, skills admin/public routes/schemas/tests, and `20260802_0005_skills.py`;
- `frontend/src/features/skills/**`, `/skills`, `/admin/skills`, skills-specific components/stories/tests/E2E/docs/evidence;
- the in-flight M4 `docs/api/openapi.json`, generated client, contract reports, traceability edits, and final M4 acceptance record.

After E2, skills remains provider-owned. M5 calls `SkillReferenceFacade`; it never imports the skills repository/ORM or changes skill visibility semantics. A skills-facade defect returns to M4 for correction and re-evidence.

### Infrastructure database-role/CI files

M5 lanes may run but must not edit:

- `backend/alembic.ini`, `backend/migrations/env.py`, shared migration templates/bootstrap, and Infrastructure-owned database-role/grant/provisioning scripts;
- `backend/app/infrastructure/database/**`, shared role/readiness/runtime/session/UoW files, and active role-isolation tests;
- `.env.example`, `compose.yaml`, Dockerfiles, `infrastructure/**`, migration/runtime credential injection, and operator topology/configuration docs under active ownership;
- `.github/workflows/**`, `.pre-commit-config.yaml`, `Makefile`, `scripts/task.py`, scanner/dependency-audit/coverage configuration, and M0 Infrastructure evidence;
- root manifests/locks.

M5 may add only its reserved `0006` revision and dedicated `test_0006_experiences*` migration files after E2. Required CI/role changes are handed to Infrastructure; M5 does not patch or weaken shared gates.

### Integration/root single-writer files

Integration/root alone writes `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator scripts or configuration, final cross-lane contract reports, traceability acceptance links, and final M5 task/milestone decisions. Requirements, architecture, ADR, UX, prior dispatches, and existing planning artifacts remain read-only unless separately dispatched.

## Owner-safe M5 lanes

| Stage                                    | Owner                           | Exclusive write area                                                                                                                                                                                                                                                                                                    | Gate and handoff                                                                                                                                            |
| ---------------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M5-T01-D` experience domain/application | Backend Domain Agent            | Experience aggregate/revision types, lifecycle/date/publication invariants, DTOs, ports/facades, controlled content validation, stable errors, and unit/service tests under `backend/app/modules/experiences/**`; `docs/evidence/M5/M5-T01-domain.md`. Excludes persistence/public-projection filenames reserved below. | Starts after E2. Produces the L1 domain/revision contract. Does not write migration, API artifact, frontend, shared DB infrastructure, or final acceptance. |
| `M5-T01-R` experience persistence        | Backend Persistence Agent       | Dedicated experience ORM/repository adapters, immutable-revision enforcement, query adapters, and repository tests inside `backend/app/modules/experiences/**`; `docs/evidence/M5/M5-T01-persistence.md`.                                                                                                               | Starts after L1. Implements inward-facing ports; repositories never commit and never import skills persistence.                                             |
| `M5-T01-M` sole migration                | Backend Migration Agent         | `backend/migrations/versions/20260802_0006_experiences.py`, dedicated migration fixtures/tests, and `docs/evidence/M5/M5-T01-migration.md`.                                                                                                                                                                             | Starts after L1 and an Integration/root `0006` reservation. Serialized with model registration; no other M5 revision or merge head.                         |
| `M5-T01-A` admin/preview API             | Backend API Agent               | Dedicated admin experience CRUD/lifecycle/preview route and transport-schema modules, API tests, and `docs/evidence/M5/M5-T01-admin-api.md`.                                                                                                                                                                            | Starts after L1; may run beside R/M only in disjoint files. Calls application facades and M4 skill facade, never repositories/ORM.                          |
| `M5-T01-P` public projection             | Backend Public Projection Agent | Dedicated experience public query/projection files, `/api/v1/public/experiences` route/schema, privacy/chronology/cache/query tests, and `docs/evidence/M5/M5-T01-public-projection.md`.                                                                                                                                | Starts after L1. Reads frozen effective revisions through a purpose-built facade and submits executable Pydantic source for L2.                             |
| `M5-T01-I` OpenAPI/client generation     | Integration/root                | Cross-lane contract tests/reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, L2, and final T01 decision.                                                                                                                                                             | Starts after D/R/M/A/P evidence. Integration/root is the sole artifact/generated-code writer; all other lanes pause those surfaces.                         |
| `M5-T02-A` experience admin frontend     | Frontend Admin Agent            | `frontend/src/features/experiences/admin/**`, `/admin/experiences`, `/admin/experiences/{id}/edit`, admin preview route/surface, experience-specific components/stories/tests/wrappers, and `docs/evidence/M5/M5-T02-admin.md`.                                                                                         | Starts after L2. Any shared admin-shell/editor primitive edit receives one separately scheduled writer window.                                              |
| `M5-T02-P` experience public frontend    | Frontend Public Agent           | `frontend/src/features/experiences/public/**`, `/experience`, semantic timeline/list components/stories/tests, SSR/cache code, and `docs/evidence/M5/M5-T02-public.md`.                                                                                                                                                 | Starts after L2 and may run beside T02-A only in disjoint files. Initial public content is server-rendered through generated wrappers.                      |
| `M5-T03-I` integration/E2E/docs          | Integration/root                | Experience API/browser fixtures/specs, sanitized traces/screenshots/reports, user/API/developer docs, traceability links, `docs/evidence/M5/M5-T03.md`, and the final M5 gate record.                                                                                                                                   | Starts after T01/T02 pass and L3. Behavioral defects return to the owning lane. It does not start M6 or mark M5 accepted without independent review.        |

No two lanes edit the same file concurrently. Experience package exports, backend router/application composition, admin sidebar, public navigation, central API wrapper, controlled-Markdown shared files, and shared fixtures each receive one Integration/root-scheduled writer window if needed. Backend owns executable Pydantic source; Integration/root alone exports/generates; frontend consumes only L2 generated types.

## Sole linear migration policy

M5 reserves exactly one revision:

```text
file: backend/migrations/versions/20260802_0006_experiences.py
revision: 20260802_0006
down_revision: 20260802_0005
scope: experience aggregate, immutable revisions, ordered revision content, revision-scoped skills, lifecycle pointers and observed indexes
```

The revision is created only after E2 proves `20260802_0005` is the accepted single head. It contains:

- `experience`: opaque UUID, visible, deterministic display position, `draft_revision_id`, `published_revision_id`, `publish_at`, `unpublished_at`, timestamps/version, and optional `deleted_at`;
- `experience_revision`: opaque UUID, aggregate FK, monotonically increasing revision number, company/URL, role, employment type, location, remote status, start/end calendar dates, current flag, short summary, controlled detailed description, frozen flag, creator, timestamps, and unique `(experience_id, revision_number)`;
- ordered revision-owned responsibilities, achievements, and technologies using relational child rows or another explicitly accepted non-executable typed representation; their order is scoped and deterministic;
- `experience_skill` relations attached to the revision, not only the stable aggregate, with FKs to accepted M4 skills; duplicate relation IDs are impossible;
- pointer integrity so draft/published pointers reference revisions belonging to the same aggregate; deferrable FKs or the accepted two-step pointer pattern resolve circular creation safely;
- check constraints for start/end/current rules, remote-status catalog, revision number/order, and frozen-state invariants where enforceable;
- partial/composite indexes justified by effective public chronology and admin lifecycle/filter queries;
- no project/media/blog/page/token/fake provider table and no scheduler/worker/outbox.

Frozen published revisions are immutable through domain/repository behavior and are reinforced by a database trigger/permission/check only when compatible with the accepted database-role architecture. M5 does not edit Infrastructure grants; any required grant is handed to its owner. Mutation/deletion attempts against a frozen revision must fail in repository and migrated PostgreSQL tests.

Migration evidence requires empty upgrade, upgrade from accepted `0005` with representative skills/site data, current/head equality, one-head verification, schema/model comparison, pointer/deferrable-FK integrity, constraints/indexes, frozen-row mutation rejection, copy-on-write data behavior, skill FK/revision relation behavior, rollback/UoW, and runtime-vs-migration-role isolation. Production startup must not migrate or schedule. A schema need found after L1 returns to the sole migration owner; parallel revisions and merge heads are prohibited.

## Experience domain and publication contract

### Employment content and date/status invariants

- Required content includes company name, role title, start date, employment type, remote status, and the fields required by the frozen transport contract. Company URL follows the accepted safe external-link policy: `https` only, with no credentials, protocol-relative form, control characters, or executable scheme.
- Employment start/end are calendar dates (`YYYY-MM-DD`), not UTC timestamps. `start_date` is required. If `end_date` is present it is on/after `start_date`.
- `current_position=true` requires `end_date=null`. `current_position=false` permits an unknown `end_date`; it does not silently invent one.
- `remote_status` is exactly `onsite`, `hybrid`, or `remote`. Employment type is a documented closed catalog frozen at L1; unknown values are field-addressable validation errors, not free-form persistence.
- Responsibilities, achievements, and technologies preserve explicit order and reject malformed/empty/duplicate values according to the frozen schema. They are data, never executable HTML.
- Detailed description uses the accepted controlled-Markdown policy where formatting is enabled: fixed extensions, raw HTML disabled, unsafe URLs rejected, sanitized rendering defense in depth. If the shared renderer is not already accepted, Integration/root reserves its backend/frontend files serially; no lane creates a second policy.
- Display position is deterministic for curated/admin surfaces. The public `/experience` timeline defaults to real chronology: current positions first, then start date descending, end date with documented null handling, display position, and opaque `id` tie-breaker. CSS never visually reverses DOM reading order.

### Revision and lifecycle semantics

- Create atomically creates the stable aggregate plus revision 1 as a mutable draft. No public pointer exists; lifecycle is `Draft`.
- Draft save mutates only the current unfrozen draft under aggregate version/`If-Match`. Saving a draft never changes the published pointer/content.
- Publish validates the entire draft and its references, freezes that revision, assigns it as `published_revision_id`, sets `publish_at` from the requested instant or database UTC now, and creates the next copy-on-write mutable draft in one transaction.
- A future `publish_at` is `Scheduled`; an effective current/past value is `Published` only when visible and not deleted. Effectiveness is evaluated with PostgreSQL `now()`, not application/server/browser clocks and not a worker.
- Editing after publish changes only the copy-on-write draft and produces `Published - changes pending`; the live projection remains byte/field-equivalent to the frozen published revision until the next publish.
- Reschedule changes only aggregate scheduling metadata under concurrency/idempotency rules; it does not mutate frozen content. Unpublish clears public eligibility immediately, retains revisions, records `unpublished_at`, and invalidates public caches.
- Visibility is independent of lifecycle. A published/effective but hidden experience is not public. Delete is a separate confirmed action, never an alias for unpublish; it removes public eligibility while preserving referential/audit integrity according to the frozen soft-delete policy.
- `Scheduled`, `Published`, `Published - changes pending`, and `Unpublished` are derived from pointers/version/content/time; no background status-flip row mutation is required.

### Skill relations through M4

- Draft skill IDs are validated through M4 `SkillReferenceFacade`; unknown, deleted, duplicate, malformed, or unauthorized references fail safely. M5 never imports skills ORM/repository.
- Relations are revision-scoped. Editing relations on a draft cannot alter or leak the live published revision's relation set.
- Hidden skills may be retained as draft references with an explicit admin warning if the frozen facade allows it. Publication validates required references; optional hidden/unavailable skills are omitted defensively from public relation summaries.
- Public experience schemas contain only visible skill reference summaries from the public M4 facade, never hidden skill IDs, category/admin metadata, or a relation that belongs only to a draft.
- Project relations are not introduced in M5. M6 owns project revisions and any reverse experience/project relation; M5 creates no fake target module/table/picker.

## Admin/public API, preview, and privacy contract

### Admin and lifecycle API

- Admin list/get/create/update/delete, reorder/visibility, preview, publish, reschedule, and unpublish operations use explicit DTO allow-lists and stable operation IDs/errors. IDs, pointers, frozen flags, versions, creator/audit data, and timestamps cannot be mass-assigned.
- Mutable reads return version-derived `ETag`. Draft save/delete/reorder/visibility/publish/reschedule/unpublish require `If-Match`, return M2 `428` when absent and `409 RESOURCE_VERSION_CONFLICT` when stale, and never silently overwrite.
- Retriable create/publish/reschedule/unpublish/reorder actions use M2 actor+route `Idempotency-Key`. Same key/same request replays the same safe result; payload mismatch conflicts; concurrent duplicate publish freezes/points/copies exactly once.
- Admin list follows M2 page pagination and allow-listed filters for lifecycle, visible, current, employment type, remote status, skill, and normalized search where accepted. Sorts are explicitly cataloged; arbitrary/duplicate/SQL-like query syntax fails `422`.
- Every use case re-checks M1 actor authorization. Unsafe cookie methods require exact trusted Origin and CSRF. Admin and preview responses are `private, no-store`.

### Preview isolation

- Preview is a separate administrator-session-only endpoint that returns the current draft projection even when not published/visible, with `Cache-Control: private, no-store` and safe request ID.
- Preview never appears in public APIs, metadata, sitemap/robots discovery, public cache tags, unauthenticated search, logs, or shareable URLs/tokens. Supplying a guessed ID without a valid session reveals no protected existence.
- The rendered preview has a persistent `Draft preview - not public` banner and `noindex` metadata, and provides a safe return to the editor. Session expiry removes the draft DOM/cache before navigation.

### Public allow-list, scheduling, chronology, and query plan

- `GET /api/v1/public/experiences` returns only aggregates with non-null published pointer, `visible=true`, `publish_at <= PostgreSQL now()`, and `deleted_at is null`, through a dedicated public schema/projection.
- Public data includes only deliberately public experience fields plus visible skill summaries. It excludes draft/published revision IDs, draft content/differences, creator/admin/audit data, version/internal pointers, hidden skills, and future/hidden/deleted/unpublished rows.
- Admin cookies or bearer credentials supplied to the public route do not widen results. Nonpublic records are absent from payload, totals, filters, timeline, metadata, caches, accessibility tree, logs, traces, and screenshots.
- Public list pagination is deterministic and traversable without loss/duplication. Minimum filters/sorts and chronology are documented and mapped to typed bound SQL expressions; every sort ends with opaque `id`.
- Query plans use a partial effective-public index and select loading for frozen revision, ordered children, and visible skill summaries. Representative data proves bounded query count/no N+1. Cache TTL does not outlive the next scheduled `publish_at`; publish/reschedule/unpublish/hide/delete invalidates affected cache tags/paths immediately.

## Contract freeze points

### L1 - Experience revision/domain freeze

Integration/root records L1 only after T01-D passes focused review/tests. L1 freezes:

- aggregate/revision ownership, field/value catalogs, employment date/status invariants, safe content policy, and deterministic chronology;
- immutable publish/copy-on-write draft, schedule/reschedule/unpublish/visibility/delete semantics and stable domain errors;
- revision-scoped skill relation rules through `SkillReferenceFacade` and explicit no-project-provider boundary;
- command/query DTOs, authorization/audit facts, concurrency/idempotency expectations;
- persistence ports and proposed `0006` schema/pointer/index contract.

L1 releases R/M/A/P. An incompatible domain/schema change stops downstream work and returns to T01-D before generation.

### L2 - Experience API and generated-client freeze

Integration/root records L2 only after T01-D/R/M/A/P pass and generation is clean. L2 freezes:

- stable admin CRUD/list/reorder/visibility/preview/publish/reschedule/unpublish/delete operation IDs and explicit envelopes/errors;
- public experience list schema, pagination/filter/sort/chronology, effective-time/cache behavior, and draft/hidden/future privacy;
- preview/session/no-store and admin session/CSRF security declarations;
- `ETag`/`If-Match`, idempotency, date/time formats, examples, relation summaries, lifecycle labels, and deprecation metadata;
- deterministic generated TypeScript client and feature-wrapper boundary.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. L2 releases frontend. Breaking changes require CHG-002 and a new reviewed generation window; frontend must not compensate with raw fetch, duplicate transport types, `any`, or hand-edited generated code.

### L3 - Experience frontend readiness freeze

Integration/root records L3 only after both T02 lanes pass focused tests and browser review. L3 freezes:

- admin list/editor/relations/preview/publication workflow, lifecycle/status/timezone/conflict states, responsive layout, and accessible ordered fields;
- public `/experience` SSR semantic timeline/list, chronology, skill evidence links, empty/error states, cache/privacy behavior, and responsive Signal Ledger treatment;
- sanitized fixture interfaces and screenshots used by T03.

L3 releases T03. L3 is not acceptance.

## Frontend behavior contract

### Admin experience manager/editor

- `/admin/experiences` provides paginated search/filter/status/visibility list, deterministic order, desktop table and equivalent mobile cards, create/edit/preview/publish/unpublish/delete actions, and text-plus-shape lifecycle/visibility status.
- The editor covers every SPEC experience field, ordered responsibilities/achievements/technologies, M4 skill relations, visibility, display order, and publication controls. Tabs such as Content, Relations, and Publication retain state and expose cross-tab error counts.
- Date controls use calendar dates. `current_position` disables/clears end date with explicit explanation; server remains authoritative. Employment type/remote status are labeled closed choices.
- Save state is textual; locally known errors validate on blur, server validation maps to a focused linked error summary, input survives failure, and dirty navigation offers `Stay`, `Leave without saving`, and valid `Save and continue`.
- Publish review shows visibility, missing/reference warnings, `Now` or configured-timezone date/time, local preview, and UTC supplementary detail. Ambiguous/nonexistent local scheduling times are rejected before submit and by the server contract.
- Preview saves or asks to save, opens the private bannered view, and never claims public availability. Publish/unpublish/delete are distinct confirmed actions.
- Editing live content shows `Published - changes pending`, `View live`, and `Preview draft`. Conflict preserves local changes and offers `Review latest version`, `Copy my changes`, and reload without overwrite.
- Session expiry removes protected draft/preview DOM and caches. Initial/loading/success/empty/no-result/validation/server/unauthorized/expired/offline/conflict states follow the accepted shell contract.

### Public semantic timeline/list

- `/experience` is a Server Component for initial content and metadata, reading the same-origin public API through generated feature wrappers. Initial timeline content is not client-only or hard-coded.
- The DOM is chronological and semantic: one heading/list structure, readable date ranges/current labels, company/role/employment/remote/location facts, achievements/responsibilities, technologies, and visible skill evidence links. Decorative timeline rails are ignored by assistive technology and CSS never changes reading order.
- Scheduled/future, draft, hidden, deleted, and unpublished experiences never render. Missing optional values have intentional omission/fallback behavior; no invented employer, date, achievement, metric, or relation appears.
- Public cache invalidation and schedule TTL make publish/reschedule/hide/unpublish/delete changes visible without source change/rebuild. JavaScript-disabled rendering remains meaningful.

## Dispatch order

1. **Do not start M5 implementation now.** Complete E0-E2 and release active M1/M3/M4/Infrastructure overlaps.
2. **After E2 - Backend `M5-T01-D`:** implement/review experience domain, revision lifecycle, date/status rules, content policy, and skills-facade contract.
3. **After domain evidence - Integration/root:** record L1 and reserve sole revision `0006`.
4. **After L1 - Backend `M5-T01-R/M/A/P`:** persistence, migration, admin/preview API, and public projection may run concurrently only in disjoint files.
5. **After all T01 backend evidence - Integration/root `M5-T01-I`:** review contract/security/data evidence, export/generate twice, compile, and record L2.
6. **After L2 - Frontend `M5-T02-A/P`:** admin and public lanes may run concurrently only in disjoint feature/route/component files.
7. **After frontend evidence - Integration/root:** run focused lifecycle/privacy/accessibility/performance review and record L3.
8. **After L3 - Integration/root `M5-T03-I`:** execute full J4 vertical integration, docs/reviews/evidence, and prepare the M5 gate record.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, record requested milestone `M5` plus trace alias `M09`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Logs, DB samples, API transcripts, screenshots, and traces are sanitized and contain no cookies, CSRF values, authorization headers, credentials, draft/private content, production dumps, or machine-specific absolute paths.

### `M5-T01` backend/data/API evidence

Required mapping: `AC-009`, applicable revision/preview patterns from `AC-020`, `AC-027`-`AC-030`, `AC-034`-`AC-040`; `F1-009`, `F2-005`, `API-001`-`API-006`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-006`-`NFR-008`, `NFR-011`, `NFR-014`-`NFR-018` applicable slice portions.

Evidence must include:

- unit/property tests for required fields, valid date combinations, end-before-start, current-with-end, unknown status/type, unsafe company URL, ordered content, safe Markdown/raw HTML/unsafe URL corpus where formatting applies, and stable errors;
- service/UoW tests for create/draft save/publish future/publish now/edit-live/copy-on-write/republish/reschedule/unpublish/visibility/reorder/delete, audit coupling, rollback, and deterministic application seams;
- immutability tests proving published/frozen content and skill relations cannot be updated/deleted by repositories or the migrated database path and draft edits never alter live data;
- M4 facade tests for valid/unknown/deleted/hidden/duplicate skills, publish validation, visible public summaries, revision-scoped isolation, and no skills repository import;
- PostgreSQL tests for pointer ownership, monotonic revisions, concurrent draft save/publish, exactly one copy-on-write draft, DB-time eligibility boundaries, scheduled cache bounds, stable chronology, bound parameters, no repository commit, and bounded select loading;
- complete `0006` migration evidence listed above, including role isolation and no second head;
- admin/preview API tests for CRUD/lifecycle/order/visibility, preview no-store/session-only, absent/stale `If-Match`, idempotent replay/mismatch/concurrent duplicate, authorization/IDOR, mass assignment, CSRF/Origin, safe errors, request IDs, and no partial state;
- pagination traversal with exact totals/no loss or duplication, accepted lifecycle/visible/current/type/remote/skill/search filters and sorts, plus duplicate/unsupported/arbitrary-expression/SQL injection negatives;
- public projection tests at database-time boundaries proving only effective visible nondeleted published revisions and visible skill summaries appear; credentials on public routes do not widen access;
- payload/HTML-equivalent projection, error, log, audit, cache, trace, and query inspection proving no draft/future/hidden content, revision pointers/IDs, creator, SQL, stack, or secret disclosure;
- OpenAPI lint/reference/security/error/example/filter/sort/deprecation review, unique operation IDs, reviewed schema diff, generation twice with no diff, strict generated compile, and wrapper-boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest and meaningful coverage reports; generated TypeScript format/lint/type checks; no disabled test or unexplained warning.

Mutable published content, draft/future/hidden leakage, invalid date/status persistence, pointer corruption, duplicate revision/draft, skills repository reach-through, lost update, duplicate publish effect, preview cache/discovery, IDOR/mass-assignment/injection success, generated drift, second migration head, failed Must requirement, or Critical/High finding blocks L1/L2.

### `M5-T02` frontend/admin/public evidence

Required mapping: `AC-009`, `AC-025`, `AC-031`-`AC-035`; `F1-002`-`F1-003`, `F1-009`, `F2-005`, `F2-019`, `NFR-001`-`NFR-010`, `SEC-004`-`SEC-005`, `SEC-009`.

Admin evidence must include:

- generated-wrapper/form tests for all fields, date/current rules, status/type choices, ordered content, skills relations, pagination/filters, preview, publish/reschedule/unpublish, `ETag`/idempotency, configured-timezone conversion, request IDs, and safe error mapping;
- component/story tests for list table/mobile cards, editor tabs/error counts, ordered-field controls, skill picker/warnings, lifecycle/status cluster, publish review, preview banner, long content, empty/no-result/loading/error/conflict states, light/dark/high-contrast/reduced-motion, narrow/zoom layouts;
- keyboard-only create/invalid-save/edit/reorder/relate/preview/publish/unpublish flow; persistent labels; focused linked errors; dirty protection; conflict draft preservation; focus restore; expiry removal of protected state;
- private preview browser inspection for no-store/noindex/nonshareability and zero draft content after sign-out/expiry;
- axe with no unresolved blocker and manual keyboard/focus/screen-reader/200%-400% zoom/touch review at representative widths.

Public evidence must include:

- Server Component/wrapper tests and built HTML inspection proving API-backed initial content, chronology/date/current semantics, visible skill links, meaningful JavaScript-disabled rendering, and no hard-coded experience data or frontend DB/backend import;
- empty/error and optional-field states plus scheduled/future/draft/hidden/deleted/unpublished/cache invalidation negatives across payload, RSC/HTML, metadata, accessibility tree, screenshots, and traces;
- semantic list/timeline headings, chronological DOM order, text date/status meaning, decorative rail isolation, readable long content, safe links, 44 px targets, visible focus, and responsive reflow.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library, Storybook interaction/a11y, production build, and focused Playwright. Record Server/Client Component rationale, route JS/bundle delta, SSR/API request count, no unnecessary hydration/overfetch, experience query plan/SQL count, schedule/cache behavior, and Lighthouse `/experience` profiles targeting performance >=90, accessibility >=95, SEO >=95 with measured variance disposition.

Broken lifecycle state, wrong timezone conversion, inaccessible preview/publish/reorder, stale private DOM/cache, raw fetch/generated bypass, client-only initial timeline, hard-coded content, draft/hidden leak, unresolved WCAG blocker, or unexplained performance regression blocks L3/T02.

### `M5-T03` vertical-slice and M5 gate evidence

Required mapping: `AC-009`, `AC-025`, `AC-027`-`AC-043` applicable slice portions; `F1-009`, `F2-005`, `DOC-001`-`DOC-003`, `SEC-004`-`SEC-006`, `SEC-009`, `NFR-001`-`NFR-018` applicable slice portions.

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0006`. Fixtures are created through APIs/factories, not demo seed. It must prove:

- administrator creates a draft, receives field-addressable invalid date/status errors, saves every experience field, orders content, relates M4 skills, previews privately, and publishes now;
- a future schedule remains absent publicly, uses the configured timezone correctly, becomes/returns effective only through DB-time/reschedule behavior, and requires no worker;
- editing published content and relations leaves live output unchanged and shows `Published - changes pending`; preview shows only the draft; republish atomically changes the live frozen revision;
- hide/show, deterministic order, unpublish, and separate delete immediately affect public SSR/cache without removing revision/audit integrity;
- concurrent editors/publishers receive conflicts without silent overwrite and idempotent retries create one published effect/copy-on-write draft;
- unauthorized/expired actor, guessed preview, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, injection, invalid skill, stale version, and idempotency mismatch fail safely without partial writes;
- public API/SSR/timeline/metadata/cache/log/trace/screenshot inspection finds no draft, future, hidden, deleted, unpublished, hidden-skill, pointer, or creator leakage;
- full affected backend/frontend/contract/migration/E2E/build/scan commands pass, generated output remains clean, revision remains one head, and no Critical/High finding remains.

Documentation/evidence must include:

- user guide for experience fields, date/current rules, ordered content, skills relations, visibility/order, draft save, private preview, now/future publish in configured timezone, pending changes, reschedule, unpublish, delete, and conflict recovery;
- API guide for admin/public/preview operations, revision lifecycle, schemas/errors, auth/CSRF, pagination/filter/sort catalogs, chronology, cache, `ETag`/`If-Match`, idempotency, DB-time scheduling, skill validation, privacy, and sanitized examples/cURL;
- developer guide for aggregate/revision/pointer model, migration `0006`, immutable/copy-on-write behavior, repository/UoW, `SkillReferenceFacade`, controlled content, effective public query/indexes/cache, SSR/generated-client workflow, and the revision pattern M6+ must reuse rather than fork;
- sanitized screenshots at 320, 390, 768, 1024, 1440, and 1920 px for list/mobile cards/editor/date errors/statuses/preview/publish/conflict and public timeline/empty states in light/dark, plus performance/query/bundle, accessibility, security/privacy, API, coverage, traceability, and independent-review reports.

Passing lane evidence does not authorize M6 until Integration/root records the separate M5 acceptance decision. The M5 gate remains blocked by any failed Must requirement, disabled/suppressed check, placeholder/mock production path, mutable published revision, draft/preview/future/hidden leak, invalid date/status persistence, pointer/revision corruption, skill-facade bypass, lost update/duplicate publish, generated drift, multiple migration heads, parallel migration/generated writer, Infrastructure-file overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
