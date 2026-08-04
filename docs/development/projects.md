# Project slice architecture

Projects are a complete modular-monolith vertical slice. Domain/application types and use cases
live under `backend/app/modules/projects`; SQLAlchemy records and UoW adapters live under
`backend/app/infrastructure/database/projects*.py`; dedicated admin/public transport modules expose
the slice. Frontend routes and components live under `frontend/src/features/projects` and consume
only the generated OpenAPI client boundary.

## Aggregate and immutable revisions

`project` is the stable route/display aggregate. `project_revision` owns all case-study, date,
status, link, SEO, technology, skill, experience, and related-project data. The aggregate points to
one mutable draft and optionally one frozen publication. Deferrable same-owner foreign keys protect
both pointers; PostgreSQL triggers reject update/delete of a frozen revision and every owned row.

Publishing is copy-on-write in one application-owned unit of work. Repositories flush but never
commit. The service owns authorization, optimistic concurrency, digest-only idempotency, relation
validation, audit facts, and the final commit. Scheduled eligibility remains a query predicate over
PostgreSQL `now()`; do not introduce a status-flipping worker.

Skills and experiences are consumed through `SkillReferenceFacade` and
`ExperienceReferenceFacade`, never provider ORM/repositories. Related projects use stable IDs and a
transaction-scoped advisory lock plus a bounded graph traversal. Self edges and duplicate targets
also have database constraints. Draft relations are revision-owned and cannot mutate live ones.

## Public queries, metadata, and media boundary

Public list/detail queries join only the effective frozen publication. One list page is bounded to
seven SELECTs: page, exact count, revisions, technologies, skills, experiences, and related
projects. Slug and ordered relation lookups use dedicated indexes; case-insensitive technology
filtering uses the `lower(value), revision_id` expression index. Search remains bounded and
allow-listed. Public DTOs are explicit allow-lists.

The `/projects/{slug}` Server Component reuses the generated public projection for content,
metadata, canonical URL, and escaped CreativeWork JSON-LD. React request caching deduplicates the
metadata/page detail read. Dynamic metadata is delivered in the initial document head for crawler
compatibility. Draft/preview routes are private, no-store, noindex/nofollow, and use a distinct
admin projection.

Media fields are a forward-compatible handoff only: null cover and empty screenshot collections
are accepted; every other value fails. Do not add a storage table, URL/path escape hatch, fake
picker, or outbound fetch before the accepted media facade is available. The public UI renders a
semantic reserved-geometry fallback.

## Migration and validation workflow

The sole migration is `backend/migrations/versions/20260802_0007_projects.py`, directly after
`20260802_0006`. Future schema changes require a new linear migration after the released revision;
never create a second head. Before release, verify empty and prior-head upgrades, model parity,
pointer/trigger/constraint/index behavior, downgrade, runtime-role isolation, and representative
query plans.

After an intentional API change, export and validate `docs/api/openapi.json`, regenerate
`frontend/src/generated/api` twice, require identical trees, and run strict TypeScript. Handwritten
frontend code must not use raw fetch types or edit generated files.

Focused validation covers:

- `backend/tests/unit/test_projects_domain.py` and `test_projects_service.py`;
- `backend/tests/database/test_projects_repository.py` and
  `backend/tests/migrations/test_0007_projects.py`;
- `backend/tests/integration/test_projects_api.py`;
- project tests and stories beside `frontend/src/features/projects`;
- `frontend/tests/e2e/projects.spec.ts` against migrated production images.

Create browser fixtures through APIs/UI, not the demo seed. Application startup must never migrate,
seed, bootstrap an administrator, or run a scheduler. The evidence boundary is indexed under
`docs/evidence/M6`.
