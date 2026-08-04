# Contributing

Thank you for helping build Useful Personal Website. The project is in its foundation milestone, so contract clarity and traceability are as important as code.

## Before you start

1. Read the [Code of Conduct](CODE_OF_CONDUCT.md) and [security policy](SECURITY.md).
2. Check existing issues before opening a new one. Use the repository issue forms for reproducible defects, proposals, or documentation gaps.
3. For a substantial, security-sensitive, architectural, migration, API-contract, or specification change, open a discussion issue before implementation.
4. Review the [requirements](docs/requirements/product-requirements.md), [accepted ADRs](docs/architecture/adr/README.md), and [implementation plan](docs/plan/implementation-plan.md) relevant to the change.

Do not include credentials, tokens, personal data, private content, production data, or machine-specific absolute paths in issues, commits, screenshots, logs, or test fixtures.

## Development readiness

Exact runtime pins and canonical noninteractive commands are being frozen during Milestone 0. Follow [docs/development/local-development.md](docs/development/local-development.md); where that guide marks a command as pending, do not substitute an undocumented local workflow in a pull request.

## Change expectations

- Keep each change focused and preserve existing behavior outside its scope.
- Add or update tests at the appropriate layer. A passing command without meaningful assertions is not sufficient.
- Keep domain rules out of route handlers and UI components; follow the documented module boundaries.
- Do not hand-edit generated API artifacts or create competing migration heads.
- Update documentation and traceability when behavior, contracts, operations, or requirements change.
- Do not weaken lint, type, test, security, accessibility, or coverage gates to make a change pass.
- Do not add dependencies without an active requirement, alternatives review, ownership, security/license review, and a test plan.

Specification changes follow `CHG-002`: state the rationale, implementation and migration impact, test impact, acceptance impact, and resolution of any contradiction. Major technical decisions follow `CHG-001` and require an ADR.

## Pull requests

Pull requests should:

- explain the problem and the chosen scope;
- link requirements, acceptance criteria, issues, and ADRs where applicable;
- list security, privacy, accessibility, API, migration, and documentation consequences;
- include reproducible validation evidence using repository-relative references;
- call out unresolved decisions and known limitations; and
- update `CHANGELOG.md` when the change affects users, operators, contributors, or compatibility.

Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md). A maintainer or designated reviewer determines acceptance; an implementer does not self-declare a release gate passed.

## Continuous integration

Run the canonical local checks before opening a pull request. The [CI guide](docs/development/ci.md) maps each diagnostic job to its local command and explains artifact handling. Pull requests must not bypass a failed job, weaken a threshold, or treat the currently pending bootstrap/seed dependency as passed. CI uses read-only repository permissions and immutable action/scanner pins; dependency or action upgrades require a focused supply-chain review.

## Commit and review hygiene

Use clear, imperative commit messages and avoid mixing generated output, broad formatting changes, or unrelated cleanup with functional work. Reviewers may request smaller commits when it improves auditability. Never rewrite or discard another contributor's work without coordination.

## License notice

The project is distributed under the [MIT License](LICENSE). By submitting a contribution, you agree
that it may be distributed under that license and confirm that you have the right to submit it. See
the [license decision record](docs/development/license-decision.md).
