# M2-T02 backend - Operational health contract

## Identity

- Requested milestone: M2
- Existing trace milestone alias(es): M05
- Requirement IDs: F2-020, API-002, API-006-API-007, SEC-004-SEC-005, SEC-009
- Acceptance IDs: AC-026-AC-030, AC-039
- Build/commit: uncommitted integration working tree
- Environment: Python 3.12.13; FastAPI 0.141.1; PostgreSQL 17.10
- Executor/reviewer: Backend implementation lane; Integration/root certification review
- Completed UTC: 2026-08-03

## Delivery

Three deliberately distinct health audiences are implemented:

| Endpoint                   | Audience and behavior                                                                  | Cache contract      |
| -------------------------- | -------------------------------------------------------------------------------------- | ------------------- |
| `GET /api/v1/health/live`  | anonymous process-only check; performs no dependency call                              | `no-store`          |
| `GET /api/v1/health/ready` | anonymous PostgreSQL connectivity plus packaged/current Alembic revision compatibility | `no-store`          |
| `GET /api/v1/admin/health` | fully authenticated safe aggregate/build summary only                                  | `private, no-store` |

Readiness returns a typed, safe `503 not_ready` state for database outage, timeout, and revision
mismatch. Admin health discloses neither host/port, connection material, SQL, environment values,
stack/exception details, nor raw migration internals.

## Validation

| Scenario                                                               | Result                                                                 |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Liveness with healthy, unreachable, and revision-mismatched dependency | Pass; identical `200` process response and no dependency invocation    |
| Ready with current PostgreSQL revision                                 | Pass; `200 ready` and correlated request ID                            |
| Database outage/timeout/revision mismatch                              | Pass; safe `503 not_ready` categories                                  |
| Admin authenticated/anonymous/expired                                  | Pass; safe success, `401`, and expiry denial                           |
| Cache and disclosure inspection                                        | Pass; exact cache headers and no forbidden infrastructure/secret terms |
| Direct final-image probes                                              | Pass; live/ready `200`, both `Cache-Control: no-store`                 |
| OpenAPI security/examples/errors/headers                               | Pass; deterministic C2 export and client generation                    |

## Finding and correction

The first probe implementation omitted explicit cache headers. The probes now set `no-store`, admin
health sets `private, no-store`, those headers are part of the OpenAPI response contract, and both
unit/integration plus live final-image requests were rerun successfully.

## Completion decision

- Gate: Pass for backend health.
- Contract freeze: C2 recorded in [M2 contract freeze](M2-contract-freeze.md).
