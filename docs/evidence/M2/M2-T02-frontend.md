# M2-T02 frontend - Administrator health experience

## Identity

- Requested milestone: M2
- Existing trace milestone alias(es): M05
- Requirement IDs: F2-019-F2-020, NFR-002-NFR-004, API-002, API-007, SEC-005, SEC-009
- Acceptance IDs: AC-025-AC-026, AC-032-AC-033, AC-039
- Build/commit: uncommitted integration working tree
- Environment: Node.js 22.23.2; pnpm 11.18.0; Next.js 16.2.12; Storybook 10.5.5
- Executor/reviewer: Frontend implementation lane; Integration/root browser/a11y review
- Completed UTC: 2026-08-03

## Delivery

`/admin/health` consumes the generated health client through the same-origin typed wrapper. It
renders Operational, Degraded, Unavailable, and Unknown states, last-checked time, retained stale
results, request-ID/documentation guidance, and a refresh action that disables only itself and
announces completion through a polite live region. Authentication expiry clears protected health
content before routing to the dedicated expiry page.

## Validation

| Category                              | Result                                                                                                                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prettier, ESLint, strict TypeScript   | Pass                                                                                                                                                                      |
| Vitest                                | Pass; 12 files and 86 tests                                                                                                                                               |
| Critical health component coverage    | 97.43% statements, 93.33% branches, 100% functions/lines                                                                                                                  |
| Aggregate frontend coverage           | 68.28% statements / 59.49% branches / 64.96% functions / 71.12% lines; generated client lowers aggregate and is covered by contract generation/compile plus wrapper tests |
| Production build                      | Pass; all 9 routes built                                                                                                                                                  |
| Storybook build                       | Pass; large-chunk notices are confined to the docs/axe harness, not the production Next bundle                                                                            |
| Production dependency audit           | Pass; no known vulnerabilities                                                                                                                                            |
| Real built-app Playwright             | Pass; health 2/2 and combined auth+health 4/4 at 320 and 1440                                                                                                             |
| Automated accessibility               | Pass; zero axe violations at both target widths                                                                                                                           |
| Manual responsive/theme/outage/expiry | Pass; 320/1440, light/dark/system, outage/recovery, and externally revoked session                                                                                        |

Screenshots:

- [320 px operational](screenshots/admin-health-320.png)
- [1440 px operational](screenshots/admin-health-1440.png)
- [manual outage in dark mode](screenshots/admin-health-outage-manual.png)

## Findings and corrective loop

| Finding                                                                              | Severity | Correction                                                                            | Retest                                                                                      |
| ------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Session expiry could race the auth boundary and briefly route through ordinary login | High     | shared expiry action plus explicit signed-out reason and one-time destination         | unit tests and real external-revocation browser proof pass; no protected health DOM remains |
| Screenshot protocol left the skip link visibly focused on mobile                     | Low      | move focus to the main landmark and verify the skip link is off-canvas before capture | regenerated 320/1440 screenshots visually inspected                                         |
| Combined auth/health E2E raced shared administrator rate-limit state                 | Medium   | configure one serial worker for the stateful real-stack lifecycle                     | combined regression 4/4                                                                     |

## Completion decision

- Gate: Pass for M2-T02 frontend.
- User documentation: [System health](../../user/system-health.md).
