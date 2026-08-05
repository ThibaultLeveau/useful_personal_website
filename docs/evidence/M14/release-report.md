# R1 release-candidate validation report

Date: 2026-08-05
Release decision: **DO NOT RELEASE YET**

## Verified outcome

- API-first public site and configurable administrator CMS capabilities F1/F2 are implemented;
- future AI work remains documentation/extension boundaries only, with no speculative runtime,
  dependency, data flow, or fake UI;
- backend: 544/544 tests, zero skips, 85.0018% branch-aware coverage;
- frontend: 157 tests, strict types/lint, production and Storybook builds;
- browser/accessibility automation: all 41 hosted tests passed, comprising 30 shell checks across
  Chromium, Firefox, and WebKit plus authentication and ten credentialed real-stack workflows;
- Lighthouse: desktop 100/100/100/100; mobile 94/100/100/100;
- current production images: exact Node 22.23.2 and Python 3.12.13, non-root, healthy;
- security: Ruff/Mypy/Bandit/pip-audit/pnpm audit pass, Gitleaks zero leaks, Trivy zero
  High/Critical findings in both current images;
- clean migration and isolated database/media restore consistency pass;
- restored-data production backend and frontend startup smoke passes;
- hosted CI: all nine diagnostic jobs and the required aggregate gate passed on release-candidate
  commit `a99b40878ca9a69801eb3d3b9821151268a8bb9d` ([run 30964510984](https://github.com/ThibaultLeveau/useful_personal_website/actions/runs/30964510984));
- traceability reconciliation: 80 of 81 normative rows Verified.

## Open acceptance items

| Requirement | Blocking evidence                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------- |
| NFR-002     | Human screen-reader, keyboard, zoom/reflow, forced-colors, and representative physical-device report |

The complete implementation was frozen in commit
`5787d544ac17f0e004b3eb8a78911af506f871bb` with a clean post-commit worktree. Hosted corrective
validation completed at `a99b40878ca9a69801eb3d3b9821151268a8bb9d`. Owner inputs still required:
privacy/controller/footer copy, public hostname/trusted origins,
contact/audit retention approval, production object-storage provider/region/auth/encryption,
secret-manager ownership, backup RPO/RTO, restore owner, monitoring/incident contacts, and analytics
decision. See [M13 owner decisions](../M13/owner-decisions.md).

There is no previous public application release, so a previous-release schema/data upgrade is not
applicable. The complete migration chain and representative prior-revision upgrades remain covered
by migration tests.

## Release decision rationale

The software and automated evidence are release-candidate quality and the canonical MIT License is
installed. Production/privacy/accessibility ownership cannot be inferred by implementation. M14
therefore remains blocked without misrepresenting the remaining items as code defaults or waivers.

The complete user/operator set now includes the validated install/start, first-administrator,
content, health, upgrade, coordinated recovery, and troubleshooting path in the
[operator runbook](../../user/operator-runbook.md). Deployment-specific provider and legal values
remain owner decisions rather than missing documentation.
