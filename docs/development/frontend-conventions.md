# Frontend Conventions

## Readiness

Executable frontend conventions and enforcement configuration arrive with `M0-T04`; the generated API-client boundary is frozen later as F4. Until then, the [UX specifications](../ux/information-architecture.md), [architecture overview](../architecture/architecture.md), and [API client ADR](../architecture/adr/0010-openapi-generated-frontend-client.md) are authoritative.

## Required boundaries

- Use the Next.js App Router and strict TypeScript.
- Prefer Server Components when they reduce client JavaScript without harming interaction quality.
- Frontend code never accesses PostgreSQL or another persistence store directly.
- Feature code consumes handwritten API wrappers over the generated client; generated output is never hand-edited.
- Public and admin experiences render API-backed state. Production paths do not use hard-coded portfolio content or disconnected fake controls.
- Shared UI primitives implement the design tokens and interaction contracts rather than feature-local visual systems.

## UX, accessibility, and state

Components must cover loading, empty, success, validation, authorization, error, offline/retry where relevant, and destructive-confirmation states. Keyboard navigation, focus management, semantic markup, labels, announcements, contrast, reflow, reduced motion, and theme behavior are implementation requirements—not deferred polish.

Use the [component inventory](../ux/component-inventory.md), [interaction specification](../ux/interactions-and-states.md), and [accessibility checklist](../ux/accessibility-checklist.md) for normative behavior.

## Quality expectations

New behavior requires strict type checking, component/interaction tests, accessibility checks, representative responsive evidence, and production-build validation as applicable. Exact commands and lint/format conventions will be documented after the frontend harness is implemented.
