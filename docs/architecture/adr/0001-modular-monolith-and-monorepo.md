# ADR-0001: Modular Monolith and Monorepo

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

R1 needs tightly integrated content, admin, API, migrations, and tests, while `NFR-007` requires a modular monolith and `NFR-017` rejects premature distributed systems.

## Options considered

Microservices; layer-only monolith; capability-modular monolith in one backend/frontend monorepo.

## Decision

Use one repository with separately deployable FastAPI and Next.js applications. Backend capability modules own domain/application/persistence boundaries; cross-module access is through application facades. PostgreSQL is shared but table ownership is explicit.

## Consequences

Transactions and local development stay simple; module discipline must be enforced by reviews/import tests. Independent service scaling is deferred. Vertical slices touch both applications but share contracts and CI.

## Follow-up

Add dependency-boundary tests and module ownership to developer docs; split a service only after measured operational need and a superseding ADR.
