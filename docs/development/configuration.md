# Configuration

## Readiness

The backend schema and infrastructure injection now form the F5 candidate. The backend remains the owner of types, validation, and safe defaults; infrastructure owns `.env.example`, container injection, and topology. Integration/root freezes F5 only after full `M0-T07`, including the separately dispatched bootstrap/seed commands.

## Environment contract

| Name                      | Visibility                                                     | Purpose                                                                                                                                                    |
| ------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `APP_ENVIRONMENT`         | Backend-private                                                | Select `development`, `test`, or secure `production` validation.                                                                                           |
| `APP_DEBUG`               | Backend-private                                                | Debug switch; production rejects true.                                                                                                                     |
| `APP_LOG_LEVEL`           | Backend-private                                                | Allow-listed structured-log level.                                                                                                                         |
| `APP_BUILD_VERSION`       | Backend-private, safe to disclose                              | Bounded release identifier returned by authenticated admin health; defaults to `0.0.0`.                                                                    |
| `APP_BUILD_COMMIT`        | Backend-private, safe to disclose                              | Lowercase hexadecimal source revision (7-64 characters) returned by authenticated admin health; defaults to `unknown`.                                    |
| `APP_TRUSTED_ORIGINS`     | Backend-private configuration                                  | JSON list of exact origins; production requires exact HTTPS values.                                                                                        |
| `APP_DATABASE_URL`        | Secret, backend or migrator process                            | Async PostgreSQL URL. Compose gives the backend runtime credentials and the explicit Alembic job migration-owner credentials.                              |
| `APP_CSRF_SIGNING_KEY`    | Secret, backend only                                           | Independent signing key; at least 32 random bytes in production.                                                                                           |
| `APP_TOKEN_DIGEST_PEPPER` | Secret, backend only                                           | Independent token-digest pepper; at least 32 random bytes in production.                                                                                   |
| `APP_PRIVACY_HMAC_KEY`    | Secret, backend only                                           | Independent privacy pseudonymization key; at least 32 random bytes in production.                                                                          |
| `UPW_API_UPSTREAM_ORIGIN` | Server-only Next.js runtime configuration; not browser-visible | Exact internal HTTP(S) origin used only when `/api/v1` reaches the Next.js fallback proxy. Required in production; Compose supplies `http://backend:8000`. |
| `UPW_PUBLIC_SITE_ORIGIN`  | Server-only Next.js runtime configuration; public value        | Externally visible exact origin used for canonical discovery output, robots, and sitemap.                                                                  |

`COMPOSE_PROJECT_NAME`, `IMAGE_TAG`, `BACKEND_PORT`, `FRONTEND_PORT`, and the `POSTGRES_*` values are local Compose inputs, not application settings. `POSTGRES_USER`/`POSTGRES_PASSWORD` are bootstrap-only cluster credentials. `POSTGRES_MIGRATION_USER`/`POSTGRES_MIGRATION_PASSWORD` own the database and schema and are used by Alembic and permission reconciliation. `POSTGRES_RUNTIME_USER`/`POSTGRES_RUNTIME_PASSWORD` are non-owner application credentials. All three role names must be distinct ASCII PostgreSQL identifiers; every password must be a distinct URL-safe random value of at least 32 characters.

`UPW_API_UPSTREAM_ORIGIN` is a non-secret, server-only routing value. It is never compiled into browser JavaScript and accepts only an exact HTTP(S) origin without credentials, path, query, fragment, wildcard, whitespace, or control characters. Next.js refuses a missing or invalid value in production. A standalone development server defaults to `http://127.0.0.1:8000`; production has no localhost fallback. The preferred production topology still routes `/api/v1` at the same-origin TLS edge before requests reach Next.js. `UPW_PUBLIC_SITE_ORIGIN` follows the same exact-origin rules and supplies the externally visible HTTPS origin at runtime. No `NEXT_PUBLIC_*` value is defined, and no database or application secret enters the frontend build or runtime.

## Configuration principles

- Configuration is supplied through environment variables or deployment secret injection, not source-controlled credentials.
- The application fails clearly when required production configuration is missing or unsafe.
- Public frontend variables contain only values safe to expose to a browser. Secrets never use a public-variable namespace.
- Production does not silently use predictable credentials, development defaults, debug behavior, wildcard origins, or permissive security settings.
- Logs and health responses do not reveal connection strings, signing material, passwords, tokens, storage credentials, or stack traces.
- Website-managed public settings are not a secret store and do not replace deployment configuration.
- Environment examples use synthetic values and explain generation/rotation rather than embedding usable credentials.

## Environment classes

The schema supports `development`, `test`, and `production`. Production rejects debug mode, weak or missing private values, default database users, non-async PostgreSQL URLs, and missing, wildcard, or non-HTTPS trusted origins. Private S3-compatible media remains the scalable default; an explicitly acknowledged private local volume is accepted for a deliberate single-host deployment and must participate in coordinated backup/recovery. `.env.example` is a local template with blank secret values; it is never copied into images.

## Contributor checklist

Before adding a configuration value, identify its owner, type, safe default or required status, secret/public classification, environments, validation, log-redaction behavior, rotation impact, documentation, and tests. Coordinate environment names with both backend and infrastructure owners.

See the [security architecture](../architecture/security-architecture.md) for normative control requirements and the [assumptions record](../requirements/assumptions-and-scope.md) for decisions still requiring operator input.
