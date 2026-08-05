# Local Development

## Readiness

The exact runtimes and package managers are frozen in [the canonical toolchain contract](toolchain.md). The cross-platform command authority is `python scripts/task.py`; the root `Makefile` is a concise forwarding interface. The infrastructure-owned container workflow is validated in the [local container runbook](containers.md). Explicit administrator bootstrap, first login, and the credential-free demo-content seed are implemented and documented.

Select the versions in `.python-version` and `.nvmrc`, then install the exact uv, Corepack, and pnpm versions recorded in the toolchain contract. Do not substitute floating versions.

## Available foundation commands

| Command                                 | Purpose                                                                                          |
| --------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `python scripts/task.py help`           | List canonical tasks.                                                                            |
| `python scripts/task.py doctor`         | Display and verify prerequisite tool versions.                                                   |
| `python scripts/task.py repo-check`     | Check repository files, relative documentation links, machine paths, and likely secret material. |
| `python scripts/task.py verify`         | Run all checks currently available at the repository-foundation stage.                           |
| `python scripts/task.py backend-check`  | Run backend lint, format, type, and tests after `backend/` is dispatched.                        |
| `python scripts/task.py frontend-check` | Run frontend lint, type, tests, and build after `frontend/` is dispatched.                       |
| `python scripts/task.py seed-demo`      | Explicitly converge fictional local content; requires a runtime-role `APP_DATABASE_URL`.          |

`make <target>` forwards to the same task where Make is available. Commands for an undispatched application fail explicitly instead of silently passing.

## Canonical workflow contract

The completed guide will provide noninteractive, platform-neutral entry points for:

1. validating prerequisite runtime and package-manager versions;
2. installing locked backend and frontend dependencies;
3. creating local configuration from committed examples without embedding secrets;
4. starting required development services;
5. running database migrations explicitly;
6. bootstrapping the first administrator separately from demo content;
7. starting backend and frontend development processes;
8. formatting, linting, strict type-checking, testing, and building both applications;
9. exporting OpenAPI and regenerating the typed client with a clean diff; and
10. stopping services and removing only explicitly named disposable local resources.

## Rules that already apply

- Use only exact versions and lockfiles accepted by the toolchain contract.
- Keep credentials in ignored local environment or secret-management facilities; never commit them.
- Startup must not migrate, bootstrap an administrator, or seed content implicitly.
- Demo seed creates no users or tokens, refuses production, and is never part of startup.
- Treat generated clients and migration lineage as reserved shared artifacts.
- Record validation without usernames, home directories, tokens, personal data, or production content.

## Current authorities

The accepted backend names and Compose-only local variables are listed in [configuration](configuration.md). `compose.yaml` is the canonical local topology and [local containers](containers.md) is its operating protocol. Follow [first administrator setup and sign-in](../user/first-login.md) for the explicit takeover-safe bootstrap. Use `seed-demo` only as a separate, non-production operator action after migration and permission reconciliation; never combine it with bootstrap or startup.
