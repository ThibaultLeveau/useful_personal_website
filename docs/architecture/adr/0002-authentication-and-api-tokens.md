# ADR-0002: Administrator Authentication and API Tokens

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Browser administration needs secure logout/revocation/CSRF controls; external consumers need scoped non-browser credentials (`F2-001`, `F2-016`, `SEC-002`–`SEC-008`).

## Options considered

Browser JWTs in storage; server-managed opaque sessions; third-party identity provider only. API tokens as JWTs or random reference tokens.

## Decision

Use Argon2id passwords and PostgreSQL-backed opaque browser sessions in a `__Host-` Secure/HttpOnly/SameSite cookie, with signed session-bound CSRF token and Origin validation. Use random bearer reference tokens with public selector, HMAC digest, scopes, expiry/revocation/rotation. Store no recoverable secret. R1 has one admin privilege level.

## Consequences

Immediate revocation and session inspection are straightforward; each authenticated request reads PostgreSQL. CSRF is explicit. Token lookup is efficient without JWT claim-staleness problems. A token secret is displayed exactly once.

## Follow-up

Benchmark Argon2id, test the complete route/scope matrix, document key rotation, and require explicit bootstrap/initial password change.
