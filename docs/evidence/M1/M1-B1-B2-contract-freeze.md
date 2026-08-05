# M1 B1/B2 - Authentication contract freeze

## Identity

- Requested milestone: M1
- Existing trace milestone alias(es): M02 authentication foundation
- Requirement IDs: F2-001, F2-002, SEC-002, SEC-003, SEC-004, SEC-005, SEC-009, SEC-010, NFR-012, NFR-014, NFR-016
- Acceptance IDs: AC-015, AC-016, AC-017, AC-024, AC-032, AC-033, AC-039
- Build/commit: uncommitted integration working tree
- Branch/PR: N/A
- Environment/image digests: Python 3.12.13; Node.js 22.23.2; pnpm 11.18.0; OpenAPI Generator 7.17.0 OCI digest `sha256:868b97eb4e5080d2cdfd5b3eeaa4d52e4bbb7c56f14e234b08b0b0bc4f38a78f`
- Executor/reviewer: Integration/root; independent Security/QA reviewer
- Completed UTC: 2026-08-02

## Delivery

- Goal and outcome: accepted the executable B1 authentication API contract and refreshed the root-owned canonical OpenAPI document and TypeScript client for B2. B2 is frozen and releases M1-T02 frontend implementation.
- Files/modules changed: `docs/api/openapi.json` and `frontend/src/generated/api/**` only for this integration window; this evidence records the review.
- Migration revision/data action: N/A for B2. The reviewed backend remains at the sole head `20260802_0002`.
- OpenAPI/client change and regeneration result: the canonical contract now contains seven operations total, including five stable authentication operation IDs. Two fail-closed regeneration comparisons produced the same complete contract-tree digest, `f5ad8b0d0019e502101cb70a7800d5d837a5c70f672129f88d942f9e4563396b`.
- Security/privacy consequences: login requires an exact `Origin` parameter; every unsafe authenticated operation requires one `AdminSessionCookie` security boundary plus required `Origin` and `X-CSRF-Token` headers. FastAPI validation responses are explicitly mapped to the stable `ErrorEnvelope`; no `HTTPValidationError` or generator validation model remains in the canonical client.
- Accessibility/UX consequences: `SessionData.must_change_password`, idle expiry, absolute expiry, and safe typed error envelopes are available to the frontend without duplicating transport models.
- Documentation changed: this contract-freeze record. Backend implementation evidence remains in `docs/evidence/M1/M1-T01-backend.md`.

## Validation

| Category                      | Command/protocol + tool version                                                                                              | Result                                                                                                                         | Repository-relative artifact                 |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| Backend unit/API contract     | split-role full suite and focused auth suite reported by backend owner; independent schema inspection                        | Pass: 74 passed, 0 skipped; auth 8/8; live schema equals canonical schema                                                      | `backend/tests/integration/test_auth_api.py` |
| OpenAPI validator             | `python -m uv run --frozen python scripts/validate_openapi.py`                                                               | Pass: seven operations                                                                                                         | `docs/api/openapi.json`                      |
| OpenAPI security/error review | parsed every operation, response schema reference, parameter, and security requirement                                       | Pass: exact cookie boundary; required Origin/CSRF headers; stable `ErrorEnvelope` including explicit 422; unique operation IDs | `docs/api/openapi.json`                      |
| Deterministic generation      | compute SHA-256 manifest of canonical OpenAPI plus every generated-client file; regenerate; revalidate; recompute            | Pass: before and after both `f5ad8b0d0019e502101cb70a7800d5d837a5c70f672129f88d942f9e4563396b`                                 | `scripts/generate_api_client.py`             |
| Frontend format/lint/type     | `pnpm --dir frontend format:check`; `eslint src/generated/api src/lib/api --max-warnings=0`; `pnpm --dir frontend typecheck` | Pass: Prettier clean, zero warnings, strict TypeScript clean                                                                   | `frontend/src/generated/api/`                |
| Frontend wrapper tests        | `vitest run src/lib/api/client.test.ts`                                                                                      | Pass: 1 file, 5 tests                                                                                                          | `frontend/src/lib/api/client.test.ts`        |
| Independent security review   | read-only final review of backend, live/canonical schema, migrations, evidence, and corrected provenance                     | Pass for backend runtime and B2; no Critical/High backend or contract defect                                                   | `docs/evidence/M1/M1-T01-backend.md`         |

## Contract matrix

| Operation ID           | Method/path                         | Security and required headers                              | Declared responses           |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------- | ---------------------------- |
| `auth_login`           | `POST /api/v1/auth/login`           | public cookie issuance; required `Origin`                  | 200, 401, 403, 422, 429, 503 |
| `auth_logout`          | `POST /api/v1/auth/logout`          | `AdminSessionCookie`; required `Origin` and `X-CSRF-Token` | 200, 401, 403, 422, 503      |
| `auth_password_change` | `POST /api/v1/auth/password/change` | `AdminSessionCookie`; required `Origin` and `X-CSRF-Token` | 200, 401, 403, 422, 503      |
| `auth_session_get`     | `GET /api/v1/auth/session`          | `AdminSessionCookie`                                       | 200, 401, 503                |
| `auth_session_refresh` | `POST /api/v1/auth/session/refresh` | `AdminSessionCookie`; required `Origin` and `X-CSRF-Token` | 200, 401, 403, 422, 503      |

## Acceptance record

| Gate                               | Status | Evidence                                                                                                     | Defect/waiver                                                         |
| ---------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| B1 executable auth API contract    | Pass   | 8/8 PostgreSQL auth tests, exact live-schema assertions, one `20260802_0002` head                            | None                                                                  |
| B2 canonical OpenAPI/client freeze | Pass   | validator, operation/security/error review, deterministic digest, strict generated compile and wrapper tests | None                                                                  |
| M1-T01 overall                     | Pass   | backend/security/contract work plus corrected CI topology and independent static review                      | The first GitHub-hosted execution remains pending and is not claimed. |
| M1-T02 release                     | Pass   | B2 is frozen at the digest above                                                                             | Frontend implementation may proceed; this is not T02 acceptance.      |

## Findings and corrective loop

| Finding                                                                                                              | Severity | Reproduction                                                                     | Root cause                                                                                                      | Attempt # | Correction                                                                                                          | Retest                                                                                 |
| -------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------: | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Validator rejected implicit FastAPI 422 schemas on refresh/logout.                                                   | High     | export followed by `scripts/validate_openapi.py`                                 | required headers caused FastAPI to add its default validation model while the explicit response map omitted 422 |         1 | backend declared 422 `ErrorEnvelope` everywhere FastAPI exposes 422 and asserted exact response sets/references     | validator passes; canonical/live schemas match; generated validation models are absent |
| Initial deterministic-digest helper used an unavailable PowerShell/.NET path API and emitted non-terminating errors. | Low      | first before/after manifest attempt                                              | local Windows PowerShell runtime lacks `Path.GetRelativePath`                                                   |         1 | discarded the result; used a validated workspace-prefix substring and terminating error mode                        | clean before/after digest match at `f5ad8b...396b`                                     |
| Hosted backend CI had only one bootstrap-style test URL.                                                             | High     | independent review of `.github/workflows/ci.yml` and `backend/tests/conftest.py` | workflow predated the migration-owner/runtime fixture split                                                     |         1 | generate/mask three credentials; initialize with reviewed scripts; migrate as owner; test as runtime; fail on skips | actionlint, repository checks, and independent static review pass; hosted run pending  |

## Completion decision

- B1/B2 contract gate: Pass.
- Remaining risks/targets and disposition: the first GitHub-hosted execution of the corrected backend job remains pending and is not claimed; the full aggregate workflow is intentionally red on the separate demo-seed dependency. M1-T02 and final browser lifecycle evidence remain downstream.
- Traceability matrix rows updated: final M1 traceability remains Integration/root M1-T03 work.
- Independent reviewer sign-off: no Critical/High backend runtime or canonical-contract defect; the former High CI integration blocker is corrected and independently passes static/local review with no finding.
