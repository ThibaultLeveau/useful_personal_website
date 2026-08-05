# Extension Guide

## Purpose

Extensions must preserve the modular-monolith, API-first, secure-by-default architecture. This guide points to accepted boundaries; it does not authorize speculative infrastructure or deferred product scope.

## Adding an R1 capability

1. Link an active requirement, user story, acceptance criterion, and dispatched task.
2. Identify the owning domain and reuse existing invariants rather than duplicating logic.
3. Design the application use case and ports before transport or vendor adapters.
4. Add persistence through the controlled migration process and API behavior through the versioned contract.
5. Regenerate the client through the integration-owned pipeline; do not hand-edit generated output.
6. Complete admin and relevant public behavior, tests, security/privacy/accessibility review, documentation, and traceability as one vertical slice.
7. Record an ADR when the change affects architecture, dependency direction, data ownership, deployment topology, or public compatibility.

## External services and dependencies

Adapters isolate external SDKs. A new dependency needs an active requirement, alternatives analysis, module owner, failure behavior, security and license review, exact locked version, and tests. Optional infrastructure is introduced only after measured need and an accepted decision.

## Future AI boundary

F3/F4 are out of R1. The [future AI extension design](../architecture/future-ai-extension-design.md) defines provider, retrieval, execution, prompt, evaluation, usage, and audit boundaries and restricts future consumption to published portfolio projections. Do not add AI runtime packages, provider credentials, embeddings/vector infrastructure, fake responses, or AI UI in R1 without an approved specification change and ADR.

## Compatibility

Extensions must preserve API versioning, explicit schemas, authorization, error contracts, idempotency/concurrency rules, public/private projection separation, migration safety, and generated-client reproducibility. Breaking changes require the `CHG-002` process and explicit migration and consumer guidance.
