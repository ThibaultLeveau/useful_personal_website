# M6 security certification

Bandit 1.9.4 scanned 16,911 backend lines with zero findings after the final persistence-index
correction. It encountered one pre-existing, narrowly explained B105 suppression on the literal
`api_token` actor-kind enum; that value is a public catalog label, not a credential. There are no
test suppressions or M6 security exclusions.

`pip-audit` 2.10.1 over the frozen Python 3.12.13 environment and
`pnpm audit --prod --audit-level high` over the locked production JavaScript graph both report no
known vulnerabilities. No severity threshold was reduced.

Pinned Trivy 0.66.0 scanned the exact candidate images with both vulnerability and secret scanners
at blocking High/Critical severity:

| Image    | Exact image ID                                                            |      Bytes | High/Critical | Secrets |
| -------- | ------------------------------------------------------------------------- | ---------: | ------------: | ------: |
| Backend  | `sha256:55951a68cbdbf8b8847b67a6774778c996035f9ec42ba2f7bd430c5c83ed4ef3` | 37,541,383 |             0 |       0 |
| Frontend | `sha256:e93fe0cd0ffffbabb4a5ea871e0975a76e8b0b5d7db7befb9e5e243ec8d51286` | 61,542,348 |             0 |       0 |

Raw machine-readable reports are [backend](trivy-backend.json) and
[frontend](trivy-frontend.json). The database scanner cache and reports contain advisory metadata
only; no application credentials are retained.

Negative project tests cover full-session authorization, guessed preview, CSRF/Origin, IDOR,
mass-assignment, query/content injection, unsafe URL schemes, stale preconditions, idempotency
mismatch, graph cycles, and unavailable media identifiers. Public API/HTML/metadata/JSON-LD and
screenshots expose no draft, future, hidden/deleted target, pointer/revision/creator/version,
storage, cookie, CSRF, or authorization value. Playwright failure traces/reports were removed after
the passing run; only sanitized synthetic screenshots remain.
