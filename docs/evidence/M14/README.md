# M14 independent release validation

Date: 2026-08-05
Disposition: **BLOCKED — automated/local validation complete; external verification remains**

## Task status

| Task                                                  | Result                                                   | Evidence                                                                                                                                                               |
| ----------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M14-T01 clean environment/build/migrate/restore/start | Local pass including implementation freeze               | [Environment manifest](environment/manifest.md), [restore drill](restore-drill.md)                                                                                     |
| M14-T02 full independent matrix                       | Automated and hosted pass; physical AT/device check open | [M13 gate](../M13/README.md), [browser review](accessibility/browser-assisted-review.md), [release report](release-report.md)                                          |
| M14-T03 traceability and release report               | Reconciled but not accepted                              | [Credentialed browser workflows](critical-browser-workflows.md), [release report](release-report.md), [traceability matrix](../../requirements/traceability-matrix.md) |

No public release is declared. The implementation freeze began at
`5787d544ac17f0e004b3eb8a78911af506f871bb`; the release-candidate corrections through
`a99b40878ca9a69801eb3d3b9821151268a8bb9d` passed hosted CI, including all 41 browser tests and
credentialed critical workflows. The owner decisions were accepted on 2026-08-05. Manual
assistive-technology/device review and validation of the actual Hostinger deployment, TLS, backup,
and restore path remain outstanding.

The remaining work now has an executable handoff: use the
[physical accessibility protocol](accessibility/manual-device-review.md) and its machine-readable
[test matrix](accessibility/wcag-2.2-aa-matrix.csv), deploy the accepted values using the
[Hostinger runbook](../../../deployments/hostinger/README.md), and apply the objective
[go/no-go rule](release/go-no-go.md).

The deterministic [screenshot integrity inventory](screenshots/inventory.json) records the path,
SHA-256, size, and safely inferable metadata for all repository evidence PNGs. Its explicit null and
`unrecorded` fields prevent historical captures from being misrepresented as candidate-specific or
human-reviewed evidence; regenerate it with `python scripts/generate_screenshot_inventory.py`.
