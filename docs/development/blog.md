# Blog slice architecture

The Blog is a complete modular-monolith vertical slice. Domain/application contracts live under
`backend/app/modules/blog`; SQLAlchemy records and UoW adapters live in
`backend/app/infrastructure/database/blog*.py`; dedicated admin/public API modules expose the
slice. Frontend routes and components live under `frontend/src/features/blog` and call only the
generated OpenAPI boundary.

## Controlled content boundary

`backend/app/common/content_policy.py` is the sole CommonMark parsing and sanitization authority.
The frozen `upw-commonmark` policy uses `markdown-it-py`, selected `mdit-py-plugins` extensions, and
`nh3`. It canonicalizes newlines, rejects raw HTML/images/embeds/unsafe URLs and control variants,
demotes source headings beneath the page title, adds safe link attributes, derives reading time,
and returns rendered HTML only with policy name/version and a SHA-256 source checksum.

The malicious corpus is versioned in `backend/tests/fixtures/content_policy_malicious.json` and is
exercised by policy, API, frontend render-boundary, and browser tests. Frontend blog content has one
audited HTML sink in `safe-rendered-content.tsx`; its prop is the generated
`SafeRenderedContentData` type. Do not add a client Markdown parser, generic trusted-HTML prop,
runtime plug-in, DOM rewrite, or unsafe fallback. CSP remains defense in depth, not the sanitizer.

## Aggregate, revisions, and taxonomy

`post` is the stable route/order/visibility aggregate. `post_revision` owns source, render
derivations, author, excerpt, SEO, tags, categories, and related posts. The aggregate points to one
mutable draft and optionally one frozen publication. Deferrable same-owner foreign keys and
PostgreSQL triggers protect pointer integrity and reject updates/deletes of frozen revisions and
their owned relation rows.

Publishing is copy-on-write inside the application-owned unit of work. Repositories flush but do
not commit. The service owns authorization, optimistic concurrency, digest-only idempotency,
relation validation, audit facts, and the final commit. A schedule is a `publish_at <= now()` query
predicate using database time; do not introduce a status-flipping worker.

Tags and categories have distinct kinds, stable normalized slugs, visibility, deterministic order,
and soft deletion. Retained revision usage blocks taxonomy deletion. Related posts use stable IDs,
reject duplicates/self/deleted targets, and expand only one bounded public-summary level; they do
not need recursive graph traversal.

## Public projection, metadata, and extension points

Public queries join only effective frozen revisions and return explicit allow-listed DTOs. Source,
creator, revision pointers, versions, future schedules, hidden taxonomy, and nonpublic related
targets never cross the boundary. `/blog` and `/blog/{slug}` are Server Components. The generated
public wrapper supplies content, canonical/Open Graph metadata, escaped Article JSON-LD, and
sitemap routes; request caching avoids duplicate detail reads.

Cover media accepts a ready M9 asset and materializes revision-scoped usage; public delivery follows
the current published post pointer without mutating frozen revisions. Configurable pages reuse the
revision/content-policy pattern instead of forking it. Future AI features may consume
approved application facades later, but no AI runtime, model SDK, prompt store, or user-facing AI
behavior belongs in this slice.

## Migration and verification

The sole migration is `backend/migrations/versions/20260802_0008_blog.py`, directly after `0007`.
Future changes require a new linear migration after the accepted head. Application startup never
migrates, seeds, bootstraps, rewrites content, or starts a scheduler.

Focused verification covers policy/domain/service tests, `test_blog_repository.py`,
`test_0008_blog.py`, `test_blog_api.py`, blog component tests/stories, and
`frontend/tests/e2e/blog.spec.ts`. The database tests deliberately use separate owner and runtime
URLs; schema fixtures reconcile DML grants while keeping `alembic_version`, audit mutation, and
functions restricted. After an intentional API change, export/validate OpenAPI, regenerate the
client twice, compare exact trees, and compile strict TypeScript. The complete evidence index is
under `docs/evidence/M7`.
