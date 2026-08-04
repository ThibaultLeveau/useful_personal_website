# API Structure and Conventions

## Namespace and audiences

All business APIs live under `/api/v1`. OpenAPI is the source for the generated TypeScript client (`API-001`, `API-002`). Endpoints are grouped by exposure rather than relying on callers to remember filters:

- `/api/v1/public/*`: unauthenticated, publication-safe, cacheable projections;
- `/api/v1/admin/*`: administrator cookie session plus CSRF on unsafe methods;
- `/api/v1/integrations/*`: bearer API token and required scopes;
- `/api/v1/auth/*`: login/logout/session/password/CSRF lifecycle;
- `/api/v1/health/live` and `/api/v1/health/ready`: operational probes.

Admin and integration endpoints can share application services but have distinct transport schemas/policies. Contact data has no public route. API tokens never authenticate browser admin pages.

## Representative endpoint map

| Area | Public | Admin | Integration scope examples |
|---|---|---|---|
| profile/settings/nav | `GET /public/site`, `/public/profile`, `/public/navigation` | `GET/PATCH /admin/...` | read `content:read`, write `content:write` |
| skills | `GET /public/skills` | CRUD, reorder, category endpoints | `content:read` / `content:write` |
| experiences | list/detail published | CRUD, preview, publish, unpublish | content scopes |
| projects | list/detail published | CRUD, relations/media, preview/publication | content scopes |
| blog | posts, tags, categories | CRUD/taxonomy/preview/publication | content scopes |
| pages | `GET /public/pages/{slug}` | CRUD/duplicate/blocks/reorder/preview/publication | content scopes |
| media | public metadata/content for publicly used assets | upload/search/detail/delete/content | `media:read` / `media:write` |
| contacts | `POST /public/contact-submissions` only | list/detail/state/delete | `contacts:read` (read/state); no token delete in R1 |
| tokens | none | create/list/rotate/revoke | browser administrator only |
| audit/health | none | safe audit list/detail, safe health summary | `admin:read` |

Mutations use explicit action subresources when they are domain transitions: `POST /projects/{id}/publish`, `POST /.../unpublish`, `POST /tokens/{id}/rotate`, `POST /contacts/{id}/archive`. CRUD methods remain conventional. Duplicate is `POST /pages/{id}/duplicate` and returns `201`.

## Success and error envelopes

Single-resource success:

```json
{
  "data": { "id": "...", "version": 4 },
  "meta": { "request_id": "01K..." }
}
```

List success:

```json
{
  "data": [],
  "meta": {
    "request_id": "01K...",
    "pagination": { "page": 1, "page_size": 20, "total_items": 0, "total_pages": 0 }
  }
}
```

Errors always use (`API-006`):

```json
{
  "error": {
    "code": "RESOURCE_VERSION_CONFLICT",
    "message": "The resource changed since it was loaded.",
    "details": { "fields": [] },
    "request_id": "01K..."
  }
}
```

`details` is an object and contains only safe, typed data. Validation errors include `fields: [{"path":"body.title","code":"required","message":"..."}]`. Production never exposes exception class names, SQL, stack traces, secret values, or object existence that the actor cannot access.

## Status and error mapping

| HTTP | Use | Example stable codes |
|---:|---|---|
| 400 | malformed semantics/action | `INVALID_REQUEST`, `SLUG_RESERVED` |
| 401 | absent/invalid/expired authentication | `AUTHENTICATION_REQUIRED`, `TOKEN_INVALID` |
| 403 | authenticated but unauthorized/CSRF | `SCOPE_REQUIRED`, `CSRF_INVALID` |
| 404 | absent or not visible to actor | `PROJECT_NOT_FOUND` |
| 409 | uniqueness/state/version conflict | `SLUG_CONFLICT`, `MEDIA_IN_USE`, `RESOURCE_VERSION_CONFLICT` |
| 413/415 | upload size/type | `UPLOAD_TOO_LARGE`, `MEDIA_TYPE_UNSUPPORTED` |
| 422 | field/domain validation | `VALIDATION_FAILED`, `EXPERIENCE_DATE_INVALID` |
| 429 | rate limit | `RATE_LIMITED` plus `Retry-After` |
| 500/503 | safe internal/unavailable | `INTERNAL_ERROR`, `DEPENDENCY_UNAVAILABLE` |

## Pagination, filtering, and sorting

R1 consistently uses page-number pagination: `page` default 1; `page_size` default 20, maximum 100 (`API-004`, ADR-0003). Invalid/out-of-range parameters return 422. `total_items` and `total_pages` are always present. Empty datasets return page 1 with zero totals. A requested page beyond the last returns an empty list, not 404.

Each endpoint declares allow-listed query parameters and maps them to typed SQLAlchemy expressions. Sorting uses `sort=field,-other_field`; unsupported/duplicate fields fail validation. Every sort appends `id` as a deterministic tie-breaker. No generic expression language, column name interpolation, or arbitrary `filter[...]` is accepted (`API-005`, `SEC-006`).

## Dates, naming, IDs, and concurrency

- JSON property names are `snake_case`, matching generated Python/TypeScript contracts.
- Timestamps are RFC 3339 ISO 8601 with `Z`; calendar dates are `YYYY-MM-DD`; writes with ambiguous local timestamps are rejected. The admin UI converts the configured IANA timezone to UTC before submission.
- IDs are opaque UUID strings. Clients must not infer order or type from them.
- Mutable admin resources return an `ETag` derived from integer version. Update/delete/action requests require `If-Match`; absent is `428 PRECONDITION_REQUIRED`, stale is 409.
- Create operations that can be retried (contact submit, token rotate, publish) accept `Idempotency-Key`; keys are scoped to actor+route and retained for 24 hours without storing private response bodies unnecessarily.

## Authentication and authorization

Admin endpoints use the `__Host-admin_session` Secure/HttpOnly/SameSite=Lax cookie. Unsafe methods also require `X-CSRF-Token` and trusted `Origin`. Integration endpoints use `Authorization: Bearer <token>` and map each route to one or more documented scopes. Public endpoints accept neither credential as a way to reveal drafts. Every use case performs resource/action authorization, not only router protection (`SEC-004`).

Token scope semantics:

- `content:read`: admin-grade reads of non-sensitive content, including drafts only where route explicitly allows it;
- `content:write`: content mutations and publication, never token/security/contact administration;
- `media:read` / `media:write`: media metadata/content operations;
- `contacts:read`: contact listing/detail and read/archive state, not hard deletion/export;
- `admin:read`: safe audit/system information;
- no API token can create/revoke tokens, change passwords, bootstrap admins, or access sessions.

The route-to-scope matrix is tested and emitted in API documentation (`F2-017`, `API-008`).

## Caching and publication privacy

Public GET responses may use `ETag` and bounded `Cache-Control` with tag/path invalidation after writes. Draft/admin/contact/token/audit/auth responses use `private, no-store`. Public list/detail schemas never contain draft revision IDs, private profile fields, storage keys, or administrator email. Sitemap and metadata generators call the same public query endpoints and use database time for publication gates.

## OpenAPI and compatibility

Every operation declares response envelopes, stable operation ID, security scheme, errors, filters/sorts, examples, and deprecation metadata. CI validates OpenAPI, checks operation-ID uniqueness, generates the TypeScript client, and fails on uncommitted generated changes. R1 makes additive compatible changes within v1; removals/semantic breaks require a deprecation window and a new version/approved change record (`CHG-002`).

## Health contracts

- `GET /health/live`: process response only, `{status: "ok"}`, no dependency calls.
- `GET /health/ready`: 200 `ready` only if PostgreSQL is reachable and migration revision compatible; otherwise 503 `not_ready` with a safe dependency category, not connection details.
- authenticated admin health adds build version, commit, and safe aggregate statuses. It never returns hostnames, credentials, SQL, environment dumps, or stack traces (`F2-020`).
