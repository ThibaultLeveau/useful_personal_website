# ADR-0011: Future AI Boundary

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

R1 must be AI-ready but must not ship fake/speculative F3/F4 infrastructure (`AI-001`–`AI-004`).

## Options considered

Preinstall an AI stack; let future AI query content tables; document provider ports and a publication-safe content source.

## Decision

R1 documents an `ai` boundary and a `PublishedContentSource` supplied by content application/public-query services. No runtime AI dependency/table/UI is added. Future real scope uses provider/retrieval/vector/agent/prompt/usage/evaluation/tracing ports. If incremental indexing is required, add a transactional outbox and rebuildable published-document projection then.

## Consequences

Publication/privacy rules remain authoritative and vendors remain replaceable. Future work must implement ingestion infrastructure rather than inheriting speculative code. Snapshot reads may be sufficient initially.

## Follow-up

Before F3/F4, approve requirements, threat/privacy/evaluation plan, provider retention, structured outputs, cost/abuse limits, outbox/worker/vector ADRs, and unpublish deletion tests.
