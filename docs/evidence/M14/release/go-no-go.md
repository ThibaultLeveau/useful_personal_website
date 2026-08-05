# R1 go/no-go record

Date: 2026-08-05
Current decision: **NO-GO**

## Passed technical gates

- Required hosted CI gate passed with all nine diagnostic jobs and all 41 browser tests on
  `a99b40878ca9a69801eb3d3b9821151268a8bb9d`.
- Backend, frontend, OpenAPI generation, migrations, production images, vulnerability scans,
  database privilege boundaries, seed safety, restore/startup, and documentation walkthroughs have
  passing evidence linked from the M14 release report.
- The canonical MIT License is installed and the traceability matrix records 80 of 81 normative rows
  Verified.

## Open release gates

- NFR-002 physical assistive-technology/device acceptance is not executed. Use the
  [protocol and matrix](../accessibility/manual-device-review.md).
- The accepted production/legal profile has not yet been exercised on the actual Hostinger VPS.
  Complete DNS/TLS, alert delivery, weekly database/media backup, and timed restore validation using
  the [Hostinger runbook](../../../../deployments/hostinger/README.md).

## Promotion rule

Change this decision to GO only after every accessibility matrix row is `PASS`, all seven accepted
owner decisions remain current, the selected production values pass their
documented validation and recovery drills, no unresolved Critical/High defect exists, the candidate
commit has a green required CI gate, and the traceability matrix has no non-Verified normative row.

Any code, dependency, migration, production configuration, or content-policy change after acceptance
creates a new candidate and requires impact-based revalidation before promotion.
