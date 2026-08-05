# ADR-0007: Publication Revisions and Scheduling

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Administrators must edit drafts/preview without changing live content and support future-dated publication (`F1-011`, `F2-005`–`F2-007`, `F2-012`).

## Options considered

Mutable row with status; full event sourcing; stable aggregate with immutable draft/published revisions.

## Decision

Pages, projects, experiences, and posts use stable aggregate rows pointing to draft and published revisions. Publishing freezes a consistent revision; later edits are copy-on-write. Public queries require a published pointer, visibility, nondeleted state, and `publish_at <= PostgreSQL now()`. Future dates need no scheduler.

## Consequences

Draft leakage and partial publication are prevented; storage/query complexity increases. Scheduled content appears based on database time and cache TTL/invalidation. Unpublish is immediate at the source.

## Follow-up

Test preview isolation, copy-on-write, concurrent publication, timezone conversion, reference validation, sitemap exclusion, and cache bounds.
