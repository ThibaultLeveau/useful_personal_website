# Assumptions and Scope

## In scope for R1

- F1 public website and F2 configurable administration interface.
- One coherent REST API under `/api/v1/`, used through shared application services by public/admin clients.
- Secure administrator bootstrap/session lifecycle and scoped API-token lifecycle.
- Profile/settings, navigation/footer, skills, experiences, projects, blog, configurable pages/blocks, media, contacts, audit, and health.
- PostgreSQL migrations, automated testing, CI validation, local/production containers, and required documentation/open-source files.
- WCAG 2.2 AA target, measurable performance/SEO/accessibility targets, and release security review.
- Documented future-AI module and data-access boundaries only.

## Explicitly out of scope for R1

- F3 agentic RAG assistant and F4 AI resume generator.
- Fake chat, generated resumes, stub LLM responses, or UI implying available AI behavior.
- Microservices, Kubernetes, speculative event-driven/distributed infrastructure, or an unneeded background-job system.
- A mandatory Redis deployment, mandatory cloud object storage, or a specific LLM/vector database/provider.
- Native mobile applications, e-commerce, subscriptions, multi-tenant organizations, and a general-purpose workflow engine.
- Arbitrary administrator-defined executable code, raw unsanitized HTML, or arbitrary database filters.

## Working assumptions requiring confirmation or ADRs

| Assumption ID | Working assumption                                                                                                                                        | Impact if changed                              | Resolution artifact                                    |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------ |
| ASM-001       | R1 has one administrator privilege level, though the data model may avoid blocking future roles.                                                          | Role/permission UI, authorization model, tests | Authentication ADR                                     |
| ASM-002       | Browser administration uses secure server-managed cookie sessions; API consumers use bearer API tokens.                                                   | CSRF/session storage/logout implementation     | Authentication ADR                                     |
| ASM-003       | Public read endpoints need no token and return only published/visible/effective content.                                                                  | API authorization and caching                  | API conventions ADR                                    |
| ASM-004       | Page-number/page-size pagination is the initial default unless the pagination ADR selects cursor pagination before contracts stabilize.                   | Client contract and indexes                    | Pagination ADR                                         |
| ASM-005       | Controlled Markdown is the initial portable blog/rich-text format unless UX needs justify structured JSON.                                                | Editor, sanitization, migration/portability    | Rich-text ADR                                          |
| ASM-006       | Local filesystem media storage is the default for development; production can select a configured storage adapter.                                        | Container volumes/deployment docs              | Media-storage ADR                                      |
| ASM-007       | “Scheduled publication architecture” means the model/query rules support future-dated publication without requiring a background scheduler in R1.         | Public-query logic and admin UI                | Publication decision note/ADR                          |
| ASM-008       | Contact submission deletion may be hard deletion after explicit confirmation; archive is the normal reversible operation.                                 | Retention/privacy/audit behavior               | Retention policy                                       |
| ASM-009       | Analytics settings are public identifiers/placeholders only; secrets stay in environment/secret management.                                               | Settings schema/deployment docs                | Configuration ADR                                      |
| ASM-010       | Audit entries are append-only through application interfaces and are not editable in the admin UI.                                                        | Schema, permissions, retention                 | Audit ADR/policy                                       |
| ASM-011       | English is the initial interface/content-management locale; locale/timezone settings prepare formatting but do not promise full translation management.   | UI copy/data model                             | Product decision                                       |
| ASM-012       | “Basic system health” shows a safe summary and never raw credentials, connection strings, or internal stack traces.                                       | Admin health API/UI                            | Health contract                                        |
| ASM-013       | API rate-limit numbers, upload limits, session duration, token defaults, and retention durations are configurable policy values to be set before release. | Security tests and operator docs               | Security/configuration ADR                             |
| ASM-014       | The maintainer selected the OSI-approved MIT License for permissive open-source distribution.                                                             | Distribution/contributions                     | [License decision](../development/license-decision.md) |
| ASM-015       | Legal/privacy page text is supplied by the owner and is not generated as legal advice.                                                                    | Launch content                                 | Content checklist                                      |

## Constraints

- Required stack choices in NFR-009–NFR-012 are binding unless `SPEC.md` is explicitly changed.
- Public/admin components cannot bypass application services or access PostgreSQL directly.
- Every schema change is migration-backed and must work from an empty database.
- Optional dependencies require a current requirement and an ADR where architecturally significant.
- Security, accessibility, API, documentation, and testing are completion gates, not post-release backlog categories.
- Requirement gaps or contradictions must be documented and resolved; implementation must not silently choose a behavior.

## Key product decisions still open

1. Browser authentication/session mechanism and timeout/renewal policy.
2. Pagination strategy and standard response envelope.
3. Block persistence/versioning model and schema evolution behavior.
4. Rich-text format, editor, sanitizer, and allowed extension set.
5. Media limits, transformations, storage selection, and orphan cleanup.
6. Exact route-reservation registry and slug normalization/collision rules.
7. Publication state machine and future-date/timezone behavior.
8. Contact retention/deletion/export policy and legally appropriate IP handling.
9. Audit retention, access, export, and tamper-evidence expectations.
10. License, deployment topology, backup/restore mechanism, and supported upgrade path.

## Change control

When an assumption is invalidated, update its row, affected requirements/acceptance criteria, the traceability matrix, and any ADR. Do not renumber existing IDs. A new requirement receives the next unused ID in its category; removed requirements become `Rejected` or `Deferred` with rationale.
