# M5 acceptance record

## Decision

M5 is accepted as a complete local professional-experience vertical slice on 2026-08-04. Domain,
immutable persistence, sole migration, administrator/public APIs, deterministic generated client,
admin/public UI, lifecycle E2E, privacy, accessibility, security, documentation, and fresh no-seed
runtime gates pass. Lighthouse accessibility/SEO pass; the measured performance target variance is
explicitly carried to release hardening.

The M6 prerequisite audit found that the acceptance text named an `ExperienceReferenceFacade`
without an executable provider. The M5 gate was reopened, the facade and public-safe summary model
were added behind the experience application/repository ports, and 28 focused unit plus 3
PostgreSQL repository tests passed. P2 was reaccepted only after that correction.

## Evidence index

- [Domain/application](M5-T01-domain.md)
- [Persistence/query behavior](M5-T01-persistence.md)
- [Migration and clean-volume runtime](M5-T01-migration.md)
- [Administrator/preview API and contract](M5-T01-admin-api.md)
- [Public projection/privacy](M5-T01-public-projection.md)
- [Administrator frontend](M5-T02-admin.md)
- [Public frontend/accessibility](M5-T02-public.md)
- [Integrated certification and corrective loop](M5-T03.md)
- [Performance/query evidence](performance/README.md)
- [Security certification](security/README.md)
- [Responsive screenshots](screenshots/)

## Frozen candidate

- Backend image: `sha256:bfc6a7bfbba6217e39d8e0efcb27ead1ffe6914113282f9c307c58346c9532cc`
  (37,515,803 bytes)
- Frontend image: `sha256:a2d45531ef2239edde68ebc2af46666cacea113cc6ca3895ee5cb99ef83b05ee`
  (61,460,497 bytes)
- OpenAPI SHA-256: `191663B7A6D0A360C6FD8F831A9A808E71A3BAE70ED20C0CA1F71B07E720B4E9`
- Database current/head: `20260802_0006`

## Boundary

This decision releases M6 planning/implementation against the accepted experience and skills
facades. It is not a production release: later feature milestones, the OSI-license owner decision,
release-wide performance retest, hosted CI, and M14 certification remain outstanding.
