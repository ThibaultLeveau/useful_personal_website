# M4 acceptance record

## Decision

M4 is accepted as a complete local skills vertical slice on 2026-08-03. Final built images, a fresh
empty database at the sole `0005` head, an independently seeded browser database, full backend and
frontend gates, responsive E2E, accessibility/performance review, deterministic generated
artifacts, and blocking image scans all pass.

## Evidence index

- [Backend/domain/API/migration evidence](M4-T01-backend.md)
- [Frontend/accessibility/performance evidence](M4-T02-frontend.md)
- [Integrated gate and acceptance decision](M4-T03.md)
- [Public screenshots](screenshots/)
- [Lighthouse JSON](performance/)
- [Trivy JSON](security/)

## Gate boundary

M4 releases the stable `SkillReferenceFacade` and sole migration head `20260802_0005` for M5. It
does not claim project/experience target links: their providers and revision-scoped associations are
explicitly pending M5/M6. Hosted CI, an external-human reviewer, mobile Lighthouse performance
above 90, release-complete documentation, media-backed icons, and later SEO/CSP work also remain
visible rather than silently waived.
