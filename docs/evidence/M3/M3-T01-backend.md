# M3-T01 backend - Site configuration and public projections

## Identity

- Requested milestone: M3
- Trace milestone aliases: M06/M07
- Requirements: F1-007, F2-003, F2-014-F2-015, API-001-API-006, SEC-004-SEC-006,
  SEC-009, NFR-006-NFR-008, NFR-011
- Acceptance: AC-007, AC-021-AC-022, AC-027-AC-030, AC-035-AC-036, AC-039-AC-040
- Build/commit: uncommitted integration working tree
- Environment: Python 3.12.13; PostgreSQL 17.10; Alembic 1.18.5; OpenAPI Generator
  7.17.0
- Executor/reviewer: Integration/root implementation and separated certification pass
- Completed UTC: 2026-08-03

## Delivery

The profile, website-settings, navigation, and footer modules are durable aggregates behind
application ports and one unit of work. Admin commands use explicit DTO allow-lists, authorization,
CSRF/Origin checks, integer-version ETags, `If-Match`, idempotency where a full tree is replaced,
and transaction-coupled audit facts. Public queries serialize distinct allow-listed projections;
private values are absent rather than redacted or returned as null.

The sole M3 migration is `20260802_0004_site_configuration.py`, directly down from `0003`. It
creates singleton ownership, deterministic tree ordering, constraints, and supporting indexes.
The demo seed is an explicit, idempotent application command that refuses production before any
write and creates only fictional public configuration. It never creates an administrator,
credential, session, token, contact, media record, private profile value, or analytics credential.

## Validation

| Category               | Result                                                                                                                                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ruff format/lint       | Pass; 99 backend files clean                                                                                                                                                                                             |
| Strict Mypy            | Pass; 99 source files, zero errors                                                                                                                                                                                       |
| Pytest                 | Pass; 158 passed, 0 skipped                                                                                                                                                                                              |
| Backend coverage       | Pass; 88.56%, above the 85% target                                                                                                                                                                                       |
| Domain/security matrix | Pass; singleton races, validation boundaries, public flags, mass assignment, link schemes/targets, depth/cycle/orphan/order rules, authorization, CSRF/Origin, concurrency, idempotency, audit rollback, and safe errors |
| Migration              | Pass from empty/current databases; exactly one head, `20260802_0004`; constraints and indexes inspected                                                                                                                  |
| Query behavior         | Pass; navigation uses two bounded repository queries; footer uses at most three; representative PostgreSQL plans used the navigation index and footer column/item indexes                                                |
| OpenAPI                | Pass; 15 paths, unique operation IDs, explicit public/admin schemas and security declarations                                                                                                                            |
| Client generation      | Pass; two exports/generations were byte-deterministic and the generated TypeScript client compiled strictly                                                                                                              |
| Security/dependency    | Pass; Ruff security rules, Bandit, pip-audit, adversarial API tests, and disclosure review found no unresolved issue                                                                                                     |

Contract fingerprints from the accepted export were OpenAPI
`ECF1...277` and generated-client manifest `73F5...F0A7`; abbreviated values avoid turning this
record into a brittle replacement for the generated manifest itself.

## Privacy and seed inspection

An isolated no-seed database was migrated through `0004`, bootstrapped with one synthetic
administrator, and populated only through the built admin UI/API. Its public profile keys were
exactly `configured`, `full_name`, `professional_title`, and `short_biography`; private email and
internal IDs were absent. It contained one profile, one settings row, two navigation items, one
footer column, one footer item, and zero seed audit events.

The separate seed gate ran with no administrator present. The first invocation reported four
changed aggregates and the second reported zero. Database inspection found no administrator or
session and no private profile, contact, media, analytics-secret, or credential-bearing value.
Production-mode invocation exited with the documented refusal code before writing.

## Findings and corrective loop

| Finding                                                                        | Severity | Correction                                                              | Retest                                                                                   |
| ------------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Initial database probe used a socket path that did not prove TCP readiness     | High     | Probe now calls `pg_isready` on `127.0.0.1`                             | Existing and fresh stacks became healthy through TCP                                     |
| A clean cluster briefly rejected TCP after the original 10-second grace period | Medium   | Increased only the PostgreSQL initialization grace period to 30 seconds | Brand-new-volume `docker compose up --wait` passed and the disposable volume was removed |
| Seed task wrapper did not preserve the project working directory               | Medium   | Corrected the wrapper invocation and added command-parity tests         | First run changed four aggregates; repeat changed zero; production refusal passed        |

## Completion decision

- Gate: Pass for M3-T01 and freezes S1/S2.
- Residual: media-backed profile images remain staged for M9; no placeholder field or storage path
  was introduced.
