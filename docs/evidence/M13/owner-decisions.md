# Owner and operator decisions required before release

Implementers must not invent these values. M13 remains blocked until the owner records them.

| Decision                                                                        | Why it blocks release                                                                 |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Privacy notice, legal/footer copy, controller/contact identity                  | Public contact collection needs accurate owner-specific disclosure                    |
| Contact and audit retention periods                                             | Production deletion schedules and notices must match policy                           |
| Production hostname and trusted origins                                         | Canonical URLs, cookies, CSRF, CORS/origin checks, sitemap, and robots depend on them |
| S3-compatible provider, region, auth source, encryption/KMS, and managed prefix | Production media storage cannot be qualified from local defaults                      |
| Backup RPO/RTO and restore owner                                                | Operations cannot accept recovery readiness without measurable objectives             |
| Monitoring, alert routing, and incident contacts                                | Health checks alone do not define production response ownership                       |
| Analytics/error-reporting decision                                              | Any service must be reviewed for consent, minimization, retention, and disclosure     |

The repository documents safe defaults and validation, but none of these placeholders may be
presented as the owner's final legal or operational choice.
