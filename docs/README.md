# Documentation

This directory is the source of truth for product intent, architecture, experience design, delivery planning, developer guidance, and durable validation evidence. Documents use stable requirement and acceptance IDs so implementation and review remain traceable.

## Product and requirements

- [Product requirements](requirements/product-requirements.md)
- [Feature inventory](requirements/feature-inventory.md)
- [User stories](requirements/user-stories.md)
- [Acceptance criteria](requirements/acceptance-criteria.md)
- [Traceability matrix](requirements/traceability-matrix.md)
- [Domain glossary](requirements/domain-glossary.md)
- [Assumptions and scope](requirements/assumptions-and-scope.md)

## Architecture

- [Architecture overview](architecture/architecture.md)
- [Domain model](architecture/domain-model.md)
- [Database model](architecture/database-model.md)
- [API structure](architecture/api-structure.md)
- [Security architecture](architecture/security-architecture.md)
- [Dependency map](architecture/dependency-map.md)
- [Future AI extension design](architecture/future-ai-extension-design.md)
- [Architecture decision records](architecture/adr/README.md)

## UX and accessibility

- [Information architecture](ux/information-architecture.md)
- [Screen inventory](ux/screen-inventory.md)
- [User journeys](ux/user-journeys.md)
- [Design system](ux/design-system.md)
- [Component inventory](ux/component-inventory.md)
- [Interactions and states](ux/interactions-and-states.md)
- [Responsive rules](ux/layouts-and-responsive-rules.md)
- [Accessibility checklist](ux/accessibility-checklist.md)
- [Visual direction](ux/visual-direction.md)

## Delivery planning

- [Implementation plan](plan/implementation-plan.md)
- [Milestone plan](plan/milestone-plan.md)
- [Task catalog](plan/task-catalog.md)
- [Quality strategy](plan/quality-strategy.md)
- [Test strategy](plan/test-strategy.md)
- [Risk register](plan/risk-register.md)
- [Milestone 0 dispatch](plan/dispatch-m0.md)
- [Delivery evidence template](plan/delivery-evidence-template.md)

Planning documents are dispatcher-owned. Contributors should not change them incidentally with implementation work.

## Developer guidance

The [developer documentation index](development/README.md) maps each required topic to its current authority and readiness. Toolchain and command details remain pending until their Milestone 0 contract freezes; skeleton pages must not be treated as executable setup instructions.

## User and API guidance

- [User and operator documentation](user/README.md)
- [First administrator setup and sign-in](user/first-login.md)
- [API documentation](api/README.md)
- [Browser administrator authentication](api/authentication.md)
- [Manage and publish skills](user/skills.md)
- [Skills API](api/skills.md)
- [Manage professional experience](user/experiences.md)
- [Experiences API](api/experiences.md)
- [Experience slice architecture](development/experiences.md)
- [Manage configurable pages and blocks](user/pages.md)
- [Pages API](api/pages.md)
- [Configurable page architecture](development/pages.md)

## Evidence

Task and milestone evidence belongs under `evidence/<requested-milestone>/` and follows the [delivery evidence template](plan/delivery-evidence-template.md). Evidence must use repository-relative references and must never contain secrets, authentication material, private data, production dumps, or machine-specific absolute paths.

The current release-readiness record is [M13 productization and hardening](evidence/M13/README.md).
It remains blocked on the documented coverage, owner-decision, production-environment, and manual
accessibility gates; it must not be read as release acceptance.

## Documentation rules

- Link to the authoritative document instead of duplicating normative content.
- Preserve stable requirement, acceptance, risk, task, and ADR identifiers.
- Mark incomplete material and unresolved owner decisions explicitly.
- Describe only commands and behavior that have been implemented and validated.
- Update nearby indexes and inbound links when adding, moving, or replacing a document.
- Use repository-relative links and examples with synthetic, non-sensitive values.
