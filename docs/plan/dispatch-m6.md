# Milestone 6 Dispatch

## Dispatcher status

This document prepares `M6-T01` through `M6-T03`. It does not release implementation, record acceptance, or authorize M7.

M6 remains blocked until Integration/root records the separate M5 acceptance decision, confirms its provider contracts, and releases every shared surface required below.

| Task     | Current state | Release condition                                                                                                                           |
| -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `M6-T01` | Blocked       | M5 passes; one Alembic head is confirmed at `20260802_0006`; active earlier-milestone/Infrastructure reservations are released; P0-P2 pass. |
| `M6-T02` | Blocked       | `M6-T01` backend/API evidence passes and project contract freeze P4 is recorded with a clean generated client.                              |
| `M6-T03` | Blocked       | `M6-T01` and `M6-T02` pass and frontend readiness freeze P5 is recorded.                                                                    |

M6 maps to trace milestone `M10` and delivers the Projects vertical slice: revision-safe case-study administration, publication/preview, skill/experience/project relations, public list/filter/detail/metadata, an accessible gallery fallback, contract generation, tests, documentation, and evidence. It does not authorize media upload/storage, blog, pages/blocks, contacts, tokens, workers/schedulers, speculative AI behavior, or an M9 acceptance claim.

## Strict dependency gates

### P0 - Accepted foundation and provider baseline

Before any M6 write, Integration/root confirms accepted M1-M3 provider contracts for:

- authenticated actor/session checks, forced-password boundary, CSRF/Origin protection, request IDs, rate limits, and safe audit facts;
- `/api/v1` envelopes/errors, pagination/filter/sort conventions, `ETag`/`If-Match`, idempotency, OpenAPI generation, and generated-client wrappers;
- site settings including the accepted IANA timezone and SEO defaults, public/admin shells, navigation, theme, metadata composition, and cache invalidation interfaces;
- one linear migration chain and one current head, with no production-startup migration behavior;
- no unresolved Critical/High finding or failed Must requirement on a consumed contract.

M6 consumes these capabilities through their released interfaces. A provider defect returns to its owner for correction and re-evidence; M6 does not fork auth, API, settings, shell, metadata, audit, database, or cache conventions.

### P1 - Accepted M4 skills provider

Integration/root confirms M4 acceptance and a stable application-facing `SkillReferenceFacade` that can validate existing/deleted/visible/hidden skills and return public-safe summaries without exposing skills repositories or ORM models.

### P2 - Separate M5 acceptance and project prerequisites

Integration/root must record the separate M5 acceptance decision and prove:

- exactly one Alembic head exists at `20260802_0006` from `20260802_0006_experiences.py`;
- the immutable published-revision/copy-on-write draft pattern, DB-time scheduling, preview isolation, concurrency/idempotency, audit, and public-projection behavior have passing evidence;
- an application-facing `ExperienceReferenceFacade` is accepted for existing/deleted/visible/public-effective experience references and public-safe summaries, without repository/ORM leakage;
- M5 migration, experience module/API/frontend/generated artifacts, E2E/evidence, and shared composition files needed by M6 are released;
- no unresolved M5 defect can corrupt publication pointers, relation validation, public privacy, cache effectiveness, or generated contracts.

P2 is a hard gate. Passing M5 lane tests or freeze points alone does not release M6.

## Active-file exclusions and ownership

### Earlier milestone files

M6 must not edit, move, delete, format, regenerate, or claim ownership of:

- M1 identity/session/rate-limit/bootstrap/auth routes, schemas, tests, UI, boundary/E2E, audit foundation, or `20260802_0002_identity_auth.py`;
- M2 common envelopes/errors/request context/idempotency/concurrency/health, handwritten client wrappers, contract fixtures/evidence, or `20260802_0003_api_conventions.py`;
- M3 profile/settings/navigation/footer modules, shells/routes/features/tests/evidence, demo seed, or `20260802_0004_site_configuration.py`;
- M4 skills/category modules, relations/facades/routes/features/tests/evidence, or `20260802_0005_skills.py`;
- M5 experiences modules, facades/routes/features/tests/E2E/evidence, or `20260802_0006_experiences.py`.

After P0-P2, those areas remain provider-owned. M6 calls the released `SkillReferenceFacade` and `ExperienceReferenceFacade`; it never imports their repositories/ORM, changes their public eligibility rules, adds reverse relations to their tables, or patches them for convenience.

### Infrastructure files

M6 lanes must not edit `backend/migrations/env.py`, shared database runtime/session/UoW/readiness or role/grant files, `infrastructure/**`, Compose/environment/Docker files, root manifests/locks, task-runner scripts, CI/workflows, scanners, deployment files, or Infrastructure evidence. Any required shared registration, grant, task, or CI change is handed to its current owner and scheduled serially.

### Integration/root single-writer files

Integration/root alone writes `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator scripts or configuration, final cross-lane contract/trace reports, and final M6 task/milestone decisions. Requirements, architecture, ADR, UX, earlier dispatches, and existing planning artifacts remain read-only unless separately dispatched.

## Owner-safe M6 lanes

| Stage                                 | Owner                           | Exclusive write area                                                                                                                                                                                                                                                                                                 | Gate and handoff                                                                                                                                             |
| ------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `M6-T01-D` project domain/application | Backend Domain Agent            | Project aggregate/revision types, lifecycle/slug/date/status/SEO/link/content/relation invariants, DTOs, ports/facades, stable errors, audit facts, and unit/service tests under `backend/app/modules/projects/**`; `docs/evidence/M6/M6-T01-domain.md`. Excludes persistence/public-query filenames reserved below. | Starts after P2. Produces P3. Does not write migration, provider modules, API artifact, generated code, frontend, Infrastructure files, or final acceptance. |
| `M6-T01-R` project persistence        | Backend Persistence Agent       | Dedicated project ORM/repository adapters, immutable-revision enforcement, relation graph/query adapters, and repository tests under `backend/app/modules/projects/**`; `docs/evidence/M6/M6-T01-persistence.md`.                                                                                                    | Starts after P3. Implements inward-facing ports; repositories never commit and never import skills/experiences persistence.                                  |
| `M6-T01-M` sole migration             | Backend Migration Agent         | `backend/migrations/versions/20260802_0007_projects.py`, dedicated migration fixtures/tests, and `docs/evidence/M6/M6-T01-migration.md`.                                                                                                                                                                             | Starts after P3 and an Integration/root `0007` reservation. Serialized with model registration; no other M6 revision or merge head.                          |
| `M6-T01-A` admin/preview API          | Backend API Agent               | Dedicated admin project CRUD/lifecycle/preview/relation route and transport-schema modules, API tests, and `docs/evidence/M6/M6-T01-admin-api.md`.                                                                                                                                                                   | Starts after P3; may run beside R/M only in disjoint files. Calls application/provider facades, never repositories/ORM.                                      |
| `M6-T01-P` public project projection  | Backend Public Projection Agent | Dedicated project list/filter/detail/public metadata query/projection files, public route/schema modules, privacy/query-plan/cache tests, and `docs/evidence/M6/M6-T01-public-projection.md`.                                                                                                                        | Starts after P3. Reads frozen effective revisions and public-safe provider summaries; submits executable Pydantic source for P4.                             |
| `M6-T01-I` OpenAPI/client generation  | Integration/root                | Cross-lane contract tests/reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, P4, and final T01 decision.                                                                                                                                                          | Starts after D/R/M/A/P evidence. Integration/root is the sole API-artifact/generated-code writer; all other lanes pause those surfaces.                      |
| `M6-T02-A` project admin frontend     | Frontend Admin Agent            | `frontend/src/features/projects/admin/**`, `/admin/projects`, `/admin/projects/{id}/edit`, admin preview route/surface, project-specific components/stories/tests/wrappers, and `docs/evidence/M6/M6-T02-admin.md`.                                                                                                  | Starts after P4. Any shared shell/editor/navigation/metadata primitive edit receives one separately scheduled Integration/root writer window.                |
| `M6-T02-P` project public frontend    | Frontend Public Agent           | `frontend/src/features/projects/public/**`, `/projects`, `/projects/{slug}`, project list/detail/filter/gallery-fallback components/stories/tests, route metadata/SSR/cache code, and `docs/evidence/M6/M6-T02-public.md`.                                                                                           | Starts after P4 and may run beside T02-A only in disjoint files. Initial public content and metadata use generated wrappers server-side.                     |
| `M6-T03-I` integration/E2E/docs       | Integration/root                | Project API/browser fixtures/specs, sanitized traces/screenshots/reports, user/API/developer docs, traceability links, `docs/evidence/M6/M6-T03.md`, and final M6 gate record.                                                                                                                                       | Starts after T01/T02 pass and P5. Defects return to owning lanes. It does not start M7 or mark M6 accepted without independent review.                       |

No two lanes edit the same file concurrently. Project package exports, backend router/application composition, shared provider adapters, admin sidebar, public navigation, central API wrapper, metadata/sitemap integration, controlled-Markdown files, shared fixtures, and model registration each receive one Integration/root-scheduled writer window if needed. Backend owns executable Pydantic source; Integration/root alone exports/generates; frontend consumes only P4 generated types.

## Sole linear migration policy

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0007_projects.py
revision: 20260802_0007
down_revision: 20260802_0006
owner: M6-T01-M only
```

The revision implements the accepted P3 schema and no adjacent capability:

- stable `project` aggregate identity with normalized case-insensitive unique slug, visibility, featured flag, deterministic display position, draft/published revision pointers, `publish_at`, `unpublished_at`, timestamps, optimistic version, and optional soft-delete marker;
- `project_revision` with monotonic revision number, complete case-study/role/status/date/SEO/link/technology content, frozen marker, safe creator reference, and timestamps;
- revision-scoped ordered technology rows when P3 chooses normalized children, plus `project_skill`, `project_experience`, and `related_project` associations with duplicate/self-reference constraints and indexes;
- pointer integrity ensuring both pointers belong to the same stable project, using accepted deferrable-FK/two-step construction;
- checks/indexes justified by P3 invariants, admin lifecycle/filter/order queries, public effective-list/detail/featured queries, relation traversal, and slug lookup;
- no media asset/usage/storage/quarantine/object table, screenshot bytes/URL/storage key, blog/page/contact/token table, scheduler/worker/outbox, speculative provider, or parallel migration.

Cycle rejection across related projects is enforced transactionally by the application/repository against stable project IDs, because a row-level check cannot validate a graph. Database constraints still reject self edges and duplicate targets. Concurrent graph edits/publishes are serialized or conflict deterministically so two individually valid requests cannot commit a cycle.

Frozen published revisions are immutable through domain/repository behavior and receive database reinforcement only when compatible with the accepted database-role architecture. M6 does not edit Infrastructure grants; a required reinforcement is handed to its owner. Frozen-row update/delete attempts must fail in repository and migrated PostgreSQL tests.

Migration evidence requires empty upgrade, upgrade from accepted `0006` with representative skill/experience data, current/head equality, exactly-one-head verification, schema/model comparison, pointer/deferrable-FK integrity, slug/order/relation/check/index inspection, frozen-row rejection, copy-on-write behavior, relation graph behavior, rollback/UoW, and runtime-vs-migration-role isolation. Production startup must not migrate or schedule. A schema need found after P3 returns to the sole migration owner; parallel revisions and merge heads are prohibited.

## Project domain and publication contract

### Stable identity, case-study content, and validation

- Slug is stable aggregate route identity: Unicode-normalized ASCII lowercase kebab case, 1-80 characters, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`, unique case-insensitively. P3 freezes any project-route segment exclusions; it does not blindly reuse the custom-page reserved catalog.
- Required/nonblank and bounded fields are frozen at P3 for name, short/full descriptions, problem, implemented solution, measurable outcome/impact, owner role/contribution, technical architecture, technologies, status, and dates. Whitespace-only content and unbounded collections fail with field-addressable stable errors.
- `start_date` is required. `end_date`, when present, is on/after start. P3 freezes whether an active/ongoing status requires a null end and whether a completed status requires an end; unknown status/role/technology catalog values fail closed rather than silently becoming public facets.
- Technologies are normalized, duplicate-free, deterministically ordered display values, not executable package metadata. Skills remain relational evidence rather than duplicated technology identities.
- Full description, problem, solution, impact, and architecture use the accepted controlled-Markdown policy where formatting is enabled: fixed extensions, raw HTML disabled, unsafe URLs rejected, and rendering sanitized defense in depth.
- Repository and live-demo links accept normalized `https` only. Credentials, fragments where disallowed, control characters, protocol-relative values, `javascript:`, `data:`, `file:`, `mailto:`, and ambiguous host forms are rejected. Rendering uses safe external-link behavior.
- SEO title/description are bounded plain text with safe fallback to public project/site values. Canonical URL is either omitted for the generated same-origin `/projects/{slug}` canonical or an approved normalized `https` URL under the P3 policy; draft/admin/preview URLs can never be canonical.
- `featured`, `visible`, and display position are stable aggregate concerns independent of lifecycle. Featured never overrides hidden, draft, future, deleted, or unpublished state. Reorder accepts a complete in-scope ID list and commits atomically under version checks.

### Immutable revision lifecycle and database-time publication

- Create atomically creates the stable aggregate and mutable revision 1. No public pointer exists; lifecycle is `Draft`.
- Save mutates only the current unfrozen draft under aggregate version and `If-Match`; live content, relations, slug resolution, and metadata stay unchanged.
- Publish validates the whole draft and every relation, freezes that revision, assigns the published pointer, sets `publish_at` from the requested instant or database UTC now, and creates one copy-on-write mutable draft in the same transaction.
- A future `publish_at` is `Scheduled`; an effective current/past value is public only when visible and nondeleted. Effectiveness uses PostgreSQL `now()`, never application/server/browser clocks and never a worker.
- Editing after publish changes only the copy-on-write draft and yields `Published - changes pending`. Live fields, relations, SEO, canonical data, and public results remain tied to the frozen published revision until republish.
- Reschedule changes aggregate scheduling metadata under concurrency/idempotency rules without mutating frozen content. Unpublish clears public eligibility immediately, retains revisions, records `unpublished_at`, and invalidates public list/detail/metadata/sitemap caches.
- Visibility is separate from publication, featured, and deletion. Delete is a separately confirmed action preserving reference/audit integrity under the P3 soft-delete policy. Lifecycle labels are derived from pointers/content/time; no background status mutation exists.

### Revision-scoped relations and graph safety

- Skill and professional-experience target IDs are revision-scoped, duplicate-free, validated through the accepted M4/M5 facades, and never resolved through provider repositories/ORM. Unknown, deleted, malformed, or unauthorized references fail safely.
- Related-project targets are stable project IDs attached to the source revision. Self-reference, duplicates, and directed cycles of any length are rejected on save and rechecked transactionally on publish using a bounded graph traversal/recursive query with explicit limits.
- Draft edits to skill, experience, or related-project relations cannot alter the live published relation set. Copy-on-write copies ordered relation values without sharing mutable rows.
- Publish rejects required references that are unusable for public output. Optional hidden/nonpublic provider targets may remain visible as admin warnings but are omitted defensively from public summaries; their IDs, titles, draft state, and existence do not leak.
- Public related-project resolution follows only effective, visible, nondeleted published targets and their frozen revisions. It never follows target draft pointers or widens because a credential was supplied. Cycles are rejected at write time and public traversal remains depth/breadth bounded as defense in depth.
- M6 does not add reverse relation rows to skills or experiences. Reverse evidence, if needed, is queried through project-owned associations behind a project application facade.

### Media-reference staging until M9

- Cover and ordered screenshot/gallery inputs are optional provider references, not URLs, paths, filenames, blobs, base64 data, object keys, or project-owned uploads.
- Until an accepted M9 `MediaReferenceFacade` and media schema exist, non-null cover/screenshot writes return the stable capability-unavailable validation result; null/empty media values remain valid. No unvalidated UUID/string is persisted, no dangling FK is created, and no fake in-memory/filesystem/S3 provider ships.
- M6 migration `0007` creates no media table and no unenforceable media FK. P3/P4 freeze nullable staged DTO semantics and a future-compatible application port only; M9 owns the forward migration that activates cover/screenshot persistence, `media_usage`, alt/caption/focal data, deletion protection, delivery, and storage adapters.
- Public M6 schemas omit storage identifiers and unavailable references. The list/detail UI renders the specified intentional case-study/gallery fallback with stable reserved geometry, no broken request, no invented image/alt text, and no claim that `AC-014` or `AC-019` has passed.
- M9 activation must reuse project application commands and immutable revision ownership; it may not mutate an already frozen revision in place. Any backfill or new revision behavior requires a reviewed forward migration and regression evidence.

## Admin/public API, preview, metadata, and privacy contract

### Admin and lifecycle API

- `/api/v1/admin/projects` provides paginated/searchable/filterable/sortable list, create, read draft/live context, patch draft, reorder/feature/visibility, delete, publish-now/future, reschedule, and unpublish through explicit DTOs/use cases and action subresources.
- Admin list filters/sorts use a documented closed catalog for lifecycle, visibility, featured, status, skill, experience, search, dates, position, and timestamps. Typed SQLAlchemy mappings and bound parameters reject unknown/duplicate/arbitrary expressions.
- Mutable responses provide an aggregate `ETag`. Update/reorder/delete/lifecycle actions require `If-Match`; missing returns 428 and stale returns `RESOURCE_VERSION_CONFLICT` without a partial write.
- Retriable create/publish/reschedule/unpublish/reorder actions use the accepted actor+route-scoped idempotency contract. Same-key/same-request replays the safe response; same-key/different-request conflicts; concurrent publish creates exactly one frozen effect and one copy-on-write draft.
- Create/update/reorder/feature/show/hide/publish/reschedule/unpublish/delete and rejected security-sensitive attempts emit controlled audit facts in the same UoW. Audit metadata contains safe actor/resource/request/outcome/change categories, never draft prose, URLs with secrets, media placeholders, SQL, or relation content dumps.
- Every use case rechecks actor authorization. Unsafe cookie requests require exact trusted Origin and CSRF. Admin and preview responses are `private, no-store`; DTO allow-lists reject mass-assigned pointers, frozen flags, versions, creator/audit data, publication timestamps, storage fields, and arbitrary relation payloads.

### Preview isolation

- A separate administrator-session-only preview endpoint returns the current draft projection, including draft-only case-study fields and valid staged relations, even when unpublished/hidden. It uses `Cache-Control: private, no-store`, a safe request ID, and `noindex` metadata.
- Preview never enters public API totals, filters, detail lookup, featured results, related recommendations, metadata, JSON-LD, sitemap/robots discovery, public cache tags, unauthenticated search, logs, or shareable URLs/tokens. Guessed IDs without a valid session do not reveal existence.
- The rendered surface has a persistent `Draft preview - not public` banner, distinguishes unavailable media with the same gallery fallback, and links safely back to the editor. Session expiry removes draft DOM/cache before safe navigation.

### Public list, detail, filters, metadata, and query plans

- `GET /api/v1/public/projects` returns only aggregates with a published pointer, `visible=true`, `publish_at <= PostgreSQL now()`, and `deleted_at is null`, through a dedicated allow-listed summary projection.
- `GET /api/v1/public/projects/{slug}` resolves exactly one effective public project or returns the same designed not-found contract used for absent/draft/future/hidden/unpublished/deleted slugs. Credentials on public routes never widen visibility.
- Public summary/detail fields are explicitly enumerated at P4: stable public ID/slug, public case-study/role/status/date/technology/SEO values, featured/order facts, and only visible public-safe skill/experience/related-project summaries. Revision/pointer/version/creator/audit/admin values, draft differences, hidden target IDs, provider internals, and media/storage placeholders are absent.
- The public filter/sort catalog is bounded and useful: documented status, technology, visible skill, related experience, featured and search filters plus deterministic position/date/name sorts, page-number pagination, exact totals, and opaque `id` tie-breaker. Unsupported/duplicate fields, free-form SQL/operators, wildcard abuse, and expensive unbounded relation expansion fail validation.
- Default list order is featured first only within public eligibility, then configured position and a deterministic tie-breaker; an explicit accepted sort overrides it. Related-project lists preserve configured order and remain bounded.
- List and detail queries join only the frozen published revision, use select-in/bounded loading for relations, avoid N+1 access, and remain a bounded SQL count. Representative PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` evidence covers effective listing/filter/sort/pagination, slug detail, featured lookup, relation summaries, and graph checks at realistic cardinality.
- Public caches are invalidated on effective project/relation/visibility/order/slug/SEO/publication changes. A scheduled entry's cache lifetime cannot extend beyond the next `publish_at`; old slugs/details/metadata disappear according to the frozen slug-change policy. Public cache keys never overlap preview/admin.
- `/projects/{slug}` metadata uses the same public detail projection for title, description, canonical, Open Graph fallbacks, and appropriate validated structured data. Nonpublic/absent projects produce no project metadata, canonical, JSON-LD, sitemap entry, alternate suggestion, or relation clue. M6 touches shared metadata/sitemap files only in a serial Integration/root window.

## Contract freeze points

### P3 - Project domain/revision freeze

Integration/root records P3 only after T01-D focused review/tests pass. P3 freezes:

- aggregate/revision ownership, slug/status/date/role/outcome/technology/content/link/SEO catalogs and stable errors;
- immutable publish/copy-on-write, DB-time schedule/reschedule/unpublish, visibility/featured/order/delete semantics;
- revision-scoped skill/experience/related-project relation rules, cycle algorithm/limits, provider-facade boundaries, and public relation policy;
- staged media-unavailable semantics and the explicit no-storage/no-dangling-reference boundary;
- command/query DTOs, authorization/audit facts, concurrency/idempotency requirements, persistence ports, and proposed `0007` schema/index/query contract.

P3 releases R/M/A/P. An incompatible domain/schema/provider decision stops downstream work and returns to T01-D before migration or generation.

### P4 - Project API and generated-client freeze

Integration/root records P4 only after T01-D/R/M/A/P pass and generation is clean. P4 freezes:

- admin list/detail/create/update/reorder/feature/visibility/delete/preview/publish/reschedule/unpublish operation IDs, DTOs, errors, and security declarations;
- public project list/detail/filter/sort/pagination, explicit public allow-lists, relation summaries, metadata inputs, cache headers, and not-found equivalence;
- `ETag`/`If-Match`, idempotency, date/time/URL/slug formats, examples, lifecycle labels, staged null media fields, and deprecation metadata;
- deterministic generated TypeScript client and approved project feature-wrapper boundary.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. P4 releases frontend. Breaking changes require CHG-002 and another reviewed generation window; frontend must not compensate with raw fetch, duplicate transport types, `any`, hand-edited generated code, arbitrary image URLs, or local lifecycle logic.

### P5 - Project frontend readiness freeze

Integration/root records P5 only after both T02 lanes pass focused tests and browser review. P5 freezes:

- admin list/editor/relation/SEO/media-unavailable/lifecycle/conflict behavior and all async states;
- public list/filter/pagination/detail/case-study/metadata/related-content/gallery-fallback behavior;
- accessible keyboard/focus/announcements, responsive layouts, sanitized fixture interfaces, and screenshots required by T03.

P5 releases T03. P5 is not M6 acceptance.

## Frontend behavior contract

### Administrator project lifecycle

- `/admin/projects` offers search and closed-catalog filters, result count, pagination, sortable accessible table at wide widths and equivalent cards at narrow widths, labeled lifecycle/visibility/featured facts, create, edit, preview, reorder, feature, show/hide, publish/reschedule/unpublish, and separately confirmed delete.
- `/admin/projects/{id}/edit` covers every active SPEC field plus role/contribution: identity/slug, summary, problem, solution, impact, architecture, technologies, dates/status, links, skills, experiences, related projects, order/featured/visibility, SEO, and publication controls. Cover/gallery controls clearly explain that media becomes available in M9 and do not expose a fake picker/upload.
- Relation pickers consume generated project/provider summaries, show selected order and safe unavailable warnings, prevent self/duplicate/cycle selection, and map server graph/reference errors to a focused issue summary. No hidden target label remains in DOM after authorization/session changes.
- Save, preview, now/future publish in configured timezone, pending changes, reschedule, unpublish, visibility, featured, reorder, and delete follow J4 and the shared interaction contract. Ambiguous/nonexistent local schedule times are rejected; server/database results remain authoritative.
- All initial/loading/success/empty/no-result/validation/server/offline/unauthorized/session-expired/conflict states are explicit. Forms retain safe input, focus the linked error summary, protect dirty navigation, preserve local work on conflicts, expose request IDs safely, and clear protected state on expiry.

### Public case-study list and detail

- `/projects` and `/projects/{slug}` are Server Components for initial content and metadata, reading the same-origin public API through generated feature wrappers. Initial cards, detail content, filters reflected in the URL, and metadata are not client-only or hard-coded.
- List cards lead with problem/outcome evidence and expose understandable name, short description, role, status/date, technologies, featured state where meaningful, and visible public relations. Featured placement never changes DOM semantics or public eligibility.
- Filters have persistent labels, active-filter summary, result count, clear action, deterministic URL/pagination, keyboard operability, and focus movement to the results heading after navigation. Empty collection differs from no-match and never reveals unpublished counts.
- Detail uses one `h1` and semantic sections for problem, intervention/solution, measurable impact, role, architecture, technologies, dates/status, safe repository/demo actions, and visible related skills/experiences/projects. It does not invent outcomes, metrics, roles, links, screenshots, or target summaries.
- Until M9, the gallery region renders only when useful; otherwise it shows a concise intentional fallback with reserved geometry. No broken `<img>`, network fetch, carousel trap, empty alt accident, or fake screenshot appears. Once activated later, galleries must follow the large-image/thumbnails desktop and labeled scroll-snap/next/previous mobile pattern.
- Draft/future/hidden/unpublished/deleted projects and nonpublic relations never render or enter RSC payloads, metadata, JSON-LD, sitemap, caches, accessibility trees, logs, traces, screenshots, result totals, or not-found alternatives.
- Public links use safe labels and `noopener noreferrer` where external. Case-study headings/landmarks, responsive content order, reduced motion, zoom/reflow, long text/URL handling, focus visibility, and light/dark contrast meet the WCAG review contract.

## Dispatch order

1. **Blocked - Integration/root:** record separate M5 acceptance, verify P0-P2, confirm head `0006`, release required reservations, and publish provider contracts.
2. **After P2 - Backend `M6-T01-D`:** implement/review project domain, revision lifecycle, slug/content/date/status/SEO/URL rules, relations/cycles, and media staging.
3. **After domain evidence - Integration/root:** record P3 and reserve sole revision `0007` on `0006`.
4. **After P3 - Backend `M6-T01-R/M/A/P`:** persistence, migration, admin/preview API, and public projection may run concurrently only in disjoint files.
5. **After all T01 backend evidence - Integration/root `M6-T01-I`:** review data/security/query/contracts, export/generate twice, compile, and record P4.
6. **After P4 - Frontend `M6-T02-A/P`:** admin and public lanes may run concurrently only in disjoint feature/route/component files.
7. **After frontend evidence - Integration/root:** run focused lifecycle/privacy/accessibility/performance/SEO review and record P5.
8. **After P5 - Integration/root `M6-T03-I`:** execute the full project/J1/J4 vertical integration, docs/reviews/evidence, and prepare the M6 gate record.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, identify requested milestone `M6` and trace alias `M10`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Logs, DB samples, API transcripts, metadata captures, screenshots, and traces are sanitized and contain no cookies, CSRF values, authorization headers, credentials, draft/private content, provider internals, storage keys, production dumps, or machine-specific absolute paths.

### `M6-T01` backend/data/API evidence

Evidence must include:

- domain/property tests for slug normalization/collision, required/bounded content, outcome/role/technology catalogs, date/status combinations, safe repository/demo/canonical URLs, controlled content, SEO fallback, order/featured/visibility independence, and stable errors;
- publication tests for immutable frozen revisions, copy-on-write independence, now/future DB-time boundaries, reschedule/unpublish/delete/visibility, live/draft SEO/relation separation, rollback, and audit coupling;
- relation tests for duplicate/unknown/deleted/hidden targets, M4/M5 facade-only validation, revision isolation, self edges, direct/indirect cycles, concurrent cycle races, bounded traversal, public optional-target filtering, and no reverse-provider mutation;
- media-staging tests proving null/empty works, every non-null cover/screenshot URL/path/key/ID/blob is rejected while M9 is absent, no storage/media table or outbound media fetch exists, and public/admin/error/log/audit/OpenAPI output exposes no fake/storage identifier;
- migration tests for empty and `0006` upgrade, one head/current equality, schema-model parity, pointers/FKs/constraints/indexes, frozen-row rejection, representative copy-on-write/relations data, and production role/startup behavior;
- PostgreSQL repository/query tests for slug race, pointer ownership, reorder/version race, concurrent save/publish, exactly one publish effect/draft, graph race, DB-time eligibility/cache bounds, deterministic pagination, bounded selected loading, no repository commit, and no N+1;
- admin/preview API tests for all fields and lifecycle actions, preview session/no-store/noindex, missing/stale `If-Match`, idempotent replay/mismatch/concurrency, authorization/IDOR, mass assignment, CSRF/Origin, injection, safe errors/request IDs, and atomic failure;
- public list/detail tests for allow-listed filters/sorts/exact pagination, effective eligibility, slug/not-found equivalence, relation privacy, metadata/canonical/JSON-LD/sitemap exclusion, credential non-widening, and payload/cache/log/trace redaction;
- representative `EXPLAIN (ANALYZE, BUFFERS)` and SQL-count evidence for default/featured/filter/search/sort/pagination, slug detail, relation summaries, and graph validation with documented data volume and index usage;
- OpenAPI lint/reference/security/error/example/filter/sort/deprecation review, unique operation IDs, reviewed schema diff, two deterministic generations with no diff, strict generated compile, and wrapper-boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest and meaningful coverage reports; generated TypeScript format/lint/type checks; no disabled test or unexplained warning.

Mutable published content, slug collision/race, invalid date/status/URL/SEO persistence, pointer/relation corruption, self/cycle edge, provider-repository reach-through, draft/future/hidden leakage, media placeholder/storage-key acceptance, lost update/duplicate publish, preview discovery/cache, IDOR/mass-assignment/injection success, N+1/unbounded query, generated drift, second migration head, failed Must requirement, or Critical/High finding blocks P3/P4.

### `M6-T02` frontend/admin/public evidence

Admin evidence must include:

- generated-wrapper/form tests for every active project field, slug/date/status/URL/SEO rules, technologies, relation pickers/cycles, order/featured/visibility, preview, publish/reschedule/unpublish/delete, `ETag`/idempotency, configured-timezone conversion, request IDs, and safe error mapping;
- component/story tests for desktop table/mobile cards, editor sections/error counts, relation warnings, media-unavailable explanation, SEO preview, lifecycle/status cluster, publish review, preview banner, long content, all async/conflict states, light/dark/high-contrast/reduced-motion, narrow and 400% zoom layouts;
- keyboard-only create/invalid-save/edit/relate/reorder/preview/publish/unpublish flow with persistent labels, focused linked errors, non-drag reorder controls, dirty protection, conflict preservation, dialog focus restore, and expiry removal of protected state.

Public evidence must include:

- SSR and generated-wrapper tests for default/featured/filtered/paginated/empty/no-result/error/not-found list/detail behavior, URL state, focus movement, relation omission, gallery fallback, link safety, and cache invalidation;
- rendered head/HTML tests for title/description/canonical/Open Graph/validated structured data and sitemap inclusion only for effective public detail routes, with draft/future/hidden/unpublished/deleted parity;
- semantic/axe/manual tests for headings, landmarks, lists/cards, result announcements, filters/pagination, case-study sections, gallery fallback, relation/link names, zoom/reflow, contrast, reduced motion, touch targets, and meaningful JavaScript-disabled initial output.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library, Storybook interaction/a11y, production build, and focused Playwright. Record Server/Client Component rationale, route JS/bundle delta, SSR/API request count, no unnecessary hydration/overfetch, project query/SQL plans, cache schedule behavior, and Lighthouse `/projects` plus representative `/projects/{slug}` profiles targeting performance >=90, accessibility >=95, and SEO >=95 with measured variance disposition.

Broken lifecycle/filter/metadata state, wrong timezone conversion, inaccessible relation/reorder/preview/publish/filter/gallery fallback, stale private DOM/cache, raw-fetch/generated bypass, client-only initial content, hard-coded case-study data, draft/relation leak, unresolved WCAG blocker, invalid JSON-LD/canonical, or unexplained performance regression blocks P5/T02.

### `M6-T03` vertical-slice and M6 gate evidence

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0007`. Fixtures are created through APIs/factories, not demo seed. It must prove:

- administrator creates a draft, receives field-addressable slug/date/status/URL/content/SEO errors, saves all active fields, orders technologies/relations, sees media staging clearly, previews privately, and publishes now;
- future publication uses the configured timezone, stays absent publicly until DB time, can reschedule/unpublish without a worker, and invalidates bounded caches correctly;
- editing live content/SEO/relations leaves public list/detail/metadata byte/field-equivalent to the frozen revision, shows `Published - changes pending`, previews only draft, and republishes atomically;
- feature/show-hide/order/delete transitions affect public list/detail/featured/filters/metadata/sitemap correctly without breaking revision/audit/relation integrity;
- skill/experience/related-project relations resolve only allowed public summaries; self, indirect cycle, hidden/draft/deleted target, concurrent cycle, and target-change cases fail or omit exactly as P3 specifies without leakage;
- list filters/pagination and detail/not-found behavior are deterministic; case-study structure, safe links, SEO/canonical/Open Graph/JSON-LD, related content, and gallery fallback render accessibly on mobile and desktop;
- concurrent editors/publishers receive conflicts without overwrite; idempotent retries produce one project/publish/reorder effect and no partial graph;
- unauthorized/expired actor, guessed preview, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, filter/content injection, unsafe URL, media placeholder, stale version, and idempotency mismatch fail safely;
- public API/RSC/HTML/metadata/JSON-LD/sitemap/cache/log/trace/screenshot inspection finds no draft, future, hidden, deleted, unpublished, hidden-target, pointer/version/creator, fake media, or storage leakage;
- full affected backend/frontend/contract/migration/E2E/build/scan commands pass, generated output remains clean, revision remains one head, and no Critical/High finding remains.

Documentation/evidence must include:

- user guide for project fields, slug/date/status/content/link/SEO rules, technologies/relations, order/featured/visibility, staged media/gallery fallback, draft save, private preview, now/future publish in configured timezone, pending changes, reschedule, unpublish, delete, filters, and conflict recovery;
- API guide for admin/public/preview operations, revision lifecycle, schemas/errors, auth/CSRF, pagination/filter/sort catalogs, slug/detail/not-found behavior, relations/cycles, metadata/cache, `ETag`/`If-Match`, idempotency, DB-time scheduling, provider validation, media-unavailable semantics, privacy, and sanitized examples/cURL;
- developer guide for aggregate/revision/pointer model, migration `0007`, immutable/copy-on-write behavior, repository/UoW, `SkillReferenceFacade`/`ExperienceReferenceFacade`, graph validation, controlled content/URLs/SEO, effective public queries/indexes/cache/metadata, media port handoff to M9, SSR/generated-client workflow, and the revision pattern M7+ must reuse rather than fork;
- sanitized screenshots at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px, plus 400% zoom where applicable, for admin list/mobile cards/editor/errors/relations/cycle/media-unavailable/SEO/statuses/preview/publish/conflict and public list/filters/pagination/detail/gallery fallback/not-found/empty states in light/dark; attach performance/query/bundle, SEO/metadata, accessibility, security/privacy, API, coverage, traceability, and independent-review reports.

Passing lane evidence does not authorize M7 until Integration/root records the separate M6 acceptance decision. The M6 gate remains blocked by any failed Must requirement, disabled/suppressed check, placeholder/mock production path, mutable published revision, draft/preview/future/hidden/related-target leak, invalid slug/date/status/URL/SEO persistence, pointer/revision/graph corruption, self/cycle relation, provider-facade bypass, fake media/storage behavior, lost update/duplicate effect, generated drift, multiple migration heads, parallel migration/generated writer, Infrastructure-file overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
