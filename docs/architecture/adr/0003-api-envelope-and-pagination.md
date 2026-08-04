# ADR-0003: API Envelope and Pagination

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

OpenAPI clients require one predictable success/error/list contract (`API-003`–`API-006`). R1 collections are admin/content sized.

## Options considered

Bare resources; `{data,meta}` envelope. Offset page pagination; cursor pagination.

## Decision

Use `{data, meta:{request_id,...}}` success and the specified `{error:{code,message,details,request_id}}` failure envelope. Lists use `page`/`page_size`, default 20 and maximum 100, with item/page totals. Filters and sorts are endpoint allow-lists with deterministic ID tie-breaker.

## Consequences

Contracts are uniform and totals support admin UI. Very deep pages are less efficient and concurrent changes can shift items; this is acceptable at R1 scale. A future high-volume endpoint may introduce cursor semantics only through a versioned contract/ADR.

## Follow-up

Publish shared Pydantic generics, contract tests, generated-client validation, and documented filter/sort catalogs.
