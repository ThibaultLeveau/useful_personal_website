# Milestone 0 Dispatch

## Dependency decision

Scope is `M0-T01` through `M0-T07`. The ADR index records all required ADRs as Accepted. The repository has no toolchain pins, manifests, application skeletons, migration baseline, generated client, or M0 evidence yet.

| Task | State | Dependency decision |
|---|---|---|
| `M0-T01` | Ready | Accepted ADRs verified. The maintainer license choice may remain open as risk `R-018`; no agent may choose it. |
| `M0-T02` | Partly ready | Governance/docs may start with T01. Task-runner and pre-commit closure wait for frozen T01 pins. |
| `M0-T03` | Blocked | Requires passing T01 and T02 evidence. |
| `M0-T04` | Blocked | Requires passing T01/T02 evidence and the route/client seam agreed with T03. |
| `M0-T05` | Blocked | Requires passing T03 evidence. |
| `M0-T06` | Blocked | Requires passing T03 and T04 evidence. |
| `M0-T07` | Blocked | Requires passing T03 and T05 evidence. |

## Three assignments ready now

Only these three assignments may write in parallel. They do not authorize application code.

### Backend Agent — `M0-T01-B`

- Owns: `.python-version`, root `pyproject.toml`, root `uv.lock`, `docs/development/toolchain-backend.md`, `docs/evidence/M0/M0-T01-backend-compatibility.md`.
- Delivers: exact Python 3.12.x/uv and compatible exact backend/test/security tool pins, deterministic lock, import/version and tool smoke, dependency license/security result.
- Excludes: `backend/**`, task-runner/pre-commit, containers/CI, canonical toolchain doc, frontend files.

### Frontend Agent — `M0-T01-F`

- Owns: `.nvmrc`, root `package.json`, `pnpm-workspace.yaml`, root `pnpm-lock.yaml`, `docs/development/toolchain-frontend.md`, `docs/evidence/M0/M0-T01-frontend-compatibility.md`.
- Delivers: exact Node 22.x/Corepack/pnpm and compatible exact frontend/test/a11y tool pins, deterministic lock, version/strict-TypeScript tool smoke, dependency license/security result.
- Excludes: `frontend/**`, task-runner/pre-commit, containers/CI, canonical toolchain doc, generated API files.

### Infrastructure Agent — `M0-T02-G`

- Owns: `.editorconfig`, `.gitignore`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/README.md`, dependency-independent `docs/development/**` skeletons excluding toolchain files, and `docs/evidence/M0/M0-T02-governance-skeleton.md`.
- Delivers: repository/link checklist, secret/private-data/absolute-path scan, platform-neutral placeholders, and an explicit unresolved-license record linked to `R-018`. Do not create a misleading `LICENSE`.
- Excludes: `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/**`, manifests/locks, application/container files, `docs/plan/**`, and unfrozen executable setup commands.

## Ownership after the first merge

Integration/root reviews the three handoffs, reconciles the two toolchain fragments into `docs/development/toolchain.md`, records `docs/evidence/M0/M0-T01.md`, and freezes F0. Root manifest/lock stewardship then transfers to Integration/root; later lane changes require coordination.

Infrastructure Agent then exclusively creates the root task runner and `.pre-commit-config.yaml` using F0 pins and closes T02. Only after passing T01/T02 evidence may the following work begin:

| Task | Primary owner | Exclusive area / overlap resolution |
|---|---|---|
| `M0-T03` | Backend Agent | `backend/pyproject.toml`, `backend/app/{main,config}.py`, `backend/app/api/v1/**`, `common/**`, non-feature module shells, backend harness/tests. Excludes `backend/app/infrastructure/database/**` and `backend/app/commands/**`. |
| `M0-T04` | Frontend Agent | `frontend/package.json`, app/components/features/general lib, tests, Storybook, styles/tokens. Excludes both Dockerfile and `frontend/src/{generated/api,lib/api}/**`. |
| `M0-T05` | Backend Agent | Sole writer of `backend/alembic.ini`, `backend/migrations/**`, `backend/app/infrastructure/database/**`, database fixtures, and migration tests. |
| `M0-T06` | Integration/root | Sole writer of `docs/api/openapi.json`, generator config/script, and `frontend/src/generated/api/**`. Backend owns executable Pydantic source/tests; Frontend receives a separate, nonconcurrent assignment for handwritten `frontend/src/lib/api/**` wrappers/tests after generation. |
| `M0-T07` | Infrastructure Agent | `.env.example`, Compose, both Dockerfiles, root `infrastructure/**`, operator docs, and root bootstrap/seed wrappers. Backend owns internal `backend/app/commands/**` plus tests through a named T07 sub-assignment after F3. |

Additional reservations:

- Integration/root exclusively owns `docs/plan/**`, cross-lane acceptance records, shared contract changes, and generated-client commits.
- Backend owns settings schema/validation; Infrastructure owns environment injection and containers. Environment names are joint-review contracts, not duplicated defaults.
- Infrastructure owns `backend/Dockerfile` and `frontend/Dockerfile`; application agents provide build commands but do not edit containers.
- Existing requirements, architecture, UX, and planning documents are read-only unless a correction is separately dispatched.

## Contract freezes

| Freeze | Owner / gate | Required before | Contract |
|---|---|---|---|
| **F0 Toolchain** | Integration/root after T01 review | T02 closure and later tasks | Exact runtimes, package managers, dependencies/tools, PostgreSQL image/digest policy, OpenAPI generator, locks, upgrade policy. |
| **F1 Commands/layout** | Integration/root after T02 pass | T03/T04 | Workspace paths and noninteractive install/format/lint/type/test/build/migrate/generate/run commands. |
| **F2 API boot seam** | T03/T04 joint review; root records | T06 | `/api/v1`, export entry point, baseline operation IDs/envelopes/errors/security, generated-client import boundary, dependency direction. |
| **F3 Database/runtime commands** | Root after T05 pass | T07 | Async session/UoW, one linear Alembic head, revision check, credential separation, migrate/bootstrap/seed command names; startup invokes none. |
| **F4 Generated client** | Integration/root after T06 pass | Frontend API consumption/T08 | Committed schema, pinned generator/config, generated path/header, wrapper boundary, clean no-diff regeneration. |
| **F5 Environment/containers** | Root after T07 pass | T08/M0 close | Environment names/visibility, PostgreSQL/local-media topology, non-root images, health/readiness, explicit migration/bootstrap/seed boundaries. |

Changes to a frozen contract require Integration/root approval before edits; backward-incompatible changes also follow `CHG-002`.

## Migration and generated-client rules

- Backend Agent receives one M0 migration reservation for T05. No other task may add a table, ORM model, fixture, data command, or Alembic revision while it is active.
- Integration/root records the revision, verifies one head and schema/model alignment, and alone may authorize a merge revision. M0 should not create one.
- Infrastructure invokes migrations but never edits them or enables startup auto-migration.
- Backend owns FastAPI/Pydantic schemas, operation IDs, errors/security/examples, and contract tests.
- Integration/root alone exports and commits OpenAPI and generated output. Generated files are never hand-edited.
- Frontend owns handwritten wrappers only after generated output exists; feature code consumes wrappers.

## Acceptance and evidence gates

All records follow `delivery-evidence-template.md`, use repository-relative links, map both milestone schemes and relevant AC/requirement IDs, and exclude secrets, private data, auth material, production dumps, and absolute local paths.

| Task | Release dependency only when | Required evidence |
|---|---|---|
| T01 | Exact compatible pins/locks reproduce; version/import/type smoke and license/security review pass. | Lane reports plus `M0-T01.md`, version/install/lock logs and diffs. |
| T02 | Canonical commands invoke backend/frontend smoke suites; links, pre-commit, secret/path checks pass; license risk remains explicit. | `M0-T02.md`, command transcripts and repository/link/scan checklist. |
| T03 | Startup/live API, invalid settings, boundary imports, safe errors/logs, Ruff, strict mypy, and Pytest pass; no feature/AI placeholders. | `M0-T03.md` and reports/live smoke. |
| T04 | Strict TS/lint/build, Vitest, Storybook, axe primitive, and 320/1440 shell smoke pass; no content/DB/fake/AI path. | `M0-T04.md`, reports and sanitized screenshots. |
| T05 | Empty upgrade/current/schema, one head, rollback/UoW, revision mismatch, and migrated readiness pass. | `M0-T05.md`, Alembic/schema/transaction logs. |
| T06 | Schema lint/snapshot, operation IDs, generated compile, wrapper test, health request, and no-diff regeneration pass. | `M0-T06.md`, lint/generator/diff/client artifacts. |
| T07 | Config, non-root images, Compose/readiness, explicit migration, bootstrap/seed separation/idempotency/production refusal, and secret-layer checks pass. | `M0-T07.md`, image metadata, Compose/command/test/scan logs. |

Integration/root, not the implementer, records Pass/Fail/Blocked. Confirmed Critical/High findings, a failed Must requirement, multiple migration heads, generated-client drift, or weakened gates block downstream dispatch.
