# ADR-0006: Media Storage Abstraction

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Development needs simple storage; production needs durable scalable storage without coupling domain code to a vendor (`F2-010`, `F2-011`).

## Options considered

Database blobs; direct filesystem calls; `MediaStorage` port with local and S3-compatible adapters.

## Decision

Keep media metadata/usage in PostgreSQL and bytes behind a storage port. Provide local persistent-volume adapter for development/single host and private S3-compatible adapter for production. Validate decoded content before promotion to opaque immutable keys. Deliver only authorized/publicly referenced objects via backend-controlled response or short-lived signed URL.

## Consequences

Storage is replaceable and objects are private by default. DB/object writes are not one atomic transaction, so upload/delete use staged keys, compensation, and reconciliation. Local storage does not support arbitrary replica scaling.

## Follow-up

Adapter contract tests, orphan reconciliation command, provider/region/backup decision, malicious upload tests, and active-usage locking on delete.
