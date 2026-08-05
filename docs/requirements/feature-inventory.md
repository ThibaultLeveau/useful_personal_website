# Feature Inventory

This inventory groups stable requirements into implementable product capabilities. Feature IDs are stable planning handles; requirement IDs remain the authoritative contract.

| Feature ID | Capability                                   | Primary actor                   | Core requirement IDs                    | Suggested milestone | R1 state                                                 |
| ---------- | -------------------------------------------- | ------------------------------- | --------------------------------------- | ------------------: | -------------------------------------------------------- |
| FEAT-001   | Repository and delivery foundation           | Contributor                     | NFR-009–NFR-013, OSS-001–OSS-002        |                 M01 | Verified                                                 |
| FEAT-002   | Backend/frontend application skeleton        | Contributor                     | API-001, NFR-007–NFR-010                |                 M02 | Verified                                                 |
| FEAT-003   | Database and migrations                      | Contributor                     | NFR-006, NFR-011                        |                 M03 | Verified                                                 |
| FEAT-004   | Administrator bootstrap and authentication   | Administrator                   | F2-001–F2-002, SEC-002–SEC-005          |                 M04 | Verified                                                 |
| FEAT-005   | API conventions and health                   | API consumer/operator           | API-001–API-007                         |                 M05 | Verified                                                 |
| FEAT-006   | Website settings and profile                 | Administrator/visitor           | F1-007, F2-003, F2-015                  |                 M06 | Verified                                                 |
| FEAT-007   | Navigation and footer                        | Administrator/visitor           | F1-001, F1-003, F2-014                  |                 M07 | Verified                                                 |
| FEAT-008   | Skills vertical slice                        | Administrator/visitor           | F1-008, F2-004                          |                 M08 | Verified                                                 |
| FEAT-009   | Experience vertical slice                    | Administrator/visitor           | F1-009, F2-005                          |                 M09 | Verified                                                 |
| FEAT-010   | Project vertical slice                       | Administrator/visitor           | F1-010, F2-006                          |                 M10 | Verified                                                 |
| FEAT-011   | Blog vertical slice                          | Administrator/visitor           | F1-011–F1-012, F2-007                   |                 M11 | Verified                                                 |
| FEAT-012   | Configurable pages and block renderer        | Administrator/visitor           | F1-005–F1-006, F2-012–F2-013            |                 M12 | Verified                                                 |
| FEAT-013   | Media library and storage abstraction        | Administrator/visitor           | F1-014, F2-010–F2-011, SEC-007          |                 M13 | Verified; production provider selection remains external |
| FEAT-014   | Contact workflow                             | Visitor/administrator           | F1-013, F2-008–F2-009                   |                 M14 | Verified                                                 |
| FEAT-015   | Scoped API token lifecycle                   | Administrator/API consumer      | F2-016–F2-017, API-008, SEC-008         |                 M15 | Verified                                                 |
| FEAT-016   | Audit log                                    | Administrator/security reviewer | F2-018, SEC-009                         |                 M16 | Verified                                                 |
| FEAT-017   | Public experience polish and discoverability | Visitor                         | F1-001–F1-004, NFR-001, NFR-004–NFR-006 |                 M17 | Verified                                                 |
| FEAT-018   | Administration UX polish                     | Administrator                   | F2-019–F2-020, NFR-001, NFR-004         |                 M17 | Verified                                                 |
| FEAT-019   | Security validation                          | Security reviewer               | SEC-001–SEC-010                         |                 M18 | Verified                                                 |
| FEAT-020   | Accessibility validation                     | All actors                      | NFR-002–NFR-003                         |                 M19 | In progress; physical AT/device acceptance remains open  |
| FEAT-021   | Automated test and release validation        | Contributor/release manager     | NFR-013–NFR-016                         |                 M20 | Verified                                                 |
| FEAT-022   | User, API, and developer documentation       | All actors                      | DOC-001–DOC-003                         |     Every slice/M20 | Verified                                                 |
| FEAT-023   | Open-source governance and change control    | Maintainer/contributor          | OSS-001–OSS-002, CHG-001–CHG-002        |      M01/continuous | Verified                                                 |
| FEAT-024   | Future AI extension boundary                 | Future developer                | AI-001–AI-004                           |      M02/continuous | Verified; boundary only, no R1 AI behavior               |

## Feature dependencies

- FEAT-001–FEAT-005 establish the shared platform and precede vertical slices.
- FEAT-006 and FEAT-007 establish site-wide data/navigation needed by the complete public shell.
- FEAT-008–FEAT-014 are independently demonstrable vertical slices after the foundation, but relationships require referential integration across skills, experiences, projects, blog, and media.
- FEAT-015 precedes third-party API-consumer acceptance.
- FEAT-016 consumes events from all security and content features and should be designed at authentication time, even though the complete viewer is M16.
- FEAT-017–FEAT-023 consolidate cross-cutting gates; their requirements apply throughout development, not only in their final milestone.
- FEAT-024 is a boundary/documentation constraint, not authorization to implement AI behavior.

## Deferred feature inventory

| Future feature                     | State             | Entry condition                                                                     | Applicable readiness IDs |
| ---------------------------------- | ----------------- | ----------------------------------------------------------------------------------- | ------------------------ |
| F3 Agentic RAG portfolio assistant | Deferred          | Explicit scope change, approved requirements, threat/privacy model, evaluation plan | AI-001–AI-004, CHG-002   |
| F4 AI resume generator             | Deferred          | Explicit scope change, approved structured-output and data-handling requirements    | AI-001–AI-004, CHG-002   |
| Background job processing          | Deferred/optional | A current asynchronous workload justifies it                                        | NFR-017, CHG-001         |
| Redis/object storage service       | Optional          | A current performance/storage requirement justifies it                              | F2-011, NFR-017, CHG-001 |
