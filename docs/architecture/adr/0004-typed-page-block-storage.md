# ADR-0004: Typed Page Block Storage

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Blocks are heterogeneous but must be schema-validated, reorderable, referentially safe, and evolvable (`F1-005`, `F1-006`).

## Options considered

One table per block; unconstrained JSON document; relational common shell with typed/versioned JSONB config and normalized references.

## Decision

Store common/queryable fields relationally, type-specific config in JSONB validated by a Pydantic discriminated-union registry, and content/media links in normalized reference rows. Every block records `block_type` and `schema_version`. Blocks belong to immutable page revisions.

## Consequences

Adding block types avoids migrations for every presentation option while validation stays explicit. Database cannot enforce every polymorphic target FK; application publish validation and reference/usage tables close that gap. Schema changes require adapters/data migrations.

## Follow-up

Create backend/frontend registry parity tests, fixtures for every type/version, reference integrity tests, and reject unknown fields/types.
