# Site configuration API

Milestone M3 exposes separate administrator resources and deliberately smaller public projections.
The canonical schemas and examples remain the generated [OpenAPI document](openapi.json); this page
explains the behavioral contract for human consumers.

## Operations

| Method and path                    | Authentication                          | Concurrency                                     | Cache                                  |
| ---------------------------------- | --------------------------------------- | ----------------------------------------------- | -------------------------------------- |
| `GET /api/v1/admin/profile`        | Administrator session                   | Returns `ETag`                                  | `private, no-store`                    |
| `PUT /api/v1/admin/profile`        | Session, Origin, CSRF                   | Requires `If-Match`                             | `private, no-store`                    |
| `GET/PUT /api/v1/admin/settings`   | Same as profile                         | `PUT` requires `If-Match`                       | `private, no-store`                    |
| `GET/PUT /api/v1/admin/navigation` | Same as profile                         | `PUT` requires `If-Match` and `Idempotency-Key` | `private, no-store`                    |
| `GET/PUT /api/v1/admin/footer`     | Same as profile                         | `PUT` requires `If-Match` and `Idempotency-Key` | `private, no-store`                    |
| `GET /api/v1/public/profile`       | None; credentials do not broaden output | N/A                                             | Public, bounded stale-while-revalidate |
| `GET /api/v1/public/site`          | None; credentials do not broaden output | N/A                                             | Public, bounded stale-while-revalidate |
| `GET /api/v1/public/navigation`    | None; credentials do not broaden output | N/A                                             | Public, bounded stale-while-revalidate |

Administrator `PUT` requests use the conventions in [API conventions](conventions.md). A missing
precondition returns `428`; a stale version returns `412` and never overwrites the newer resource.
Tree replacements replay safely only when the same idempotency key and canonical payload match.

## Privacy and settings boundaries

The administrator profile contains values plus an explicit `public_fields` selection. The public
profile is an allow-list projection: an unapproved field is absent, not `null`, masked, or copied
into metadata. Supplying administrator credentials to a public endpoint does not reveal more.

Website settings accept presentation and public metadata only. Credential-like property names,
unknown analytics providers or fields, scripts/HTML, database or storage identifiers, and extra
properties are rejected. The analytics value is a provider-specific public identifier, never a
secret or script-injection surface.

## Link, tree, and ordering rules

- Internal links are canonical root-relative registered routes. Unknown, encoded-bypass,
  protocol-relative, and unpublished destinations are rejected.
- External links require HTTPS without credentials or control characters. Internal links always
  use the same window; a new-window external link is emitted with safe `rel` behavior by the UI.
- Navigation permits top-level items and one child level only. Self-parenting, cycles, orphans,
  foreign IDs, and depth greater than two fail the complete replacement atomically.
- Navigation siblings, footer columns, and footer items use zero-based contiguous order. The API
  normalizes a valid submitted order deterministically and rejects duplicate or missing identities.
- Hidden parents and hidden footer columns suppress their descendants from public projections.

## Safe request examples

Public reads contain no authentication material:

```console
curl --fail-with-body --header "Accept: application/json" \
  http://localhost:8000/api/v1/public/profile
```

For an authenticated update, first read the resource and retain its response `ETag`. The browser
client sends the administrator session cookie, readable CSRF-cookie value, exact `Origin`, request
ID, and precondition through the same-origin frontend proxy. Never paste those values into logs,
documentation, or support requests.

```http
PUT /api/v1/admin/profile HTTP/1.1
Accept: application/json
Content-Type: application/json
If-Match: "opaque-current-version"
Origin: https://portfolio.example
X-CSRF-Token: [browser-cookie-value]
X-Request-ID: 0123456789abcdef0123456789abcdef

{"full_name":"Example Owner","public_fields":["full_name"]}
```

Errors use the shared safe envelope and request ID. Validation details use stable field paths;
responses never include SQL, stack traces, credentials, private resource snapshots, or raw rejected
headers. See [authentication](authentication.md) for session and CSRF behavior.
