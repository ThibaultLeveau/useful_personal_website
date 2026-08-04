# Useful Personal Website

Useful Personal Website is an open-source, API-first personal website and content-management
platform. It combines a premium public portfolio with a secure back office for managing profile
content, pages, navigation, projects, writing, media, contact submissions, and API access.

## Project status

The complete R1 feature set is implemented and locally qualified. Backend, frontend, API, browser,
accessibility automation, security, production-image, migration, backup/restore, and startup gates
pass. Production deployment still requires owner-approved legal/privacy content, infrastructure and
recovery values and physical assistive-technology review. Hosted CI is green on the frozen release
candidate. See the
[release-candidate report](docs/evidence/M14/release-report.md).

The R1 scope covers the public site and configurable back office. AI features are explicitly deferred. The architecture documents extension boundaries for future AI work without shipping fake interfaces, runtime dependencies, or user-facing claims.

## Start here

- [Product specification](SPEC.md)
- [Documentation index](docs/README.md)
- [Product requirements](docs/requirements/product-requirements.md)
- [Architecture overview](docs/architecture/architecture.md)
- [UX information architecture](docs/ux/information-architecture.md)
- [Implementation plan](docs/plan/implementation-plan.md)
- [Developer documentation](docs/development/README.md)

## Architecture at a glance

The accepted direction is a modular monolith with a FastAPI backend, a Next.js frontend, PostgreSQL persistence, and versioned APIs under `/api/v1`. Public and administrative experiences use the official API contract where practical. See the [architecture decision index](docs/architecture/adr/README.md) for the decisions and their consequences.

## Local development

Toolchain pins and canonical commands are recorded in the [local development guide](docs/development/local-development.md). For the validated PostgreSQL/backend/frontend container workflow, follow the [local container runbook](docs/development/containers.md); it keeps migration explicit and does not bootstrap or seed data during startup.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating. Potential vulnerabilities require private handling; follow [SECURITY.md](SECURITY.md) and do not disclose sensitive details in a public issue.

## License

Licensed under the permissive [MIT License](LICENSE). The maintainer's decision is recorded in the
[license decision record](docs/development/license-decision.md).

## Releases

There is no released version yet. Planned changes are recorded in [CHANGELOG.md](CHANGELOG.md); the release process is outlined in [docs/development/release-process.md](docs/development/release-process.md).
