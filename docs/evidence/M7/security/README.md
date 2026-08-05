# M7 security certification

Bandit 1.9.4, `pip-audit` 2.10.1, and the locked production pnpm audit report no findings or known
vulnerabilities. The pnpm audit was repeated inside the exact Node 22.23.2 image to avoid a host
runtime warning.

Pinned Trivy 0.66.0 scanned the exact M7 images with vulnerability and secret scanners at blocking
High/Critical severity:

| Image    | Exact image ID                                                            |      Bytes | High/Critical | Secrets |
| -------- | ------------------------------------------------------------------------- | ---------: | ------------: | ------: |
| Backend  | `sha256:b4af3d19e0308557350d35333de024eccb66d84d30f8df2e85b43d917df6ec4f` | 38,911,582 |             0 |       0 |
| Frontend | `sha256:94c993fb23fcab953fe0515f1f1cb3d2b781ce5423383ddd1646ddeecf2ad98c` | 61,698,482 |             0 |       0 |

The scanner warned that a third-party SBOM can reduce detection precision and that Alpine 3.23 was
not yet in its local EOL catalog; neither warning reports an application vulnerability. Raw reports
are `trivy-backend.json` and `trivy-frontend.json`.

The malicious corpus and browser journey assert no script/event node, attacker request,
navigation, privileged DOM mutation, or unsafe fallback. Preview guessing, source export without a
session, CSRF/Origin failures, IDOR, mass assignment, unsafe Markdown/URL, stale versions,
idempotency mismatch, taxonomy usage conflicts, and nonpublic projections fail closed. Sanitized
screenshots contain no cookies, CSRF values, credentials, private source, or administrator email.
