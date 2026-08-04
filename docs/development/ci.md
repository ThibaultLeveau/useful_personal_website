# Continuous Integration

## Status

`.github/workflows/ci.yml` is the executable diagnostic CI workflow. Every required aggregate-gate dependency now contains real checks, including the accepted administrator-bootstrap and M3 demo-seed safety contract; there is no placeholder success or intentional red job.

The workflow runs on pull requests, pushes to `main`, and manual dispatch. It grants only `contents: read`, does not persist checkout credentials, cancels superseded runs on the same ref, uses bounded timeouts, and caches only package/scanner data that is never a source of truth.

## Diagnostic jobs and local parity

| Job                 | CI checks                                                                                                                                              | Local authority                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Repository          | Repository policy, pre-commit, whitespace, actionlint, Gitleaks history scan                                                                           | `python scripts/task.py repo-check`; `uv run pre-commit run --all-files`; `git diff --check`                                |
| Backend             | Ruff lint/format, strict Mypy, split-role PostgreSQL Pytest with zero skips and branch coverage, Bandit, pip-audit                                     | `python scripts/task.py backend-check` plus documented Bandit/pip-audit commands                                            |
| Frontend            | Frozen scripts-disabled install, production dependency audit, Prettier, zero-warning ESLint, strict TypeScript, Vitest coverage, Storybook, Next build | `python scripts/task.py frontend-check` plus `pnpm audit --prod --audit-level high`, `test:coverage`, and `storybook:build` |
| Browser             | Pinned Chromium install and Playwright 320/1440 accessibility matrix                                                                                   | `pnpm --dir frontend test:e2e`                                                                                              |
| Contract            | Deterministic OpenAPI export/generation, convention validation, client compile/lint/test, clean diff                                                   | `python scripts/task.py api-generate`; `python scripts/task.py api-check`; clean Git diff                                   |
| Migrations          | One Alembic head, empty PostgreSQL upgrade, exact current revision, schema drift check                                                                 | [Database migration protocol](database-and-migrations.md)                                                                   |
| Database privileges | Isolated three-role Compose stack; fail-closed gates; owner migration/rollback; runtime allow/deny matrix; password-output scan; exact-project cleanup | [Database role and grant contract](database-and-migrations.md) and [local container protocol](containers.md)                |
| Containers          | Compose config, both production builds, non-root/health metadata, blocking Trivy Critical/High scans with retained JSON reports                        | [Local container runbook](containers.md) plus image inspection/scanning                                                     |
| Bootstrap/seed      | Production refusal, empty migration, first/idempotent seed, and credential/private-data separation                                                     | `python scripts/task.py seed-demo` after explicit migration and permissions                                                 |
| Gate                | Aggregates every required job even after failures                                                                                                      | Integration/release evidence review                                                                                         |

CI uses scripts-disabled pnpm installation because unapproved dependency lifecycle scripts are rejected by the frozen supply-chain policy. Next, Storybook, Vitest, and Playwright use pinned platform packages and explicit commands rather than install-time execution.

## Isolated database-privilege job

`database_privileges` uses a unique Compose project derived only from the numeric workflow run ID and attempt. It supplies three distinct synthetic URL-safe credentials, builds the migration image from the repository's immutable base pins, and uses the digest-pinned PostgreSQL service already frozen in `compose.yaml`.

The job proves the runtime gate fails before migration and again before grant reconciliation; captures exactly one Alembic head; migrates with owner credentials; reconciles and reconnects as runtime; and verifies ordinary administrator/session/rate-limit CRUD plus audit insert/select. Negative probes require denial of audit update/delete/truncate, audit-trigger disable, persistent DDL, temporary DDL, ordinary-table alteration, and Alembic metadata writes. It then exercises owner downgrade-to-base, upgrade-to-head, and a second reconciliation.

Captured command and PostgreSQL output is scanned for all three synthetic password values. An `if: always()` cleanup step invokes `down --volumes --remove-orphans` with the exact project name and asserts that no project-labelled container, volume, or network remains. The job is a required input to `gate`; cleanup never targets a shared or default Compose project.

The backend job uses the same three-role contract without duplicating its SQL. It generates and masks three distinct synthetic credentials, starts an exact-name digest-pinned PostgreSQL container with the bootstrap-only identity, runs the mounted `init-roles.sh`, migrates through `TEST_DATABASE_OWNER_URL`, and runs `reconcile-permissions.sh`, which reconnects through the runtime permission check. Pytest receives `TEST_DATABASE_OWNER_URL` only for destructive migration fixtures and `TEST_DATABASE_URL` for application/repository tests. A JUnit summary check requires at least the frozen 74-test inventory and zero skips, so a missing owner/runtime URL cannot produce a misleading pass.

The temporary JUnit report is never uploaded. An always-run scan rejects any database password or URL in backend reports before the coverage artifact can upload, and a later always-run cleanup removes and verifies absence of the exact backend PostgreSQL container. Workflow commands pass password values to containers only through masked environment variables, never command-line values.

## Immutable action and scanner pins

The following tag commits were resolved from the named upstream Git repositories on 2026-08-02. Workflow references use the commit, with the human-readable tag only as a comment.

| Upstream                  | Tag      | Immutable commit                           |
| ------------------------- | -------- | ------------------------------------------ |
| `actions/checkout`        | `v4.2.2` | `11bd71901bbe5b1630ceea73d27597364c9af683` |
| `actions/setup-python`    | `v5.6.0` | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| `actions/setup-node`      | `v4.4.0` | `49933ea5288caeca8642d1e84afbd3f7d6820020` |
| `actions/cache`           | `v4.2.3` | `5a3ec84eff668545956fd18022155c47e93e2684` |
| `actions/upload-artifact` | `v4.6.2` | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| `astral-sh/setup-uv`      | `v6.7.0` | `b75a909f75acd358c2196fb9a5f1299a9a8868a4` |

Scanner containers are pinned by OCI index digest: actionlint 1.7.7 at `sha256:887a259a5a534f3c4f36cb02dca341673c6089431057242cdc931e9f133147e9`, Gitleaks 8.28.0 at `sha256:cdbb7c955abce02001a9f6c9f602fb195b7fadc1e812065883f695d1eeaba854`, and Trivy 0.66.0 at `sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`.

Pin upgrades are dedicated supply-chain changes: resolve the exact upstream tag, review release notes and action source, update the SHA/comment together, and rerun actionlint plus the affected jobs. Floating major tags are prohibited.

## Evidence and sensitive output

Coverage, Storybook, Playwright, and Trivy JSON reports use short retention and must contain no credentials, cookies, tokens, contact data, private content, or machine-specific paths. Both image scans run and upload reports before a separate enforcement step fails the job; unfixed Critical/High findings are not hidden. Gitleaks redacts detected values. CI test database credentials are synthetic expressions scoped to isolated runner services and are never production values. The database-privilege job retains no log artifact and scans its temporary captured output for every synthetic password before exact-project cleanup. Failed security output must be sanitized before it is copied into repository evidence.
