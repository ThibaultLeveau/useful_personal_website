# M0-T07-I - Environment and container infrastructure

## Identity

- Requested milestone: M0
- Existing trace milestone alias(es): M01, M03, M20
- Requirement IDs: F2-002, NFR-012, NFR-016, OSS-002
- Acceptance IDs: AC-015, AC-036, AC-041, AC-044
- Build/commit: baseline `8f6a5e1`; uncommitted candidate working tree
- Branch/PR: `main`; no PR
- Environment/image digests: Docker Engine 29.2.1, Compose 5.0.2, Linux amd64; local image IDs recorded below
- Executor/reviewer: Infrastructure Agent / integration reviewer pending
- Started/completed UTC: 2026-08-02 / 2026-08-02

## Delivery

- Goal and outcome: Added the infrastructure-owned F5 candidate: secure environment example, root Docker context policy, digest-pinned multi-stage backend/frontend images, private PostgreSQL/local-media topology, explicit one-shot migration profile, health/readiness checks, and operator documentation. This slice is ready for integration review.
- Files/modules changed: `.env.example`, `.dockerignore`, `compose.yaml`, both application Dockerfiles, `infrastructure/README.md`, container/configuration/development/database documentation, root README link, and this record.
- Migration revision/data action (or N/A): No migration file changed. The isolated validation database upgraded explicitly from empty to the sole head `20260802_0001` before application startup.
- OpenAPI/client change and regeneration result (or N/A): N/A; no schema, generated client, or API code changed.
- Security/privacy consequences: Images contain no injected build secret, run as UID/GID 10001, declare health checks, and use read-only roots plus `no-new-privileges` in Compose. PostgreSQL remains on an internal network with no host port. Application ports bind loopback only. `.env` and credential artifacts are excluded from build context.
- Accessibility/UX consequences: No UI code changed. Frontend production route returned HTTP 200 after healthy backend startup.
- Documentation changed: Added a complete local container protocol and updated configuration visibility, migration, developer index, and root onboarding links.

## Validation

| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | No application code change | N/A | — |
| Backend unit/service/repository/API | Existing accepted T03/T05 code exercised through built image | Pass: liveness and database/migration readiness returned successful responses | [T03 acceptance](M0-T03.md), [T05 acceptance](M0-T05.md) |
| Migration/empty DB/upgrade | Isolated Compose PostgreSQL; `docker compose --profile operations run --rm migrate` before application `up` | Pass: transactional upgrade to `20260802_0001`; one-shot container removed | [Container runbook](../../development/containers.md) |
| OpenAPI/generator diff | No contract change | N/A | — |
| Frontend format/lint/type/build | Multi-stage Node 22.23.2 image; frozen pnpm 11.18.0 install with dependency scripts disabled; `next build` | Pass: compiled, strict TypeScript completed, four static pages generated | [Frontend Dockerfile](../../../frontend/Dockerfile) |
| Frontend unit/component/Storybook/a11y | No UI behavior change | N/A; accepted T04 evidence remains authoritative | [T04 acceptance](M0-T04.md) |
| E2E/integration | Unique Compose project: config, PostgreSQL health, explicit migration, backend/frontend start, readiness, HTTP smoke, bounded cleanup | Pass: both containers healthy; frontend 200; zero validation containers after cleanup | [Compose topology](../../../compose.yaml) |
| Security/privacy | Inspect image config/history/filesystem and running container metadata | Pass: zero validation-secret/history matches, zero private contract environment variables baked into images, no `.env`/`.git`, UID/GID 10001, read-only roots, `no-new-privileges` | [Docker context policy](../../../.dockerignore) |
| Manual UX/a11y/browser | HTTP smoke only; no UX change | Pass for route availability | [T04 acceptance](M0-T04.md) |
| Performance/coverage | Image sizes inspected | Backend 63,376,627 bytes; frontend 180,281,632 bytes; no release budget asserted | This record |
| Documentation/link walkthrough | Compose/configuration/runbook review and `git diff --check` | Pass | [Container runbook](../../development/containers.md) |

## Image metadata

| Image | Local image ID | Runtime user | Base contract |
|---|---|---|---|
| Backend | `sha256:621e00458b257f165676c5489de946a53cbd83fc3f5e366d4a5d1b0adabe2315` | `10001:10001` | Python 3.12.13 and uv 0.12.1 exact index digests |
| Frontend | `sha256:c53bfb48b91dfc38ca78fb8182e340ea8bcc56d66d19574a24cfc883a8ba81e1` | `10001:10001` | Node 22.23.2 exact index digest; Corepack 0.35.0; pnpm 11.18.0 |
| PostgreSQL | F0 index `sha256:4f736ae292687621d4dbe0d499ffd024a36bd2ee7d8ca6f2ccd4c800f047b394` | Official image contract | PostgreSQL 17.10 Bookworm |

## Acceptance record

| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| AC-015 | Not run | Infrastructure preserves explicit bootstrap separation and performs no startup/bootstrap action. | Secure idempotent bootstrap implementation and tests remain the named backend sub-assignment. |
| AC-036 | Not run | Production images build; explicit empty migration and Compose startup/readiness pass. | Integration/root records the task decision. |
| AC-041 | Not run | No bootstrap or seed path exists in this infrastructure slice. | Backend bootstrap/seed implementation, idempotency, separation, and production-refusal tests remain required. |
| AC-044 | Not run | No secrets, private data, machine paths, `.env`, or repository metadata were added to image layers. | Integration/root performs the cross-repository acceptance review. |

## Findings and corrective loop

| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| Frontend frozen install rejected ignored transitive build scripts | Medium | First clean frontend image build | pnpm strict dependency-build policy rejected unapproved `esbuild` and `unrs-resolver` scripts | 1 | Disabled all dependency lifecycle scripts for the image install; relied on locked prebuilt platform packages | Next production build and runtime health pass |
| Migrator console script referenced the builder path | High | First isolated one-shot migration | Virtual environment was created at `/build/.venv` then copied, leaving non-relocatable shebangs | 1 | Created the frozen environment at its final `/app/.venv` path in the builder | Rebuild, migration, readiness, HTTP smoke, and cleanup pass |

## Completion decision

- Gate: Blocked
- Remaining risks/targets and disposition: The infrastructure-owned slice passes implementer validation. Full `M0-T07` remains blocked until a named backend sub-assignment implements and tests the internal bootstrap and demo-seed commands, after which infrastructure may wire only their accepted command names. No placeholder wrappers were created. F5 remains an integration/root decision.
- Traceability matrix rows updated: None; integration/root owns cross-lane acceptance records and F5.
- Independent reviewer sign-off: Pending integration/root review.
