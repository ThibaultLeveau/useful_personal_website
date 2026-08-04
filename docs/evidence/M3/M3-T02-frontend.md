# M3-T02 frontend - Public profile and configuration editors

## Identity

- Requested milestone: M3
- Trace milestone aliases: M06/M07
- Requirements: F1-002-F1-004, F1-007, F2-003, F2-014-F2-015, F2-019,
  NFR-001-NFR-010, SEC-004-SEC-005, SEC-009
- Acceptance: AC-003, AC-007, AC-021-AC-022, AC-025, AC-031-AC-035
- Build/commit: uncommitted integration working tree
- Environment: Node.js 22.23.2; pnpm 11.18.0; Next.js 16.2.12; Storybook 10.5.5;
  Playwright; Lighthouse 12.8.2
- Executor/reviewer: Integration/root implementation plus manual browser and separated built-image
  review
- Completed UTC: 2026-08-03

## Delivery

The public home/about shell, header, navigation, and footer render through a server-only wrapper
around the generated public client. Public routes use bounded 60-second revalidation and targeted
tag/path invalidation after authenticated admin mutation. Missing configuration renders explicit
empty states rather than invented business content. Admin profile, settings, navigation, and footer
editors provide labeled validation, dirty-state navigation protection, safe failures, conflict
recovery, and keyboard-accessible ordering controls.

The production image uses Next standalone output. Browser headers include CSP restrictions for
base, form, frame, and object contexts, HSTS, `nosniff`, same-origin opener/resource policies,
referrer policy, permissions policy, and frame denial. A per-request script nonce is intentionally
deferred because the current public routes use ISR; the policy does not add `unsafe-inline`.

## Validation

| Category                            | Result                                                                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Prettier, ESLint, strict TypeScript | Pass; zero warnings/errors                                                                                                                 |
| Vitest                              | Pass; 17 files and 104 tests                                                                                                               |
| Coverage                            | 50.37% statements / 32.98% branches / 44.39% functions / 52.94% lines overall; generated client materially dilutes aggregate coverage      |
| Critical component coverage         | Auth 82%, health 97%; M3 editors approximately 58-67% statements, below the 80% improvement target but covered by focused real-stack E2E   |
| Storybook                           | Pass; expected static docs/axe chunk notice only                                                                                           |
| Production build                    | Pass; `/` and `/about` are ISR routes with one-minute revalidation                                                                         |
| Production E2E                      | Pass; 12/12 combined auth, health, shells, and site-configuration tests at 320/1440                                                        |
| Fresh no-seed E2E                   | Pass; authentication 2/2 and configuration 2/2 at 320/1440 against final built images and database head `0004`                             |
| Accessibility                       | Automated axe: zero violations; manual keyboard/reflow/theme/drawer pass; desktop Lighthouse accessibility 100                             |
| Desktop Lighthouse                  | Home 100/100/100 performance/accessibility/SEO; About 99/100/100; CLS 0; LCP 639/797 ms; transferred about 178 KB, about 158 KB JavaScript |
| Mobile Lighthouse                   | Home 68/100/100 and About 78/100/100; CLS 0; performance target variance recorded below                                                    |

Screenshots:

- [configured About at 320 px](screenshots/configured-about-320.png)
- [configured About at 1440 px](screenshots/configured-about-1440.png)

Manual in-app browser review verified the 320-pixel modal menu, dark theme, no horizontal
overflow, scroll lock, Escape/Close behavior, and focus restoration to the Menu control. Console
inspection found no error. Public pages contained no private email.

## Findings and corrective loop

| Finding                                                               | Severity | Correction                                                              | Retest                                                                                                  |
| --------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Build-time API absence could freeze the public fallback indefinitely  | High     | Added route-level 60-second revalidation                                | Built image refreshed from the live API without rebuild                                                 |
| Stale-while-revalidate could serve one old response after mutation    | High     | Server Action uses immediate tag expiry plus explicit path revalidation | Admin-to-public E2E shows updated content and removed private data on reload                            |
| Runtime packaging depended on a network-heavy deploy step             | Medium   | Switched to traced Next standalone output                               | Production image built, started read-only/non-root, and E2E passed; compressed size is 61,388,319 bytes |
| Authentication redirect and ambiguous field locators caused E2E races | Medium   | Waited for either valid redirect and used exact accessible labels       | Full built-stack suite passed 12/12                                                                     |
| Next responses lacked the browser security-header baseline            | High     | Added tested response headers without weakening CSP via `unsafe-inline` | Live `/about` header inspection and final image E2E passed                                              |

## Target variances and disposition

- Mobile Lighthouse performance (68/78) is below the >=90 target under Windows/Docker CPU
  throttling, while desktop is 99-100, accessibility/SEO are 100, CLS is zero, and the route payload
  is approximately 178 KB. Treat this as an explicit M17/M20 optimization target, not a waiver or a
  passing mobile performance claim.
- M3 editor statement coverage is below the preferred 80% critical-form target. The behavior is
  covered by component tests and real built-app E2E, but focused conflict/error/reorder unit coverage
  remains an improvement item for the continuous coverage gate.

## Completion decision

- Gate: Pass for M3-T02 and S3; no WCAG blocker or private-content leak was found.
- Residual: full metadata/OG/sitemap delivery is M17 scope, media-backed fields are M9 scope, and
  full script-nonce CSP hardening remains M18 scope.
