# ADR-0010: OpenAPI-Generated Frontend Client

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Next.js must consume the API without schema drift or database access (`API-001`, `API-002`, `NFR-008`).

## Options considered

Handwritten fetch types; shared Python/TypeScript models; generated TypeScript client from OpenAPI.

## Decision

Generate a pinned TypeScript client from the validated FastAPI OpenAPI artifact and wrap it in feature-level frontend functions. Server Components and client islands use the same wrappers. Upload streaming may use a small reviewed handwritten adapter while retaining generated request/response types.

## Consequences

Contract drift fails CI and frontend calls remain typed. Generated code adds review noise and generator compatibility constraints. Domain/UI types may still differ intentionally and are mapped in feature code.

## Follow-up

Pin generator, stabilize operation IDs, regenerate/check diff in CI, and contract-test envelopes/security schemes.
