# ADR-0012: Production Deployment Topology

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

R1 needs production-oriented containers, health checks, migrations, media durability, and no direct frontend database access (`NFR-008`, `NFR-012`, `API-007`).

## Options considered

Single combined container; Kubernetes/microservices; TLS edge with separate Next.js/FastAPI containers, PostgreSQL, private object storage.

## Decision

Deploy Next.js and FastAPI separately behind one TLS edge/same origin. PostgreSQL and private S3-compatible storage remain on private networks. Run Alembic once as a release job before rollout; runtime containers never auto-migrate. Liveness is process-only; readiness checks PostgreSQL and migration compatibility. Redis/worker are absent.

## Consequences

Frontend/backend scale and release independently while retaining a simple topology. Production requires coordinated DB/object backups and trusted-origin/proxy configuration. Local Compose may use PostgreSQL and local media volume.

## Follow-up

Choose provider/region/hostnames, secret manager, backup RPO/RTO, restore exercise, container hardening, edge headers/limits, and rollout/rollback runbook before release.
