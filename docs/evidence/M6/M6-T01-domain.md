# M6-T01-D - Project domain and P3 freeze

## Identity

- Requested milestone: M6; trace alias: M10
- Requirements: F1-010, F2-006; applicable API-001-API-006, SEC-004-SEC-006,
  NFR-006-NFR-008, NFR-014-NFR-018
- Executor/reviewer: Integration/root
- Environment: Windows development shell, Python 3.12.13
- Completed UTC: 2026-08-04

## P0-P2 correction and release

M1-M4 provider contracts and M5 acceptance were inspected from the current worktree. The audit
found that M5 documentation named an `ExperienceReferenceFacade` that did not exist. M5 was reopened
for that provider defect. The facade now returns provider-owned admin identity/status facts and
nests public company/role data only when PostgreSQL-time eligibility is true. Duplicate/missing IDs
fail the complete set. Ruff, strict Mypy, 28 experience domain/service tests, and 3 PostgreSQL
repository tests pass. P2 was reaccepted after this correction; the sole head remains `0006`.

## P3 frozen project contract

### Stable identity and content

- Slugs normalize Unicode input to ASCII lowercase kebab case, match
  `^[a-z0-9]+(?:-[a-z0-9]+)*$`, are 1-80 characters, and are immutable after creation. Case-insensitive
  uniqueness is reserved transactionally. Because slugs never change, a draft edit cannot alter a
  live route or create old-slug cache ambiguity.
- Required bounded fields are name, short/full description, problem, solution, measurable impact,
  owner role/contribution, architecture, at least one ordered technology, status, and start date.
- Status is exactly `planned`, `active`, `paused`, `completed`, `maintenance`, or `archived`.
  Planned/active/maintenance require an open end; completed/archived require an end; paused may have
  an optional end. Every end is on/after start.
- Case-study fields store controlled CommonMark source. Raw HTML and unsafe Markdown destinations
  are rejected; fixed rendering/sanitization remains mandatory at the frontend boundary.
- Repository, demo, and optional canonical links are credential-free, fragment-free HTTPS URLs.
  SEO falls back deterministically to public name/short description.

### Aggregate, lifecycle, and relations

- Stable aggregate fields are slug, visibility, featured, position, draft/published pointers,
  schedule/unpublish/delete timestamps, and optimistic version. All case-study/SEO/link/date/status
  content and ordered skill/experience/project relations belong to revisions.
- Publish freezes the draft and creates one identical mutable copy in one UoW. Scheduling uses
  PostgreSQL time without a worker. Reschedule, unpublish, visibility, featured, reorder, and delete
  remain distinct actions. Pending state derives from complete draft/publication equality.
- Skills and experiences resolve only through the accepted M4/M5 facades. Deleted provider targets
  fail. Hidden/nonpublic optional targets remain admin-only warnings and have no nested public
  summary.
- Related projects are ordered stable IDs. Duplicates, self edges, missing/deleted targets, and a
  directed cycle of any length fail. The persistence port freezes a transaction-time bounded graph
  check at 256 visited nodes; publication rechecks the graph.
- No reverse provider rows are added to skills or experiences.

### Media staging

`cover_media_id` is nullable and `screenshot_media_ids` may be empty for forward contract
compatibility. Every non-null/nonempty value fails with `capability_unavailable` until the accepted
M9 media facade exists. M6 persists no URL, path, filename, blob, base64 value, object key, dangling
media ID, storage provider, media table, or outbound media request.

## Verification

Ruff format/check and Mypy 2.3.0 strict pass the project domain/application/port sources and tests.
Pytest 9.1.1 passes 34 focused tests covering normalization, content/Markdown/URL/SEO bounds,
status/date combinations, ordered relations, media rejection, immutable revisions, lifecycle,
authorization-ready commands, slug collision, missing targets, bounded cycles, copy-on-write,
idempotent publication/reorder, independent flags/actions, public relation filtering, and provider
facades. Alembic reports the pre-reservation sole head `20260802_0006`.

## Decision

P3 passes and reserves exactly `backend/migrations/versions/20260802_0007_projects.py` with
`down_revision = 20260802_0006`. This is not P4, P5, T01, or M6 acceptance.
