# M0-T01-B - Backend toolchain compatibility

## Identity

- Requested milestone: M0
- Existing trace milestone alias(es): M01, M02
- Requirement IDs: NFR-009, NFR-017, CHG-001
- Acceptance IDs: AC-035, AC-040, AC-043, AC-045
- Build/commit: baseline `8f6a5e1a4c9ffb894260103cb105d43f21d41fca`; candidate changes uncommitted
- Branch/PR: `main`; no PR
- Environment/image digests: Windows x86_64; uv-managed CPython 3.12.13; no container used
- Executor/reviewer: Backend Agent; Integration/root review pending
- Started/completed UTC: 2026-08-02T17:15:00Z / 2026-08-02T17:32:00Z

## Delivery

- Goal and outcome: selected an exact Python/uv contract and compatible exact
  backend runtime, test, quality, and security pins; generated a universal uv
  lock with artifact hashes; all implementer compatibility checks passed.
- Files/modules changed: `.python-version`, `pyproject.toml`, `uv.lock`,
  `docs/development/toolchain-backend.md`, and this record.
- Migration revision/data action (or N/A): N/A; migrations are excluded from
  `M0-T01-B`.
- OpenAPI/client change and regeneration result (or N/A): N/A; no application
  or contract code exists in this assignment.
- Security/privacy consequences: the dependency vulnerability audit found no
  known vulnerabilities. The license inventory contains only recognized
  open-source licenses. The repository's own license remains deliberately
  unresolved as `R-018`; no license was selected here.
- Accessibility/UX consequences: N/A; no user interface changed.
- Documentation changed: backend toolchain rationale, reproducible workflow,
  ownership boundary, selection sources, and upgrade policy documented in
  `docs/development/toolchain-backend.md`.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | `uv run --frozen ruff --version`; `uv run --frozen mypy --strict -c <typed Pydantic/SQLAlchemy smoke>` with Ruff 0.16.1 and Mypy 2.3.0 | Pass; strict Mypy reported no issues and revealed the expected `int` and `InstrumentedAttribute[int]` types. Ruff executable/version smoke passed; source lint begins with the application harness in M0-T03. | `pyproject.toml`, `docs/development/toolchain-backend.md` |
| Backend unit/service/repository/API | CPython import/version smoke for FastAPI, Pydantic, pydantic-settings, SQLAlchemy, Alembic, asyncpg, argon2-cffi, structlog, and Uvicorn; `pytest --version` | Pass; every import succeeded at the exact direct version and Pytest 9.1.1 executed. No application tests are authorized in this assignment. | `pyproject.toml`, `uv.lock` |
| Migration/empty DB/upgrade | N/A - M0-T05 responsibility | Not run | N/A |
| OpenAPI/generator diff | N/A - M0-T06 responsibility | Not run | N/A |
| Frontend format/lint/type/build | N/A - frontend lane | Not run | N/A |
| Frontend unit/component/Storybook/a11y | N/A - frontend lane | Not run | N/A |
| E2E/integration | No user flow exists at toolchain selection time. Substitute: managed-runtime install plus frozen offline environment synchronization. | Pass; `uv python install`, `uv sync --all-groups --frozen`, and a second `--offline` frozen sync succeeded. | `.python-version`, `uv.lock` |
| Security/privacy | `bandit --version` 1.9.4; `pre-commit --version` 4.6.1; `pip-audit --local --strict` 2.10.1; installed-metadata inventory; `licensecheck --groups test quality security` 2026.0.8 | Pass with recorded license disposition; no known vulnerabilities. All 89 installed distributions expose recognized licenses and none report a GPL/proprietary license. The independent licensecheck resolution reviewed 67 packages; `certifi` and `pathspec` are tooling-only MPL-2.0 transitive dependencies and retain their own license obligations. Project-license compatibility remains part of `R-018`. | `pyproject.toml`, `uv.lock`, this record |
| Manual UX/a11y/browser | N/A | Not run | N/A |
| Performance/coverage | N/A; no executable application code | Not run | N/A |
| Documentation/link walkthrough | Reviewed repository-relative file references and authoritative Python/uv/PyPI source links. | Pass | `docs/development/toolchain-backend.md` |

### Reproducibility transcript summary

- uv executable: `uv 0.12.1 (329541a50 2026-07-31)`.
- Managed runtime: `CPython 3.12.13`.
- Resolver: 90 packages resolved; 89 packages installed across all groups.
- Lock integrity: SHA-256 before and after a second `uv lock` was
  `20A4BC6EE07EEEA4641B61D45370687F3ADA70604CE3F483DE3DEB2FED027AC9`.
- `uv lock --check` passed.
- `uv sync --all-groups --frozen --offline` passed from the populated cache,
  proving the lock was sufficient without a resolver refresh.
- `pip-audit --local --strict`: `No known vulnerabilities found`.
- Installed-distribution metadata inventory: 89 distributions, zero unknown
  licenses, and no GPL/proprietary license marker.
- Exact direct-pin/lock comparison: all 19 direct requirements match their
  locked versions.
- `git diff --check` and an explicit untracked-file trailing-whitespace/final-LF
  scan passed.
- No source, test, migration, frontend, pre-commit configuration, container, CI,
  or task-runner file was added by this lane.

## Acceptance record

| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| AC-035 | Not run | Backend stack subset is pinned/imported here; the integrated architecture review belongs to Integration/root. | None; pending combined T01 review. |
| AC-040 | Not run | Dependency review found no optional infrastructure or speculative AI dependency; full milestone-slice review is broader than this lane. | None; pending combined T01 review. |
| AC-043 | Not run | Backend toolchain workflow and upgrade policy are documented; the complete new-contributor walkthrough occurs after T02. | None; pending downstream documentation gate. |
| AC-045 | Not run | Exact pins implement accepted ADR decisions and introduce no new architectural decision; Integration/root owns F0 acceptance. | None; pending combined T01 review. |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| Initial local uv installation attempt hit a transient Windows socket-buffer exhaustion error. | Low | The first `pip install uv==0.12.1` could not reach the package index. | Transient host network resource exhaustion, not package incompatibility. | 1 | Retried the exact no-cache installation after metadata access recovered. | uv 0.12.1 installed and all later network/lock/sync operations passed. |
| `licensecheck --version` is not a supported CLI option. | Low | The CLI returned argument error for `--version`; its actual inventory command was unaffected. | Tool exposes version only through package metadata. | 1 | Replaced the documentation smoke with `importlib.metadata.version('licensecheck')`. | Reported 2026.0.8; full grouped inventory completed. |
| License compatibility cannot be computed against an unselected repository license; the inventory marks MPL-2.0 tooling dependencies for review. | Low / known risk | Grouped license inventory reports repository license unknown and identifies `certifi` and `pathspec` as MPL-2.0. | Maintainer license decision is intentionally open as `R-018`. | 1 | Recorded packages, scope, and continuing obligations without selecting a project license. | Manual review confirmed both are tooling-only transitive dependencies under recognized MPL-2.0. |

## Completion decision

- Gate: Pending Integration/root decision; implementer validation passed.
- Remaining risks/targets and disposition: `R-018` remains open by dispatch;
  Integration/root must combine backend/frontend lane reports and freeze F0.
- Traceability matrix rows updated: none; Integration/root owns cross-lane
  acceptance and traceability records.
- Independent reviewer sign-off: pending Integration/root.
