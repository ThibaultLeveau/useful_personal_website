# M6 acceptance record

## Decision

M6 is accepted as a complete local project case-study vertical slice on 2026-08-04. Project domain,
immutable persistence, sole migration, administrator/public APIs, deterministic generated client,
administrator/public UI, lifecycle E2E, privacy, accessibility, SEO, security, documentation, and
fresh no-seed runtime gates pass. Throttled-mobile Lighthouse performance remains explicitly open
for release hardening.

## Evidence index

- [Domain/application and P3](M6-T01-domain.md)
- [Persistence and query behavior](M6-T01-persistence.md)
- [Migration `0007`](M6-T01-migration.md)
- [Administrator/preview API](M6-T01-admin-api.md)
- [Public projection and P4](M6-T01-public-projection.md)
- [Administrator frontend](M6-T02-admin.md)
- [Public frontend and P5](M6-T02-public.md)
- [Integrated certification and corrective loop](M6-T03.md)
- [Performance and metadata](performance/README.md)
- [PostgreSQL plans](performance/query-plans.md)
- [Security certification](security/README.md)
- [Responsive screenshots](screenshots/)

## Frozen candidate

- Backend image:
  `sha256:55951a68cbdbf8b8847b67a6774778c996035f9ec42ba2f7bd430c5c83ed4ef3`
  (37,541,383 bytes)
- Frontend image:
  `sha256:e93fe0cd0ffffbabb4a5ea871e0975a76e8b0b5d7db7befb9e5e243ec8d51286`
  (61,542,348 bytes)
- OpenAPI SHA-256: `7d5d7e7242138ad56de22ffe8c6a4fc593bf14ba71b833487038631b449ee1a3`
- Generated client tree SHA-256:
  `2a08dc54f20f2c85829cb893891e7b4170eb596ea72c8508896c1fe8acd55338`
- Database current/head: `20260802_0007`

## Boundary

This decision releases M7 against the accepted project, experience, and skills application-facing
contracts. It is not a production release: later content/media/API/operations milestones, the
OSI-license owner decision, mobile performance optimization, hosted CI, and M14 certification
remain outstanding. Future AI extension points stay architectural only; no AI runtime or user-facing
claim is shipped.
