# M5-T01-A - Administrator and preview API

## Outcome

Pass. Eleven admin operations implement list, create, get, draft replacement, complete reorder,
preview, visibility, publish/schedule, reschedule, unpublish, and confirmed soft delete. They use
the shared session, CSRF/origin, envelope, request-ID, ETag/If-Match, idempotency, pagination,
filter/sort, and error contracts.

Preview is authenticated, `private, no-store`, and `noindex, nofollow`. Reads and mutations do not
expose secret material in errors. Tests cover missing/forced-password sessions, CSRF/origin,
authorization/IDOR, unknown/malformed fields and skill IDs, mass assignment, stale ETags,
idempotency replay/payload conflict, lifecycle transitions, reorder conflicts, and safe errors.

The exported OpenAPI 3.1 document validates with 44 operations across 31 paths. It regenerated with
the typed TypeScript client twice without drift; the frozen OpenAPI SHA-256 is
`191663B7A6D0A360C6FD8F831A9A808E71A3BAE70ED20C0CA1F71B07E720B4E9` and the client contains 106
files. Frontend typecheck consumes that generated boundary successfully.
