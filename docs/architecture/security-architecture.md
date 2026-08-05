# Security Architecture

## Trust boundaries and assets

Untrusted inputs include every browser/API field, Markdown, URLs, uploads, forwarded headers, and storage callbacks. The edge, Next.js, FastAPI, PostgreSQL, and object storage are separate trust zones. Critical assets are password/session/token secrets, contact data, drafts, storage objects, audit integrity, signing/pepper keys, and database credentials (`SEC-001`).

## Authentication

### Administrator sessions

- Bootstrap is an explicit idempotent CLI using secret input/environment injection; it refuses when an administrator exists. There are no production defaults. Initial login is limited to password change/logout/session inspection (`F2-002`).
- Passwords use Argon2id with parameters benchmarked to about 250–500 ms on production hardware (minimum memory 64 MiB, iterations 3, parallelism 1) and a unique salt. Rehash on login when policy increases. Minimum 12 characters; allow password managers/64+ characters; check compromised/common-password list without logging input.
- Login errors do not enumerate accounts. Defaults: 5 failures per account+IP pseudonym per 15 minutes, progressive delay/temporary block up to one hour; edge IP throttling complements PostgreSQL counters. Successful/failed attempts are audited safely.
- Session secret is 256 random bits, stored only as a digest, and sent in `__Host-admin_session` with `Secure`, `HttpOnly`, `Path=/`, no `Domain`, `SameSite=Lax`. Default idle timeout 30 minutes, absolute timeout 12 hours; rotate on login and privilege/password change. Password change revokes all other sessions; logout revokes current.
- Unsafe cookie-authenticated methods require exact trusted-Origin validation and a signed double-submit token: `__Host-admin_csrf` is Secure, SameSite=Lax, non-HttpOnly, Path `/`, contains a nonce/session binding authenticated by HMAC, and must exactly match `X-CSRF-Token`. Login also enforces Origin and rate limiting. GET/HEAD/OPTIONS are mutation-free (`SEC-005`).

### API access tokens

Token format is `pp_live_<public_id>.<256-bit-secret>`. The public ID locates a row; an HMAC-SHA-256 digest using a deployment pepper is compared in constant time. Only the creation/rotation response contains the secret and is `no-store`. UI defaults to 90-day expiry; maximum 365 days. No-expiry tokens are allowed only with explicit confirmation because the requirement makes expiry optional. Rotation atomically revokes the old token and creates a new one (`SEC-008`).

Scopes are deny-by-default and enforced in route policy and application use case. Token management, sessions, password/bootstrap, and contact hard deletion are never token-authorized in R1.

## Authorization and data protection

- Public/admin/integration schemas are distinct. Repository methods are inaccessible to routers and frontend. Actor context and resource checks protect against IDOR; request DTO allow-lists protect against mass assignment (`SEC-004`).
- Contacts, drafts, audit, tokens, and sessions are `private, no-store`. Public services explicitly select public fields and effective revisions.
- TLS is required outside local development. Database/object storage use private networking and encryption at rest supplied by the deployment platform. Backups are encrypted and access-controlled.
- Logs redact headers/cookies/query secrets and fields matching password/token/message/email policies. Contact bodies and token secrets are never passed to logging calls (`SEC-009`).

## Input/content/upload controls

- SQLAlchemy bound parameters only; filter/sort expressions map from endpoint allow-lists.
- Controlled Markdown disables raw HTML, sanitizes generated output, and permits only `http/https` content URLs under the context-specific URL policy. React escaping remains enabled.
- Navigation URLs follow the link rules in `domain-model.md`. Security headers: CSP with nonces/no `unsafe-inline` scripts, HSTS, `nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, restrictive `Permissions-Policy`, and `frame-ancestors 'none'` (or equivalent X-Frame-Options).
- Upload defaults: 10 MiB, 6000 px per side, 36 MP; JPEG/PNG/WebP, GIF animation disabled, SVG rejected. Stream with hard byte cap; inspect decoder/magic bytes; reject decompression bombs/mismatch; strip unsafe metadata; generate opaque keys; store privately (`SEC-007`).

## Rate limits and anti-spam

Contact default: 5 submissions/15 minutes/IP pseudonym and 20/day, plus a honeypot and minimum form-completion time. Return generic success where revealing spam classification would aid attackers, while storing exactly one valid accepted submission. Login/token authentication and upload have separate policy buckets. PostgreSQL is authoritative in R1; edge limits protect volumetric attacks. Trusted proxy hops are explicit so clients cannot forge source IP.

## CORS, errors, dependencies, operations

CORS is disabled for browser cross-origin access by default; configured origins are exact HTTPS origins, never wildcard with credentials. Error mapping is centralized and stack traces remain internal. Production config rejects weak/missing keys, debug mode, non-HTTPS trusted origins, and default credentials.

CI runs dependency lockfile audit, static analysis, secret scanning, container scanning, and security tests; confirmed critical/high findings block release (`SEC-010`). Runtime identities are non-root and least privilege. Signing/pepper/privacy keys are independently rotatable with versioned key IDs. Incident response can revoke sessions/tokens and rotate keys without exposing their values.

## Retention and privacy defaults

Contacts default to 365 days; audit defaults to 400 days; sessions/rate buckets/idempotency records use short operational retention. Raw IP is not stored in audit. Abuse correlation uses a rotating-key HMAC pseudonym; contact records include consent time/policy version. Retention purge is an explicit dry-run-capable operator command in R1. Deployment owners must validate these periods and privacy/legal text for jurisdiction before release; until then the secure behavior is retention-limited and non-public, not indefinite accidental storage.

## Required security verification

Tests cover bootstrap replay, password hash parameters, enumeration, expiry/revocation/rotation, CSRF/Origin/CORS, every scope, cross-resource access, mass assignment, injection, XSS/Markdown URLs, malicious uploads, redaction, publication leakage, rate limits, and safe errors/health (`AC-015`–`AC-024`, `AC-039`).
