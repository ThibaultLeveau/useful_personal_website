# M0-T04 - frontend foundation implementer evidence

## Identity

- Requested milestone: M0
- Existing trace milestone alias(es): M01, M02, M03; early boundary parts of M20
- Requirement IDs: F1-002, NFR-001, NFR-002, NFR-003, NFR-004, NFR-008, NFR-010, AI-004
- Acceptance IDs: AC-002, AC-031, AC-035, AC-037, AC-046
- Build/commit: working tree; commit assigned by Integration/root
- Branch/PR: assigned by Integration/root
- Environment/image digests: Windows host; Node 22.23.2, Corepack 0.35.0, pnpm 11.18.0; no container image
- Executor/reviewer: Frontend Agent / Integration/root review pending
- Started/completed UTC: 2026-08-02 / 2026-08-02

## Delivery

- Goal and outcome: a strict Next.js App Router foundation now renders separate public and administration shells. Server Components are the default; client components are limited to navigation dialogs and synchronized system/light/dark theme selection.
- Files/modules changed: `frontend/package.json`, frontend framework/lint/format/type/test/Storybook/Playwright configuration, `frontend/src/app/**`, `frontend/src/components/{ui,public,admin}/**`, `frontend/src/lib/classes.ts`, `frontend/tests/**`, and this record.
- Migration revision/data action: N/A.
- OpenAPI/client change and regeneration result: N/A. `frontend/src/generated/**` and `frontend/src/lib/api/**` were not created or edited.
- Security/privacy consequences: no database client, secret environment value, authentication material, personal content, direct API implementation, raw error detail, or private cache was added. Administration metadata is `noindex`/`nofollow`.
- Accessibility/UX consequences: semantic landmarks, first-focus skip links, native dialog navigation, 44 px controls, focus-visible treatment, reliable hydration-safe light/dark/system tokens, reduced-motion and forced-colors handling, safe loading/error/not-found states, responsive public/admin shells, Testing Library/axe coverage, addon-a11y Storybook configuration, and passing 320/1440 Playwright coverage were added. The active admin index now provides 6.61:1 light-theme and 7.21:1 dark-theme contrast against its selection surface.
- Documentation changed: this implementer evidence only; existing normative UX and development documents remain read-only.
- Workspace integration: `frontend/package.json` uses only frozen `catalog:` entries. pnpm mechanically added the new `frontend` importer to the integration-owned root lock during the first workspace command. Integration/root must review and own that lock delta; the Frontend Agent did not hand-edit the root manifest, catalog, overrides, or lock.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | N/A; frontend-only assignment | N/A | N/A |
| Backend unit/service/repository/API | N/A; frontend-only assignment | N/A | N/A |
| Migration/empty DB/upgrade | N/A; no persistence change | N/A | N/A |
| OpenAPI/generator diff | Boundary inspection | Pass; reserved generated/client-wrapper paths untouched | `frontend/src` |
| Frontend format/lint/type/build | `pnpm --dir frontend format:check`; `pnpm --dir frontend lint`; `pnpm --dir frontend typecheck`; `pnpm --dir frontend build` with Prettier 3.9.6, ESLint 9.39.5, TypeScript 5.9.3, Next 16.2.12 | Pass; Next compiled, type-checked, and statically generated `/`, `/_not-found`, and `/admin` | `frontend/package.json`, `frontend/src/app` |
| Frontend unit/component/Storybook/a11y | `pnpm --dir frontend test --run`; `pnpm --dir frontend storybook:build` with Vitest 4.1.10, axe-core 4.12.1, Storybook 10.5.5 | Pass after corrective iteration 1; 3 test files/4 tests including axe primitive and stored-theme hydration; Storybook static build completed with addon-a11y configured to error | `frontend/src/**/*.test.tsx`, `frontend/src/**/*.stories.tsx`, `frontend/.storybook` |
| E2E/integration | `pnpm --dir frontend test:e2e` with Playwright 1.62.1/Chromium revision 1234 | Pass after corrective iteration 1: 6/6 tests at 320 and 1440, including public/admin axe scans, reflow, skip focus, screenshots, and persisted dark-theme application. The Integration-provided web-server command remains `node node_modules/next/dist/bin/next dev`; test/server origin is consistently `localhost` | `frontend/tests/e2e/shells.spec.ts`, `frontend/playwright.config.ts` |
| Security/privacy | reserved-path scan plus forbidden database/AI/runtime term scan across `frontend/src` and `frontend/tests`; rendered safe-error copy review | Pass; reserved paths absent and boundary-term matches zero | This record |
| Manual UX/a11y/browser | Automated rendered browser review at 320 and 1440 with screenshots and axe | Pass for the M0 shell smoke; no claim of complete manual WCAG conformance | `frontend/tests/e2e/shells.spec.ts` |
| Performance/coverage | Next production compilation and static generation | Pass for foundation build; no release performance claim | `frontend/src/app` |
| Documentation/link walkthrough | evidence, ownership, and repository-relative path review | Pass for implementer record | This record |

## Acceptance record

Integration/root owns Pass/Fail decisions. Implementer validation and corrective browser evidence are ready for review.

| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| AC-002 | Not run | Public and admin shells build and pass rendered 320/1440 smoke | Integration/root decision pending |
| AC-031 | Not run | Signal Ledger tokens and responsive shells pass rendered light/dark and axe checks | Integration/root decision pending |
| AC-035 | Not run | Strict type/lint/test/build and Storybook build pass locally | Root lock acceptance remains Integration/root-owned |
| AC-037 | Not run | Canonical frontend-check-compatible scripts pass locally | Integration/root gate pending |
| AC-046 | Not run | No AI UI/runtime, database access, fake data, or disconnected controls; source boundary scan returned zero matches | Integration/root decision pending |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| `exactOptionalPropertyTypes` rejected an explicit undefined link handler | Low | First `pnpm --dir frontend typecheck` | Optional callback prop was always emitted | 1 | Spread `onClick` only when provided | Typecheck Pass |
| React lint rejected synchronous state initialization in an effect | Medium | First `pnpm --dir frontend lint` | Theme preference treated browser storage as component state rather than an external store | 1 | Replaced effect state writes with `useSyncExternalStore` and a storage/custom-event subscription | Lint, typecheck, theme unit test Pass |
| Playwright browser revision missing | Medium | Initial `pnpm --dir frontend test:e2e` | Host cache contained older Chromium revisions, not Playwright 1.62.1 revision 1234 | 1 | No gate weakening; preserved the exact Playwright pin and Integration installed the required browser artifact | Pass: full 6/6 browser matrix after Integration provisioned revision 1234 |
| Workspace command mechanically updated root lock | Integration | First `pnpm --dir frontend format` after creating the new workspace package | Frozen lock had no `frontend` importer before M0-T04 | 1 | Stopped treating the delta as Frontend-owned and notified Integration/root for review/ownership | Frontend importer resolves exact catalog pins; Integration decision pending |
| M0-T04-FE-001: dark selection left the document on the light token set | High | Integration Playwright theme test at 320 and 1440; first corrective retest showed the selector remained disabled and mobile dialog could not open | Playwright opened `127.0.0.1` while Next dev served the client runtime from its `localhost` origin, so Next blocked the cross-origin development resource and React never hydrated. The server-rendered selector also allowed a pre-hydration interaction window | 1 | Kept Integration's cross-platform `node node_modules/next/dist/bin/next dev` command, aligned Playwright base/server URLs on `localhost`, disabled the selector until hydration via `useSyncExternalStore`, applied preference synchronously in the change handler, and asserted storage plus both document theme attributes | Pass: focused 4/4 browser retest and full 6/6 browser matrix; 2 theme unit tests pass |
| M0-T04-FE-002: active admin index contrast was 4.35:1 | High | Integration axe color-contrast result on desktop `/admin`: `#667085` over `#dff3fc` | The active link retained the general subtle metadata foreground despite moving onto the selection surface | 1 | Active index now uses semantic `--brand` while inactive metadata remains subtle; calculated ratios are 6.61:1 light and 7.21:1 dark | Pass: `/admin` axe scan at 320 and 1440; full 6/6 browser matrix |

## Completion decision

- Gate: pending Integration/root review; implementer does not record the M0-T04 Pass/Fail gate.
- Remaining risks/targets and disposition: Integration/root must review/accept the mechanically generated root lock importer and record the gate decision. Storybook reports expected documentation-bundle chunk-size warnings, not an application-bundle failure. Complete manual WCAG validation remains a later milestone responsibility; the required M0 automated browser matrix is green.
- Traceability matrix rows updated: no; Integration/root owns cross-lane acceptance records.
- Independent reviewer sign-off: pending.
