# M0-T07 demo-seed closure

## Identity

- Milestone: M0 dependency delivered and certified in M3
- Requirements: F2-002, NFR-012, OSS-002
- Acceptance: AC-015, AC-036, AC-041, AC-044
- Reviewer: Integration/root
- Date: 2026-08-03

## Validation

The explicit demo-seed command uses accepted M3 application facades and the existing transaction
boundary. It is noninteractive, deterministic, fictional, safe to repeat, and never runs during
startup or migration.

| Check                             | Result                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------- |
| Production refusal                | Pass; exits with documented refusal before any write                            |
| Empty migrated database           | Pass; first run reports four changed aggregates                                 |
| Idempotency                       | Pass; second run reports zero changes and no duplicate tree nodes               |
| Authentication separation         | Pass; zero administrators and zero sessions created                             |
| Privacy                           | Pass; private profile/contact/media/analytics fields remain absent              |
| Audit                             | Pass; one safe seed audit fact; no content values or credentials retained       |
| Task/Makefile/Compose/docs wiring | Pass; all invoke the accepted command explicitly                                |
| CI parity                         | Pass locally; workflow repeats refusal, migration, two runs, and SQL inspection |

## Decision

The demo-seed dependency reserved by M0-T07 is closed. The broader environment/container acceptance
remains as recorded in [M0-T07](M0-T07.md); hosted CI execution is not implied by this local result.
