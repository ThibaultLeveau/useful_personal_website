# PostgreSQL owner/runtime separation - CI implementer record

## Identity

- Scope: CI enforcement follow-up for the accepted PostgreSQL three-role topology
- Requirements: SEC-009, SEC-010, NFR-012, NFR-016
- Candidate state: uncommitted working tree; hosted execution and integration acceptance pending
- Executor/reviewer: CI implementer / independent review pending
- Completed UTC: 2026-08-02

## Delivery

- Added a required `database_privileges` job with a run-and-attempt-scoped Compose project and three distinct synthetic credentials.
- The job validates both Compose profiles, excludes mutators from default startup, starts the existing digest-pinned PostgreSQL stack, and invokes the repository's role initialization, migration, permission reconciliation, and permission-check services explicitly.
- It requires fail-closed checks before migration and before grant reconciliation, exactly one Alembic head, owner upgrade/current checks, runtime allow/deny probes, and owner downgrade/upgrade/reconciliation.
- Runtime proof covers ordinary administrator/session/rate-limit DML and audit insert/select. It requires denials for audit update/delete/truncate, trigger disable, persistent and temporary DDL, ordinary-table alteration, and Alembic metadata writes.
- An always-run credential scan checks captured output for every synthetic password. No database-privilege log is uploaded or retained as an artifact.
- A later always-run cleanup removes the exact job-owned project with volumes and asserts that no project-labelled container, volume, or network remains.
- Added the job to the required aggregate gate.
- Corrected the backend job after independent review: it generates and masks three distinct synthetic credentials, starts an exact-name pinned PostgreSQL container, bootstraps roles through the existing role script, gives Alembic only the migration-owner URL, gives Pytest application fixtures only the runtime URL, and runs the existing permission reconciliation/check scripts before tests.
- Added a temporary JUnit inspection that requires at least the frozen 74-test inventory with zero skips. The JUnit report is not uploaded; the existing credential-free coverage artifact remains the only backend test artifact.
- Added an always-run report credential scan before artifact upload and an exact-container always-run cleanup. Database passwords and URLs are masked and passed to Docker only by environment-variable name.

## Static and local validation

| Check                       | Result                                                                                                                                                                                  |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workflow semantics          | Pass: digest-pinned actionlint reported no findings.                                                                                                                                    |
| Compose interpolation       | Pass: default and `operations` profile configurations resolve with representative distinct synthetic credentials.                                                                       |
| Default startup boundary    | Pass: workflow explicitly rejects `role-init`, `migrate`, or `permissions` in the default service set.                                                                                  |
| Immutable action references | Pass: every `uses` reference remains a full 40-character lowercase commit SHA.                                                                                                          |
| Aggregate wiring            | Pass: `database_privileges` is both a `gate.needs` dependency and an evaluated aggregate result.                                                                                        |
| Backend credential topology | Pass: static workflow inspection proves distinct bootstrap/owner/runtime values, owner-only migration, runtime-only application URL, and reuse of the reviewed role/permission scripts. |
| Backend skip enforcement    | Pass: the temporary JUnit check rejects any skip and an inventory below 74 tests.                                                                                                       |
| Backend test inventory      | Pass: local collection finds 74 tests; the backend implementer record reports 74/74 under the split-role local stack. Hosted execution remains pending.                                 |
| Formatting                  | Pass: Prettier reports the workflow and both CI documentation files clean.                                                                                                              |
| Repository policy           | Pass at validation: repository checks completed for 295 visible files.                                                                                                                  |
| Whitespace                  | Pass: `git diff --check` reported no findings.                                                                                                                                          |

## Corrective loop

| Finding                                                                                                                                                                                     | Severity | Correction                                                                                                                                                                                                                                         | Retest                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| The backend CI job supplied one PostgreSQL bootstrap identity as `TEST_DATABASE_URL` and omitted `TEST_DATABASE_OWNER_URL`, so split-role tests could skip or run with excessive privilege. | High     | Generate and mask distinct credentials; initialize roles with `init-roles.sh`; migrate as owner; reconcile/check grants with the existing scripts; assign owner/runtime fixture URLs explicitly; fail on skips; scan reports and clean up exactly. | Actionlint, YAML/semantic inspection, Compose/script contract review, repository checks, and focused local backend tests pass. Hosted 74-test execution remains pending. |

No hosted GitHub Actions run was available from this implementation environment, so this record does not claim that the new job has executed on a hosted runner. The full database privilege behavior remains covered by the accepted isolated infrastructure proof; the workflow now encodes that same boundary for hosted enforcement.

## Completion decision

- CI implementation: complete and statically validated, including the backend split-role correction.
- Hosted execution: pending the next pull request, push to `main`, or manual dispatch; this record does not claim the hosted 74-test job has run.
- Acceptance: not asserted; integration/root and an independent reviewer own the decision.
