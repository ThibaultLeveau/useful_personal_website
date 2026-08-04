# Backend toolchain fragment

This document records the `M0-T01-B` candidate for the backend portion of the
F0 toolchain contract. Integration/root owns the canonical F0 record and any
changes after review.

## Exact runtime and package-manager contract

| Component | Exact version | Role |
|---|---:|---|
| CPython | 3.12.13 | Backend runtime selected within the required Python 3.12 line |
| uv | 0.12.1 | Python acquisition, dependency resolution, environment synchronization, and command execution |

`.python-version` is the executable runtime pin. `project.requires-python`
allows only the selected Python 3.12 patch or a newer 3.12 security patch, so
the metadata remains truthful if the runtime pin is deliberately upgraded.
`tool.uv.required-version` rejects a different uv version before it can change
the environment or lock.

Python 3.12.13 is the current 3.12 security release. CPython publishes it as a
source-only security release; uv 0.12.1 supplies managed, verified CPython
distributions for the supported development platforms. This avoids selecting
the older 3.12.10 solely because it was the last python.org binary release.

## Exact direct dependency contract

### Application and operations

| Package | Exact version | Justification |
|---|---:|---|
| FastAPI | 0.141.1 | Versioned HTTP/OpenAPI transport |
| Pydantic | 2.13.4 | Explicit request, response, and domain-boundary validation |
| pydantic-settings | 2.14.2 | Typed environment configuration |
| SQLAlchemy | 2.0.51 | SQLAlchemy 2 async persistence and unit-of-work implementation |
| Alembic | 1.18.5 | Explicit PostgreSQL schema migrations |
| asyncpg | 0.31.0 | Async PostgreSQL driver for the selected SQLAlchemy design |
| argon2-cffi | 25.1.0 | Required Argon2id password hashing |
| structlog | 26.1.0 | Required structured logging with application-controlled redaction |
| Uvicorn | 0.52.1 | Local and container ASGI process |

The root dependency contract intentionally omits Redis, workers/brokers,
Kubernetes libraries, AI/LLM/vector packages, JWT libraries, and cloud SDKs.
The accepted architecture does not require them in R1. Uvicorn's optional
`standard` extra is also omitted because the baseline does not need its extra
watcher, YAML, WebSocket, or alternate event-loop packages.

### Test, quality, and security tooling

| Group | Package | Exact version | Role |
|---|---|---:|---|
| test | HTTPX | 0.28.1 | In-process and live HTTP client tests |
| test | Pytest | 9.1.1 | Backend test runner |
| test | pytest-asyncio | 1.4.0 | Async service/repository/API tests |
| test | pytest-cov | 7.1.0 | Coverage measurement and reports |
| quality | Ruff | 0.16.1 | Formatting and linting |
| quality | Mypy | 2.3.0 | Strict static type checking |
| quality | pre-commit | 4.6.1 | Pinned hook runner; hook configuration is owned by `M0-T02` |
| security | Bandit | 1.9.4 | Python static security analysis |
| security | pip-audit | 2.10.1 | Python dependency vulnerability audit |
| security | licensecheck | 2026.0.8 | Dependency-license inventory and policy check |

`uv.lock` resolves all groups together for every platform supported by the
universal lock. Direct requirements are exact pins; transitive artifacts and
hashes are frozen in the lockfile.

## Reproducible workflow

Install the exact uv release using one of uv's documented installation methods,
then run from the repository root:

```console
uv --version
uv python install
uv sync --all-groups --frozen
uv lock --check
uv run python --version
```

`uv sync --all-groups --frozen` must be the clean-environment install path. It
fails rather than changing a stale lock. Use `uv lock` only when intentionally
refreshing the dependency contract.

Tool smoke commands:

```console
uv run python -c "import alembic, argon2, asyncpg, fastapi, pydantic, pydantic_settings, sqlalchemy, structlog, uvicorn"
uv run pytest --version
uv run ruff --version
uv run mypy --version
uv run bandit --version
uv run pre-commit --version
uv run pip-audit --version
uv run python -c "import importlib.metadata as m; print(m.version('licensecheck'))"
```

Application-specific Ruff, strict Mypy, Pytest, and Bandit configuration belongs
with the backend harness in `M0-T03`; the root file freezes compatible executable
versions without pre-empting that task. The pre-commit hook configuration is
similarly reserved for Infrastructure after F0 review.

## Upgrade policy

1. Integration/root owns the root manifest and lock after F0 is accepted.
2. Review runtime and direct dependencies at least monthly and immediately for
   relevant security advisories or Python security releases.
3. Change exact pins in one reviewed upgrade change. Do not hand-edit
   `uv.lock`; regenerate it with the exact pinned uv release.
4. Re-run a frozen clean sync, import/version smoke, Ruff, strict Mypy, Pytest,
   Bandit, `pip-audit`, and the license review. Exercise migrations and OpenAPI
   generation once those tasks exist.
5. Treat a Python minor, framework major, database-driver change, resolver
   change, removed dependency, or new optional infrastructure as an explicit
   compatibility/change review. Update an ADR when the architectural decision
   changes.
6. Commit the manifest, runtime pin, lockfile, documentation, and sanitized
   evidence together. No automatic dependency merge may bypass the gates.

## Selection sources

- [Python 3.12.13 release](https://www.python.org/downloads/release/python-31213/)
- [uv Python version management](https://docs.astral.sh/uv/concepts/python-versions/)
- [uv dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- [uv configuration reference](https://docs.astral.sh/uv/reference/settings/)
- Package release metadata and Python compatibility: each package's canonical
  JSON metadata endpoint under `https://pypi.org/pypi/<package>/json`, reviewed
  on 2026-08-02.
