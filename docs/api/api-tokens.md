# API tokens and integration scopes

Administrator sessions alone manage tokens below `/api/v1/admin/api-tokens`. Create and rotate responses reveal a `pp_live_<public_id>.<secret>` credential exactly once and use `private, no-store`; later list/detail responses expose only name, public selector, six-character suffix, scopes, timestamps, status, and version. Mutations require Origin, CSRF, and `If-Match` where applicable.

Integration clients send the complete credential only in `Authorization: Bearer …`. Query parameters, cookies, browser administration, token management, sessions, password operations, contact deletion, and unspecified routes never accept API tokens.

| Integration route | Scope | Behavior |
| --- | --- | --- |
| `GET /api/v1/integrations/projects` | `content:read` | Paginated private project metadata, with the same allow-listed filters as administration. |
| `GET /api/v1/integrations/projects/{id}` | `content:read` | One private project projection. |
| `GET /api/v1/integrations/contacts` | `contacts:read` | Paginated private contact summaries. |
| `GET /api/v1/integrations/contacts/{id}` | `contacts:read` | One private contact detail. |

The initial catalog also reserves `content:write`, `media:read`, `media:write`, and `admin:read`. They grant nothing until a separately reviewed integration route is added. Scopes have no wildcard or prefix implication. Unknown, expired, revoked, rotated, wrong-key-version, and under-scoped tokens all fail with the same credential error.
