# Milestone 7 Dispatch

## Dispatcher status

This document prepares `M7-T01` through `M7-T03`. It does not release implementation, record acceptance, or authorize M8.

M7 remains blocked until Integration/root records the separate M6 acceptance decision, confirms the accepted provider/revision contracts, and releases every shared surface required below.

| Task     | Current state | Release condition                                                                                                                    |
| -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `M7-T01` | Blocked       | M6 passes; one Alembic head is confirmed at `20260802_0007`; earlier-milestone/Infrastructure reservations are released; B0-B2 pass. |
| `M7-T02` | Blocked       | `M7-T01` backend/API evidence passes and blog contract freeze B4 is recorded with a clean generated client.                          |
| `M7-T03` | Blocked       | `M7-T01` and `M7-T02` pass and frontend readiness freeze B5 is recorded.                                                             |

M7 maps to trace milestone `M11` and delivers the Blog vertical slice: revision-safe posts, tags/categories, related posts, controlled CommonMark, authenticated preview/publication, public discovery/article routes, metadata/sitemap integration, contract generation, tests, documentation, and evidence. It does not authorize configurable pages, media upload/storage, contacts, API tokens, workers/schedulers, speculative AI behavior, or acceptance of a later milestone.

## Strict dependency gates

### B0 - Accepted foundation and shared providers

Before any M7 write, Integration/root confirms accepted M1-M3 contracts for:

- authenticated actor/session enforcement, forced-password boundary, CSRF/Origin, request IDs, rate limits, safe audit facts, and protected-state clearing;
- `/api/v1` envelopes/errors, page pagination, allow-listed filters/sorts, `ETag`/`If-Match`, idempotency, OpenAPI/client generation, and generated-wrapper boundaries;
- accepted IANA timezone, locale/site SEO defaults, public/admin shells, navigation/theme, metadata/sitemap/cache interfaces, and one current linear Alembic head;
- production startup revision checking without automatic migration, scheduling, seed, or worker behavior;
- no unresolved Critical/High finding or failed Must requirement on a consumed contract.

M7 consumes these interfaces without forking auth, common API, settings, shell, metadata, audit, database, cache, or generated-client conventions. Provider defects return to their owner for correction and re-evidence.

### B1 - Accepted revision and controlled-content decisions

Integration/root confirms ADR-0005 and ADR-0007 remain Accepted and unsuperseded. The M5/M6 immutable published-revision/copy-on-write pattern, database-time scheduling, preview isolation, cache-boundary behavior, controlled Markdown policy seam, and concurrency/idempotency behavior are available for reuse rather than reimplementation by variation.

### B2 - Separate M6 acceptance and released project baseline

Integration/root must record the separate M6 acceptance decision and prove:

- exactly one Alembic head exists at `20260802_0007` from `20260802_0007_projects.py`;
- project/public metadata/sitemap/shared route changes and generated artifacts are accepted and released;
- the shared controlled-Markdown files, if M6 touched them, have one accepted owner/version and no in-flight writer;
- M6 module/API/frontend/E2E/evidence and all shared composition files needed by M7 are released;
- no unresolved M6 defect can corrupt revision pointers, public eligibility, public not-found/privacy, cache scheduling, metadata, sitemap, or generated contracts.

B2 is a hard gate. Passing M6 lanes or freeze points alone does not release M7.

## Active-file exclusions and ownership

### Earlier milestone files

M7 must not edit, move, delete, format, regenerate, or claim ownership of:

- M1 identity/session/rate-limit/bootstrap/auth/audit foundation, protected UI/E2E/evidence, or `20260802_0002_identity_auth.py`;
- M2 common API/application primitives, health/client/contract tests/evidence, or `20260802_0003_api_conventions.py`;
- M3 profile/settings/navigation/footer modules, shells/features/tests/evidence/demo seed, or `20260802_0004_site_configuration.py`;
- M4 skills/category modules/facades/routes/features/tests/evidence or `20260802_0005_skills.py`;
- M5 experiences modules/facades/routes/features/tests/evidence or `20260802_0006_experiences.py`;
- M6 projects modules/facades/routes/features/tests/E2E/evidence or `20260802_0007_projects.py`.

After B0-B2, these remain provider-owned. Blog relations resolve only through blog-owned stable post identities; M7 does not patch project/experience/skill reverse relations or import any provider repository/ORM.

### Infrastructure files

M7 lanes must not edit `backend/migrations/env.py`, shared database runtime/session/UoW/readiness or role/grant files, `infrastructure/**`, Compose/environment/Docker files, root manifests/locks, task-runner scripts, CI/workflows, scanners, deployment files, or Infrastructure evidence. Dependency pin/config, CSP/header, runtime-role, task, or CI changes are handed to their current owner and scheduled serially.

### Integration/root and shared single-writer files

Integration/root alone writes `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator configuration, final cross-lane contract/trace reports, and final M7 task/milestone decisions. Requirements, architecture, ADR, UX, earlier dispatches, and existing planning artifacts remain read-only unless separately dispatched.

The shared CommonMark policy, sanitizer wrapper, safe rendered-content type, malicious corpus, CSP/header configuration, metadata/sitemap composition, backend/frontend router composition, central API wrapper, and shared editor/renderer primitives each have exactly one named writer window. No blog lane may create a competing Markdown/sanitizer policy in a feature directory to avoid that reservation.

## Owner-safe M7 lanes

| Stage                                | Owner                           | Exclusive write area                                                                                                                                                                                                                                                                             | Gate and handoff                                                                                                                                                          |
| ------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M7-T01-C` controlled content policy | Content Security Agent          | One Integration/root-reserved backend CommonMark/parser/sanitizer/safe-output policy location, malicious corpus and policy tests; `docs/evidence/M7/M7-T01-content-security.md`. If a frontend render boundary is shared, it is handed off serially after the backend policy contract freezes.   | Starts after B2. Produces B3a. Owns policy/version/corpus only; does not edit blog domain, migration, API artifact/generated code, routes, UI, CSP config, or acceptance. |
| `M7-T01-D` blog domain/application   | Backend Domain Agent            | Post/taxonomy/revision/relation types, lifecycle/slug/SEO/reading-time/taxonomy invariants, DTOs, ports, stable errors/audit facts, and unit/service tests under `backend/app/modules/blog/**`; `docs/evidence/M7/M7-T01-domain.md`. Excludes persistence/public-query filenames reserved below. | Starts after B3a. Produces B3. Does not write migration, shared policy, API artifact, frontend, Infrastructure files, or final acceptance.                                |
| `M7-T01-R` blog persistence          | Backend Persistence Agent       | Dedicated post/taxonomy ORM/repositories, immutable-revision enforcement, query adapters, and repository tests under `backend/app/modules/blog/**`; `docs/evidence/M7/M7-T01-persistence.md`.                                                                                                    | Starts after B3. Repositories never commit and never import transport/frontend code.                                                                                      |
| `M7-T01-M` sole migration            | Backend Migration Agent         | `backend/migrations/versions/20260802_0008_blog.py`, dedicated migration fixtures/tests, and `docs/evidence/M7/M7-T01-migration.md`.                                                                                                                                                             | Starts after B3 and an Integration/root `0008` reservation. Serialized with model registration; no other M7 revision or merge head.                                       |
| `M7-T01-A` admin/preview/export API  | Backend API Agent               | Dedicated admin post/taxonomy CRUD/lifecycle/preview/source-export route and transport-schema modules, API tests, and `docs/evidence/M7/M7-T01-admin-api.md`.                                                                                                                                    | Starts after B3; may run beside R/M only in disjoint files. Calls application services and content policy, never repositories/ORM.                                        |
| `M7-T01-P` public blog projection    | Backend Public Projection Agent | Dedicated public post list/filter/detail/relation/metadata query/projection files, route/schema modules, privacy/query-plan/cache tests, and `docs/evidence/M7/M7-T01-public-projection.md`.                                                                                                     | Starts after B3. Reads frozen effective revisions and canonical safe render output; submits executable Pydantic source for B4.                                            |
| `M7-T01-I` OpenAPI/client generation | Integration/root                | Cross-lane contract/security reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, B4, and final T01 decision.                                                                                                                                   | Starts after C/D/R/M/A/P evidence. Sole API-artifact/generated-code writer; all other lanes pause those surfaces.                                                         |
| `M7-T02-A` blog admin frontend       | Frontend Admin Agent            | `frontend/src/features/blog/admin/**`, `/admin/blog`, `/admin/blog/{id}/edit`, admin preview/source-export UI, blog-specific components/stories/tests/wrappers, and `docs/evidence/M7/M7-T02-admin.md`.                                                                                          | Starts after B4. Shared Markdown/editor/render files receive a separate serialized writer window; feature code cannot fork sanitizer logic.                               |
| `M7-T02-P` public blog frontend      | Frontend Public Agent           | `frontend/src/features/blog/public/**`, `/blog`, `/blog/{slug}`, list/article/taxonomy/pagination/safe-render components/stories/tests, route metadata/SSR/cache code, and `docs/evidence/M7/M7-T02-public.md`.                                                                                  | Starts after B4 and may run beside T02-A only in disjoint files. Initial article/list/metadata use generated wrappers server-side.                                        |
| `M7-T03-I` integration/E2E/docs      | Integration/root                | Blog API/browser/export-reload fixtures/specs, sanitized traces/screenshots/reports, user/API/developer docs, traceability links, `docs/evidence/M7/M7-T03.md`, and final M7 gate record.                                                                                                        | Starts after T01/T02 pass and B5. Defects return to owning lanes. It does not start M8 or mark M7 accepted without independent review.                                    |

No two lanes edit the same file concurrently. Blog package exports, backend model/router/application composition, admin sidebar, public navigation, common content policy, frontend render boundary, metadata/sitemap, central API wrapper, shared fixtures, and CSP configuration each receive one Integration/root-scheduled writer window if needed. Backend owns executable Pydantic source; Integration/root alone exports/generates; frontend consumes only B4 generated types.

## Sole linear migration policy

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0008_blog.py
revision: 20260802_0008
down_revision: 20260802_0007
owner: M7-T01-M only
```

The revision implements only the accepted B3 schema:

- stable `post` aggregate with normalized case-insensitive unique slug, visibility, deterministic display position where admin ordering applies, draft/published revision pointers, `publish_at`, `unpublished_at`, timestamps, optimistic version, and optional soft-delete marker;
- `post_revision` with monotonic revision number, title, excerpt, canonical UTF-8 CommonMark source, author display/reference, server-derived reading minutes, SEO/canonical values, frozen flag, safe creator reference, and timestamps;
- stable `tag` and `post_category` taxonomy rows with normalized unique name/slug, deterministic positions, timestamps/version, and the B3 visibility/deletion policy;
- revision-scoped `post_tag`, `post_category_link`, and ordered `related_post` associations with duplicate/self-reference constraints and indexes;
- pointer integrity requiring post pointers to reference revisions owned by the same post, using the accepted deferrable-FK/two-step pattern;
- checks/indexes justified by slug/taxonomy/order/lifecycle invariants, admin queries, effective public chronology, tag/category filters, detail lookup, and related-post loading;
- no rendered HTML as an unversioned mutable source of truth, no media asset/usage/storage/key field, no page/block/contact/token table, no scheduler/worker/outbox, and no parallel migration.

Canonical Markdown source is stored; sanitized render output is computed through the versioned policy or stored only as a derived cache tied to exact source checksum and renderer-policy version. A cache is never independently editable and cannot survive a source/policy mismatch.

Frozen published revisions are immutable in domain/repository behavior and receive database reinforcement only when compatible with accepted role architecture. M7 does not edit Infrastructure grants. Frozen-row update/delete attempts must fail in repository and migrated PostgreSQL tests.

Migration evidence requires empty upgrade, upgrade from accepted `0007` with representative earlier content, current/head equality, exactly-one-head verification, schema/model comparison, pointers/FKs/checks/indexes, case-insensitive slug/taxonomy races, ordered/duplicate/self relations, frozen-row rejection, copy-on-write behavior, rollback/UoW, and runtime-vs-migration-role isolation. Production startup must not migrate, render/rewrite all posts, or schedule. A schema need found after B3 returns to the sole migration owner; parallel revisions and merge heads are prohibited.

## Controlled CommonMark contract

### Canonical source and fixed policy

- Source is normalized UTF-8 CommonMark with LF line endings and a documented size/depth/token limit. The fixed extension allow-list is exactly tables, strikethrough, task lists, fenced code, and autolinks unless an approved ADR/CHG-002 changes it.
- Embedded raw HTML nodes are disabled and rejected with field-addressable positions; they are never interpreted, passed through, or made executable. Parsing is AST-based rather than regex-only so ordinary comparison characters remain valid text.
- Links allow normalized `https` and the accepted canonical root-relative internal form. `javascript:`, `data:`, `vbscript:`, `file:`, protocol-relative forms, credentials, control characters, Unicode/percent-encoded scheme tricks, and disallowed redirect forms fail closed.
- Inline/remote image and embed syntax is rejected until the M9 `MediaReferenceFacade` is accepted. M7 accepts no arbitrary image URL, iframe, object, SVG, data URI, storage key, or raw media identifier. Cover media stays null/omitted under the staged media contract inherited from M6.
- Fenced/inline code is always text-escaped and never executed. Language labels map through a bounded token catalog before becoming CSS classes; unknown labels degrade to plain code. No eval, runtime package fetch, executable playground, or arbitrary highlighter plugin is introduced.
- Table output uses semantic table structure inside a labeled horizontal overflow region; malformed/oversized tables fail limits safely. Task-list controls are rendered noninteractive in public/preview output unless an explicitly accessible read-only semantic is defined.
- Heading output is normalized into the article hierarchy and receives deterministic collision-safe IDs derived only from sanitized text. User-authored IDs/classes/styles/scripts are not accepted. Links render with safe names; external new-window behavior, if used, includes `noopener noreferrer`.

### Rendering and defense in depth

- One pinned backend parser/render/sanitizer policy is authoritative for validation, preview, public output, export/reload tests, and reading-time text extraction. Policy name/version and source checksum accompany any derived render cache.
- Sanitization runs after Markdown rendering even though raw HTML and unsafe URL nodes are disabled. The allow-list covers only required semantic prose/headings/lists/quotes/links/code/table/task-list output and strips event handlers, style, scriptable attributes/elements, dangerous URL encodings, DOM-clobbering names/IDs, and namespace tricks.
- Public/admin transport does not label an arbitrary string as trusted HTML. Any frontend HTML insertion is confined to one audited render component accepting only the generated safe-render DTO, with no concatenation, client plugin, DOM parser rewrite, or bypass. React escaping remains enabled everywhere else.
- CSP, `nosniff`, restrictive framing/referrer/permissions headers, and browser isolation are defense in depth, not substitutes for validation/sanitization. A CSP header change is owned serially by Infrastructure/Integration, not a blog lane.
- The shared malicious corpus covers script/style/template/iframe/object/embed/SVG/MathML, event handlers, raw HTML blocks/inline tags, malformed tags/comments/entities, unsafe/obfuscated URLs, autolink confusion, protocol-relative/credential URLs, DOM clobbering, code-fence breakouts, nested lists/quotes, oversized/deep documents, table/task-list edge cases, bidi/control characters, Unicode confusables, and sanitizer mutation-XSS regressions.
- Corpus expected results are reviewed fixtures used by backend policy, API, frontend render-boundary, SSR, and browser tests. No snapshot-only pass counts without assertions that dangerous nodes/attributes/requests/execution are absent and supported formatting remains intact.

### Portability, export/reload, and reading time

- Authenticated source export returns the exact normalized Markdown source plus safe filename/content type, renderer-policy version, source checksum, and post identity/revision metadata in a `private, no-store` response. It never exports rendered HTML, draft relations, admin identity, audit data, cookies, or storage values by accident.
- Reload uses the ordinary create/update draft command and the same validation/policy path; M7 does not introduce a bulk archive, filesystem import, privileged restore, or startup content loader. Exported source can be reloaded into a new draft and re-exported byte-equivalently after documented newline normalization.
- Portability evidence compares source, parsed semantic structure, safe rendered structure, links, fenced code, tables, task lists, and reading time before export and after reload. Sanitizer-policy version differences require an explicit migration/version note, not silent output drift.
- Reading minutes are derived server-side from normalized visible text, never accepted from a client. B3 freezes Unicode tokenization, treatment of code/table text, words-per-minute constant, empty/minimum behavior, rounding, overflow limit, and recalculation trigger. Draft edits recalculate draft reading time; frozen live reading time stays unchanged until publish.

## Post, taxonomy, relation, and publication contract

### Post identity, taxonomy, SEO, and media staging

- Post slug is stable route identity: Unicode-normalized ASCII lowercase kebab case, 1-80 characters, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`, unique case-insensitively. B3 freezes any `/blog/{slug}` exclusions without borrowing unrelated page-route rules blindly.
- Title/excerpt/body/author requirements and bounds are frozen at B3. Author is an explicit public display value or safe accepted profile reference; it is never inferred from administrator email/account internals.
- Tags and categories have normalized unique names/slugs, documented bounds, deterministic positions, explicit admin CRUD/order semantics, and safe delete/merge/reference conflict behavior. A post can have zero or bounded-many tags/categories as frozen at B3; duplicates fail.
- SEO title/description are bounded plain text with fallback to public post/site values. Canonical is omitted for generated same-origin `/blog/{slug}` or a normalized approved `https` value; preview/admin/draft URLs can never be canonical.
- Cover media is optional and unavailable until M9. Non-null URL/path/key/ID/blob writes fail with the staged capability-unavailable error; no fake media table/provider or broken public image is introduced, and M7 makes no `AC-014`/`AC-019` claim.
- Visibility and display position are stable aggregate concerns separate from lifecycle. Position affects deterministic admin/public ordering only as frozen at B3 and never makes nonpublic content eligible.

### Revision-scoped taxonomy and related posts

- Tag/category links and ordered related-post IDs belong to a revision. Draft taxonomy/relation edits cannot change live lists, filters, totals, metadata, or recommendations until publish; copy-on-write creates independent association rows.
- Related targets use stable post IDs, reject self-reference/duplicates/malformed/deleted targets, and are revalidated atomically at publish. M7 does not require an acyclic graph because related posts are not recursively expanded; public traversal is one bounded level.
- Draft may retain optional nonpublic target warnings under the B3 policy. Public related-post summaries resolve only target posts with an effective visible nondeleted published revision and never reveal target draft title/slug/ID/status or that an unavailable target exists.
- Taxonomy filters count and return only effective public source posts. Hidden/deleted taxonomy values and terms linked only to nonpublic posts are absent from public facets, totals, metadata, sitemap, caches, logs, and accessibility trees.

### Immutable lifecycle and database-time scheduling

- Create atomically creates the stable post plus mutable revision 1. No published pointer exists; lifecycle is `Draft`.
- Save changes only the current unfrozen draft under aggregate version and `If-Match`, recalculating safe render/reading-time derivations without altering live source, taxonomy, relations, metadata, or route output.
- Publish validates canonical source, sanitizer result, SEO, taxonomy, related targets, and all required public fields; freezes the revision; sets the published pointer and `publish_at` to the requested instant or database UTC now; and creates exactly one copy-on-write mutable draft in one transaction.
- Future `publish_at` yields derived `Scheduled`; a current/past value is public only when visible and nondeleted. PostgreSQL `now()` is authoritative. No scheduler, worker, status-flip mutation, Redis, or outbox is added.
- Editing after publication produces `Published - changes pending`; live article/source/render/reading time/taxonomy/relations/SEO stay on the frozen revision until republish.
- Reschedule changes aggregate scheduling metadata under concurrency/idempotency rules without mutating frozen content. Unpublish removes list/detail/filter/relation/metadata/sitemap eligibility immediately, retains revisions, records `unpublished_at`, and invalidates caches.
- Visibility is independent of lifecycle. Delete is a separate confirmed action preserving taxonomy/relation/audit integrity under the B3 soft-delete policy. Derived status labels follow J4 and never rely on browser time.

## Admin/public API, preview, metadata, and privacy contract

### Admin, taxonomy, lifecycle, and export API

- `/api/v1/admin/posts` provides paginated/searchable/filterable/sortable list, create, draft/live read, draft patch, visibility/order, delete, publish-now/future, reschedule, unpublish, preview, and source export through explicit DTOs/use cases/action subresources.
- Dedicated admin taxonomy endpoints provide tag/category list/create/update/order/delete or merge only where B3 explicitly supports it. Delete conflicts enumerate safe usage locations/counts without returning post source or nonpublic titles to an unauthorized actor.
- Admin filters/sorts use a closed catalog for lifecycle, visibility, tag, category, author display, schedule/date, position, title/search, and timestamps. Typed SQLAlchemy mappings/bound parameters reject unknown/duplicate/free-form expressions.
- Mutable responses carry aggregate/taxonomy `ETag`s. Update/order/delete/lifecycle actions require `If-Match`; missing returns 428 and stale returns `RESOURCE_VERSION_CONFLICT` without partial writes.
- Retriable create/publish/reschedule/unpublish/order/taxonomy mutations use accepted actor+route idempotency. Same-key/same-request replays; same-key/different-request conflicts; concurrent publish yields exactly one frozen effect and one copy-on-write draft.
- Post/taxonomy CRUD/order, save, export, preview, publish/reschedule/unpublish/delete and rejected security-sensitive attempts emit controlled audit facts in the same UoW where applicable. Audit metadata contains safe actor/resource/request/outcome/policy-version/change categories, never Markdown source/rendered HTML, URLs with secrets, taxonomy dumps, or private preview content.
- Every use case rechecks actor authorization. Unsafe cookie requests require trusted Origin and CSRF. Admin/export/preview responses are `private, no-store`; DTO allow-lists reject mass-assigned pointers, derived reading time/render cache, frozen flags, creator/audit data, publication timestamps, storage fields, and arbitrary HTML.

### Preview isolation

- A separate administrator-session-only preview endpoint renders the current draft through the same authoritative policy used for public output, even when unpublished/hidden. It carries `Cache-Control: private, no-store`, safe request ID, render-policy version, and `noindex` metadata.
- Preview never enters public list/filter/detail/related endpoints, taxonomy facets/counts, metadata, JSON-LD, sitemap/robots, public cache tags, unauthenticated search, logs, or shareable URLs/tokens. A guessed ID without a valid session reveals no protected existence.
- The UI shows a persistent `Draft preview - not public` banner and safe return to source. Session expiry removes source/preview DOM and caches. Preview errors remain safe and never fall back to rendering unsanitized source.

### Public listing, article, taxonomy, metadata, sitemap, and queries

- `GET /api/v1/public/posts` returns only posts with non-null published pointer, `visible=true`, `publish_at <= PostgreSQL now()`, and `deleted_at is null`, through an explicit summary allow-list.
- `GET /api/v1/public/posts/{slug}` returns one effective public frozen article or the same not-found contract for absent/draft/future/hidden/unpublished/deleted slugs. Credentials supplied to public routes never widen access.
- Public post schemas include only deliberate title/slug/excerpt/author display/publication date/derived reading minutes/safe-render payload/SEO plus public taxonomy and related-post summaries as appropriate. Draft source, raw/sanitized internal cache fields, revision/pointer/version/creator/audit data, hidden taxonomy IDs, private target data, and media/storage placeholders are absent.
- Public list filters are allow-listed tag/category and documented search if approved at B3; sorts include effective publication date and deterministic supported fields. Page-number pagination supplies exact totals, stable `id` tie-breakers, page-beyond-last empty results, and no loss/duplication under the tested snapshot assumptions.
- Default chronology is effective publication date descending then opaque ID, unless an explicit accepted display-position contract precedes it. Tag/category facets and related-post ordering are deterministic, bounded, and based only on public-effective data.
- Public list/detail/filter/facet/related queries join only frozen published revisions, select-in/bounded-load associations, avoid N+1, and have bounded SQL counts. Representative PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` covers chronological pagination, tag/category filters and counts, slug detail, and related-post summaries at realistic cardinality.
- Cache invalidation covers source/publication/visibility/order/slug/SEO/taxonomy/related changes. Cache TTL cannot cross the next scheduled `publish_at`; old slug/detail/metadata behavior follows the B3 slug-change policy. Admin/preview/export cache keys never overlap public caches.
- `/blog` and `/blog/{slug}` metadata use the same public projection for title/description/canonical/Open Graph/validated article structured data. Only effective public detail routes enter sitemap. Draft/future/hidden/unpublished/deleted posts and private taxonomy/relations produce no metadata, JSON-LD, canonical, sitemap, alternate suggestion, count, or timing clue.

## Contract freeze points

### B3a - CommonMark policy freeze

Integration/root records B3a only after T01-C policy review and malicious-corpus tests pass. B3a freezes parser/sanitizer packages and versions, extension/element/attribute/URL/language allow-lists, limits, canonical newline/source rules, safe-render DTO semantics, policy versioning, corpus fixture format, and frontend render-boundary requirements.

B3a releases T01-D. A content-policy change stops downstream work and returns to T01-C before database/API/client work.

### B3 - Blog domain/revision freeze

Integration/root records B3 only after T01-D focused review/tests pass. B3 freezes:

- post/taxonomy/revision ownership, slug/content/author/SEO/media-staging bounds and stable errors;
- reading-time algorithm, source/export/reload semantics, and B3a policy dependency;
- immutable publish/copy-on-write, DB-time schedule/reschedule/unpublish, visibility/order/delete behavior;
- revision-scoped tag/category/related-post rules, target validation, and public relation/facet policy;
- command/query DTOs, authorization/audit facts, concurrency/idempotency expectations, persistence ports, and proposed `0008` schema/index/query contract.

B3 releases R/M/A/P. An incompatible domain/schema/policy decision stops downstream work and returns to its owner before migration or generation.

### B4 - Blog API and generated-client freeze

Integration/root records B4 only after T01-C/D/R/M/A/P pass and generation is clean. B4 freezes:

- admin post/taxonomy/list/detail/create/update/order/delete/preview/export/publish/reschedule/unpublish operation IDs, DTOs, errors, and security declarations;
- public list/detail/tag/category/filter/sort/pagination, explicit public allow-lists, related summaries, safe-render contract, metadata inputs, cache headers, and not-found equivalence;
- `ETag`/`If-Match`, idempotency, date/time/slug/URL formats, policy/checksum/reading-time fields, examples, lifecycle labels, staged null cover media, and deprecation metadata;
- deterministic generated TypeScript client and approved blog feature-wrapper/render boundary.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. B4 releases frontend. Breaking changes require CHG-002 and another reviewed generation window; frontend must not compensate with raw fetch, duplicate transport types, `any`, hand-edited generated code, alternate Markdown libraries, arbitrary HTML insertion, or client-derived reading time.

### B5 - Blog frontend readiness freeze

Integration/root records B5 only after both T02 lanes pass focused tests, corpus parity, and browser review. B5 freezes:

- admin list/source-preview/taxonomy/relations/SEO/schedule/export/lifecycle/conflict behavior and every async state;
- public list/filter/pagination/article/related/metadata/sitemap/safe-code-table behavior;
- audited render boundary, browser nonexecution/CSP evidence, accessible keyboard/focus/announcements, responsive layouts, and sanitized fixtures/screenshots required by T03.

B5 releases T03. B5 is not M7 acceptance.

## Frontend behavior contract

### Administrator source/preview lifecycle editor

- `/admin/blog` provides search/closed filters, result count, pagination, accessible sortable table at wide widths and equivalent mobile cards, explicit lifecycle/visibility facts, create/edit/preview/export/order/publish/reschedule/unpublish and separately confirmed delete.
- `/admin/blog/{id}/edit` covers title/slug/excerpt/canonical Markdown source/author/tags/categories/related posts/visibility/order/SEO/publication plus staged cover-media explanation. It never exposes a WYSIWYG/raw-HTML mode, hidden trusted-HTML field, fake media picker, client reading-time override, or unsafe plugin control.
- Source and Preview are explicit modes/tabs with keyboard-operable toolbar actions that insert portable Markdown without stealing focus. Preview uses the authenticated server policy, shows code/table overflow behavior and the persistent private banner, and identifies policy/validation errors without rendering unsafe fallback content.
- Taxonomy and relation comboboxes are labeled, searchable, keyboard operable, preserve selection/order, expose unavailable warnings, and reject duplicate/self targets. Tag/category management retains source edits and protects against destructive usage conflicts.
- Save/preview/export/now-or-future publish/reschedule/unpublish/order/delete follow J4. The publish dialog shows configured timezone, local/UTC interpretation, validation warnings, taxonomy/related effects, and derived reading time; ambiguous/nonexistent local times fail.
- Initial/loading/success/empty/no-result/validation/render/server/offline/unauthorized/session-expired/conflict states are explicit. Forms retain safe source, focus linked summaries, protect dirty navigation, preserve local changes on conflict, safely expose request IDs, and clear source/preview/export data on expiry.

### Public listing and article

- `/blog` and `/blog/{slug}` are Server Components for initial content and metadata using the same-origin public API through generated wrappers. Initial posts/article/taxonomy/filter/pagination/metadata are not client-only or hard-coded.
- Listing exposes semantic article summaries with title, excerpt, author display where configured, publication date, reading time, public tags/categories, and clear detail links. Filters have persistent labels, active summary, exact public result count, clear action, URL persistence, and focus movement to results after navigation.
- Empty collection differs from filtered zero; page beyond last is an intentional empty result, not 404. No state reveals nonpublic totals, scheduled timing, hidden taxonomy, or related target existence.
- Detail uses one `h1`, semantic `<article>`, understandable author/date/reading metadata, safe heading hierarchy, named links, lists/quotes, nonexecuting fenced/inline code, copy feedback, labeled scrollable tables, read-only task lists, and one bounded related-post section.
- The one audited render component accepts only B4 safe-render DTOs. No feature uses `dangerouslySetInnerHTML` with arbitrary/local strings, DOM parser mutation, runtime Markdown plugin loading, eval, inline event handlers, or unsanitized error fallback.
- Draft/future/hidden/unpublished/deleted posts, target drafts, private taxonomy, source Markdown, and internal sanitizer/cache values never enter RSC payloads, HTML, metadata, JSON-LD, sitemap, caches, live regions, logs, traces, screenshots, or client storage.
- Long prose remains in the 720 px measure; code/tables use contained horizontal scrolling without whole-page overflow or clipped focus. Headings/landmarks, pagination, zoom/reflow, contrast, reduced motion, copy announcements, touch targets, and JavaScript-disabled initial content meet the WCAG review contract.

## Dispatch order

1. **Blocked - Integration/root:** record separate M6 acceptance, verify B0-B2, confirm head `0007`, release reservations, and name shared-file writers.
2. **After B2 - `M7-T01-C`:** implement/review the canonical CommonMark/sanitizer policy and malicious corpus; Integration/root records B3a.
3. **After B3a - `M7-T01-D`:** implement/review blog domain, taxonomy, revision lifecycle, relations, reading time, export/reload, SEO, and media staging.
4. **After domain evidence - Integration/root:** record B3 and reserve sole revision `0008` on `0007`.
5. **After B3 - `M7-T01-R/M/A/P`:** persistence, migration, admin/preview/export API, and public projection may run concurrently only in disjoint files.
6. **After all T01 evidence - Integration/root `M7-T01-I`:** review policy/data/security/query/contracts, export/generate twice, compile, and record B4.
7. **After B4 - Frontend `M7-T02-A/P`:** admin and public lanes may run concurrently only in disjoint files and after any shared render writer handoff.
8. **After frontend evidence - Integration/root:** run focused lifecycle/privacy/accessibility/performance/SEO/CSP-XSS review and record B5.
9. **After B5 - Integration/root `M7-T03-I`:** execute J2/J4, export-reload, browser nonexecution, docs/reviews/evidence, and prepare the M7 gate record.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, identify requested milestone `M7` and trace alias `M11`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Logs, DB samples, Markdown/export fixtures, API transcripts, metadata captures, screenshots, and traces are sanitized and contain no cookies, CSRF values, authorization headers, credentials, private/draft content, administrator identity, storage values, production dumps, or machine-specific absolute paths.

### `M7-T01` content/backend/data/API evidence

Evidence must include:

- fixed CommonMark policy tests for every allowed extension and all rejected raw-HTML/image/embed/unsafe-URL forms, parser limits, Unicode/newline canonicalization, deterministic headings, safe links, language labels, code/table/task-list behavior, sanitizer allow-list, safe DTO provenance, and policy-version/checksum behavior;
- versioned malicious corpus results across parser, sanitizer, API, SSR-safe render, and browser fixtures, asserting both dangerous-node/attribute/request/execution absence and supported-format preservation; include mutation-XSS and encoded/bidi/control variants;
- domain/property tests for post/tag/category slug normalization/collisions, content/author/SEO bounds, taxonomy CRUD/order/usage conflicts, revision-scoped duplicate/self relations, cover-media rejection, reading-time derivation/recalculation/rounding/limits, and stable errors;
- exact normalized source export/reload/re-export tests for Unicode, supported extensions, code/tables/task lists/links, semantic parse/render equivalence, checksum/policy version, reading time, content type/filename, authorization, and `private, no-store`;
- publication tests for immutable frozen revisions, copy-on-write source/taxonomy/relation independence, now/future PostgreSQL-time boundaries, reschedule/unpublish/delete/visibility/order, live/draft SEO/render/reading-time separation, rollback, cache invalidation, and audit coupling;
- migration tests for empty and `0007` upgrade, one head/current equality, schema-model parity, pointers/FKs/checks/indexes, slug/taxonomy races, relation ordering/self constraints, frozen-row rejection, representative copy-on-write data, and production role/startup behavior;
- PostgreSQL repository/query tests for concurrent slug/taxonomy/order/save/publish, exactly one publish effect/draft, DB-time eligibility/cache bounds, stable pagination/taxonomy counts, bounded relation loading, no repository commit/N+1, and realistic `EXPLAIN (ANALYZE, BUFFERS)` plans;
- admin/preview/export API tests for all post/taxonomy/lifecycle actions, source privacy, preview policy/no-store/noindex, missing/stale `If-Match`, idempotent replay/mismatch/concurrency, authorization/IDOR, mass assignment, CSRF/Origin, content/filter injection, safe errors/request IDs, and atomic failure;
- public list/detail tests for tag/category filters, sorts/exact pagination, effective eligibility, publication date/reading time, safe render, relation/taxonomy privacy, metadata/canonical/JSON-LD/sitemap exclusion, credential non-widening, and response/cache/log/trace redaction;
- OpenAPI lint/reference/security/error/example/filter/sort/deprecation review, unique operation IDs, reviewed schema diff, two deterministic generations with no diff, strict generated compile, and wrapper/render-boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest and meaningful coverage reports; generated TypeScript format/lint/type checks; no disabled test, corpus omission, or unexplained warning.

Raw HTML acceptance/execution, unsafe URL/request, sanitizer bypass/mutation-XSS, source/render/checksum drift, client-controlled reading time, mutable live revision, taxonomy/relation draft leak, self relation, nonpublic list/detail/metadata/sitemap/facet leak, media/storage placeholder, lost update/duplicate publish, preview/export cache/discovery, IDOR/mass-assignment/injection success, N+1/unbounded query, generated drift, second migration head, failed Must requirement, or Critical/High finding blocks B3a/B3/B4.

### `M7-T02` frontend/admin/public evidence

Admin evidence must include:

- generated-wrapper/form tests for every active field, source normalization, raw HTML/unsafe URL errors, slug/SEO/taxonomy/relation rules, server reading time, source/preview/export, order/visibility, publish/reschedule/unpublish/delete, `ETag`/idempotency, timezone conversion, request IDs, and safe error mapping;
- component/story tests for table/mobile cards, source/preview modes and toolbar, code/table/task-list preview, taxonomy/relation comboboxes, cover-media-unavailable explanation, SEO preview, lifecycle/publish dialog, preview banner, long/malicious content, every async/conflict state, light/dark/high-contrast/reduced-motion, narrow and 400% zoom layouts;
- keyboard-only create/invalid-save/format/tag/categorize/relate/preview/export/publish/unpublish flow with persistent labels, focused linked errors, dirty protection, conflict source preservation, dialog/tab focus handling, copy feedback, and expiry clearing.

Public evidence must include:

- SSR/generated-wrapper tests for chronological/tag/category/filtered/paginated/empty/no-result/error/not-found list/article behavior, URL state/focus, safe relation omission, taxonomy counts, and cache invalidation;
- safe-render/corpus tests asserting semantic supported output, no dangerous DOM insertion path, no script/event execution, no attacker-controlled request/navigation, no hydration mutation bypass, and no unsanitized fallback under parse/API/client errors;
- rendered head/HTML tests for title/description/canonical/Open Graph/validated article structured data and sitemap inclusion only for effective public routes, with draft/future/hidden/unpublished/deleted parity;
- semantic/axe/manual tests for article headings/landmarks/metadata, named links, lists/quotes, code labels/copy announcements, table context/overflow, task-list semantics, filters/pagination/focus, zoom/reflow, contrast, reduced motion, touch targets, and meaningful JavaScript-disabled output.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library, Storybook interaction/a11y, production build, and focused Playwright. Record Server/Client Component rationale, route JS/bundle delta, SSR/API request count, sanitizer/render cost on bounded large content, no unnecessary hydration/overfetch, blog SQL/query plans, cache schedule behavior, and Lighthouse `/blog` plus representative `/blog/{slug}` profiles targeting performance >=90, accessibility >=95, and SEO >=95 with measured variance disposition.

Browser security evidence must capture effective CSP/security headers and instrument dialogs, global errors, DOM mutations, navigation, downloads, network requests, cookies/storage, and side effects while rendering the malicious corpus in preview and public article. Any script/event execution, unexpected request/navigation, DOM clobber, CSP weakening/violation attributable to shipped code, private source retention, or unsafe HTML fallback blocks B5/T02.

### `M7-T03` vertical-slice and M7 gate evidence

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0008`. Fixtures are created through APIs/factories, not demo seed. It must prove:

- administrator creates a post draft, receives field-addressable slug/content/HTML/URL/SEO/taxonomy/relation errors, authors every supported CommonMark extension, previews through the canonical policy, exports/reloads source, and publishes now;
- export -> ordinary draft reload -> re-export preserves normalized source/checksum and semantic safe render/code/tables/task lists/links/reading time without importing admin/private metadata;
- future publication uses configured timezone, remains absent from public list/detail/taxonomy/relations/metadata/sitemap until PostgreSQL time, and reschedules/unpublishes without a worker while respecting cache bounds;
- editing published source/taxonomy/relations/SEO leaves live article/render/reading time/list/facets/metadata byte/field-equivalent to the frozen revision, shows `Published - changes pending`, previews only draft, and republishes atomically;
- tag/category CRUD/order/usage conflict and list filter/pagination flows produce exact public-only totals, stable URLs/focus, page-beyond-last/empty/no-match states, and no nonpublic taxonomy clue;
- related posts reject self/duplicate/deleted targets and render only effective public frozen summaries in deterministic bounded order without target-draft leakage;
- malicious corpus content cannot execute scripts/events, navigate, fetch attacker URLs, mutate privileged DOM, escape code/table regions, weaken CSP, or survive through alternate preview/public/error/export-reload paths;
- metadata/canonical/Open Graph/article JSON-LD/sitemap and not-found behavior are correct for public vs draft/future/hidden/unpublished/deleted states;
- concurrent editors/publishers/taxonomy writers receive conflicts without overwrite; idempotent retries create one post/taxonomy/order/publish effect and no partial relation state;
- unauthorized/expired actor, guessed preview/export, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, unsafe Markdown/URL, filter injection, stale version, and idempotency mismatch fail safely;
- public API/RSC/HTML/metadata/JSON-LD/sitemap/cache/log/trace/screenshot/storage inspection finds no draft source/render, future/hidden/deleted/unpublished post, hidden taxonomy/target, revision/pointer/version/creator, cover placeholder, or sanitizer internals;
- full affected backend/frontend/contract/migration/E2E/build/scan commands pass, generated output remains clean, revision remains one head, and no Critical/High finding remains.

Documentation/evidence must include:

- user guide for post/source fields, supported CommonMark syntax, raw HTML/image/embed/URL restrictions, code/tables/task lists, slug/author/SEO, reading time, tags/categories/related posts, visibility/order, staged cover media, draft/private preview/export, normalized reload, now/future publish in configured timezone, pending changes, reschedule, unpublish, delete, filters, and conflict recovery;
- API guide for post/taxonomy/admin/public/preview/export operations, source/safe-render/checksum/policy fields, revision lifecycle, schemas/errors, auth/CSRF, pagination/filter/sort, reading time, related-post privacy, metadata/cache/sitemap, `ETag`/`If-Match`, idempotency, DB-time scheduling, media-unavailable behavior, and sanitized examples/cURL;
- developer/security guide for CommonMark parser/extensions/sanitizer/limits/versioning/corpus, trusted-render boundary/CSP, aggregate/revision/pointer/taxonomy model, migration `0008`, immutable/copy-on-write/UoW, reading-time algorithm, export/reload, effective public query/index/cache/metadata flow, M9 media handoff, SSR/generated-client workflow, and the revision/content pattern M8 must reuse rather than fork;
- sanitized screenshots at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px, plus 400% zoom where applicable, for admin list/mobile cards/source-preview/supported formatting/errors/taxonomy/relations/cover-unavailable/SEO/statuses/publish/conflict and public list/filters/pagination/article/code/table/task-list/not-found/empty states in light/dark; attach corpus/CSP-XSS, export-reload, performance/query/bundle, SEO/metadata, accessibility, security/privacy, API, coverage, traceability, and independent-review reports.

Passing lane evidence does not authorize M8 until Integration/root records the separate M7 acceptance decision. The M7 gate remains blocked by any failed Must requirement, disabled/suppressed check, placeholder/mock production path, raw HTML/unsafe URL acceptance or execution, sanitizer/render/export drift, mutable published revision, draft/preview/future/hidden/taxonomy/related leak, invalid slug/SEO/taxonomy persistence, pointer/revision/relation corruption, self relation, fake media/storage behavior, client reading-time override, lost update/duplicate effect, generated drift, multiple migration heads, parallel migration/generated/policy writer, shared/Infrastructure-file overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
