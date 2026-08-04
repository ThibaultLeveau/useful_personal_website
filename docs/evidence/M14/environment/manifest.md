# M14 local validation environment manifest

Date: 2026-08-04
Executor: Codex local release-validation session
Host: Windows 10.0.26200, x86-64, 16 GB class workstation
Docker: client/server 29.2.1

## Source state

- repository baseline HEAD: `8f6a5e1a4c9ffb894260103cb105d43f21d41fca`;
- the implemented release candidate is an uncommitted worktree, so the required frozen-commit and
  clean-checkout proof is **not satisfied**;
- dependencies were installed from frozen `uv.lock` and `pnpm-lock.yaml` inputs;
- repository checks enumerate only cached/untracked/tracked non-ignored release files.

## Exact production images

| Component | Immutable local digest                                                    | Runtime        | User          |
| --------- | ------------------------------------------------------------------------- | -------------- | ------------- |
| Backend   | `sha256:c9e51227d30a4a3f662771e98f5ad25c1e96b7e9fac06f3146c1bc849650f8a9` | Python 3.12.13 | `10001:10001` |
| Frontend  | `sha256:88ff64d60eba82254af940f17012814e040713d48ecc419f237c093d6671c86f` | Node 22.23.2   | `10001:10001` |

Both were built from the current worktree with `docker build --pull`. The frontend production build
generated 28 outputs. Both container health checks reached `healthy` as non-root users against the
restored database topology.

## Restored-data startup smoke

- PostgreSQL: digest-pinned PostgreSQL 17 image, isolated disposable container;
- backend: production configuration validation enabled, separate non-superuser runtime role,
  current migration head required;
- backend liveness: HTTP 200;
- backend readiness: HTTP 200, `ready`;
- frontend routes: `/`, `/about`, `/skills`, `/admin/login`, `/robots.txt`, and `/sitemap.xml` all
  returned HTTP 200 through the current production image.

All credentials and origins used in this drill were synthetic, local, and destroyed with the
disposable environment.
