# ADR-0009: No Required Redis or Worker in R1

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Redis/workers are optional and must be justified. R1 publication can be time-gated and workloads are low volume (`NFR-017`).

## Options considered

Mandatory Redis+worker; in-memory scheduling/limits; PostgreSQL security counters plus platform cron/operator commands.

## Decision

Do not deploy Redis, broker, or application worker in R1. Use PostgreSQL atomic rate-limit buckets, edge volumetric throttling, database-time publication, and idempotent CLI commands for retention/orphan maintenance. Define an application-command boundary so a later worker can call the same use cases.

## Consequences

Operations and failure modes stay small. PostgreSQL handles modest extra writes; maintenance timing belongs to the operator. Long-running/retry-heavy capabilities require a later queue decision.

## Follow-up

Load-test security counters. Add Redis/worker only with an active workload, availability/idempotency analysis, metrics, and superseding ADR.
