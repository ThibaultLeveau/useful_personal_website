# Browser administrator authentication

## Boundary

Administrator authentication is a same-origin browser session flow. Browser code calls relative
`/api/v1` paths; it never receives a backend origin, database credential, session secret, or token
pepper. In local Compose, Next.js rewrites the versioned path to the internal backend service. A
production TLS edge should route the same path before Next.js.

The session cookie is `Secure`, `HttpOnly`, host-only, `SameSite=Lax`, and scoped to `/`. Its opaque
256-bit secret is stored by the server only as a SHA-256 digest. The companion signed
`__Host-admin_csrf` cookie is intentionally readable by same-origin browser code and is bound to the
session; it is not an authentication credential.

## Operations

| Method and path                     | Purpose                                                      | Required request controls                                                          |
| ----------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `POST /api/v1/auth/login`           | Validate credentials and establish the session/CSRF cookies. | Exact `Origin`; JSON `email` and `password`.                                       |
| `GET /api/v1/auth/session`          | Read the current session without extending it.               | Valid session cookie.                                                              |
| `POST /api/v1/auth/session/refresh` | Extend the idle expiry without exceeding the absolute limit. | Valid session, exact `Origin`, matching `X-CSRF-Token`.                            |
| `POST /api/v1/auth/password/change` | Change the password and rotate/revoke sessions.              | Valid session, exact `Origin`, matching `X-CSRF-Token`, current/new password body. |
| `POST /api/v1/auth/logout`          | Revoke the current session and clear both cookies.           | Valid session, exact `Origin`, matching `X-CSRF-Token`.                            |

Session responses contain `administrator_id`, `display_name`, `must_change_password`,
`idle_expires_at`, and `absolute_expires_at`. Timestamps are ISO 8601 UTC values. An initial-password
session may call only the session, password-change, and logout operations; ordinary protected
administrator access is denied until `must_change_password` becomes false.

Unsafe same-origin browser requests use the CSRF cookie value as the header value:

```javascript
const csrf = document.cookie
  .split(";")
  .map((part) => part.trim())
  .find((part) => part.startsWith("__Host-admin_csrf="))
  ?.slice("__Host-admin_csrf=".length);

await fetch("/api/v1/auth/session/refresh", {
  method: "POST",
  credentials: "same-origin",
  headers: { "X-CSRF-Token": decodeURIComponent(csrf ?? "") },
});
```

The checked-in generated client and handwritten authentication boundary implement this procedure;
application features should use that boundary instead of duplicating cookie parsing.

## Failures, rate limits, and caching

Errors use the stable `ErrorEnvelope` shape with `error.code`, a safe message/details object, and a
32-character `error.request_id`. Authentication failures never confirm whether an email exists.
Repeated failures use PostgreSQL-backed fixed-window protection; a blocked request returns `429`
with `Retry-After`.

Missing or forged CSRF values return `CSRF_INVALID`; missing or untrusted origins return
`ORIGIN_INVALID`. They never mutate session state. Authentication responses and errors use
`Cache-Control: private, no-store` and `Pragma: no-cache`. No wildcard CORS policy is used.

Do not log request bodies, cookies, CSRF values, password fields, or raw authorization headers.
Request IDs are the safe correlation mechanism.
