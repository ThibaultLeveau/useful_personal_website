# Security, privacy, and supply-chain review

Date: 2026-08-04

## Passing automated gates

- repository checks: 1,201 visible files, all links/hygiene rules passed;
- `git diff --check`: passed;
- `uv lock --check`: passed;
- Ruff and strict Mypy: passed;
- Bandit 1.9.4: no findings after the M13 SQL repair;
- pip-audit 2.10.1: no known vulnerabilities;
- pnpm production audit: no known vulnerabilities;
- licensecheck: every Python dependency is compatible under its reported license;
- Gitleaks 8.30.1 staged-source scan: no leaks after reviewed narrow false-positive allowlists;
- Trivy 0.73.0 current-image scans: zero High/Critical findings in both release-candidate images.

The pnpm audit used the frozen pnpm 11.18.0 through Corepack. The host audit emitted an engine
warning because the host has Node 22.14.0. The actual current production image was subsequently
rebuilt from the digest-pinned Node 22.23.2 Dockerfile, produced all 28 expected outputs, and
reported runtime `v22.23.2`. Exact production-runtime qualification now passes. See
[current-image and secret-scan evidence](security/README.md).

## Security-sensitive repairs

- closed-choice website-settings media eligibility now selects one of three complete static SQL
  statements; no identifier is interpolated;
- scanner false positives on rate-limit policy identifiers were removed by using names that do not
  imply stored credentials;
- API token integration coverage confirms one-time plaintext display, digest-only persistence
  projection, scope denial, rotation invalidation, revocation invalidation, and malformed bearer
  denial;
- contact integration coverage confirms proof validation, consent/policy validation, honeypot
  rejection, idempotent replay, private admin reads, optimistic concurrency, and audit correlation;
- local qualification data uses fictional `example.test` identities only.

## Open blockers

- the production hostname/origin, secret manager, S3 provider/region/encryption choice, retention
  values, and incident contacts remain owner/operator decisions;
- manual assistive-technology and representative physical-device review remains human work.
