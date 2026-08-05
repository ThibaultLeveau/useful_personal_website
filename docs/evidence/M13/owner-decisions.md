# Owner and operator decisions required before release

Status: **Resolved and superseded on 2026-08-05.** See the accepted
[M14 owner-decision record](../M14/prerequisites/owner-decision-record.md). The table below is kept as
historical context for the decision categories that originally blocked M13.

Implementers must not invent these values. The owner has now recorded them for the R1 candidate.

| Decision                                                                        | Why it blocks release                                                                 |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Privacy notice, legal/footer copy, controller/contact identity                  | Public contact collection needs accurate owner-specific disclosure                    |
| Contact and audit retention periods                                             | Production deletion schedules and notices must match policy                           |
| Production hostname and trusted origins                                         | Canonical URLs, cookies, CSRF, CORS/origin checks, sitemap, and robots depend on them |
| S3-compatible provider, region, auth source, encryption/KMS, and managed prefix | Production media storage cannot be qualified from local defaults                      |
| Backup RPO/RTO and restore owner                                                | Operations cannot accept recovery readiness without measurable objectives             |
| Monitoring, alert routing, and incident contacts                                | Health checks alone do not define production response ownership                       |
| Analytics/error-reporting decision                                              | Any service must be reviewed for consent, minimization, retention, and disclosure     |

The accepted values are represented in M14 evidence. External deployment and recovery validation
remain release gates rather than unresolved owner choices.
