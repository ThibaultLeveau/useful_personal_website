# M2-T01 backend - Common API conventions and persistence

## Identity

- Requested milestone: M2
- Existing trace milestone alias(es): M05 API conventions and health
- Requirement IDs: API-001-API-006, SEC-004, SEC-006, NFR-007-NFR-008, NFR-011, NFR-014-NFR-016
- Acceptance IDs: AC-027-AC-030, AC-035-AC-039
- Build/commit: uncommitted integration working tree
- Branch/PR: N/A
- Environment: Python 3.12.13; PostgreSQL 17.10; Alembic 1.18.5
- Executor/reviewer: Backend implementation lane; Integration/root certification review
- Completed UTC: 2026-08-03

## Delivery

The backend common layer now provides typed actor contexts, explicit authorization decisions,
UTC/date/opaque-ID rules, page metadata and deterministic ordering, allow-listed collection query
parsing, integer-version preconditions, stable error mapping, and digest-only actor/route-scoped
idempotency. The implementation remains behind application/domain ports; it does not reach into
identity ORM types or expose database concepts to API consumers.

The sole M2 migration is `20260802_0003_api_conventions.py`, down from accepted revision
`20260802_0002`. It adds only the idempotency record and operational indexes. Stored keys and
payloads are digests; successful replay retains a safe result code/status rather than a private
response body. Expired records are reusable and purgeable after the 24-hour policy window.

## Validation

| Category             | Protocol                                                                                                                               | Result                                                                                |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Format/lint/type     | Ruff format/check and strict Mypy over the backend                                                                                     | Pass; 85 files clean and no type errors                                               |
| Backend tests        | Pytest unit, service, repository, integration, architecture, and migration suites against isolated PostgreSQL                          | Pass; 116 passed, 0 skipped                                                           |
| Coverage             | Branch-aware coverage                                                                                                                  | Pass; 91.47% total, above the 85% backend target                                      |
| Query grammar        | Defaults/max/beyond-last metadata; duplicate, arbitrary `filter[...]`, encoded operator, SQL-shaped, and unsupported sort/filter cases | Pass; invalid input is rejected with typed `422` behavior and no column interpolation |
| PostgreSQL traversal | Five tied records, page size two, allow-listed filter/sort, mandatory `id` tie-breaker                                                 | Pass; exact totals, no loss/duplication, empty beyond-last page                       |
| Idempotency          | acquire/replay/payload conflict/expiry/purge and synchronized duplicate admission                                                      | Pass; one record and one acquisition, replay for the duplicate                        |
| Migration            | empty database, accepted `0002` to head, current database, constraints/indexes, single-head checks                                     | Pass; exact packaged head `20260802_0003`                                             |
| Architecture         | import-boundary scan                                                                                                                   | Pass; API -> application -> domain with infrastructure behind ports                   |
| Security             | Bandit 1.9.4 and pip-audit 2.10.1                                                                                                      | Pass; no findings and no known dependency vulnerabilities                             |

The narrow Bandit suppression on the public `api_token` actor-kind enum is a documented
hard-coded-password false positive; the value is a type discriminator, not a credential. Bandit
was rerun after the scoped annotation and remained clean.

## Acceptance record

| Acceptance | Status | Evidence                                                                   |
| ---------- | ------ | -------------------------------------------------------------------------- |
| AC-027     | Pass   | Stable `/api/v1` schemas and the [contract freeze](M2-contract-freeze.md)  |
| AC-028     | Pass   | Common contract unit suite and [API conventions](../../api/conventions.md) |
| AC-029     | Pass   | PostgreSQL deterministic traversal and adversarial query-parser suite      |
| AC-030     | Pass   | Error/status registry, safe details, correlation, and disclosure tests     |
| AC-035     | Pass   | Architecture-boundary test and typed ports                                 |

## Findings and corrective loop

| Finding                                                                   | Severity | Root cause                                                | Correction                                                   | Retest                                  |
| ------------------------------------------------------------------------- | -------- | --------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------- |
| Persistence tests depended on a database left migrated by an earlier test | High     | fixture did not independently establish the packaged head | isolated fixture now migrates its own database to exact head | full isolated PostgreSQL suite: 116/116 |
| Bandit classified an actor-kind string as a password                      | Low      | lexical false positive                                    | narrow, explained line annotation only                       | Bandit: zero findings                   |

## Completion decision

- Gate: Pass for M2-T01 backend.
- Residual: the first production collection consumer will exercise these frozen helpers in its own
  vertical-slice API; M2 verifies the contract through an isolated PostgreSQL conformance harness
  rather than adding a fake production collection route.
