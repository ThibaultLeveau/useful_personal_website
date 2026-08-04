# API conventions

This document is the human-readable contract for the release-1 API baseline established by
Milestone 2 (`M2`, trace milestone `M05`). The executable source is FastAPI, and the canonical
machine-readable contract is [OpenAPI 3.1](openapi.json).

## Base URL, version, and discovery

All application operations use same-origin paths below `/api/v1`. A deployment at
`https://portfolio.example` therefore serves the API at `https://portfolio.example/api/v1`; browser
code should use relative paths. The interactive schema is `/api/v1/docs`, and the JSON schema is
`/api/v1/openapi.json`.

Version `v1` is part of the path. Clients must not infer a backend service hostname or call the
private container network directly. The checked-in TypeScript client is generated from the same
OpenAPI document and is consumed through the handwritten wrapper in `frontend/src/lib/api`.

## Audiences and authentication

- Health liveness/readiness are unauthenticated operational probes and expose no infrastructure
  coordinates.
- `/api/v1/auth/*` implements the administrator browser-session lifecycle.
- `/api/v1/admin/*` requires a valid administrator cookie session. Unsafe methods additionally
  require an exact trusted `Origin` and the session-bound `X-CSRF-Token` value.
- `/api/v1/public/*` and `/api/v1/integrations/*` are reserved audience namespaces. They have no
  shipped M2 operations; later milestones must document every public projection or token scope
  before adding one.

See [browser administrator authentication](authentication.md) and the reviewed
[route/security catalog](catalogs.md).

## Success and error envelopes

A single-resource success always contains `data` and request correlation metadata:

```json
{
  "data": { "status": "ok" },
  "meta": { "request_id": "docs-request-id-0001" }
}
```

A collection success uses an array and exact pagination metadata:

```json
{
  "data": [],
  "meta": {
    "request_id": "docs-request-id-0001",
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 0,
      "total_pages": 0,
      "has_previous": false,
      "has_next": false
    }
  }
}
```

Every failure uses one safe envelope:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request contains invalid fields.",
    "details": {
      "fields": [
        {
          "path": "query.page",
          "code": "range",
          "message": "Value is invalid."
        }
      ]
    },
    "request_id": "docs-request-id-0001"
  }
}
```

`details` is always an object. Validation details contain only bounded paths and catalog codes; the
server does not reflect rejected values. SQL, stack traces, exception classes, credentials,
connection strings, raw response bodies, and hidden-resource existence never belong in an error.
The stable code/status registry is in [catalogs](catalogs.md#error-catalog).

## Request correlation

Clients may send `X-Request-ID` using 16-128 ASCII letters, digits, `.`, `_`, or `-`, beginning with
an alphanumeric character. Invalid or absent values are replaced with a random 128-bit identifier.
The accepted/generated value is returned in `X-Request-ID` and in `meta.request_id` or
`error.request_id`. Use it for support and log correlation; do not place secrets or personal data in
it.

## Pagination, filtering, and sorting

Collections use page-number pagination:

| Parameter   | Default | Allowed                  |
| ----------- | ------: | ------------------------ |
| `page`      |     `1` | positive base-10 integer |
| `page_size` |    `20` | integer `1`-`100`        |

Totals are exact. Empty collections return page 1 with zero totals. A page beyond the last returns
an empty `data` array with the actual totals, not `404`.

Each operation owns an allow-list of direct filter keys. Arbitrary `filter[...]`, expression
languages, SQL fragments, unknown parameters, and duplicate parameters are rejected with `422`.
Sorting uses a single comma-separated value such as `sort=created_at,-title`; `-` means descending.
Unsupported or repeated sort fields are rejected, and the server appends ascending `id` when absent
to make ordering deterministic. M2 ships the parser/persistence contract but no collection
operation, so the current per-operation filter/sort catalog is empty. Later operations must add
their exact catalog to OpenAPI and [catalogs](catalogs.md) before release.

## Names, dates, and identifiers

- JSON properties and query keys use `snake_case`.
- Instants are timezone-aware RFC 3339 UTC values; outbound domain timestamps use `Z`.
- Calendar-only values use `YYYY-MM-DD` and are not silently converted to instants.
- IDs are canonical hyphenated opaque UUID strings. Their value conveys no ordering, type, or
  database location.
- Undeclared object fields are rejected by API models.

## Optimistic concurrency

Mutable resources use a positive integer version rendered as a strong ETag, for example `"v4"`.
An update, delete, or action must send exactly one current `If-Match` value. A missing value returns
`428 PRECONDITION_REQUIRED`; malformed, weak, wildcard, or list syntax returns `400 BAD_REQUEST`;
a stale value returns `409 RESOURCE_VERSION_CONFLICT` with only safe current-version facts.

No mutable content resource ships in M2. Consumers must use this behavior only where an operation's
OpenAPI response declares `ETag` and its request declares `If-Match`.

## Idempotency

Retry-safe commands declare `Idempotency-Key` in their operation contract. Keys are opaque 16-128
character values limited to ASCII letters, digits, `.`, `_`, `~`, and `-`. Admission is scoped to
the authenticated actor, canonical route template, and key for 24 hours:

- same key and same canonical request replays the safe completed outcome;
- same key and different request returns `409 IDEMPOTENCY_CONFLICT`;
- a concurrent unfinished request returns `409 IDEMPOTENCY_IN_PROGRESS`;
- the command effect and completion record commit in the caller's transaction.

Persistence stores one-way SHA-256 actor/key/request fingerprints and bounded outcome metadata. It
does not store the plaintext key, submitted payload, credential, or response body. M2 establishes
this provider contract; no current HTTP operation advertises `Idempotency-Key` yet.

## Rate limits

Rate policies are endpoint-specific and PostgreSQL-backed. A rejected request returns
`429 RATE_LIMITED` plus a positive integer `Retry-After` header in seconds. Consumers should wait at
least that duration and avoid parallel automatic retries. The current shipped rate policy protects
administrator login; later public or integration routes must publish their own policy without
revealing anti-abuse internals.

## Cache behavior

| Response class                    | Cache contract                                          |
| --------------------------------- | ------------------------------------------------------- |
| Liveness/readiness success        | `Cache-Control: no-store`, `Pragma: no-cache`           |
| Administrator health/auth success | `Cache-Control: private, no-store`, `Pragma: no-cache`  |
| API errors                        | `Cache-Control: private, no-store`, `Pragma: no-cache`  |
| Future public reads               | Operation-specific, only after public-projection review |

Credentials and protected responses must never enter a shared cache. Operational monitors must use
the response they just received rather than a cached readiness result.

## Compatibility and change policy

Within `v1`, additions are compatible only when existing required fields, error semantics,
authorization, ordering, and side effects remain unchanged. New optional fields and new operations
still require OpenAPI export, generated-client regeneration, wrapper tests, and consumer review.
Removal, renaming, type/meaning changes, narrower accepted inputs, or changed authorization require
deprecation plus an approved `CHG-002` impact record and, when compatibility cannot be preserved, a
new API version. Generated files are never edited by hand.

## Minimal cURL examples

```console
curl --fail-with-body \
  --header "Accept: application/json" \
  --header "X-Request-ID: docs-request-id-0001" \
  https://portfolio.example/api/v1/health/live
```

```console
curl --silent --show-error \
  --header "Accept: application/json" \
  --write-out "\nHTTP %{http_code}\n" \
  https://portfolio.example/api/v1/health/ready
```

For protected health, first complete the documented same-origin authentication flow and use a
temporary cookie jar with restrictive filesystem permissions; never paste a session cookie into a
URL, command history, issue, or committed file.
