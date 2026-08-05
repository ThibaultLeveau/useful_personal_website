# Testing and Evidence

The [test strategy](../plan/test-strategy.md) is the normative test inventory; the [quality strategy](../plan/quality-strategy.md) defines gates and corrective routing. This page orients contributors without replacing either document.

## Test selection

Choose the smallest layer that proves the behavior, then add integration or browser coverage where contracts, persistence, security, or user workflows cross boundaries. Critical workflows require end-to-end proof; snapshot-only or execution-only assertions do not establish correctness.

The planned inventory includes backend unit, service, repository, API, authentication/authorization, migration, validation, error-contract, and audit tests; frontend component, form, page, API-state, accessibility, responsive, Storybook interaction, and production-build checks; and the complete browser workflows listed in the test strategy.

## Evidence rules

- Use the [delivery evidence template](../plan/delivery-evidence-template.md).
- Record the command or protocol, relevant tool version, result, and repository-relative artifact.
- Record both requested milestone and existing trace milestone aliases.
- A failing or unrun required check remains visible; do not relabel it as pass.
- Sanitize logs, screenshots, traces, API transcripts, and database samples.
- Never store secrets, auth headers, cookies, token reveals, contact data, production dumps, usernames, or absolute local paths in evidence.
- Implementers provide evidence; integration or an independent reviewer records the gate decision.

## Corrective work

Reproduce and classify a finding, identify the requirement and affected regression scope, apply the smallest correction, rerun the failed check plus impacted gates, and preserve before/after evidence. Tests, types, scanners, and thresholds must not be weakened to obtain a green result.

The F1 command contract begins at `python scripts/task.py`; application agents extend the backend and frontend scripts they invoke without changing the public task names. Evidence artifacts live under `docs/evidence/<milestone>/`.
