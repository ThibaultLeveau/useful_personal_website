# API route and error catalogs

This catalog reflects the current canonical OpenAPI artifact. Planned namespaces or codes are not active
capabilities until they appear in that artifact and pass the contract gate.

## Route and security catalog

| Method and path                     | Operation ID            | Audience and controls                                        | Cache                                       |
| ----------------------------------- | ----------------------- | ------------------------------------------------------------ | ------------------------------------------- |
| `GET /api/v1/health/live`           | `health_live`           | Anonymous; process-only, no dependency access                | `no-store`                                  |
| `GET /api/v1/health/ready`          | `health_ready`          | Anonymous; database connectivity and migration compatibility | `no-store` success; errors no-store/private |
| `POST /api/v1/auth/login`           | `auth_login`            | Anonymous; exact trusted `Origin`; rate limited              | `private, no-store`                         |
| `GET /api/v1/auth/session`          | `auth_session_get`      | `AdminSessionCookie`                                         | `private, no-store`                         |
| `POST /api/v1/auth/session/refresh` | `auth_session_refresh`  | Cookie, exact `Origin`, `X-CSRF-Token`                       | `private, no-store`                         |
| `POST /api/v1/auth/password/change` | `auth_password_change`  | Cookie, exact `Origin`, `X-CSRF-Token`                       | `private, no-store`                         |
| `POST /api/v1/auth/logout`          | `auth_logout`           | Cookie, exact `Origin`, `X-CSRF-Token`                       | `private, no-store`                         |
| `GET /api/v1/admin/health`          | `admin_health_get`      | Full administrator session; forced password change completed | `private, no-store`                         |
| `GET /api/v1/public/skills`         | `public_skills_list`    | Anonymous; visibility-enforced public projection             | shared cache; 60-second freshness           |
| `/api/v1/admin/skill-categories*`   | `admin_skill_category*` | Full administrator session; Origin/CSRF on unsafe methods    | `private, no-store`                         |
| `/api/v1/admin/skills*`             | `admin_skill*`          | Full administrator session; Origin/CSRF on unsafe methods    | `private, no-store`                         |

`AdminSessionCookie` is the OpenAPI security scheme for the host-only Secure/HttpOnly session
cookie. CSRF and Origin are additional unsafe-method controls, not authentication schemes.

## Filter and sort catalog

The common grammar is frozen in [API conventions](conventions.md#pagination-filtering-and-sorting).
The administrator skills collection allows filters `category_id`, `visible`, `featured`, `search`
and sorts `position`, `name`, `created_at`, `updated_at`, `id`. The public skills collection allows
filters `category`, `featured`, `search` and sorts `position`, `name`, `featured`, `id`. See the
[skills API guide](skills.md) for exact paging, concurrency, idempotency, and relation behavior. An
absent catalog still means arbitrary fields are rejected; it never means every field is queryable.

## Error catalog

| HTTP | Stable code                 | Meaning                                                  |
| ---: | --------------------------- | -------------------------------------------------------- |
|  400 | `BAD_REQUEST`               | Malformed or unsupported request semantics               |
|  401 | `AUTHENTICATION_REQUIRED`   | A valid credential/session is required                   |
|  401 | `AUTHENTICATION_FAILED`     | Credentials are invalid without account enumeration      |
|  403 | `AUTHORIZATION_DENIED`      | Actor is not allowed; no hidden-resource detail          |
|  403 | `CSRF_INVALID`              | Missing or invalid session-bound CSRF value              |
|  403 | `ORIGIN_INVALID`            | Missing or untrusted Origin on an unsafe browser request |
|  403 | `PASSWORD_CHANGE_REQUIRED`  | Initial password must be changed first                   |
|  404 | `NOT_FOUND`                 | Resource absent or not visible to the actor              |
|  405 | `METHOD_NOT_ALLOWED`        | HTTP method is unsupported                               |
|  409 | `RESOURCE_VERSION_CONFLICT` | Submitted resource version is stale                      |
|  409 | `IDEMPOTENCY_CONFLICT`      | Key was used for a different canonical request           |
|  409 | `IDEMPOTENCY_IN_PROGRESS`   | Matching command is still executing                      |
|  413 | `REQUEST_TOO_LARGE`         | Request exceeds the route limit                          |
|  415 | `UNSUPPORTED_MEDIA_TYPE`    | Media type is unsupported                                |
|  422 | `VALIDATION_FAILED`         | One or more request fields are invalid                   |
|  422 | `PASSWORD_POLICY_INVALID`   | Replacement password fails the policy                    |
|  428 | `PRECONDITION_REQUIRED`     | Current `If-Match` is required                           |
|  429 | `RATE_LIMITED`              | Retry after the response's `Retry-After` seconds         |
|  500 | `INTERNAL_ERROR`            | Safe unexpected-failure projection                       |
|  503 | `DEPENDENCY_UNAVAILABLE`    | Required dependency is unavailable or incompatible       |

Operation-specific OpenAPI responses are authoritative about which subset can occur. Consumers
must branch on `error.code`, retain `error.request_id` for support, and treat unknown additive codes
as safe failures rather than success.
