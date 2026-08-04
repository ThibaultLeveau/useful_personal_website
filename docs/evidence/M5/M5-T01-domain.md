# M5-T01-D - Experience domain and application

## Outcome

Pass. The aggregate owns independent visibility, a mutable draft, an optional frozen publication,
database-time schedule metadata, deterministic position, soft deletion, and optimistic version.
Revision-owned content and skill references are validated before persistence. Publish is atomic
copy-on-write; later draft edits cannot alter the live revision.

The closed catalogs are nine employment types and `onsite`, `hybrid`, or `remote`. Employment dates
are calendar dates. Current positions cannot have an end date; noncurrent positions may have an
unknown end date. Company URLs are credential-free HTTPS URLs. Ordered values are bounded plain
text, preserve order, and reject empty/normalized duplicates.

## Boundaries and security

- Every admin use case requires an accepted administrator actor.
- M4 skills are reached only through `SkillReferenceFacade`; no skills persistence type leaks in.
- Create, publish, reschedule, unpublish, and reorder use the shared digest-only idempotency store.
- Mutations use aggregate version preconditions and controlled audit facts.
- Public projection types have an explicit allow-list and no draft, creator, pointer, schedule,
  deletion, audit, or version field.
- No scheduler, worker, outbox, project/media/blog/page/token, or speculative AI behavior was added.

## Verification

The authoritative full backend run passed 226 tests in 589.80 seconds at 85.30% branch coverage.
Focused domain and service cases cover date/content validation, safe URLs, frozen revisions,
copy-on-write, pending-change derivation, skill resolution, authorization, concurrency,
idempotency replay/conflict, reorder completeness, visibility, scheduling, unpublishing, deletion,
and public privacy. Ruff 0.16.1 and Mypy 2.3.0 strict pass the final 138/129-file scopes.

The subsequent M6 provider audit added the previously documented but missing
`ExperienceReferenceFacade`. It returns complete admin identity/status facts and nests public
company/role data only when PostgreSQL-time eligibility is true. Duplicate or missing IDs fail the
complete set. The correction passes Ruff, strict Mypy, 28 focused service/domain tests, and 3
PostgreSQL repository tests.

Findings corrected before acceptance: copied drafts initially derived pending status from pointer
identity rather than value equality; reorder coverage lacked complete/duplicate/incomplete/replay
cases; both received regression tests. No waiver remains.
