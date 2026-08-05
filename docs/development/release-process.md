# Release Process

## Current status

No project release exists. This skeleton records policy direction but cannot authorize a release. The independent Release Validator accepts or rejects a release candidate using durable evidence.

## Versioning and changelog

The project intends to use Semantic Versioning once public compatibility contracts exist. User-, operator-, API-, security-, migration-, and contributor-visible changes belong under `Unreleased` in [CHANGELOG.md](../../CHANGELOG.md). A release moves those entries to a dated version only after validation and maintainer approval.

## Release candidate gate

A candidate must have:

- every applicable Must requirement traced to implementation, tests, documentation, and passing evidence;
- clean installation, builds, migrations, startup/readiness, OpenAPI regeneration, and full automated suites from a clean environment;
- independent code, security, accessibility/UX, and API review with no unresolved Critical or High confirmed finding;
- validated backup/restore and previous-release upgrade behavior when a previous release exists;
- sanitized evidence, release notes, known limitations, compatibility/migration guidance, and a rollback plan; and
- resolved maintainer decisions required for lawful and secure distribution, including an installed OSI-approved license and private reporting channels.

The complete clean-release protocol is defined in the [implementation plan](../plan/implementation-plan.md) and [Milestone 14 task/evidence records](../plan/task-catalog.md).

## Pending details

Tag naming, signing, artifact publication, container registry, provenance/SBOM, protected environments, support window, and vulnerability-response targets remain maintainer/operator decisions. Do not publish artifacts or create a release from this skeleton alone.
