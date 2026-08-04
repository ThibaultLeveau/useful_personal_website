# M0-T01-F - frontend toolchain compatibility

## Identity

- Requested milestone: M0
- Existing trace milestone alias(es): M01, M02, M03; early boundary parts of M20
- Requirement IDs: NFR-009, NFR-010, NFR-017, CHG-001
- Acceptance IDs: AC-035, AC-040, AC-043, AC-045
- Build/commit: working tree; commit assigned by Integration/root
- Branch/PR: assigned by Integration/root
- Environment/image digests: Windows compatibility host plus downloaded official Node 22.23.2 distribution; no image used
- Executor/reviewer: Frontend Agent / Integration/root review pending
- Started/completed UTC: 2026-08-02 / 2026-08-02

## Delivery

- Goal and outcome: exact frontend runtime, package-manager, framework, language, lint, format, unit, component, browser, accessibility, and Storybook versions selected for the F0 review candidate.
- Files/modules changed: `.nvmrc`, `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `docs/development/toolchain-frontend.md`, this record.
- Migration revision/data action: N/A.
- OpenAPI/client change and regeneration result: N/A; generated API files are outside this assignment.
- Security/privacy consequences: exact direct versions, package-manager integrity, strict peer handling, frozen lock, minimum package age, license inventory, and production-dependency audit are the controls in scope. No secret or private data is introduced.
- Accessibility/UX consequences: exact axe, Playwright, Testing Library, and Storybook addon-a11y pins establish later M0-T04 gates; no UI is created here.
- Documentation changed: frontend toolchain fragment and upgrade policy added.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | N/A; frontend-only assignment | N/A | N/A |
| Backend unit/service/repository/API | N/A; frontend-only assignment | N/A | N/A |
| Migration/empty DB/upgrade | N/A; no database changes | N/A | N/A |
| OpenAPI/generator diff | N/A; no contract/generated changes | N/A | N/A |
| Frontend format/lint/type/build | Node 22.23.2 + Corepack 0.35.0 + pnpm 11.18.0 version smoke; strict-peer lock resolution; `pnpm install --frozen-lockfile --ignore-scripts` | Runtime/package-manager versions, strict-peer resolution, and frozen install pass; combined post-install tool/type command was terminated before output was returned, so tool/type result is not claimed; build belongs to M0-T04 | This record |
| Frontend unit/component/Storybook/a11y | exact package and peer compatibility resolution only; application harness belongs to M0-T04 | Lock resolution pass; executable import/version smoke not claimed because the final validation process was terminated | This record |
| E2E/integration | N/A; no application/browser flow | N/A | N/A |
| Security/privacy | official Node archive checksum; pnpm package-manager SHA-512; strict peer/supply-chain-age/frozen-lock checks | Integrity and lock controls pass; dependency audit and license inventory were terminated before results were returned and remain Not run | This record |
| Manual UX/a11y/browser | N/A; no UI exists | N/A | N/A |
| Performance/coverage | N/A; no application code | N/A | N/A |
| Documentation/link walkthrough | manual ownership/scope/link review | Pass for the lane fragment; canonical toolchain reconciliation remains Integration/root-owned | `docs/development/toolchain-frontend.md` |

## Acceptance record

Integration/root owns the cross-lane Pass/Fail decision. These statuses describe only the frontend handoff candidate.

| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| AC-035 | Not run | Exact lock and frozen install pass, but strict TypeScript/tool smoke was terminated before output and is not claimed | `M0-T01-F-VAL-001` |
| AC-040 | Not run | Integrity and strict-peer checks pass; dependency audit/license inventory did not complete | `M0-T01-F-VAL-001` |
| AC-043 | Not run | Frontend bootstrap fragment reviewed, but clean-clone walkthrough is Integration/root work | `M0-T01-F-VAL-001` |
| AC-045 | Not run | Exact pins and upgrade policy exist; final repository-wide diff/link gate not completed | `M0-T01-F-VAL-001` |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| None confirmed | N/A | N/A | N/A | 0 | N/A | N/A |
| Three exact direct packages were younger than the 72-hour supply-chain delay | Low | `pnpm install --lockfile-only` returned `ERR_PNPM_NO_MATURE_MATCHING_VERSION` | Selected exact releases were published inside the configured age window | 1 | Added narrow documented `minimumReleaseAgeExclude` entries | Pass; lock generation completed |
| Latest ESLint 10.8.0 and TypeScript 7.0.2 violate strict transitive peer ranges | Medium | Strict lock resolution returned `ERR_PNPM_PEER_DEP_ISSUES` for Next ESLint plugins, TypeScript-ESLint, and Storybook `tsconfck` | Latest upstream major releases moved ahead of the required framework/tooling peer contracts | 1 | Selected newest supported ESLint 9.39.5 and TypeScript 5.9.3 | Pass; strict-peer lock generation and frozen install completed |
| M0-T01-F-VAL-001: final combined tool/type/audit/license validation did not return before the bounded process was terminated | Medium | Combined post-install validation process was explicitly terminated after the requested final wait | Registry-backed validation had already been unusually slow; the combined process exposed no partial output before termination | 1 | Preserve the passing lock/frozen install and report unverified gates without suppression | Not run; Integration/root may rerun local tool/type and registry audit/license commands |

## Completion decision

- Gate: pending Integration/root review; implementer does not record the M0-T01 Pass/Fail gate. The frontend lane is not ready to claim Pass while `M0-T01-F-VAL-001` remains unverified.
- Remaining risks/targets and disposition: rerun strict TypeScript/tool smoke, dependency audit, license inventory, deterministic lock hash, and repository-wide `git diff --check`; two deprecated transitive warnings (`@testing-library/jest-dom@6.10.0` and `tsconfck@3.1.6`) require review. Release license choice R-018 remains outside this assignment. Node 22 is Maintenance LTS and requires an explicit supported-line upgrade before 2027-04-30.
- Traceability matrix rows updated: no; Integration/root owns cross-lane acceptance records.
- Independent reviewer sign-off: pending.

## Integration review addendum

Integration/root reran the unverified checks with the exact Node 22.23.2 and
pnpm 11.18.0 binaries. Tool version smoke passed for TypeScript 5.9.3, ESLint
9.39.5, Prettier 3.9.6, Vite 8.2.0, Vitest 4.1.10, Playwright 1.62.1, and
Storybook 10.5.5. The first full audit exposed three High and one Moderate
transitive advisories in `sharp` 0.34.5 and `postcss` 8.4.31. Integration added
narrow workspace overrides to patched `sharp` 0.35.3 and `postcss` 8.5.25,
regenerated the lock, and completed a frozen install. The final full audit
reports zero Info, Low, Moderate, High, or Critical vulnerabilities. The
license inventory covers 514 packages in 13 recognized license groups; final
compatibility with the repository license remains part of `R-018`.

The corrected lock SHA-256 is
`2885f033b3c657771beaf28664dc0237ce8b2024da6036e2217c41f862ce4123`.
The cross-lane acceptance decision is recorded in `M0-T01.md`.
