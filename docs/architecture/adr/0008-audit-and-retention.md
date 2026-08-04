# ADR-0008: Audit and Retention

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Security/content actions need attribution without turning audit into a secret/PII repository; contacts require documented archive/delete behavior (`F2-008`, `F2-018`, `SEC-009`).

## Options considered

Ordinary logs only; mutable audit table; append-only application audit with controlled retention.

## Decision

Use an append-only audit table with controlled event types, actor/resource/request IDs, outcome, schema-versioned allow-listed metadata, and keyed-HMAC IP pseudonym where needed. No password/token/auth header/contact body/email. Application role cannot update audit. Default audit retention is 400 days. Contacts archive reversibly, allow explicit audited hard delete, and default to 365-day retention. R1 purges through dry-run-capable operator commands.

## Consequences

Useful traceability is retained with bounded privacy exposure. Application-level append-only is not cryptographic tamper evidence; database/operator access remains privileged. Jurisdiction may require shorter/different periods.

## Follow-up

Owner/legal validates periods before release; test event coverage/redaction; document backup/purge permissions. Add tamper-evident export only if a real compliance requirement appears.
