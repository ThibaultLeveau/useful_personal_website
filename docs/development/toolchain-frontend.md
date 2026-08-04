# Frontend toolchain contract

This is the frontend lane fragment of the M0 F0 toolchain freeze. Integration/root owns the canonical `docs/development/toolchain.md` and any changes after F0 is accepted.

## Runtime and package manager

| Component | Exact version | Contract location |
|---|---:|---|
| Node.js (Jod, maintenance LTS) | 22.23.2 | `.nvmrc`, `package.json#engines` |
| Corepack | 0.35.0 | pnpm catalog/root compatibility importer |
| pnpm | 11.18.0 | `packageManager` with SHA-512, `package.json#engines` |

Node 22 remains supported through 2027-04-30. Node 22.23.2 is the latest security release in the required 22.x line as of 2026-08-02. Corepack 0.35.0 and pnpm 11.18.0 both require a sufficiently recent Node 22 patch; this contract therefore must not be exercised with an earlier 22.x binary.

Bootstrap from a Node-version-manager shell after selecting `.nvmrc`:

```sh
npm install --global corepack@0.35.0
corepack enable
corepack install
node --version
corepack --version
pnpm --version
pnpm install --frozen-lockfile
```

The expected outputs are `v22.23.2`, `0.35.0`, and `11.18.0`. Corepack verifies the pnpm tarball against the SHA-512 embedded in `package.json`.

## Frozen package lines

All direct frontend dependencies are exact in the default catalog in `pnpm-workspace.yaml`. Workspace package manifests consume them with `catalog:`; adding an independent range or floating tag is a contract violation.

| Area | Exact versions |
|---|---|
| Framework | Next.js 16.2.12; React/React DOM 19.2.8 |
| Language/types | TypeScript 5.9.3; `@types/node` 22.20.1; `@types/react` 19.2.18; `@types/react-dom` 19.2.4 |
| Styling | Tailwind CSS and `@tailwindcss/postcss` 4.3.3 |
| Lint/format | ESLint 9.39.5; `eslint-config-next` 16.2.12; `eslint-plugin-storybook` 10.5.5; Prettier 3.9.6 |
| Unit/component | Vitest and `@vitest/coverage-v8` 4.1.10; Vite 8.2.0; React plugin 6.0.5; jsdom 30.0.1 |
| Testing Library | DOM 10.4.1; React 16.3.2; jest-dom 7.0.0; user-event 14.6.1 |
| Browser/a11y | Playwright 1.62.1; axe-core and `@axe-core/playwright` 4.12.1 |
| Component workshop | Storybook, Next.js Vite framework, addon-a11y, and addon-docs 10.5.5 |
| Required application libraries | React Hook Form 7.84.0; Zod 4.4.3; TanStack Query 5.101.4 |

The root compatibility importer exists only to resolve and audit the F0 set before `frontend/package.json` is dispatched. M0-T04 should consume the catalog and must not copy floating version ranges.

## Compatibility rationale

- Next 16.2.12 supports Node 20.9+ and React 18.2/19, including React 19.2.8.
- `eslint-config-next` 16.2.12 accepts ESLint 9+, but its current transitive React/import/a11y plugins cap ESLint at 9; ESLint 9.39.5 is the newest compatible 9.x release.
- The current TypeScript-ESLint chain requires TypeScript below 6.1 and Storybook's `tsconfck` peer requires TypeScript 5.x; TypeScript 5.9.3 is the newest compatible release.
- Vitest 4.1.10 accepts Vite 6/7/8; the React Vite plugin 6.0.5 requires Vite 8.
- Storybook's Next.js Vite framework 10.5.5 accepts Next 14/15/16, React 16-19, and Vite 5-8.
- Testing Library React 16.3.2 accepts React 18/19 and Testing Library DOM 10.x.
- Node 22.23.2 satisfies the strictest direct engine floors: Corepack/jsdom require Node 22.22.2+ and pnpm requires Node 22.13+.

## Determinism and supply-chain policy

- `pnpm-workspace.yaml` overrides transitive `postcss` to 8.5.25 and `sharp`
  to 0.35.3. Integration added these narrow overrides after the first complete
  audit found three high-severity and one moderate advisory in the versions
  selected by Next.js. Both overrides are above the published patched floors;
  the full dependency audit now reports zero known vulnerabilities.
- `pnpm install --frozen-lockfile` is the only verification/install mode after the lock is committed.
- `catalogMode: strict` rejects dependency additions that bypass an existing catalog entry.
- `strictPeerDependencies: true` converts peer incompatibilities into install failures.
- The default 72-hour `minimumReleaseAge` reduces exposure to newly published packages. The exact direct releases `@types/react-dom@19.2.4`, `@types/react@19.2.18`, and `react-hook-form@7.84.0` were published inside the window, were individually compatibility-reviewed, and are explicit bootstrap exceptions. Remove each exception once it naturally ages past the window. Any future time-sensitive security exception must be exact, documented, and approved through change control.
- The root lockfile and the `packageManager` SHA-512 are committed. Store caches are performance-only and never a source of truth.
- Playwright browser binaries are platform artifacts and are installed separately by M0-T04/CI with the pinned Playwright CLI; they are not committed.
- Do not weaken peer, engine, integrity, audit, or frozen-lockfile failures to make an upgrade pass.

## Upgrade policy

Dependency upgrades are deliberate maintenance changes, never incidental installs. Create a dedicated change, update exact catalog pins and runtime/package-manager hashes together, regenerate the lock from a clean store, and run install, peer/engine, strict TypeScript, lint, unit/component, Storybook, Playwright, accessibility, production-build, license, and security gates. Major upgrades require an ADR or the accepted change-control path (`CHG-001`/`CHG-002`). Integration/root must approve changes after F0.

Authoritative metadata used for the 2026-08-02 selection:

- Node release index: <https://nodejs.org/dist/index.json>
- Node release schedule: <https://github.com/nodejs/Release#release-schedule>
- Corepack releases and usage: <https://github.com/nodejs/corepack>
- npm registry metadata: `https://registry.npmjs.org/<package>/latest`
