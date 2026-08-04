# M6-T01-A - Administrator and preview API

## Outcome

Pass. Fourteen project operations are present across eleven paths in the validated OpenAPI
contract. The administrator surface covers filtered list, create, read/update, reorder, preview,
featured, visibility, publish, reschedule, unpublish, and soft delete. Preview requires a full
session, is private/no-store, and returns both `X-Robots-Tag: noindex, nofollow` and an explicit
nonpublic banner.

All input models forbid extra fields. Unsafe methods use the accepted CSRF/Origin boundary;
aggregate mutations require `If-Match`; effect-producing create/reorder/publication operations use
digest-only idempotency. Stable safe errors map validation, missing provider/project references,
cycles, slug conflicts, stale versions, frozen content, and idempotency mismatch without exposing
SQL, pointers, storage, or credentials.

## Verification

The four real PostgreSQL/FastAPI integration tests exercise full create/preview/publish, public
isolation, copy-on-write/republish, feature/show-hide/unpublish/delete, scheduling/rescheduling,
ordering, stale/missing preconditions, idempotent replay/mismatch, anonymous preview denial,
injection-shaped queries, unsafe URLs, media placeholders, and mass-assignment rejection.

Unit transport tests additionally prove public/admin schema mapping, safe error mapping, operation
security metadata, and query catalogs. The complete backend candidate previously passed 274 tests
at the configured 85% branch threshold; the final migration/repository corrections pass their
affected suites without relaxing a gate.
