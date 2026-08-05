# Milestone 8 Dispatch

## Dispatcher status

This document prepares `M8-T01` through `M8-T03`. It does not release implementation, record acceptance, or authorize M9.

M8 remains blocked until Integration/root records the separate M7 acceptance decision, confirms all published-safe provider contracts, resolves the block-catalog count discrepancy, and releases every shared surface required below.

| Task     | Current state | Release condition                                                                                                                        |
| -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `M8-T01` | Blocked       | M7 passes; one Alembic head is `20260802_0008`; catalog/provider/shared-file gates G0-G2 pass; sole `0009` reservation is recorded.      |
| `M8-T02` | Blocked       | `M8-T01` registry/domain/persistence/migration evidence passes and page registry freeze G3 is recorded.                                  |
| `M8-T03` | Blocked       | `M8-T02` API/public-projection evidence passes, generated client is clean at G4, and all frontend/integration ownership windows release. |

M8 maps to trace milestone `M12`. For this requested three-task dispatch, `M8-T03` includes the task-catalog's builder, all public-renderer, E2E, documentation, and slice-closure responsibilities; no separate `M8-T04` is released. Scope is configurable Home/custom pages, typed/versioned blocks, normalized references, revision-safe lifecycle/preview, public SSR/metadata, and evidence. It does not authorize media storage/upload, contacts, tokens, workers/schedulers, speculative AI behavior, or M9 acceptance.

## Strict dependency and reconciliation gates

### G0 - Accepted foundation and shared providers

Before any M8 write, Integration/root confirms accepted M1-M3 contracts for:

- actor/session authorization, forced-password boundary, CSRF/Origin, request IDs, rate limits, protected-state clearing, and safe audit facts;
- `/api/v1` envelopes/errors, page pagination, allow-listed filters/sorts, `ETag`/`If-Match`, idempotency, OpenAPI/client generation, and wrapper boundaries;
- site settings/locale/IANA timezone/SEO defaults, public/admin shells, navigation/theme, metadata/sitemap/cache composition, not-found behavior, and reserved-route ownership;
- one current linear Alembic head, production revision checks, and no startup migration/seed/scheduler behavior;
- no unresolved Critical/High finding or failed Must requirement in a consumed contract.

M8 consumes these interfaces without forking auth, common API, settings, navigation, shell, metadata, audit, database, cache, or generated-client conventions. Provider defects return to their owning milestone for correction and re-evidence.

### G1 - Separate M7 acceptance and published-safe content facades

Integration/root must record the separate M7 acceptance decision and prove:

- exactly one Alembic head exists at `20260802_0008` from `20260802_0008_blog.py`;
- the immutable published-revision/copy-on-write, PostgreSQL-time scheduling, preview privacy, safe CommonMark, metadata/sitemap, cache, and concurrency/idempotency contracts pass and are released;
- released application-facing facades exist for public profile/site facts, skills, experiences, projects, and posts, each validating target existence/state and returning only published-safe/public-approved summaries without repository/ORM exposure;
- a page-owned internal destination facade/port can validate Home/custom page targets without recursively importing page persistence;
- M7 module/API/frontend/E2E/evidence, CommonMark/render boundary, and shared router/metadata/sitemap/generated files needed by M8 are released.

G1 is a hard gate. Passing M7 lanes or freeze points alone does not release M8.

### G2 - Required block-catalog reconciliation

The accepted SPEC §5.2 and architecture registry currently name 19 identifiers:

1. `hero`
2. `profile_summary`
3. `call_to_action`
4. `statistics`
5. `skills_grid`
6. `featured_skills`
7. `experience_summary`
8. `experience_list`
9. `project_grid`
10. `featured_projects`
11. `latest_posts`
12. `rich_text`
13. `image`
14. `image_with_text`
15. `links_collection`
16. `contact_callout`
17. `testimonial`
18. `divider`
19. `spacer`

Integration/root reconciled the catalog on 2026-08-02: the two derived planning references to 20 were transcription errors. SPEC §5.2 is authoritative and explicitly lists the 19 kinds above; the accepted architecture registry already matches it exactly. The task catalog and milestone plan now say all 19 SPEC-listed kinds. This is a derived-artifact correction, not a scope change, so it does not require CHG-002 and no twentieth placeholder is introduced. G2 requires exact registry/schema/renderer parity for these 19 canonical kinds.

G2 also freezes canonical names for SPEC presentation labels: professional-experience summary/list map to `experience_summary`/`experience_list`; section divider/spacing map to `divider`/`spacer`. Aliases are import adapters only if approved, never separately public registry kinds.

## Active-file exclusions and ownership

### Earlier milestone files

M8 must not edit, move, delete, format, regenerate, or claim ownership of:

- M1 identity/session/rate-limit/bootstrap/auth/audit foundation, UI/E2E/evidence, or `20260802_0002_identity_auth.py`;
- M2 common API/application/health/client/contract files/evidence or `20260802_0003_api_conventions.py`;
- M3 profile/settings/navigation/footer modules, shells/features/tests/evidence/demo seed, or `20260802_0004_site_configuration.py`;
- M4 skills/category modules/facades/routes/features/tests/evidence or `20260802_0005_skills.py`;
- M5 experiences modules/facades/routes/features/tests/evidence or `20260802_0006_experiences.py`;
- M6 projects modules/facades/routes/features/tests/evidence or `20260802_0007_projects.py`;
- M7 blog/taxonomy/CommonMark policy/render boundary/routes/features/tests/E2E/evidence or `20260802_0008_blog.py`.

After G0-G2, earlier modules remain provider-owned. Pages call only released application facades and never import provider repositories/ORM, reinterpret visibility/publication, patch reverse relations, or fork the M7 safe-rich-text policy.

### Infrastructure files

M8 lanes must not edit `backend/migrations/env.py`, shared database runtime/session/UoW/readiness or role/grant files, `infrastructure/**`, Compose/environment/Docker files, root manifests/locks, task-runner scripts, CI/workflows, scanners, deployment files, or Infrastructure evidence. Dependency/config/grant/task/CI changes are handed to their current owner and scheduled serially.

### Integration/root and shared single-writer files

Integration/root alone writes `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator configuration, final cross-lane registry/contract/trace reports, and final M8 decisions. Requirements, architecture, ADR, UX, earlier dispatches, and existing planning artifacts remain read-only unless G2 explicitly routes an approved CHG-002 update to its owner.

The backend registry, serializer/upgrader catalog, reference-kind catalog, frontend renderer registry, shared block fixtures, Home/custom dynamic route boundary, route-reservation constant/tests, public/admin router composition, metadata/sitemap composition, central API wrapper, shared editor/render primitives, and shared CommonMark/CSP files each have exactly one named writer window. Feature lanes do not create competing registries or compatibility shims.

## Owner-safe M8 lanes

| Stage                                     | Owner                           | Exclusive write area                                                                                                                                                                                                                                                                                           | Gate and handoff                                                                                                                                                 |
| ----------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M8-T01-G` registry/domain/application    | Backend Page Registry Agent     | Page/revision/block/reference domain, canonical registry, strict config schemas/serializers/upgraders/reference extractors, lifecycle/slug/order/duplicate/export rules, ports/DTOs/errors/audit facts, fixtures and tests under `backend/app/modules/pages/**`; `docs/evidence/M8/M8-T01-registry-domain.md`. | Starts after G2. Produces G3. Excludes reserved persistence/public-query/API files; no migration/artifact/frontend/Infrastructure/final acceptance.              |
| `M8-T01-R` page persistence               | Backend Persistence Agent       | Dedicated page/block/reference ORM/repositories, immutable revision enforcement, bounded resolver/query adapters, and repository tests under `backend/app/modules/pages/**`; `docs/evidence/M8/M8-T01-persistence.md`.                                                                                         | Starts after G3. Repositories never commit or import provider persistence/transport.                                                                             |
| `M8-T01-M` sole migration                 | Backend Migration Agent         | `backend/migrations/versions/20260802_0009_pages_blocks.py`, dedicated migration fixtures/tests, and `docs/evidence/M8/M8-T01-migration.md`.                                                                                                                                                                   | Starts after G3 and Integration/root reservation. Serialized with model registration; no other M8 revision or merge head.                                        |
| `M8-T02-A` admin/preview/export API       | Backend API Agent               | Dedicated admin page/block CRUD/action/preview/export route and transport-schema modules, contract/API tests, and `docs/evidence/M8/M8-T02-admin-api.md`.                                                                                                                                                      | Starts after T01-R/M pass; calls application services/facades only. Does not export/generate client artifacts.                                                   |
| `M8-T02-P` public page projection         | Backend Public Projection Agent | Dedicated Home/custom page/reference-resolution query/projection files, public route/schema modules, privacy/query-plan/cache/metadata tests, and `docs/evidence/M8/M8-T02-public-projection.md`.                                                                                                              | Starts after T01-R/M and may run beside T02-A only in disjoint files. Resolves one internally consistent frozen revision for G4.                                 |
| `M8-T02-I` OpenAPI/client generation      | Integration/root                | Cross-lane registry/contract/security reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, G4, and final T01/T02 decisions.                                                                                                                                   | Starts after G/A/R/M/P evidence. Sole artifact/generated-code writer; all other lanes pause those surfaces.                                                      |
| `M8-T03-A` admin page-builder frontend    | Frontend Page Builder Agent     | `frontend/src/features/pages/admin/**`, `/admin/pages`, `/admin/pages/{id}/edit`, admin preview/export UI, page-specific catalog/outline/inspector/canvas/publication components/stories/tests/wrappers, and `docs/evidence/M8/M8-T03-admin.md`.                                                               | Starts after G4. Shared admin/editor primitives require a separately serialized Integration/root writer handoff.                                                 |
| `M8-T03-P` public block renderer/frontend | Frontend Public Renderer Agent  | Canonical frontend renderer registry, page-specific renderer components/stories/tests, `frontend/src/features/pages/public/**`, Home/custom page integration in reserved route files, SSR/cache/metadata behavior, registry parity evidence, and `docs/evidence/M8/M8-T03-public.md`.                          | Starts after G4. Shared Home/dynamic-route/components files receive named serial windows; may run beside T03-A only in disjoint files.                           |
| `M8-T03-I` integration/E2E/docs           | Integration/root                | Page/block API/browser/export fixtures/specs, sanitized traces/screenshots/reports, user/API/developer docs, traceability links, `docs/evidence/M8/M8-T03.md`, G5, and final M8 gate record.                                                                                                                   | Starts after both frontend lanes pass. Defects return to owners. It does not release M9 or mark M8 accepted without independent review and G2/media disposition. |

No two lanes edit the same file concurrently. Backend owns executable Pydantic source/registry semantics; Integration/root alone exports/generates; frontend consumes only G4 generated discriminated types. Registry fixtures are written once by T01-G, published read-only at G3/G4, and consumed by API/frontend/E2E without editing them in parallel.

## Sole linear migration policy

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0009_pages_blocks.py
revision: 20260802_0009
down_revision: 20260802_0008
owner: M8-T01-M only
```

The revision implements only the accepted G3 schema:

- stable `page` aggregate with route kind (`home` singleton or `custom`), normalized custom slug, navigation visibility, public visibility, deterministic page position where applicable, draft/published revision pointers, `publish_at`, `unpublished_at`, timestamps, optimistic version, and optional soft-delete marker;
- `page_revision` with monotonic revision number, title, description, bounded SEO/canonical fields, frozen flag, safe creator reference, and timestamps;
- relational `page_block` shell owned by one page revision: opaque ID, canonical `block_type`, positive `schema_version`, zero-based contiguous `position`, visible flag, bounded common title/subtitle/description, allow-listed theme/layout values, bounded validated responsive JSON, strict bounded type-specific `config JSONB`, timestamps;
- normalized `page_block_reference`: block/revision ownership, closed `reference_kind`, typed target ID, closed role, deterministic position, required/optional intent, and composite uniqueness/cardinality support;
- case-insensitive unique custom slugs plus route-kind/singleton/pointer/order/reference/check/index constraints justified by admin editor and public route/query plans;
- no provider mirror table, arbitrary JSON document, rendered HTML/CSS/code/query, media asset/usage/storage object/key, contact/token table, scheduler/worker/outbox, or parallel revision.

Polymorphic target existence/publication cannot be enforced by a generic SQL FK. Save/publish services resolve normalized references through provider facades; database constraints enforce shape, ownership, kind/role catalogs, uniqueness, cardinality-supporting indexes, and block/revision consistency. Media is the staged exception below.

Frozen published page revisions, their blocks, configs, and references are immutable through domain/repository behavior and receive database reinforcement only when compatible with accepted role architecture. M8 does not edit Infrastructure grants. Frozen child update/delete/reparent attempts must fail in repository and migrated PostgreSQL tests.

Migration evidence requires empty upgrade, upgrade from accepted `0008` with representative provider data, current/head equality, exactly-one-head verification, schema/model comparison, singleton/slug/pointer/FK/check/index integrity, JSONB bounds, block/reference ownership, contiguous order, frozen parent/child rejection, copy-on-write deep copy, rollback/UoW, and runtime-vs-migration-role isolation. Production startup must not migrate, rewrite configs, publish, or schedule. A schema need after G3 returns to the sole migration owner; parallel revisions/merge heads are prohibited.

## Registry, schema, serializer, and migration contract

### Canonical registry entry

Every G2-resolved kind has exactly one backend registry entry containing:

- canonical `block_type`, current positive `schema_version`, strict Pydantic config model with `extra='forbid'`, common-field applicability, defaults, and bounded collection/string/nesting limits;
- allowed theme/layout/responsive tokens and CTA/link fields; arbitrary CSS/classes/styles/HTML/JavaScript/components/database expressions are not fields;
- canonical serializer/deserializer producing JSON-compatible primitives deterministically, rejecting NaN/infinity/duplicate-key ambiguity, non-string object keys, unknown fields/types/versions, invalid unions, and oversized/deep payloads;
- ordered reference extractor declaring closed target kind/role, cardinality, required/optional semantics, target ID type, duplicate policy, and published-safe provider facade;
- renderer key, accessible fallback/error behavior, public data resolver, cache tags, query budget, and media-stage policy;
- explicit pure upgrade adapter from each supported prior version to the next, fixture/checksum expectations, and removal/deprecation notes.

Registry construction fails on duplicate kind/version/renderer key, missing current schema, broken adapter chain, undeclared config/reference field, fixture absence, or canonical count/name mismatch. Production cannot dynamically register plugins or accept client-provided schema/renderer names.

### Version and data migration strategy

- New writes use only the current registry version. Reads validate the recorded kind/version before deserialization; unknown/unsupported data fails closed with an admin diagnostic and safe public omission/section error according to G3, never raw JSON rendering.
- Compatible old versions may be adapted in memory for a bounded deprecation window without writing during GET. Persisted upgrades use an explicit forward Alembic/data command with representative fixtures, idempotency, dry-run/reporting where appropriate, and rollback/backup plan.
- A schema change that alters stored meaning, references, or rendering requires a new version, adapter/data-migration impact, fixture/renderer/OpenAPI/client updates, visual/accessibility/security regression review, and CHG-002 when observable contracts change. Silent mutation or reinterpreting a frozen revision is prohibited.
- Canonical export includes page/revision metadata, registry version manifest, ordered blocks/common fields/config, normalized reference descriptors, and checksum in a documented bounded JSON format. It excludes rendered HTML, resolved provider payloads, admin/audit identity, secrets, cache data, storage keys, and arbitrary database fields.
- M8 export is authenticated read-only and `private, no-store`; no bulk import/startup loader is authorized. Export fixtures must deserialize through a non-persisting validator and round-trip canonically to prove portability, but persistence/import remains future scope unless separately specified.

### Required block behavior matrix

G3 freezes a fixture and schema/renderer/reference contract for every G2-resolved kind. At minimum:

- `hero`: semantic primary heading/supporting copy, bounded CTA links, optional public profile evidence; never a required full-viewport panel;
- `profile_summary`: public-approved profile projection only, explicit optional fields, safe About link;
- `call_to_action` and `contact_callout`: heading/copy and bounded safe internal/HTTPS actions; no form submission, invented privacy promise, `mailto`/`tel` unless allowed by the shared link policy;
- `statistics`: bounded ordered label/value/context items; values are authored evidence, no executable formula/query/animated counter by default;
- `skills_grid`/`featured_skills`: bounded public skill/category facades, deterministic order/filter policy, hidden target omission;
- `experience_summary`/`experience_list`: effective public experience summaries/list with semantic chronology and bounded item count;
- `project_grid`/`featured_projects`: effective public project summaries, deterministic featured/order rules, intentional staged image fallback;
- `latest_posts`: effective public post summaries ordered by publication time with bounded count, date/reading/category facts;
- `rich_text`: M7 canonical CommonMark safe-render contract only; no raw HTML/CSS/code execution or competing sanitizer;
- `image`/`image_with_text`: typed media-reference intent, purpose/alt/caption/layout/focal configuration schema, but publication behavior remains staged until M9 as specified below;
- `links_collection`: bounded ordered named links using the shared internal/HTTPS URL policy and safe external behavior;
- `testimonial`: bounded quote/attribution/context supplied by the administrator, no fabricated identity/claim or arbitrary HTML;
- `divider`/`spacer`: decorative semantics and bounded tokenized responsive size; no blank-heading/focus target or arbitrary pixels/CSS.

All kinds share applicable title/subtitle/description, visibility, order, theme/layout, CTA, content reference, responsive, and type-specific fields through explicit schemas. “Not applicable” means the field is absent/rejected, not silently ignored.

## Page aggregate, lifecycle, block operations, and references

### Slugs, Home/custom identity, and SEO

- Custom slug normalization is ASCII lowercase kebab case, 1-80 characters, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`, unique case-insensitively. It is one path segment only.
- Reserved values are exactly `admin`, `api`, `_next`, `about`, `experience`, `experiences`, `skills`, `projects`, `blog`, `contact`, `privacy`, `legal`, `robots.txt`, `sitemap.xml`, `favicon.ico`, `assets`, `media`, `health`, `docs`, and `openapi.json`, plus any route added through the G3 reviewed registry. The constant is parity-tested against actual Next.js/platform routes.
- Home is a singleton route kind for `/`, not a custom slug. Custom pages cannot shadow Home, required public routes, API/health/static internals, admin, or another normalized/soft-deleted route under the G3 collision policy.
- Page title/description/SEO title/description/canonical are bounded safe text/URL. Canonical defaults to the current public route; preview/admin/draft/reserved/old slugs can never become canonical. Navigation visibility is independent from public lifecycle and does not mutate M3 menus implicitly without an accepted navigation facade command.

### Immutable lifecycle and copy-on-write blocks

- Create atomically creates the stable page plus mutable revision 1 with an empty ordered block list. Duplicate deep-copies current draft content/blocks/configs/references to a new Draft page with new IDs, no published pointer, and a collision-safe administrator-reviewed slug.
- Draft save changes only the unfrozen draft under aggregate version/`If-Match`; it validates the whole page, registry configs, extracted references, and order in one UoW. Live page/blocks/references/metadata remain unchanged.
- Publish validates all blocks/references/required provider data and public renderability, freezes the internally consistent revision/children, points the aggregate to it, sets `publish_at` from requested instant or database UTC now, and creates exactly one deep copy-on-write draft in one transaction.
- Future `publish_at` yields derived `Scheduled`; effective public pages require published pointer, visible, nondeleted, and `publish_at <= PostgreSQL now()`. No worker/status-flip row/Redis/outbox is added.
- Editing after publication yields `Published - changes pending`; live block order/config/references/metadata stay byte/field-equivalent until republish. Reschedule does not mutate frozen data. Unpublish immediately removes public/metadata/sitemap/cache/navigation eligibility while retaining revisions.
- Delete is separate from unpublish and preserves stable reference/audit integrity under G3. Home deletion/duplication/slug transitions have explicit stricter rules; no action can leave two Home aggregates or silently remove the required `/` route.

### Atomic block actions

- Add inserts a validated current-version block at a defined draft position and reindexes atomically. Duplicate creates a new block ID adjacent to the source with deep-copied canonical config/reference rows; later edits share no mutable object/row.
- Hide/show changes only the draft block visibility; hidden blocks remain editable/previewable as authoring state but public projection omits the block and every referenced payload/query.
- Complete-list reorder accepts each current draft block ID exactly once, no unknown/duplicate/missing/foreign ID, and rewrites contiguous positions in one transaction under page `If-Match`. Partial/fractional ordering and per-row commit loops are prohibited.
- Delete removes only the mutable draft block after confirmation and reindexes atomically. A published block is never deleted/mutated in place; deleting the page is not a block-delete shortcut.
- Concurrent add/duplicate/reorder/hide/delete/save/publish requests serialize or conflict deterministically. Idempotent retries create one block/copy/order/publish effect and never duplicate references or positions.

### Published-safe references and media staging

- Save extracts references from validated configs and rewrites normalized rows transactionally; clients cannot directly mass-assign reference rows that disagree with config. Extraction is deterministic and complete for the registered schema version.
- Profile/skill/experience/project/post/internal-page targets validate through released application facades. Draft save may retain an existing nonpublic optional target with a linked warning under G3; publish rejects required unusable targets. Public resolution returns only public-approved/effective frozen summaries and omits optional unavailable targets without revealing identity/existence.
- Internal page targets cannot self-reference where the block would create a recursive render and are checked for bounded render dependency cycles. Public resolvers never recursively render an arbitrary page graph; link references resolve to safe destinations only.
- Media reference roles exist in the registry so M9 can activate them without redesign. Before M9, a syntactically valid opaque media target may be retained only as unresolved draft intent, marked unavailable, never resolved/fetched/public, and never treated as proof an asset exists. No media FK/table/usage row/storage adapter/key/URL is created in `0009`.
- A block requiring media (`image`, and media-required `image_with_text` variants) cannot publish before an accepted M9 `MediaReferenceFacade`; optional media on other blocks is omitted with intentional fallback. Preview shows an explicit unavailable placeholder/banner, never a broken image or fabricated alt text.
- M8 cannot claim the media-dependent portion of `AC-005`, `AC-014`, or `AC-019`. M9 owns forward persistence/usage activation, validation/delivery, deletion protection, and the final media-backed renderer evidence without mutating frozen revisions in place.

## Admin/public API, preview, privacy, and query contract

### Admin page/block/lifecycle/export API

- `/api/v1/admin/pages` provides paginated/search/filter/sort list, create, duplicate, draft/live read, page patch, block add/update/duplicate/hide/show/delete/complete-reorder, visibility/navigation order, preview, export, publish-now/future, reschedule, unpublish, and page delete through explicit DTOs/use cases/action subresources.
- Admin list filters/sorts use a closed catalog for route kind, lifecycle, visibility/navigation visibility, slug/title/search, schedule/date, position, and timestamps. Bound typed expressions reject unknown/duplicate/arbitrary database fields.
- Admin page/block responses carry aggregate `ETag`; every mutation requires `If-Match`, missing returns 428, stale returns `RESOURCE_VERSION_CONFLICT`, and the response supplies safe recovery context without leaking another actor's content.
- Retriable create/duplicate/add-block/duplicate-block/reorder/publish/reschedule/unpublish actions use accepted actor+route idempotency. Same-key/same-request replays, mismatch conflicts, concurrent attempts yield exactly one effect.
- Page/block create/update/duplicate/order/hide/show/delete/export/preview/publish/reschedule/unpublish and rejected security-sensitive attempts emit controlled audit facts where applicable in the same UoW. Metadata contains safe actor/resource/request/outcome/type/version/change categories, never config/source/reference payloads, provider details, storage intent, HTML, or secrets.
- Every use case rechecks actor/resource authorization. Unsafe cookie requests require trusted Origin and CSRF. Admin/preview/export are `private, no-store`; DTOs reject pointers/frozen/audit/creator/derived reference rows/render keys/arbitrary JSON/HTML/CSS/query/code and extra fields.

### Preview isolation

- A separate administrator-session-only preview resolves the current draft through the exact canonical registry/public renderer path while allowing explicit editor selection decoration outside rendered spacing. It is `private, no-store`, `noindex`, carries safe request/policy/registry versions, and displays `Draft preview - not public` persistently.
- Preview never enters public Home/custom endpoints, metadata/JSON-LD/sitemap/robots/navigation discovery, public caches/tags, search, provider reverse relations, logs, or shareable tokens/URLs. Guessing an ID without session reveals no existence.
- Missing required references and unsupported versions render a safe linked issue state, never raw config or an unsanitized fallback. Session expiry clears draft config/preview/selection from DOM, RSC caches, client state, and history-sensitive storage.

### Public Home/custom SSR, metadata, 404 privacy, cache, and query plans

- `/` and `GET /api/v1/public/pages/home` resolve the singleton effective Home revision; `/{custom-slug}` and `GET /api/v1/public/pages/{slug}` resolve only effective custom pages after platform routes win routing precedence.
- Public eligibility is non-null published pointer, `visible=true`, `publish_at <= PostgreSQL now()`, and nondeleted. Hidden blocks are excluded before reference resolution. Credentials on public requests never widen page/block/reference access.
- Public DTOs are renderer-ready allow-lists of page metadata and validated ordered visible block unions plus public-safe resolved reference DTOs. They exclude raw JSONB, unknown fields, hidden blocks/references, draft data/differences, revision/pointer/version/creator/audit/admin fields, provider internals, unresolved media IDs, and registry implementation details.
- Absent/draft/future/hidden/unpublished/deleted/reserved/invalid custom slugs return the same designed public 404 without counts, suggestions, timing differences, metadata, sitemap entries, cache clues, or provider reference hints. `/`, required routes, admin/API/static paths cannot fall through to custom page lookup.
- Public metadata uses the same page projection for title/description/canonical/Open Graph and appropriate validated structured data. Only effective discoverable custom pages enter sitemap/navigation discovery; Home uses canonical `/`. Hidden blocks/references never contribute metadata.
- Public caches invalidate on page/slug/visibility/navigation/SEO/publication/block/config/reference/provider-public-state changes. TTL cannot cross next scheduled publication; admin/preview/export caches never share keys. Old-slug behavior is frozen at G3 and cannot leak former draft identity.
- Page queries load exactly one frozen revision, ordered visible blocks, normalized references, and grouped provider projections with bounded per-kind calls/batches. No block performs an ORM/API request during React render. Query/request budgets are independent of block count up to documented limits, avoiding N+1.
- Representative PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` and instrumentation cover Home/custom slug lookup, sitemap effective-page query, admin list, block loading/order, reference extraction lookup, and provider batch resolution with realistic maximum blocks/references. Unknown/malicious payloads cannot trigger arbitrary query shapes.

## Contract freeze points

### G3 - Page registry/domain/schema freeze

Integration/root records G3 only after G2 resolution and T01-G focused review/tests pass. G3 freezes:

- exact required catalog count/names, registry entry/fixture format, common fields, per-kind versioned schemas, serializer/upgrader/reference/renderer/resolver contracts and limits;
- Home/custom aggregate identity, reserved slug registry, SEO/navigation/duplicate/delete/export behavior;
- immutable publish/copy-on-write, DB-time schedule/reschedule/unpublish, page/block visibility/order/action semantics;
- provider-facade/reference/media-staging rules, internal cycle/depth policy, public omission/error behavior;
- command/query DTOs, audit/authorization/concurrency/idempotency, persistence ports, and proposed `0009` schema/index/query contract.

G3 releases R/M and then T02 after their pass. Any incompatible schema/catalog/provider decision returns to T01-G before migration/API/generation.

### G4 - Page/block API and generated-client freeze

Integration/root records G4 only after T01-G/R/M and T02-A/P pass and generation is clean. G4 freezes:

- admin page/list/detail/create/duplicate/update/delete/preview/export/publication and all block action operation IDs, discriminated DTOs, errors, and security declarations;
- public Home/custom page union DTO, renderer/reference resolution, metadata/cache/404 behavior, and staged media omissions;
- `ETag`/`If-Match`, idempotency, slug/time/URL/JSON bounds, registry/schema versions, examples, lifecycle labels, and deprecation/migration metadata;
- deterministic generated TypeScript client, discriminated unions, registry fixtures, and feature-wrapper boundary.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. G4 releases frontend. Breaking changes require CHG-002 and a reviewed generation window; frontend cannot compensate with raw fetch, `any`, duplicate types, raw JSON editors, hand-edited generated code, alternate renderer names, or client-only validation.

### G5 - Frontend/integration readiness and M8 decision boundary

Integration/root records G5 only after T03-A/P pass focused tests, renderer parity, malicious corpus, and browser review. G5 freezes admin builder/public renderer behavior, accessible/responsive states, sanitized fixtures, query/bundle evidence, and screenshot set for T03-I.

G5 releases final integration only. It is not M8 acceptance. Final M8 disposition must explicitly record G2 resolution and the M9-staged media limitation; it cannot claim media-dependent AC coverage that has not run.

## Frontend behavior contract

### Accessible administrator page list and builder

- `/admin/pages` provides search/closed filters/result count/pagination, sortable accessible table at wide widths and equivalent cards on narrow widths, route/lifecycle/visibility/navigation facts, create/duplicate/edit/preview/export/publish/reschedule/unpublish and separately confirmed delete.
- `/admin/pages/{id}/edit` provides metadata/slug/SEO, ordered outline, searchable palette grouped Narrative/Evidence/Media/Conversion, selected-block canvas summary, schema-specific inspector sections for Content/References/Appearance/Responsive, validation issue counts, and lifecycle panel. Raw JSON/config editing is never exposed.
- Every G2-resolved kind appears exactly once with accessible name/description/mini-preview and appropriate availability state. Media-required kinds explain M9 staging and may be saved only as unresolved drafts; no fake picker/upload or false successful public preview.
- Add inserts after selection and focuses the new inspector. Duplicate selects the independent adjacent copy. Hide/show is reversible and announced. Delete confirms draft-only effect and restores focus predictably.
- Reorder supports drag handle only as pointer origin, keyboard Space/lift/arrows/drop/Escape, Move up/down and Move to position. Live announcements report name and position. Server save sends the complete ID list and preserves selection/scroll after success/conflict recovery.
- Three-pane layout at >=1440, reduced panes/drawers/sheets down to 768, and linear outline/form/full-screen preview below 768 follow the frozen responsive rules. Sticky save/publish bars respect safe areas/keyboards and never obscure focus/errors.
- Save/preview/export/now-or-future publish/reschedule/unpublish/delete follow J4/J5 with configured timezone, linked publication issues, `Published - changes pending`, live vs draft links, dirty navigation, version conflict preservation/copy/reload, and no optimistic destructive/publication claims.
- Initial/loading/success/empty/no-result/validation/unsupported-version/missing-reference/render/server/offline/unauthorized/session-expired/conflict states are explicit. Protected config/preview/export is cleared on expiry; request IDs are safe; no private payload appears in toast/URL/storage.

### Public registry and renderers

- Home and custom routes are Server Components using the same-origin public API through generated wrappers. Ordered initial content/metadata are server-rendered; block data is not hard-coded or client-only.
- A frontend registry maps every G2-resolved generated discriminant/version to exactly one renderer key. Backend registry, OpenAPI union, fixture manifest, frontend registry, stories, and E2E cases have bidirectional parity; unknown entries fail closed and never render raw config.
- Renderers use semantic native structure, one page `h1` policy, meaningful heading hierarchy, named links/actions, bounded lists/grids, chronological evidence, safe M7 rich text, intentional media fallbacks, decorative divider/spacer semantics, and provider-specific empty/missing-reference behavior.
- Hidden blocks and all their reference DTOs are absent, not CSS-hidden. Required missing references prevent publish; optional unavailable public targets omit or show the G3 safe fallback without revealing identity. No renderer reaches providers directly.
- Theme/layout/responsive tokens map to reviewed CSS/component variants only. Config never becomes raw class/style/HTML/URL/query/code. CSS reordering cannot change DOM/reading order; motion is nonessential and reduced-motion aware.
- Malformed/unsupported rendered DTOs produce the frozen observable section error or safe omission with request correlation, never a stack trace, raw JSON, unsafe HTML, repeated fetch loop, hydration crash, or whole-page private fallback.

## Dispatch order

1. **Blocked - Integration/root:** record separate M7 acceptance, verify G0-G1/head `0008`, release reservations, and resolve G2 without inventing a type.
2. **After G2 - `M8-T01-G`:** implement/review canonical registry, schemas/fixtures/serializer/upgraders/references, page lifecycle/operations/export, and media staging.
3. **After registry/domain evidence - Integration/root:** record G3 and reserve sole revision `0009` on `0008`.
4. **After G3 - `M8-T01-R/M`:** persistence and migration run only in disjoint files and with serialized model registration.
5. **After T01 pass - `M8-T02-A/P`:** admin/preview/export API and public Home/custom projection run in disjoint files.
6. **After T02 evidence - Integration/root `M8-T02-I`:** review registry/data/security/query/contracts, export/generate twice, compile, and record G4.
7. **After G4 - `M8-T03-A/P`:** admin builder and public renderers run concurrently only in disjoint files and named shared windows.
8. **After frontend evidence - Integration/root:** run registry parity, malicious payload, privacy/accessibility/performance/SEO review and record G5.
9. **After G5 - `M8-T03-I`:** execute J4/J5/full catalog public render/export/docs/evidence and prepare the M8 decision without releasing M9.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, identify requested milestone `M8` and trace alias `M12`, and include date, executor, environment, commit/worktree identity, tool versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Logs, DB/JSON/export fixtures, API transcripts, metadata, screenshots, and traces are sanitized and contain no cookies, CSRF/auth headers, credentials, private/draft content, provider internals, unresolved media identifiers, production dumps, or machine-specific absolute paths.

### `M8-T01` registry/domain/data evidence

Evidence must include:

- G2 resolution record and exact catalog manifest; one current/previous-version fixture per kind as applicable; registry construction/parity failures for missing/duplicate kind/version/renderer/resolver/fixture/adapter;
- property/schema tests per kind for valid round-trip/defaults/common/type-specific fields, `extra='forbid'`, discriminants, unions, variants, responsive/CTA config, canonical serialization/checksum, depth/bytes/items/strings/numbers, malformed/duplicate-key/nonfinite/Unicode payloads;
- serializer/upgrader tests for every supported edge, pure/idempotent conversion, reference preservation, unknown type/version/field failure, no GET-time write, frozen revision stability, and explicit migration/version-note behavior;
- malicious config tests for HTML/script/style/event/DOM-clobbering, unsafe/encoded URL, arbitrary class/CSS/query/code/component/renderer/provider kind, prototype-like keys, recursive/deep/wide/oversized JSON, reference mismatch/IDOR, and resource-exhaustion bounds;
- domain/property tests for Home singleton, reserved/normalized/case-collision slugs, duplicate page/block deep-copy independence, complete-list reorder permutations and missing/duplicate/foreign IDs, hide/delete/reindex, SEO/navigation, export validation, and stable errors;
- reference tests for deterministic extraction, role/cardinality/duplicate/required rules, provider facade-only validation, internal self/cycle/depth, draft/public separation, provider state changes, optional omission, required publish block, hidden-block no-resolution, and unresolved media draft-only behavior;
- publication/concurrency tests for immutable parent/children, copy-on-write deep independence, now/future DB-time, reschedule/unpublish/delete/visibility, concurrent add/duplicate/reorder/save/publish, exactly one idempotent effect/draft, rollback, cache invalidation, and audit coupling;
- migration tests for empty/`0008` upgrade, one head/current equality, schema-model parity, singleton/slug/pointer/block/reference constraints/indexes, JSONB limits, frozen child rejection, representative deep copy/export, and production role/startup behavior;
- Ruff format/lint, strict Mypy, full affected Pytest, meaningful overall/critical coverage, and no disabled test, fixture omission, or unexplained warning.

Catalog ambiguity, unknown config persistence, schema/serializer/reference drift, silent data rewrite, raw HTML/CSS/query/code execution, unsafe URL, unbounded JSON, provider repository reach-through, invalid slug/order/reference persistence, mutable frozen data, pointer/block/reference corruption, media resolution/storage behavior, lost update/duplicate effect, second migration head, failed Must requirement, or Critical/High finding blocks G3.

### `M8-T02` API/public-projection/generated evidence

Evidence must include:

- admin API tests for page list/CRUD/duplicate and every block add/update/duplicate/hide/show/delete/reorder action, lifecycle/preview/export, exact DTO/error paths, no raw JSON/ref mass assignment, auth/IDOR/CSRF/Origin, missing/stale `If-Match`, idempotent replay/mismatch/concurrency, safe request IDs, and atomic failure;
- preview/export tests for session-only `private, no-store`/noindex, canonical registry renderer, issue states, config/reference privacy, export manifest/checksum/bounds/nonpersisting validation, guessed ID/session expiry, and no metadata/sitemap/cache/log discovery;
- public Home/custom tests for eligibility/route precedence/reserved/invalid/absent parity, ordered visible union DTOs, hidden/reference omission, provider public-safe batching, staged media absence, 404 equivalence, credential non-widening, cache/schedule invalidation, metadata/canonical/Open Graph/JSON-LD/sitemap/navigation privacy;
- performance tests and representative PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)`/SQL/provider-call counts for Home/custom/sitemap/admin list/max block/reference pages, no N+1, bounded batches, stable plans, and no query-shape injection;
- OpenAPI lint/reference/security/error/example/deprecation review, exact discriminated union for every resolved kind/version, unique operation IDs, reviewed schema diff, two deterministic generations/no diff, strict generated compile, registry fixture parity, and raw-fetch/duplicate-type boundary scan.

Draft/hidden/reference/config/media leak, public route shadowing, preview/export discovery, raw JSON union escape, mass assignment/IDOR/injection, unbounded/N+1 resolver, incorrect metadata/404/cache behavior, generated/registry drift, or Critical/High finding blocks G4.

### `M8-T03` frontend/renderer/integration evidence

Admin evidence must include:

- generated-wrapper/form tests for page metadata/slug/SEO/navigation/lifecycle/export and every resolved block inspector, applicable common/type/reference fields, client hints plus server error mapping, `ETag`/idempotency/timezone/request ID behavior;
- component/story interaction tests for list/table/cards, searchable grouped palette, outline/issue counts, inspector sections, canvas/viewport controls, add/duplicate/hide/show/delete, drag/keyboard/Move reorder, save/publish panels, media staging, all async/conflict/unsupported/missing-reference states, light/dark/high-contrast/reduced-motion, narrow/400% layouts;
- keyboard-only and touch-equivalent J5 workflow with focus restoration, lift/move/drop announcements, non-drag controls, linked errors across inspector sections, dirty protection, local conflict preservation, full-screen preview/banner, confirmation and protected-state clearing.

Public evidence must include:

- one unit/story/render fixture per G2-resolved kind/version, registry/OpenAPI/frontend/story/E2E parity, supported common/type config visual effects, safe optional/required missing-reference behavior, hidden omission, provider batching, unknown-type/version fail-closed behavior;
- semantic/axe/manual checks for Home and custom pages: landmarks/one-h1/headings, lists/grids/timelines/articles/quotes/links/CTAs, rich-text code/tables, divider/spacer decoration, staged media fallback, DOM order, keyboard/focus, screen reader, 200% text/400% zoom, contrast, forced colors, motion, touch and JavaScript-disabled content;
- malicious payload browser tests proving no script/event execution, attacker request/navigation, raw HTML/config, CSS/class injection, DOM clobber, unsafe URL, hydration mutation bypass, repeated resolver loop, or private reference/content exposure across public/preview/error/export paths;
- SSR/head/cache tests for ordered Home/custom content, route precedence/404 parity, metadata/canonical/Open Graph/structured data/sitemap, publication/provider invalidation, no client-only initial content, and no hard-coded business content.

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0009`. It must prove:

- administrator creates Home/custom drafts, hits reserved/duplicate/invalid slug and malicious config/reference errors, adds/configures every G2-resolved kind, saves unresolved media only as warned draft intent, and exports a canonical validated manifest;
- block add/duplicate/hide/show/complete-reorder/delete is atomic, keyboard/touch accessible, independently copied, conflict-safe, and reflected identically by outline/preview;
- private preview renders the draft registry path with banner/issues but never leaks to public route/metadata/sitemap/cache/logs; publication blocks required media/unusable refs and succeeds for a complete publishable page;
- future publication remains absent until PostgreSQL time and works without a worker; edit-live leaves frozen public page/metadata/references unchanged until republish; reschedule/unpublish/delete/visibility/navigation behavior invalidates safely;
- public Home/custom routes render every publishable required kind in configured DOM order, omit hidden blocks and nonpublic optional targets, preserve provider/public privacy, return equivalent 404s, and use bounded SQL/provider calls;
- concurrent editors/publishers/reorders/duplicates receive conflict/idempotent behavior without overwrite, duplicate block/reference/position, or partial publication;
- unauthorized/expired actor, guessed preview/export, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, malicious JSON/HTML/CSS/URL/query/reference, stale version, and idempotency mismatch fail safely;
- API/RSC/HTML/metadata/JSON-LD/sitemap/cache/log/trace/screenshot/storage inspection finds no draft/hidden/config/reference/provider/admin/revision/pointer/unresolved-media leak;
- full affected backend/frontend/contract/migration/E2E/build/scan commands pass, generated and registry outputs remain clean, revision remains one head, and no Critical/High finding remains.

Quality/performance evidence must include Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library/Storybook/Playwright, production build, registry parity, and coverage reports. Record Server/Client Component rationale, route/editor JS and CSS bundle deltas, SSR/API/provider/SQL counts, max-page render/validation latency and memory, cache schedule behavior, and Lighthouse `/` plus representative custom-page profiles targeting performance >=90, accessibility >=95, and SEO >=95 with measured variance disposition.

Documentation/evidence must include:

- user guide for Home/custom page fields, reserved slugs, list/create/duplicate/delete, palette/inspector, every resolved block kind/common/type/reference option, add/duplicate/hide/show/reorder/delete, media staging, save/private preview/export, publish/schedule/pending changes/reschedule/unpublish, conflicts, and responsive/keyboard workflows;
- API guide for page/block/admin/public/preview/export operations, discriminated/versioned schemas, registry errors/migrations, normalized references/providers/media staging, lifecycle, auth/CSRF, filters/sorts/pagination, `ETag`/`If-Match`, idempotency, DB-time, cache/metadata/sitemap/404 privacy, and sanitized examples/cURL;
- developer/security guide for relational shell/JSONB/reference model, migration `0009`, registry/serializer/upgrader/fixture parity, bounds/threats, immutable/copy-on-write/UoW, provider batching/query plans, public SSR/renderer/cache/metadata, export format, M7 CommonMark reuse, M9 media activation, and extension procedure for a new type/version without silent migration;
- sanitized screenshots at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px plus 400% zoom for page list/mobile cards, all builder layouts, palette/outline/inspectors, every renderer, errors/issues, duplicate/reorder/media staging/status/preview/publish/conflict and public Home/custom/404/empty states in light/dark; attach registry matrix, malicious-payload, export, performance/query/bundle, SEO/metadata, accessibility, security/privacy, API, coverage, traceability, and independent-review reports.

Passing lane evidence does not authorize M9 until Integration/root records the separate M8 acceptance decision and its staged-media handoff. The M8 gate remains blocked by unresolved G2 catalog count, any failed Must requirement, disabled/suppressed check, placeholder/dead block, fake provider/storage path, unknown/unvalidated JSON or reference, raw HTML/CSS/query/code execution, unsafe URL, mutable published revision, draft/preview/future/hidden/config/reference leak, invalid/reserved slug, pointer/block/order corruption, lost update/duplicate effect, generated/registry drift, multiple migration heads, parallel migration/generated/registry/shared writer, Infrastructure overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
