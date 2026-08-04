# Canonical Toolchain Contract (F0)

Status: Frozen for Milestone 0 on 2026-08-02. Integration/root owns changes.

## Runtime and package managers

| Area               | Exact contract                                                                                                                                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend            | CPython 3.12.13; uv 0.12.1                                                                                                                      |
| Frontend           | Node.js 22.23.2; Corepack 0.35.0; pnpm 11.18.0                                                                                                  |
| Database           | PostgreSQL 17.10 Bookworm OCI index `postgres@sha256:4f736ae292687621d4dbe0d499ffd024a36bd2ee7d8ca6f2ccd4c800f047b394`                          |
| OpenAPI generation | OpenAPI Generator 7.17.0 OCI index `openapitools/openapi-generator-cli@sha256:868b97eb4e5080d2cdfd5b3eeaa4d52e4bbb7c56f14e234b08b0b0bc4f38a78f` |

The executable runtime pins are `.python-version` and `.nvmrc`. Root manifests
and lockfiles are `pyproject.toml`, `uv.lock`, `package.json`,
`pnpm-workspace.yaml`, and `pnpm-lock.yaml`. Exact backend and frontend package
versions, rationale, install commands, and upgrade rules are defined in
`toolchain-backend.md` and `toolchain-frontend.md`.

PostgreSQL and OpenAPI Generator are pinned by multi-platform OCI index digest;
deployment may resolve the matching platform manifest without silently moving
to a newer release. Containers consume these digests in M0-T07 and M0-T06.

## Security corrections in the frozen lock

The frontend workspace overrides transitive `sharp` to 0.35.3 and `postcss` to
8.5.25. These are the smallest current corrections that clear the advisories
found during Integration review. Removing or weakening an override requires a
clean full audit and evidence that the parent framework has adopted a safe
version.

## Change policy

After F0, only Integration/root may change root pins or locks. A change must be
an explicit upgrade, regenerate the affected lock with the pinned resolver,
pass frozen installation, import/tool/type smoke, vulnerability and license
review, and rerun affected builds, migrations, contract generation, and tests.
Runtime minor changes, framework majors, database changes, generator changes,
or new infrastructure require the accepted change-control/ADR path.

The project is licensed under the MIT License. Dependency license inventories remain separately
authoritative for third-party obligations.
