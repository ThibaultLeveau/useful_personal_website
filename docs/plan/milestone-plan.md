# R1 Milestone Plan

## Milestone alias policy

The requested execution sequence is `M0`-`M14`. The requirements traceability matrix retains its existing `M01`-`M20` values. The table below is the non-destructive crosswalk; implementations and evidence must record both labels. No existing traceability row is renumbered.

| Requested milestone | Outcome / vertical slice                                                                                                                                    | Existing trace milestone aliases           | Exit gate                                                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| M0                  | Repository foundation: pinned toolchain, monorepo/app skeletons, database/Alembic, test harnesses, containers, CI, OpenAPI client workflow, docs/governance | M01, M02, M03; early boundary parts of M20 | `AC-035`-`AC-037`, `AC-040`, `AC-043`-`AC-046` foundation checks; all baseline commands run locally                                     |
| M1                  | Identity/authentication: bootstrap, login/logout/session, forced password change, CSRF/rate limit, auth audit                                               | M04                                        | `AC-015`-`AC-017`, auth portion of `AC-024`; browser E2E proves the full lifecycle                                                      |
| M2                  | Core API conventions: namespace/envelopes/errors, pagination/filter/sort, request IDs, concurrency/idempotency, health, generated client                    | M05                                        | `AC-026`-`AC-030`; schema generation is clean and a client smoke flow passes                                                            |
| M3                  | Profile/settings/navigation/footer and shared public/admin shells                                                                                           | M06, M07                                   | `AC-003`, `AC-007`, `AC-021`, `AC-022`; public rendering changes through admin API/UI                                                   |
| M4                  | Skills complete vertical slice                                                                                                                              | M08                                        | `AC-008`; category/CRUD/order/feature/visibility/relations render publicly                                                              |
| M5                  | Professional experiences complete vertical slice                                                                                                            | M09                                        | `AC-009`; date invariants, revision/publication, relations, accessible presentation                                                     |
| M6                  | Projects complete vertical slice                                                                                                                            | M10                                        | `AC-010`; case-study CRUD/publication/SEO/filter/detail/relations/screenshots                                                           |
| M7                  | Blog complete vertical slice                                                                                                                                | M11                                        | `AC-011`, `AC-012`; taxonomy, controlled Markdown, schedule/publication, public listing/detail                                          |
| M8                  | Configurable pages and typed blocks complete vertical slice                                                                                                 | M12                                        | `AC-005`, `AC-006`, `AC-020`; all block types, editor/reorder/preview/publication/public renderer                                       |
| M9                  | Media complete vertical slice                                                                                                                               | M13                                        | `AC-014`, `AC-019`; adapter contract, validation/quarantine/usage/deletion and UI integration                                           |
| M10                 | Contact complete vertical slice                                                                                                                             | M14                                        | `AC-013`, `AC-018`; anti-abuse submission plus private admin lifecycle/retention                                                        |
| M11                 | Scoped API-token complete vertical slice                                                                                                                    | M15                                        | `AC-023`; one-time secret, digest/scopes/expiry/rotation/revocation and consumer docs                                                   |
| M12                 | Audit and system administration                                                                                                                             | M16                                        | `AC-024`, `AC-026`; complete event catalog/viewer, safe health/application metadata, retention commands                                 |
| M13                 | Product polish, security validation, accessibility validation                                                                                               | M17, M18, M19                              | `AC-001`-`AC-004`, `AC-025`, `AC-031`-`AC-034`, `AC-039`, `AC-044`, `AC-046`; no Critical/High defect                                   |
| M14                 | Independent clean release validation and release report                                                                                                     | M20                                        | Every R1 Must criterion `AC-001`-`AC-046` applicable to a Must requirement passes with durable evidence; targets measured/dispositioned |

## Incremental milestones

### M0 - Repository foundation

**Goal:** make an empty checkout reproducibly lint, type-check, test, build, migrate, generate its API client, and start in development before feature code begins.

**Tasks:** `M0-T01` toolchain/decision lock; `M0-T02` repository/task-runner/governance skeleton; `M0-T03` backend skeleton; `M0-T04` frontend/design-system skeleton; `M0-T05` PostgreSQL/Alembic/test DB; `M0-T06` OpenAPI client pipeline; `M0-T07` containers/environment/bootstrap-vs-seed commands; `M0-T08` CI/pre-commit/security baseline; `M0-T09` clean foundation proof.

**Pinned decisions:** Python 3.12.x and Node 22.x LTS are exact-patched in version files; backend dependencies are locked with `uv` and frontend dependencies with Corepack-pinned `pnpm`; FastAPI/Pydantic/SQLAlchemy/Alembic and Next.js/React/TypeScript/Tailwind major lines are locked, not floating; Ruff formats/lints, mypy is strict-by-default with narrow documented exceptions, ESLint/Prettier/`tsc --noEmit` are authoritative; Pytest/Vitest/Testing Library/Storybook/Playwright are configured; PostgreSQL 17 container image is digest-pinned; OpenAPI Generator CLI is version/digest-pinned; lockfiles and CI actions are pinned. Exact patch values are selected and recorded by `M0-T01` after compatibility checks, then treated as a contract.

**Gate:** documented commands work from a clean clone; a baseline migration upgrades an empty PostgreSQL database; backend and frontend tests/builds pass; OpenAPI regeneration is reproducible; production images build and run non-root; no default credentials, seed, Redis, worker, or fake AI runtime exists.

### M1 - Identity and authentication

**Goal:** deliver secure operator bootstrap and browser authentication before exposing ordinary admin routes.

**Tasks:** identity/session migration and services; explicit bootstrap CLI; login/logout/session/password APIs; CSRF/Origin/rate-limit/security headers; forced-change UI and protected shell; audit events and end-to-end lifecycle.

**Gate:** bootstrap replay and production-default tests pass; Argon2id policy is benchmarked; invalid login is non-enumerating; expiry/logout/password change revoke access; CSRF and brute-force negatives pass; no credential appears in logs/evidence.

### M2 - Core API conventions

**Goal:** stabilize contracts that all subsequent slices consume.

**Tasks:** envelopes/errors/request IDs; pagination/filter/sort; actor/authorization/concurrency/idempotency primitives; health endpoints; OpenAPI lint/examples/security declarations; client generation and wrapper smoke test.

**Gate:** `AC-026`-`AC-030` pass, generator diff is clean, and contract-breaking changes require CHG-002.

### M3 - Website settings and navigation

**Goal:** allow the owner to configure public identity and global chrome without source edits.

**Tasks:** profile/settings model/API/admin/public projections; nav/footer tree validation and API; Signal Ledger tokens/shared primitives; responsive public header/footer/theme and admin shell; settings/navigation E2E.

**Gate:** public/private projection review passes; unsafe links/secrets are rejected; mobile/keyboard nav/theme work in all states.

### M4 - Skills

**Goal:** full category/skill workflow from admin change to public evidence.

**Tasks:** skill/category domain + migration/API; admin manager/order/relation UI; public group/filter/evidence UI; generated client/tests/docs.

**Gate:** `AC-008` plus negative score/years/slug/authorization and accessibility tests.

### M5 - Professional experiences

**Goal:** revision-safe professional history with validated dates and a polished public presentation.

**Tasks:** aggregate/revisions/relations migration and use cases; admin editor/publication/preview; public timeline/list; tests/docs.

**Gate:** `AC-009`, preview isolation and published-changes-pending behavior pass.

### M6 - Projects

**Goal:** end-to-end case studies with relations, screenshots, filters, detail routes, and SEO.

**Tasks:** aggregate/revisions/relations/SEO persistence and API; admin list/editor/publication; public listing/detail/filter/metadata; tests/docs.

**Gate:** `AC-010`; draft/hidden leakage, self-relation, N+1, not-found, and metadata tests pass.

### M7 - Blog

**Goal:** safe portable writing with taxonomy, schedule-ready publication, and public discovery.

**Tasks:** post revisions/taxonomy/relations; pinned CommonMark sanitizer; admin Markdown editor/preview/publication; public list/detail/filters/SEO; malicious corpus and E2E.

**Gate:** `AC-011`-`AC-012`; future/draft data excluded from page, metadata, sitemap, and relations.

### M8 - Configurable pages and blocks

**Goal:** make core/custom pages schema-driven and editable without code.

**Tasks:** page revision/block registry/reference persistence; all 19 SPEC-listed block schemas/renderers; page/block APIs; accessible responsive builder/reorder/preview/publication; registry parity and E2E.

**Gate:** `AC-005`, `AC-006`, `AC-020`; every block fixture round-trips, unknown config fails closed, reserved slugs collide safely.

### M9 - Media

**Goal:** private validated image storage and reusable media management integrated with all owners.

**Tasks:** media metadata/usage migration; local/S3 adapter contracts; streaming quarantine/validation/promotion/cleanup; admin library/picker; public authorized delivery/optimization; usage/deletion integration; tests/docs.

**Gate:** `AC-014`, `AC-019`; malicious formats/bombs/mismatches rejected and DB/object compensation/reconciliation proven.

### M10 - Contact

**Goal:** accept exactly one legitimate private inquiry and support safe admin triage/retention.

**Tasks:** private model/lifecycle/rate limits/idempotency; public form with consent/honeypot/timing; admin inbox/detail/archive/delete; purge command/docs; privacy/security/E2E.

**Gate:** `AC-013`, `AC-018`; no public list/detail, URL/log/cache/audit leakage, and rate-limit behavior passes.

### M11 - API tokens

**Goal:** provide secure scoped integration access without browser-admin privilege.

**Tasks:** token/scope persistence and digest service; create/list/rotate/revoke/auth APIs; one-time reveal UI; complete route-scope matrix; API/cURL docs and E2E.

**Gate:** `AC-023`; secret absent after modal close and from DB/log/audit/URL; expired/revoked/rotated/under-scoped paths deny.

### M12 - Audit and system administration

**Goal:** complete safe traceability and operator visibility across every implemented capability.

**Tasks:** event catalog coverage/redaction; audit viewer/filter API/UI; admin health/build screen; retention/purge and safe operational metadata; coverage audit.

**Gate:** `AC-024`, `AC-026`; every specified event has a passing producer test and no forbidden metadata.

### M13 - Product polish

**Goal:** consolidate a coherent premium, accessible, secure, performant product rather than defer quality to release day.

**Tasks:** public route/SEO completion; admin/dashboard/onboarding and all async states; cross-device Signal Ledger visual review; manual WCAG matrix and fixes; ASVS/API/security review and fixes; Lighthouse/query/bundle optimization; OSS docs/screenshots/hygiene.

**Gate:** `AC-001`-`AC-004`, `AC-025`, `AC-031`-`AC-034`, `AC-039`, `AC-044`, `AC-046`; all confirmed Critical/High defects closed.

### M14 - Release validation

**Goal:** independently prove a release candidate from clean environments using only shipped documentation.

**Tasks:** clean install/migrate/build/start; full suites/reviews/scans; upgrade/backup/restore drill; OpenAPI/API consumer walkthrough; user/developer docs walkthrough; traceability reconciliation; screenshots and final report.

**Gate:** every R1 Must trace row is `Verified`, targets measured/dispositioned, production images and restore set work, and the final evidence manifest identifies commit, environment, executor, dates, reports, and defects/waivers.
