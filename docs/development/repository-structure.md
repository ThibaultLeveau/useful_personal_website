# Repository Structure

## Current layout

| Path | Purpose | Stewardship |
|---|---|---|
| `SPEC.md` | Original product and engineering specification | Product/architecture governance |
| `docs/requirements/` | Stable requirements, stories, criteria, glossary, and traceability | Requirements owner |
| `docs/architecture/` | Architecture, models, security, dependencies, future extension design, and ADRs | Architecture owner |
| `docs/ux/` | Information architecture, journeys, design system, states, responsiveness, and accessibility | UX owner |
| `docs/plan/` | Milestones, dispatch, task catalog, quality/test strategy, risks, and evidence format | Integration/dispatcher |
| `docs/development/` | Contributor-facing implementation and operational guidance | Topic owner with documentation review |
| `docs/evidence/` | Sanitized, durable task and milestone evidence | Executor; gate decision by independent reviewer |
| `.github/` | Repository collaboration templates; workflows are separately owned | Governance/infrastructure |

## Planned application layout

Accepted ADR 0001 establishes a monorepo containing a FastAPI backend, Next.js frontend, infrastructure assets, and repository-level scripts. Application directories are created only by their dispatched owners. This document does not create or reserve implementation paths beyond the ownership rules in the [Milestone 0 dispatch](../plan/dispatch-m0.md).

Use these authorities when the planned tree and a local observation differ:

1. the active dispatcher reservation for write ownership;
2. accepted ADRs and architecture boundaries;
3. the task catalog's expected files; and
4. this orientation page.

## Boundary rules

- The backend is a modular monolith with domain, application, infrastructure, and API concerns separated as documented in the [architecture overview](../architecture/architecture.md).
- Frontend code does not access the database directly and consumes the official versioned API through the generated-client/wrapper boundary.
- Database changes use one controlled Alembic lineage. Generated API artifacts are integration-owned and never hand-edited.
- Infrastructure injects environment configuration but does not duplicate backend validation or defaults.
- `docs/plan/` and shared contracts are not changed incidentally by feature work.
- Runtime AI packages, fake AI interfaces, and user-facing AI claims are outside R1.

## Adding a top-level path

A new top-level path requires an active task, clear owner, purpose, ignore/packaging implications, and documentation impact. Architecturally significant changes require an ADR; specification changes follow `CHG-002`.
