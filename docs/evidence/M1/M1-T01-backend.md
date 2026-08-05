# M1-T01 - Administrator identity, sessions, rate limiting, and minimal audit

## Identity

- Requested milestone: M1
- Existing trace milestone alias(es): M02 authentication foundation
- Requirement IDs: F2-001, F2-002, SEC-002, SEC-003, SEC-004, SEC-005, SEC-009, SEC-010, NFR-012, NFR-014, NFR-016
- Acceptance IDs: AC-015, AC-016, AC-017, AC-024, AC-032, AC-033, AC-039, AC-041
- Build/commit: uncommitted integration working tree
- Branch/PR: N/A
- Environment/image digests: Python 3.12.13; PostgreSQL 17.10; Docker Engine 29.2.1; repository-pinned PostgreSQL image
- Executor/reviewer: Backend Agent; Integration/root and independent review pending
- Completed UTC: 2026-08-02

## Delivery

- Goal and outcome: implemented one-administrator R1 identity, explicit takeover-safe bootstrap, Argon2id passwords, opaque digest-only sessions, forced initial password change, login/logout/session refresh/password rotation, PostgreSQL rate limits, and minimal append-only audit facts.
- Files/modules changed: identity and audit domain/ports/services; outward SQLAlchemy adapters and rate-limit repository; auth API/errors/schemas/composition; bootstrap CLI; identity migration and database revision expectation; unit, API, database, and migration tests.
- Migration revision/data action: sole linear head `20260802_0002`, down revision `20260802_0001`; no seed or default credential is created. Empty, current, prior-baseline, downgrade, and offline SQL paths pass.
- OpenAPI/client change and regeneration result: executable FastAPI schema exposes five stable auth operations with precise response/security/header declarations. The checked-in root-owned OpenAPI artifact and generated client remain pending Integration/root refresh; Backend did not edit them.
- Security/privacy consequences: 256-bit URL-safe session secrets are stored only as SHA-256 digests; cookies use `__Host-`, Secure, Path `/`, SameSite=Lax, no Domain, and HttpOnly for the session. Unsafe operations require exact Origin plus signed session-bound double-submit CSRF. Authentication failures do not enumerate accounts. Password work is admitted through a bounded semaphore and occurs outside database transactions. Audit metadata is allow-listed and excludes password, email, cookies, headers, and raw IP.
- Denylist provenance: the offline subset is pinned to SecLists commit `2d5dc7504a40962c53f932a6d9d5ece4b213dfc6`, path `Passwords/Common-Credentials/10-million-password-list-top-100.txt`. The immutable upstream raw/canonical 101-entry payload SHA-256 is `780ebec6f93bd80aff2121c2644cf9e198ac1e361379ca73f28528fbcf044443`. Derivation takes upstream entries 1-100, omits entry 63, excludes upstream entry 101 as outside the named top-100 selection, and appends 16 reviewed local baseline entries. The resulting normalized 115-entry non-comment payload SHA-256 is `a591b9683f6b8a3d45e28c32bc112355fbcf893d998d76a8a013dc6e102aedf9`. Runtime performs no network access.
- Database privilege consequence: fixtures use `TEST_DATABASE_OWNER_URL` only for Alembic/destructive schema work and `TEST_DATABASE_URL` for application/repository work. The application was proof-run as a distinct non-owner runtime role. Runtime can perform required ordinary DML and audit insert/select, but cannot mutate/truncate audit, alter/drop its trigger, create persistent or temporary objects, or update Alembic metadata.
- Accessibility/UX consequences: API session state exposes `must_change_password`; initial-password sessions are denied ordinary administrator use by a reusable server policy. No frontend was changed in this backend assignment.
- Documentation changed: this implementer evidence only. First-login/operator documentation and final traceability remain Integration/root T03 work.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | `ruff format --check backend`; `ruff check backend`; `mypy --strict backend` | Pass: 66 files formatted; Ruff clean; strict Mypy clean | `backend/` |
| Backend unit/service/repository/API | `pytest -q backend/tests` with distinct owner/runtime URLs | Pass: 74 passed, 0 skipped | `backend/tests/` |
| Migration/empty DB/upgrade | `alembic heads`; `pytest -q --no-cov backend/tests/migrations/test_baseline.py` | Pass: exactly `20260802_0002 (head)`; 4 passed, 0 skipped | `backend/migrations/versions/20260802_0002_identity_auth.py` |
| OpenAPI/generator diff | live schema convention assertions | Pass for executable schema: five stable operation IDs, cookie-only security plus required CSRF/Origin headers, exact response sets, and explicit 422 `ErrorEnvelope` declarations on every operation FastAPI exposes with 422; checked artifact re-export pending root | `backend/tests/integration/test_auth_api.py` |
| E2E/integration | PostgreSQL-backed auth suite against migration-owner/runtime split | Pass: 8 passed; bootstrap, login, forced change, rotation, refresh, expiry, logout, sequential/concurrent rate limiting, and adversarial paths | `backend/tests/integration/test_auth_api.py` |
| Security/privacy | `bandit -q -r backend/app`; runtime privilege probes; audit/log/DB inspection | Pass: Bandit clean; raw non-ASCII/overlong cookies return safe 401; Origin/CSRF/mass-assignment/injection negatives pass; forbidden runtime operations all denied | `backend/tests/integration/test_auth_api.py` |
| Performance/coverage | full Pytest branch coverage; focused identity coverage; three Argon2id hashes | Pass: overall 92.33% (target 85%); identity service/security combined 98% (target 95%), service 99%, security 96%; Argon2id median 384.6 ms with samples 360.9/391.3/384.6 ms | `backend/tests/unit/test_identity_service_state_machine.py` |
| Documentation/link walkthrough | evidence links and dispatch ownership reviewed | Pass for backend evidence; root-owned contract/operator docs remain downstream | `docs/plan/dispatch-m1.md` |

## Security and behavior matrix

| Control | Result |
|---|---|
| Bootstrap invocation/replay | Explicit CLI only; password from environment or stdin; no startup action; replay refused even after administrator deactivation; output contains no password. |
| Password storage | Argon2id `m=65536 KiB`, `t=3`, `p=1`, 32-byte hash, 16-byte salt; versioned offline denylist and 12-1024 character bounds. |
| Session lifecycle | Digest-only 256-bit secret; 30-minute sliding idle and 12-hour absolute cap; GET is mutation-free; explicit refresh; password rotation revokes prior/other sessions; logout revokes current. |
| Abuse resistance | Atomic PostgreSQL fixed-window counters; attempt five blocks; progressive 60-second doubling capped at 3600 seconds; active blocks cross window boundaries; known/unknown paths share safe errors; Argon2 concurrency bounded at two. |
| Request defenses | Missing/untrusted Origin, missing/forged/mismatched CSRF, extra fields, SQL-shaped input, invalid credentials, revoked/expired/malformed sessions all fail closed with no-store error envelopes. |
| Audit integrity/privacy | Controlled bootstrap/login/password/logout events; no raw identifier/secret metadata; repository is insert-only; trigger defense plus runtime SELECT/INSERT-only grants; mutation, truncate, trigger, DDL, and Alembic writes denied. |

## Acceptance record

| AC ID | Status | Evidence | Defect/waiver |
|---|---|---|---|
| AC-015 | Pass for backend | explicit bootstrap, replay refusal, forced-change policy, migration/API tests | Demo seed remains outside M1-T01 and therefore M0-T07 is not fully closed. |
| AC-016 | Pass for backend | login/session/password/logout lifecycle and safe state/errors | Frontend/browser acceptance belongs to T02/T03. |
| AC-017 | Pass for backend slice | invalid/revoked/expired sessions reveal no protected state | Ordinary admin resource routes arrive in later milestones. |
| AC-024 | Pass for minimal M1 catalog | allow-listed append-only audit inspection and privilege denial | Full audit catalog/viewer/retention remains M12. |
| AC-032 | Pass for backend contract | forced change and session-expiry projections are explicit | Responsive UI evidence belongs to T02/T03. |
| AC-033 | Pass for backend contract | stable safe envelopes, request IDs, no-store, validation mapping | UI error-state evidence belongs to T02/T03. |
| AC-039 | Pass for backend security tests | adversarial request, persistence, redaction, and privilege cases | Final browser/security integration remains T03. |
| AC-041 | Pass for bootstrap half | real CLI tested; no default/takeover behavior | Demo-seed half remains separately blocked. |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| Login failed with `DetachedInstanceError` after the short read transaction closed. | High | First migrated PostgreSQL login test | SQLAlchemy rollback expired a returned ORM record before Argon2 work. | 1 | Return persistence-neutral read snapshots while retaining locked ORM records for writes. | 8/8 auth and 74/74 full tests pass. |
| Initial unsafe OpenAPI declaration produced alternative cookie/header security paths and broad response maps. | High | Live schema inspection | Independent cookie and header security helpers were rendered as OR alternatives. | 1 | Keep the session cookie as the security scheme and declare required CSRF/Origin headers explicitly per operation. | Convention assertions and independent schema retest pass. |
| Rate blocks could disappear at a fixed-window boundary. | High | Deterministic boundary test | The check initially considered only the current bucket. | 1 | Query the maximum active `blocked_until` across subject buckets. | 45-second carry-over and progressive-cap assertions pass. |
| Read-only GET and browser cookie lifetimes did not initially align with sliding server expiry. | High | Contract review | Sliding activity and cookie issuance were implicit/incomplete. | 1 | Keep GET mutation-free; add explicit CSRF-protected refresh and cap cookie Max-Age at absolute expiry. | Refresh, 31-minute survival, and 12-hour rejection pass. |
| Single database credential could not prove append-only/DDL resistance. | High | ADR-0008 privilege review | Table-owner connections can bypass/drop table-local controls. | 1 | Adopt Infrastructure's migration-owner/runtime topology and split backend fixtures. | Runtime identity and eight forbidden-operation probes pass. |
| Critical identity coverage measured below the 95% target. | Medium | focused branch coverage | Race/error state-machine branches were not directly exercised. | 1 | Add deterministic admission, rehash, concurrent-rate, stale-admin/password, missing-session, refresh, rotation, and logout tests. | Focused service/security coverage is 98%. |
| B2 validation rejected implicit FastAPI 422 responses on refresh/logout. | High | `scripts/validate_openapi.py` after root-owned export | Required header parameters caused FastAPI to emit 422 automatically, but the explicit response map omitted the stable `ErrorEnvelope` declaration. | 1 | Declare 422 `ErrorEnvelope` responses on every auth operation that exposes 422 and assert exact response sets/schema references. | Focused source-schema tests, Ruff, Mypy, and Bandit pass; root re-export/revalidation pending. |
| Same-subject PostgreSQL rate-limit concurrency lacked direct evidence. | Medium | independent security review | Sequential threshold/window tests did not prove concurrent UPSERT behavior across transactions. | 1 | Add twelve synchronized independent runtime transactions against one bucket and assert the exact returned backoff multiset, stored count, and capped block time. | PostgreSQL concurrency test passes with count 12 and 3600-second cap. |
| Offline denylist cited SecLists without immutable source identity. | Medium | independent security review | Asset comments named only the repository/path and local version. | 1 | Pin the last pre-removal upstream commit, upstream SHA-256, retrieval date, and canonical bundled checksum; add an offline integrity test. | Provenance/integrity unit test passes; no runtime network behavior added. |

## Completion decision

- Backend implementer gate: Pass.
- Remaining risks/targets and disposition: Integration/root must re-export and revalidate the root-owned OpenAPI artifact and generated TypeScript client after the explicit 422 correction before B2/final T01 acceptance. Browser/UI/operator-doc evidence remains T02/T03. Demo seed is deliberately not implemented here. No backend security or database-role blocker remains.
- Traceability matrix rows updated: not updated by this implementer; Integration/root owns final milestone traceability.
- Independent reviewer sign-off: pending Integration/root review of this record and the root-owned OpenAPI/client diff.
