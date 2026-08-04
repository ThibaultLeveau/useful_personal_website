# M13 current-image and secret-scan evidence

Date: 2026-08-04
Disposition: **Pass**

## Release-candidate images

Both images were rebuilt from the current worktree with `--pull` and the repository Dockerfiles.

| Image | Local immutable digest | Runtime | Runtime user |
| --- | --- | --- | --- |
| Backend | `sha256:c9e51227d30a4a3f662771e98f5ad25c1e96b7e9fac06f3146c1bc849650f8a9` | Python 3.12.13 | `10001:10001` |
| Frontend | `sha256:88ff64d60eba82254af940f17012814e040713d48ecc419f237c093d6671c86f` | Node 22.23.2 | `10001:10001` |

The frontend build generated all 28 expected static outputs. Its runtime reported exactly
`v22.23.2`, matching `.nvmrc`, `package.json`, and the digest-pinned production base image.

## Trivy

- Scanner: Trivy 0.73.0;
- scanner image digest:
  `sha256:7cced7cae583819fc7806d4cbc0dbbc7cad18b99f7d3e235192e6da8c091045c`;
- threshold: every fixed or unfixed `HIGH` or `CRITICAL` finding;
- backend result: **0 High/Critical**;
- frontend result: **0 High/Critical**.

Machine-readable reports:

- [Backend image report](trivy-backend.json)
- [Frontend image report](trivy-frontend.json)

## Gitleaks

- Scanner: Gitleaks 8.30.1;
- scanner image digest:
  `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`;
- scope: all cached, untracked, and tracked non-ignored release-source files, staged into a clean
  temporary directory; includes the final Trivy reports;
- output redaction: enabled;
- final result: **0 leaks**.

The first pass produced 28 false positives. Every candidate was reviewed before a narrow allowlist
was added in `.gitleaks.toml`: synthetic idempotency test identifiers, published OpenAPI hashes,
public GPG key identifiers in historical image metadata, and two exact security-documentation
phrases. No path-wide or rule-wide suppression is used. The clean final report is
[gitleaks.json](gitleaks.json).
