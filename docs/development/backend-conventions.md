# Backend Conventions

## Current baseline

M0 provides the executable FastAPI factory, settings validation, structured
logging, and quality harness. M1 provides the administrator identity/session
boundary. M2 freezes the common API and health contracts documented in the
[API conventions](../api/conventions.md), [catalogs](../api/catalogs.md), and
[health guide](../api/health.md). The
[architecture overview](../architecture/architecture.md), [API structure](../architecture/api-structure.md),
[security architecture](../architecture/security-architecture.md), and accepted
ADRs remain normative.

## Application entry point and health seam

- The factory is `app.main:create_app`; the default ASGI export is
  `app.main:app` and can be loaded with `--app-dir backend`.
- Business API paths are under `/api/v1`. Baseline probes are
  `GET /api/v1/health/live` (`health_live`) and
  `GET /api/v1/health/ready` (`health_ready`).
- Success uses `{data, meta}` and errors use
  `{error: {code, message, details, request_id}}`.
- Liveness calls no dependency. Readiness uses an injected application port and
  fails closed on database connectivity, timeout, or migration mismatch.
- Probe successes use `Cache-Control: no-store`; administrator health and all
  errors use `private, no-store`.
- A bounded caller request ID is preserved; invalid IDs are replaced with a
  generated 128-bit value and returned in both `X-Request-ID` and envelopes.

## Required boundaries

- Route handlers translate transport concerns and invoke application services; they do not contain business logic or direct database access.
- Domain logic is independent of FastAPI, SQLAlchemy, and external SDKs.
- Application services orchestrate use cases, authorization, transactions, and ports.
- Infrastructure adapters implement persistence and external integrations behind explicit interfaces.
- API request and response models are explicit. Database entities are not exposed directly.
- Public, preview, and administrative projections remain distinct so drafts and private fields cannot leak.
- Dependencies point inward; boundary tests enforce prohibited imports.

## Common application conventions

R1 APIs are versioned under `/api/v1`. Reuse the M2 common value objects and
transport projections instead of implementing endpoint-local variants:

- `ActorContext`, `AccessPolicy`, and `require_authorized` provide a
  transport-neutral, deny-by-default use-case authorization boundary. Never pass
  ORM/session records as actor identity.
- `PageRequest`, `page_metadata`, `QueryCatalog`, and
  `parse_collection_query` enforce the frozen page and allow-list grammar. Map
  catalog keys to explicit SQLAlchemy columns; never interpolate a caller field.
- `format_etag` and `require_matching_version` implement the strong integer
  version contract.
- `IdempotencyRequest`, `IdempotencyStore`, and the PostgreSQL adapter provide
  actor+route+key admission with digest-only 24-hour records. The command effect
  and `complete` call belong to the same unit of work.
- `ApiError`, the stable registry, `map_common_error`, `success`, and
  `list_success` own HTTP-safe projections and request correlation.

Credentials and sensitive payloads must never be logged. Sensitive actions
require authorization and audit coverage at the application boundary. Adding an
error code, filter/sort key, security scheme, cache policy, or idempotent command
requires documentation, contract tests, OpenAPI regeneration, and consumer
review.

Request logs are JSON and contain the event, UTC timestamp, request ID, route
template, method, status, and duration. They do not include raw URLs, query
values, headers, cookies, bodies, exception messages, or credentials. The
redaction processor also recursively removes password/token/secret/CSRF/email/
message-shaped fields before rendering.

## Settings contract

Backend settings use the `APP_` namespace. The current baseline defines
`APP_ENVIRONMENT`, `APP_DEBUG`, `APP_LOG_LEVEL`, `APP_TRUSTED_ORIGINS`,
`APP_DATABASE_URL`, `APP_CSRF_SIGNING_KEY`, `APP_TOKEN_DIGEST_PEPPER`, and
`APP_PRIVACY_HMAC_KEY`. Infrastructure must jointly review these names before
F5; it owns injection, while the backend remains the only owner of validation
and defaults.

`APP_BUILD_VERSION` and `APP_BUILD_COMMIT` are bounded public deployment labels
used by administrator health. They must not contain URLs or secrets.

Development defaults to non-debug with CORS disabled. Production rejects debug,
missing/weak secrets, a non-`postgresql+asyncpg` DSN, default database
credentials, and missing/wildcard/non-HTTPS trusted origins. Secret values use
masked Pydantic types and settings objects must never be logged.

## Quality expectations

New behavior requires strict typing, meaningful unit/service/repository/API tests as applicable, deterministic time/identifier seams, structured safe errors, and documentation impact review. Tool-specific commands, formatter settings, and allowed type exceptions will be documented only after the backend harness is implemented.

Run the frozen root environment with backend-owned configuration:

```console
uv run --frozen ruff check backend
uv run --frozen ruff format --check backend
uv run --frozen mypy --config-file backend/pyproject.toml backend
uv run --frozen pytest -c backend/pyproject.toml backend
uv run --frozen bandit -r backend/app -c backend/pyproject.toml
```

Ruff enables all rules with only formatter-conflict choices, test assertion/
fixture exceptions, and the unresolved `R-018` copyright-header gate documented
in configuration. Mypy is strict with the Pydantic plugin. Pytest enforces
strict markers/configuration and branch-aware coverage of at least 85%.
