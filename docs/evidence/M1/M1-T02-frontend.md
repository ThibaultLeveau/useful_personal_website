# M1-T02 - Authenticated administration frontend

## Identity

- Requested milestone: M1
- Existing trace milestone alias(es): M04 authentication foundation
- Requirement IDs: F2-001, F2-002, F2-019, SEC-005, NFR-002, NFR-003, NFR-004, NFR-014, NFR-015, NFR-016
- Acceptance IDs: AC-015, AC-016, AC-017, AC-025, AC-032, AC-033, AC-038, AC-039
- Build/commit: uncommitted integration working tree
- Branch/PR: N/A
- Environment/image digests: Node.js 22.23.2; pnpm 11.18.0; Next.js 16.2.12; Chromium through Playwright 1.58.2
- Executor/reviewer: Frontend Agent; Integration/root browser and acceptance review
- Completed UTC: 2026-08-03

## Delivery

- Goal and outcome: implemented login, mandatory initial-password change, expired-session, account/session actions, logout retry, and the protected administration boundary against the frozen generated client.
- Files/modules changed: `frontend/src/features/auth/**`, protected administrator routes/layout, administrator shell, same-origin `frontend/src/proxy.ts`, focused tests/stories, and `frontend/tests/e2e/auth.spec.ts`.
- Migration revision/data action: N/A.
- OpenAPI/client change and regeneration result: no handwritten contract change. The wrapper consumes the accepted generated authentication client at complete-tree digest `f5ad8b0d0019e502101cb70a7800d5d837a5c70f672129f88d942f9e4563396b`.
- Security/privacy consequences: credentials are never persisted in browser storage; the HttpOnly session remains opaque to JavaScript; unsafe actions use the session-bound CSRF cookie/header; protected content is withheld until server verification and cleared before logout revocation is attempted.
- Accessibility/UX consequences: linked/focused error summaries, labels, password-manager autocomplete, paste/reveal controls, skip links, loading/error/empty/expired states, mobile navigation, and keyboard-visible session actions are implemented.
- Documentation changed: first-login/operator and browser-auth API guides, same-origin configuration/container guidance, and M1 evidence.

## Validation

| Category                        | Command/protocol + tool version                                                    | Result                                                                                                                  | Repository-relative artifact                                                                                                                                                                           |
| ------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Frontend format/lint/type/build | Prettier 3.9.6; ESLint 9.39.5; TypeScript 5.9.3 strict; `next build`               | Pass with zero lint/type errors; all static-generation units and one production Proxy boundary                          | `frontend/`                                                                                                                                                                                            |
| Frontend unit/component         | `vitest run --coverage`                                                            | Pass: 11 files, 76 tests, 0 skipped                                                                                     | `frontend/src/features/auth/`                                                                                                                                                                          |
| Critical coverage               | V8 branch coverage                                                                 | Auth: 82.24% statements, 86.61% branches, 81.72% functions, 84.39% lines; exceeds the 80% critical-frontend target      | `frontend/coverage/`                                                                                                                                                                                   |
| Storybook/a11y                  | `storybook build`; component axe plus browser `@axe-core/playwright`               | Pass; auth state stories build; browser axe reports zero violations at both target widths                               | `frontend/src/features/auth/auth.stories.tsx`                                                                                                                                                          |
| E2E/integration                 | `playwright test` against the real same-origin Compose API                         | Pass: 8 tests, 0 skipped across Chromium 320×800 and 1440×1000                                                          | `frontend/tests/e2e/auth.spec.ts`                                                                                                                                                                      |
| Security/privacy                | invalid login, missing/forged CSRF, protected reload, logout/history/reload probes | Pass: non-enumerating error; CSRF denials are 403 with request ID and `private, no-store`; no stale protected DOM       | `frontend/tests/e2e/auth.spec.ts`                                                                                                                                                                      |
| Manual UX/a11y/browser          | in-app Chromium, responsive DOM/overflow inspection, keyboard/role locators        | Pass: forced first change, overview, account refresh, sign-out, old-password rejection, mobile menu, 320 px no-overflow | `screenshots/`                                                                                                                                                                                         |
| Production visual review        | full-page Playwright screenshots, visually inspected                               | Pass: coherent desktop/mobile layout with no credentials or private content captured                                    | [login 320](screenshots/admin-login-320.png), [overview 320](screenshots/admin-overview-320.png), [login 1440](screenshots/admin-login-1440.png), [overview 1440](screenshots/admin-overview-1440.png) |

Storybook reports large chunks for its own iframe, docs components, and bundled axe tooling. These
assets are absent from the successful Next.js production route build; the warning is therefore a
development-harness bundle observation, not an application bundle regression or suppressed gate.
It remains a later tooling-performance review target.

## Acceptance record

| AC ID  | Status                  | Evidence                                                                                                  | Defect/waiver                                                                        |
| ------ | ----------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| AC-015 | Pass for frontend       | forced first-change browser path; ordinary shell withheld until rotation                                  | None                                                                                 |
| AC-016 | Pass for frontend       | invalid/valid login, protected reload, refresh, logout, old-password rejection                            | Expiry timer is covered deterministically rather than by a 30-minute live wait.      |
| AC-017 | Pass for frontend slice | missing/forged CSRF live probes and same-origin transport                                                 | Cross-origin and backend authorization matrix are accepted in T01/T03.               |
| AC-025 | Pass for M1 workflow    | desktop/mobile pointer and keyboard-discoverable account/session actions                                  | Later content-management workflows remain owning slices.                             |
| AC-032 | Pass for M1 workflow    | component axe, browser axe, focus/label/error/skip-link review at 320/1440                                | Full-product AT/zoom/theme matrix remains M13.                                       |
| AC-033 | Pass for M1 workflow    | checking, connection error/retry, invalid, unauthorized, expired, forced-change, empty and success states | None                                                                                 |
| AC-038 | Pass                    | critical frontend coverage exceeds 80%; tests assert behavior and safe DOM transitions                    | Generated client lowers aggregate coverage and is separately deterministic/compiled. |
| AC-039 | Pass for T02            | no disabled assertions, no hidden test failure, no placeholder protected controls                         | Hosted CI remains separately unclaimed.                                              |

## Findings and corrective loop

| Finding                                                                                     | Severity | Reproduction                                                   | Root cause                                                          | Attempt # | Correction                                                                     | Retest                                              |
| ------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------- | ------------------------------------------------------------------- | --------: | ------------------------------------------------------------------------------ | --------------------------------------------------- |
| Safe-return prefix accepted unrelated `/administrator` paths.                               | High     | focused return-path unit case                                  | prefix check lacked a path-segment boundary                         |         1 | require `/admin` or `/admin/…` exactly                                         | focused and full unit suites pass                   |
| Logout could hide server-revocation failure without an actionable retry.                    | High     | disconnected logout component review                           | protected DOM clearing and revocation confirmation shared one state |         1 | clear immediately, persist an unconfirmed flag, expose retry on sign-in        | component and real logout tests pass                |
| Component axe emitted a jsdom canvas warning without checking real contrast.                | Medium   | full Vitest output                                             | axe color contrast requires a rendered browser canvas               |         1 | document and disable only that jsdom rule; run unmodified axe in real Chromium | component output clean; browser axe zero violations |
| Initial in-app full-width screenshots used stale responsive frames after client navigation. | Medium   | compare screenshot pixels with live DOM geometry/media queries | in-app capture state did not match evaluated viewport               |         1 | replace authoritative images with repository Playwright full-page captures     | visually inspected 320/1440 evidence is correct     |

## Completion decision

- M1-T02 gate: Pass.
- Remaining risks/targets and disposition: Storybook-only tooling chunk sizes are recorded above; complete product accessibility/performance audits remain M13. No M1 frontend blocker remains.
- Traceability matrix rows updated: final M1-T03 record owns the consolidated update.
- Independent reviewer sign-off: Integration/root accepted after real-stack browser, source, test, coverage, build, and screenshot review.
