# R1 Test Strategy

## Test layers

| Layer | Required coverage | Typical location | Gate |
|---|---|---|---|
| Backend unit/domain | Invariants, policies, validators, publication, scopes, redaction, Markdown, block schemas | `backend/tests/unit` or module tests | Every backend task |
| Backend service/repository | Use cases, UoW/rollback, optimistic concurrency, query projections/N+1, audit coupling | `backend/tests/service`, `repository` | Every backend slice |
| Backend API/integration | Envelopes/errors, authz, CSRF, filters/sorts, idempotency, health, uploads, OpenAPI | `backend/tests/integration` | Every API task |
| Migration | Empty upgrade, current revision, representative prior-data upgrade, constraints/indexes | `backend/tests/migrations` | Every schema change/M14 |
| Frontend unit/component | Wrappers, mappings, forms, validation, all async states, focus, responsive alternatives | `frontend/src/**/*.test.*` | Every frontend task |
| Storybook interaction/a11y | Reusable states, long/narrow/zoom/theme/error/loading, keyboard behavior | `frontend/src/**/*.stories.*` | Every reusable component |
| Contract | OpenAPI lint/snapshot, operation IDs, security/errors/examples, regeneration no-diff | backend + generated-client CI | Every contract change |
| E2E | Complete browser/API vertical workflows against PostgreSQL and built apps | `frontend/e2e` | Every slice/release |
| Manual/browser | Signal Ledger visual bar, WCAG matrix, responsive/focus/screen reader, Lighthouse | `docs/evidence/<milestone>` | User-facing milestone/M13-M14 |

## Minimum E2E inventory

- bootstrap, login valid/invalid, forced password change, logout/expiry, protected-route denial;
- create/edit/order/feature/show-hide/delete skills and verify public rendering;
- create/edit/relate/preview/publish/edit-live/unpublish experiences and projects;
- author safe Markdown, taxonomy/filter, publish/schedule/unpublish blog content;
- create page, add/configure/duplicate/hide/reorder every block class, preview/publish/unpublish, verify custom route;
- upload/use media, reject malicious input, block in-use deletion, unlink/delete;
- submit consented contact once, exercise validation/rate limits, read/archive/restore/delete privately;
- create/copy-once/use/under-scope/rotate/revoke/expire API token;
- inspect audit coverage and safe health ready/not-ready;
- verify SEO metadata, sitemap/robots, unauthorized/draft/private-content rejection.

## Fixtures and environments

- Deterministic clock/UUID factories; secrets generated per test and never printed.
- PostgreSQL is used for repository/integration/migration/E2E behavior; unit tests may use fakes only at explicit ports, never SQLite as a PostgreSQL substitute.
- `seed-demo` is not a test fixture dependency. Tests create minimal isolated data through factories/APIs and clean by transaction/database reset.
- Storage adapters share one contract suite; local plus a compatible S3 test service/fake at the adapter boundary, with failure injection for promotion/delete.
- E2E runs built Next.js/FastAPI through the same-origin edge contract and a fresh migrated database. Parallel workers isolate DB/schema and media namespaces.

## Security and privacy tests

Cover bootstrap replay, Argon2 parameters, enumeration, session/token digest storage, expiry/revocation/rotation, CSRF/Origin/CORS/headers, every route-scope pair, IDOR/mass assignment, SQL/filter injection, XSS/unsafe Markdown URLs, upload bombs/mismatch/path traversal, rate limits/idempotency, publication/preview leakage, safe errors/health, and log/audit/cache/trace redaction.

## Accessibility and responsive tests

Automated axe/component checks never replace manual review. Execute the checklist at 320, 360, 390, 768, 1024, 1280, 1440, 1920 and 400% zoom where applicable, in light/dark/system and reduced motion. Required manual workflows are public navigation/home blocks, projects, blog, contact, auth, admin list/form/conflict, page builder/reorder, media, tokens, and contacts. Record browser, assistive technology, viewport, theme, result, finding and retest.

## Coverage and flake policy

Coverage thresholds are reported by meaningful suites and critical modules separately. A test with no behavioral assertion does not count as completion evidence. A flaky failure is a defect: capture trace, classify root cause, fix or quarantine only with owner/expiry/linked defect and a separate release-blocking disposition. Retries cannot convert a consistently failing test into a pass.

## Test selection and reruns

During implementation run focused tests plus contract/type/lint checks. At task close run the entire affected feature and integration path. At milestone close run all affected backend/frontend/E2E, migrations, schema generation, scans, and browser review. At M14 run every suite from a clean release environment.
