# M0-T08 - Diagnostic CI and security gates

## Identity

- Requested milestone: M0
- Existing trace milestone alias(es): M01, M20
- Requirement IDs: NFR-013, NFR-014, NFR-015, NFR-016, SEC-010, OSS-002
- Acceptance IDs: AC-037, AC-038, AC-039, AC-040, AC-044
- Build/commit: baseline `8f6a5e1`; uncommitted candidate working tree
- Branch/PR: `main`; no PR or hosted run
- Environment/image digests: Local workflow validation with Docker Engine 29.2.1; scanner digests recorded in CI documentation
- Executor/reviewer: Infrastructure Agent / integration reviewer pending
- Started/completed UTC: 2026-08-02 / 2026-08-02

## Delivery

- Goal and outcome: Added a least-privilege, immutable-pin diagnostic CI workflow for repository hygiene, backend, frontend, browser, OpenAPI/client, migrations, production containers, and final aggregation. The workflow intentionally fails its bootstrap/seed dependency job because real commands and tests do not exist.
- Files/modules changed: `.github/workflows/ci.yml`, CI developer documentation, contributor/security guidance, developer index, and this implementer record.
- Migration revision/data action (or N/A): No migration changed. CI captures the sole Alembic head dynamically, rejects zero/multiple heads, upgrades an empty PostgreSQL service, matches `current` to that head, and runs `alembic check`.
- OpenAPI/client change and regeneration result (or N/A): No contract or generated file changed. CI runs the accepted deterministic exporter/generator/validator, compiles/lints/tests the client boundary, and requires a clean generated diff.
- Security/privacy consequences: Read-only workflow permissions, non-persisted checkout credentials, Gitleaks redaction, Bandit, pip-audit, pnpm production audit, Trivy scans without `--ignore-unfixed`, retained scanner reports, ephemeral database credentials, and short artifact retention.
- Accessibility/UX consequences: CI runs the accepted Playwright 320/1440 axe matrix and retains failure reports. No UI code changed.
- Documentation changed: Added job/local-command parity, immutable pin provenance, cache/artifact policy, pending dependency status, and security-output rules.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | Workflow mapping reviewed against accepted root/backend commands | Defined; hosted job not run | [CI workflow](../../../.github/workflows/ci.yml), [T03 acceptance](M0-T03.md) |
| Backend unit/service/repository/API | PostgreSQL-backed Pytest/coverage job plus Bandit and pip-audit | Defined; hosted job not run | [CI guide](../../development/ci.md) |
| Migration/empty DB/upgrade | actionlint semantic validation of dynamic single-head/upgrade/current/check job | Pass for workflow semantics; hosted PostgreSQL job not run | [CI workflow](../../../.github/workflows/ci.yml) |
| OpenAPI/generator diff | Deterministic F4 commands and clean-diff gate mapped | Defined; hosted job not run | [T06 acceptance](M0-T06.md) |
| Frontend format/lint/type/build | Frozen scripts-disabled install, blocking production audit, Prettier, zero-warning ESLint, strict TS, Storybook/Next jobs mapped | Defined; hosted job not run | [CI workflow](../../../.github/workflows/ci.yml) |
| Frontend unit/component/Storybook/a11y | Vitest coverage, Storybook artifact, Playwright/axe report jobs mapped | Defined; hosted jobs not run | [T04 acceptance](M0-T04.md) |
| E2E/integration | Playwright and production-container build jobs mapped | Defined; hosted jobs not run | [CI guide](../../development/ci.md) |
| Security/privacy | Pinned Gitleaks 8.28.0 history scan | Pass: one existing commit, no leaks; uncommitted candidate covered by repository/pre-commit checks | This record |
| Manual UX/a11y/browser | No product change | N/A | — |
| Performance/coverage | Coverage artifact paths and retention validated semantically | Defined; hosted artifacts not produced | [CI workflow](../../../.github/workflows/ci.yml) |
| Documentation/link walkthrough | Repository checks over 223 visible files; focused pre-commit; Git diff whitespace check | Pass | [CI guide](../../development/ci.md) |

## Workflow and pin validation

| Check | Result |
|---|---|
| PyYAML parse | Pass; mapping with nine jobs |
| actionlint 1.7.7 OCI digest | Pass; zero findings after all review corrections |
| Third-party `uses:` references | Pass; every action uses a 40-character commit SHA with a version comment |
| Upstream tag resolution | Pass; six action commits resolved by `git ls-remote` from the named upstream repositories |
| Focused pre-commit | Pass; repository policy passed and non-applicable Python hooks skipped |
| Repository policy | Pass; 223 visible files |
| `git diff --check` | Pass |
| Gitleaks executable/history smoke | Pass; pinned digest, no leaks in existing history |

Verified upstream action refs:

- `actions/checkout` `v4.2.2` → `11bd71901bbe5b1630ceea73d27597364c9af683`
- `actions/setup-python` `v5.6.0` → `a26af69be951a213d495a4c3e4e4022e16d87065`
- `actions/setup-node` `v4.4.0` → `49933ea5288caeca8642d1e84afbd3f7d6820020`
- `actions/cache` `v4.2.3` → `5a3ec84eff668545956fd18022155c47e93e2684`
- `actions/upload-artifact` `v4.6.2` → `ea165f8d65b6e75b540449e92b4886f43607fa02`
- `astral-sh/setup-uv` `v6.7.0` → `b75a909f75acd358c2196fb9a5f1299a9a8868a4`

## Acceptance record

| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| AC-037 | Not run | All required M0 diagnostic categories have independent jobs and final aggregation. | No hosted GitHub Actions run exists; `bootstrap_seed` deliberately fails. |
| AC-038 | Not run | Backend/frontend coverage commands and artifacts are configured. | Hosted reports and threshold evidence are not yet produced. |
| AC-039 | Not run | Playwright responsive/axe job and report artifact are configured. | Hosted browser evidence is not yet produced. |
| AC-040 | Not run | Jobs are bounded, diagnostic, pinned, and do not add speculative runtime dependencies. | Integration review pending. |
| AC-044 | Not run | Repository/pre-commit/history scans pass locally; CI secret/image scans are configured. | Hosted Gitleaks/Trivy reports are not yet produced. |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| Migration job asserted the M0 baseline revision | Medium | Review against the reserved forward identity migration | Fixed revision would become stale after a legitimate single-head migration | 1 | Capture exactly one head dynamically and require `current` to match | actionlint Pass |
| Container scan hid unfixed findings and retained no durable report | High | Security gate review | Initial scanner flags omitted unfixed vulnerabilities and emitted log-only evidence | 1 | Removed `--ignore-unfixed`; run both scans, retain JSON artifacts, then enforce both outcomes | actionlint Pass |
| Frontend production dependency audit absent | High | Dependency-gate inventory | Frozen install alone did not query advisories | 1 | Added blocking `pnpm audit --prod --audit-level high` | actionlint Pass |

## Completion decision

- Gate: Blocked
- Remaining risks/targets and disposition: T08 cannot be accepted while `bootstrap_seed` deliberately fails; this is intentional and visible in the final aggregate gate. The named backend assignment must implement and test bootstrap idempotency/separation and seed production refusal/no-credential behavior, after which this job must be replaced with those real commands. A hosted GitHub Actions run must then produce passing job results and durable coverage/browser/scanner artifacts before integration/root can pass T08.
- Traceability matrix rows updated: None; integration/root owns cross-lane acceptance records.
- Independent reviewer sign-off: Pending integration/root review and hosted CI evidence.
