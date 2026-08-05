# Milestone 14 Dispatch

## Dispatcher status and release boundary

This document prepares `M14-T01` through `M14-T03`, the independent qualification of one frozen R1
release candidate. It does not accept M13, implement a feature, choose a release version or license,
author legal advice, select a host/storage provider/region, set retention or RPO/RTO, deploy to
production, create a release tag before a Go decision, or permit a validator to accept their own
work.

| Task      | Current state | Release condition                                                                                                                                                |
| --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M14-T01` | Blocked       | Q0-Q3 pass: M13 is separately accepted, every M0-M13 record is closed, owner/operator blockers are resolved, and one immutable candidate is available.          |
| `M14-T02` | Blocked       | T01 proves a clean-clone install/build/migrate/seed/start environment and publishes its exact environment and artifact identities.                               |
| `M14-T03` | Blocked       | T01-T02 pass without unresolved release blocker; all corrective changes are re-frozen and independently retested; traceability and artifact manifests reconcile. |

M14 maps to trace milestone `M20`. The only successful outcome is a reproducible **Go** report for
one exact candidate, backed by complete durable evidence. Any incomplete prerequisite or failed,
missing, stale, self-reviewed, suppressed, or irreproducible gate produces **No-Go** or **Blocked**,
never a conditional Pass hidden in prose.

## Qualification gates

### Q0 - Separately accepted M13 and complete predecessor closure

Before any release-qualification execution, Integration/root must verify and record:

- a separately signed M13 acceptance record at an exact commit; an M13 plan, lane handoff, green CI
  badge, or implementer statement is not acceptance;
- one dated acceptance/evidence record for every task in M0 through M13, including the mapping to
  trace milestones, requirements, acceptance criteria, defects, waivers, residual risks, and any
  rolled-forward item;
- every R1 Must scheduled through M13 has a durable evidence link and no row is merely `Planned`,
  `Implemented`, or `Pass` without the required independent verification;
- all target variances have a measured value, target, cause, owner, expiry/follow-up, and explicit
  approval; no variance may waive a Must, a Critical/High security issue, or a WCAG 2.2 AA blocker;
- all prior migration, generated-contract, lockfile, root configuration, shared UI, infrastructure,
  evidence, and screenshot writers are stopped and their reservations released; and
- no unresolved Critical/High defect, unexplained skip/deselection/retry, expired waiver,
  placeholder/mock production path, fake AI behavior, generated drift, or evidence privacy incident
  remains.

If any M0-M13 record is missing, contradictory, stale relative to the candidate, or points to an
unavailable artifact, M14 stays blocked and the gap returns to that milestone's acceptance owner.
M14 does not manufacture retrospective acceptance.

### Q1 - Owner, legal, privacy, hosting, and recovery decisions

The Maintainer, Product owner, Legal/Privacy owner, and Operator must supply approved, versioned
records for all of the following:

1. the exact release version and versioning policy;
2. an OSI-approved repository license plus copyright, notice, attribution, dependency, font, icon,
   image, demo-content, and screenshot provenance obligations;
3. reviewed privacy, cookie/analytics, contact-consent, terms/legal, retention/deletion, and footer
   copy that matches actual behavior and the selected jurisdiction;
4. final contact and audit retention periods, backup-retention interaction, deletion limitations,
   purge ownership, and approval or replacement of the existing 365/400-day defaults;
5. production public/admin/API hostnames, canonical origin, TLS edge, exact trusted origins, proxy
   hops, cookie behavior, callback/media hosts, and sitemap/robots/feed base URLs;
6. S3-compatible provider, region/data-residency choice, bucket ownership, endpoint style,
   credential/secret-manager owner, encryption, versioning, lifecycle, and backup responsibility;
   and
7. database and object-storage RPO/RTO, backup frequency/retention, restore authority, restore-test
   cadence, rollback authority, and incident escalation.

Every item must cite the approving owner, date, exact decision, and governing artifact. An undecided,
placeholder, example-only, internally contradictory, or behavior-mismatched item is a release blocker
under `R-018`. Validators may test supplied choices but may not invent or silently infer any of them.

### Q2 - Immutable candidate identity and one-head/current equality

Release Manager and Integration/root freeze exactly one candidate and publish:

- source commit SHA, tree SHA, branch/ref, clean tracked/untracked status, submodule state if any,
  source archive hash, lockfile hashes, generated-artifact hashes, and the absence of post-freeze local
  patches;
- exact Python, uv, Node, Corepack, pnpm, PostgreSQL, browser, container engine, Compose, OpenAPI
  generator, scanner, and operating-system versions;
- production image names, immutable digests, build platforms, Dockerfile/context hashes, base-image
  digests, build invocation, and build logs tied to the same source commit;
- the **actual** sole Alembic head `H` returned from the candidate, not a revision copied from a plan;
  `alembic heads` must return exactly one head, every empty/prior-release environment must report
  `current == H`, and schema-drift/permissions checks must agree; and
- the prior released version, image digests, schema head, compatible backup set, and documented
  upgrade/rollback path used by the rehearsal.

The candidate is invalid if the checkout is dirty, identity is ambiguous, there is more than one
head, current differs from `H`, an artifact cannot be traced to the commit, the previous-release
input is not authentic, or a mutable image tag is used as proof without its digest.

### Q3 - Independent clean-room and reviewer readiness

Operations provisions a disposable, isolated environment from a fresh clone or source archive with
empty dependency/build caches where practical, a new PostgreSQL database, new media/object
namespaces, newly generated synthetic secrets, no developer `.env`, no existing `node_modules`,
`.venv`, build output, browser state, database volume, or media volume, and no production credentials
or endpoints. The environment uses only committed documentation and examples.

Release Manager assigns independent named executors for Security, API, Accessibility/UX,
Operations, Documentation, and final release review. A person who implemented or corrected a surface
may collect diagnostics but cannot be its sole reviewer or accept its fix. Missing required
browser/assistive-technology/scanner/backup capability blocks the corresponding gate; an emulator or
stub is labeled accurately and cannot impersonate required production-shaped evidence.

## No-feature and corrective-change policy

M14 reserves no feature work and no migration. It permits only the smallest correction supported by
a reproducible qualification defect and explicit triage containing requirement/AC IDs, severity,
reproduction, candidate SHA, root cause, owner, changed files/contracts/data, migration and rollback
impact, and impacted-gate list. New requirements, redesign, dependency modernization, convenience
refactors, speculative indexes/migrations, scope additions, and gate weakening return to change
control and produce No-Go for the frozen candidate.

After any correction, Integration/root freezes a new candidate identity; the old evidence is marked
superseded. The failed check, every affected gate, generated no-diff checks, repository/privacy scans,
and final manifest are rerun independently. A schema correction requires explicit CHG-002 approval,
fresh verification of the actual sole predecessor head, one named migration writer, empty and
prior-release upgrades, restore/rollback impact review, and a full candidate reset. No task guesses a
revision or edits an accepted migration.

There are at most five corrective attempts per root cause. The fifth failure stops changes in that
area, preserves diagnostics, and records No-Go. Quarantine, retry, snapshot replacement, threshold
reduction, scanner exclusion, warning suppression, or skipped platform cannot turn a failure green.

## Disjoint release-qualification lanes

| Lane | Owner | Exclusive responsibility and evidence area | Prohibited overlap / acceptance boundary |
| ---- | ----- | ------------------------------------------ | ---------------------------------------- |
| `M14-RM` release management | Release Manager | Candidate/version freeze, changelog reconciliation, release-note draft, tag plan, artifact/checksum/provenance inventory, defect register, and `docs/evidence/M14/release-management/**` | Does not implement fixes, choose unresolved owner values, publish/tag before Go, or self-approve final release. |
| `M14-SEC` security/privacy/supply chain | Independent Security and Privacy reviewers | Adversarial review, secret/PII scans, dependency/container/SBOM/license/provenance reports, finding/retest records, and `docs/evidence/M14/security/**` | Read-only first; fixes return to owners. Reviewers do not accept their own fixes or change scan policy to pass. |
| `M14-API` API/contract | Independent API Reviewer | OpenAPI export/lint/diff, client regeneration/compile, route-operation/security/error/example/scope coverage, consumer walkthrough, and `docs/evidence/M14/api/**` | Sole qualification generator window scheduled by root; no hand-edited schema/client, feature/API design, or shared lock/config edit. |
| `M14-A11Y` accessibility/UX | Independent Accessibility/UX Reviewer | Automated/manual WCAG 2.2 AA, responsive/theme/browser/AT/touch review, visual inventory, finding/retest evidence, and `docs/evidence/M14/accessibility/**` | No visual redesign or self-acceptance. Product fixes return to the owning lane and require a new candidate. |
| `M14-OPS` clean environment/operations | Independent Operations Validator | Clean clone/install/build/images, migrate/seed/bootstrap/start, production refusal, health, upgrade, backup/restore/rollback, S3 checks, and `docs/evidence/M14/environment/**` plus `operations/**` | Uses isolated synthetic resources only. Does not choose provider/region/RPO/RTO or touch production. Infrastructure fixes require triage and reset. |
| `M14-DOC` documentation | Independent Documentation Reviewer | User/API/developer/operator clean-room walkthroughs, link/version/command/config consistency, legal-copy presence checks, limitations, and `docs/evidence/M14/documentation/**` | Does not invent behavior, legal text, endpoints, secrets, guarantees, or silently fix product/config during review. |
| `M14-I` integration/root evidence | Integration/root with independent final reviewers | Reservations, candidate orchestration, full-suite correlation, sanitized evidence/screenshot manifest, traceability closure, Go/No-Go assembly, and `docs/evidence/M14/{integration,traceability,screenshots,release}/**` | Sole evidence-index/shared-surface writer. Root cannot be the sole acceptor of its work and does not overwrite lane findings. |

Every file has one writer at a time. Root manifests/locks, CI, Compose, Dockerfiles, environment
examples, OpenAPI/generated client, migrations, shared UI, traceability, changelog, evidence index,
and tags are serialized windows. Qualification lanes normally write reports only; any candidate-file
edit stops execution and enters corrective change control.

## Ordered qualification windows

1. **W0 - prerequisite audit:** root verifies Q0-Q1 and publishes a blocker-free predecessor index.
2. **W1 - candidate freeze:** Release Manager and root record Q2, pause writers, and reserve one
   candidate SHA. No test evidence predating this SHA is final M14 evidence.
3. **W2 - clean-room construction:** Operations performs Q3 from the documented clone/archive and
   records tool, environment, network, cache, clock, and synthetic-fixture identities.
4. **W3 - install/build/migrate/start:** Operations completes T01, including empty and prior-release
   paths, production images, refusal checks, S3 contract, and coordinated backup/restore/rollback.
5. **W4 - deterministic API window:** API Reviewer exports and regenerates once from the frozen
   checkout; root verifies no diff and releases generated surfaces.
6. **W5 - parallel independent reviews:** Security, Accessibility/UX, Documentation, and read-only
   performance validators run against the same image digests and isolated dataset. They do not share
   writable fixtures, reports, or screenshots.
7. **W6 - full integration/E2E:** root runs all backend/frontend/Storybook/Playwright suites and the
   minimum workflow inventory against the built candidate. No corrective writer is active.
8. **W7 - corrective loop if required:** root triages failures back to a single owner, invalidates
   affected evidence, re-freezes, and returns to the earliest impacted window.
9. **W8 - root screenshot/evidence window:** with product writers paused, root captures the final
   responsive/theme inventory, sanitizes evidence, hashes every artifact, and closes traceability.
10. **W9 - independent Go/No-Go:** Release Manager assembles the report; designated independent
    reviewers sign their lanes and an independent release authority records the final decision.
11. **W10 - release materialization after Go only:** create the approved immutable tag, verify that it
    resolves to the candidate commit, generate/publish artifacts from that tag without rebuild drift,
    and append tag/artifact provenance. A mismatch revokes Go.

## Clean-room T01 protocol

### Clone, install, and deterministic build

From an empty parent directory, the Operations validator clones or unpacks the recorded source,
checks out the exact SHA, verifies archive/tree/lock hashes and clean status, and follows only the
published developer/operator instructions. The minimum recorded command sequence, adapted only for
the documented platform shell, is:

```text
python scripts/task.py doctor
python -m uv sync --frozen
corepack pnpm install --frozen-lockfile
python scripts/task.py verify
python scripts/task.py backend-check
corepack pnpm --dir frontend format:check
corepack pnpm --dir frontend lint
corepack pnpm --dir frontend typecheck
corepack pnpm --dir frontend test:coverage
corepack pnpm --dir frontend storybook:build
corepack pnpm --dir frontend build
```

The validator records exit code, start/end UTC, duration, tool version, sanitized stdout/stderr, and
produced hashes for every command. An undocumented prerequisite, network-fetched floating version,
lock mutation, generated diff, warning treated inconsistently with CI, missing production artifact,
or reliance on a workstation cache blocks T01. Build every production container from this checkout,
inspect final users/layers/config/health/read-only behavior, and retain immutable image digests.

### Database, seed, bootstrap, startup, and refusal checks

Against a new PostgreSQL instance and fresh media namespace:

- capture `alembic heads`, require exactly one `H`, upgrade an empty database to `head`, then require
  `alembic current` to report exactly `H`; run schema-drift, constraint/index, runtime-role,
  migration-role, operator-role, and append-only audit permission checks;
- restore a sanitized authentic prior-release backup at its recorded schema head, start only the
  migration job, upgrade once to `H`, verify data/count/checksum/invariant/media-reference
  consistency, prove idempotent re-entry or the documented refusal, and run all migration tests;
- prove demo seed is explicit, deterministic/idempotent as documented, never runs at startup,
  creates no user/token/credential/real PII, and refuses production; prove tests do not depend on it;
- prove administrator bootstrap is explicit, refuses unsafe/replayed/production-invalid input,
  never runs at startup, logs no credential, and still enforces first-login password change;
- start production images with complete owner-approved synthetic configuration, verify liveness,
  readiness, dependency-failure degradation, safe health output, non-root/read-only operation,
  bounded startup/shutdown, and core smoke; and
- separately prove fail-closed refusal for missing/empty/known-default/too-short secrets, debug in
  production, wildcard or malformed trusted origins, insecure cookie/TLS/proxy combinations,
  invalid database/storage endpoints, absent token/privacy/CSRF keys, unsafe media paths, and any
  unsupported environment value. Refusal output must itself be redacted.

The exact refusal catalog comes from accepted configuration contracts. Validators do not invent a
production hostname, origin, key, bucket, or endpoint merely to make startup succeed.

### Backup, restore, S3, and rollback rehearsal

Operations uses disposable production-shaped PostgreSQL and the owner-selected S3-compatible adapter
with synthetic data. It creates a coordinated database/object backup using documented commands,
records start/end and consistency boundary, encrypts and access-controls artifacts as approved,
restores into entirely new database/bucket namespaces, upgrades if documented, and verifies row,
object, digest, metadata, ownership, reference, publication, contact, audit, and missing/orphan object
consistency before running core public/admin/API smoke.

Measure achieved recovery point and recovery time using the approved definitions and compare them to
owner-supplied RPO/RTO. Rehearse documented deployment rollback to the prior immutable application
artifact and compatible schema; never improvise a destructive downgrade. Exercise interrupted
backup, corrupt/incomplete backup, unavailable database/object storage, denied credentials,
wrong-region/endpoint, partial restore, and rollback-refusal paths. No production system, credential,
bucket, backup, or customer data is used. Missing owner choices, an untestable procedure, RPO/RTO
miss, cross-store inconsistency, data loss beyond RPO, unsafe rollback, or unredacted log is No-Go.

## T02 independent test and review matrix

### Backend, frontend, Storybook, API, and E2E

Run from the clean environment against PostgreSQL and built applications:

```text
python scripts/task.py repo-check
python scripts/task.py verify
python scripts/task.py backend-check
python scripts/task.py api-generate
git diff --exit-code -- docs/api/openapi.json frontend/src/generated/api
python scripts/task.py api-check
corepack pnpm --dir frontend format:check
corepack pnpm --dir frontend lint -- --max-warnings=0
corepack pnpm --dir frontend typecheck
corepack pnpm --dir frontend test:coverage
corepack pnpm --dir frontend storybook:build
corepack pnpm --dir frontend build
corepack pnpm --dir frontend test:e2e
```

The API lane additionally verifies deterministic byte-for-byte OpenAPI/client generation in two
fresh directories; unique operation IDs; documented authentication/security, scopes, CSRF, errors,
pagination/filter/sort catalogs, examples, idempotency/concurrency, uploads, safe health, and every
route/capability mapping; generated-client compilation and wrapper use; and a redacted external
consumer token lifecycle. Handwritten generated output or an unexplained diff is blocking.

All backend unit/domain/service/repository/API/integration/migration/permission/coverage suites,
frontend unit/component/interaction/coverage suites, Storybook stories/a11y interactions, and
Playwright Chromium/Firefox/WebKit journeys execute with zero unexplained skip, deselection,
quarantine, retry, warning, open handle, or snapshot update. Minimum coverage remains backend
`>=85%`, critical/security backend `>=95%`, critical frontend `>=80%`, and the accepted frozen
critical-E2E target. Every workflow in `docs/plan/test-strategy.md` runs, including bootstrap/auth,
all content slices/publication, pages/blocks, media, contact privacy/lifecycle, API tokens, audit,
health, discovery, unauthorized/draft/private denial, session expiry, conflict, and destructive
confirmation.

### Security, privacy, secrets, supply chain, license, and provenance

Independent reviewers run the accepted ASVS/API abuse matrix: route/use-case authorization, IDOR,
mass assignment, injection/filter abuse, XSS/Markdown/URL sanitization, CSRF/Origin/CORS/security
headers, redirect/SSRF, upload mismatch/bomb/traversal, rate/idempotency abuse, session/token/bootstrap
replay/expiry/rotation/revocation, publication/preview leakage, cache clearing, audit immutability,
safe errors/health, and storage failure boundaries.

The frozen-toolchain scan set must include Ruff, strict Mypy, Bandit, pip-audit, JavaScript dependency
audit, Gitleaks full-history plus candidate tree, repository private-path/credential scan, production
image Trivy scan, Dockerfile/Compose/base-image/action pin review, Python/Node/container OS dependency
inventories, SBOM for every release artifact/image, and license/notice/provenance review covering
dependencies and all bundled visual/demo assets. Store machine-readable output plus sanitized human
triage. No scanner database or exclusion changes during qualification without explicit review.

A separate PII/secret scan covers source/history, built browser assets/source maps, OpenAPI/examples,
logs, audit rows, database/media fixtures, screenshots, videos/traces/HAR, metrics/traces, backups,
SBOM/provenance, docs, release notes, and evidence. Forbidden material includes real contact/body/email,
passwords, session/API tokens or digests, authentication headers/cookies, raw IP, unapproved identifiers,
connection strings/keys, private endpoints/buckets, developer absolute paths, or sensitive exception
payloads. Approved synthetic test shapes are documented and redacted. Any confirmed secret/PII leak,
Critical/High vulnerability, unresolved incompatible/unknown license, missing top-level approved OSI
license, mutable/untraceable dependency or image, missing SBOM, or unjustified scanner suppression is
No-Go.

### Accessibility, UX, responsive/theme screenshots, and performance

Accessibility/UX runs automated axe plus manual keyboard-only, focus/order/visibility, skip-link,
landmark/name/role/value, heading, error/status/live-region, form, dialog/drawer, table/card, drag/reorder
alternative, touch target, contrast/forced-colors, motion, screen-reader, zoom/reflow, text-spacing, and
session-protected-state checks mapped to WCAG 2.2 AA success criteria. Record exact OS, browser/version,
assistive technology/version, device, viewport, input, theme, route/journey, criterion, result,
finding, executor, and retest. At minimum use current stable Chromium, Firefox, and WebKit plus the
owner-approved support matrix; use NVDA with Firefox or Chrome, VoiceOver with Safari, and TalkBack
with Chrome on real available devices where those combinations are required. Emulation is labeled.

The final root-owned screenshot inventory covers every public route and core admin journey/state at
`320`, `360`, `390`, `768`, `1024`, `1280`, `1440`, and `1920` CSS px; 400% zoom where applicable;
light, dark, and system themes; reduced motion; forced colors/high contrast; keyboard focus; long
content; minimum/typical/large data; and loading, empty, validation, error, offline, unauthorized,
expired, conflict, rate-limited, not-found, and destructive-confirmation states. The inventory maps
each PNG to candidate SHA, image digest, browser/device, viewport/DPR, theme/state/journey, fixture,
timestamp, hash, reviewer, and sanitization result. Capture secrets and real PII never appear.

Run production Lighthouse and Core Web Vitals profiles with the M13-frozen hardware, network/CPU,
viewport, cache, dataset, build, samples, and variance method. Require Lighthouse performance
`>=90`, accessibility `>=95`, SEO `>=95`, and documented p75 Good bands `LCP <=2.5s`, `INP <=200ms`,
`CLS <=0.1`, plus every frozen per-route JS/image/font/request/API/query/startup budget. Run backend
load/query-count/EXPLAIN/no-N+1 checks and frontend bundle/source-map/image/font inspection against
production artifacts. A missing profile, score gaming, lab-as-field claim, unexplained regression,
or undispositioned target miss blocks Go.

### Documentation and link verification

Documentation Reviewer follows the published instructions as a new user, external API consumer,
developer, and operator. Verify all local/relative/external links and anchors, commands from a clean
shell, version/filename/route/operation references, configuration matrix, secrets handling,
install/build/test/migrate/bootstrap/seed/start steps, upgrade/backup/restore/rollback/S3/monitoring/
incident procedures, API examples, accessibility limitations, browser support, privacy/retention
behavior, and known limitations against the candidate.

Owner-supplied license/legal/privacy text is checked for presence, version, approval reference, and
behavioral consistency, not rewritten as legal advice. Broken links, undocumented required steps,
unsafe examples, stale screenshots, fabricated capability, missing operator recovery information, or
a walkthrough that cannot be completed from the docs is No-Go.

## Exact M14 artifact inventory

Every artifact is candidate-specific, sanitized, immutable after signing, and listed with SHA-256,
media type, byte size, producer, reviewer, UTC timestamps, candidate commit, image digest where
applicable, command/profile, exit/result, and supersession state in
`docs/evidence/M14/manifest.json`. Required paths are:

```text
docs/evidence/M14/prerequisites/m0-m13-index.json
docs/evidence/M14/prerequisites/m13-acceptance.md
docs/evidence/M14/prerequisites/owner-decisions.json
docs/evidence/M14/release-management/candidate.json
docs/evidence/M14/release-management/version-and-tag-plan.md
docs/evidence/M14/release-management/changelog-review.md
docs/evidence/M14/release-management/defects.json
docs/evidence/M14/environment/clean-clone.json
docs/evidence/M14/environment/toolchain-and-install.json
docs/evidence/M14/environment/build-and-images.json
docs/evidence/M14/environment/migration-empty.json
docs/evidence/M14/environment/migration-upgrade.json
docs/evidence/M14/environment/seed-bootstrap-startup.json
docs/evidence/M14/environment/production-refusals.json
docs/evidence/M14/operations/s3-contract.json
docs/evidence/M14/operations/backup-restore.json
docs/evidence/M14/operations/rollback.json
docs/evidence/M14/api/openapi-determinism.json
docs/evidence/M14/api/route-capability-matrix.json
docs/evidence/M14/api/consumer-walkthrough.md
docs/evidence/M14/tests/backend.json
docs/evidence/M14/tests/frontend.json
docs/evidence/M14/tests/storybook.json
docs/evidence/M14/tests/playwright.json
docs/evidence/M14/security/findings.json
docs/evidence/M14/security/dependencies-and-licenses.json
docs/evidence/M14/security/container-and-sbom.json
docs/evidence/M14/security/secrets-and-pii.json
docs/evidence/M14/accessibility/wcag-2.2-aa-matrix.csv
docs/evidence/M14/accessibility/findings-and-retests.json
docs/evidence/M14/performance/lighthouse-and-cwv.json
docs/evidence/M14/performance/backend-query-load.json
docs/evidence/M14/documentation/user-walkthrough.md
docs/evidence/M14/documentation/api-walkthrough.md
docs/evidence/M14/documentation/developer-walkthrough.md
docs/evidence/M14/documentation/operator-walkthrough.md
docs/evidence/M14/documentation/link-report.json
docs/evidence/M14/screenshots/inventory.json
docs/evidence/M14/traceability/requirements.json
docs/evidence/M14/traceability/acceptance-criteria.json
docs/evidence/M14/traceability/closure-report.md
docs/evidence/M14/release/artifact-provenance.json
docs/evidence/M14/release/checksums.sha256
docs/evidence/M14/release/go-no-go.md
docs/evidence/M14/manifest.json
```

Native machine-readable scanner, coverage, test, Lighthouse, Playwright, axe, SBOM, image, log,
trace, and screenshot files live below the corresponding directory and are referenced by these
indexes; raw sensitive output is not committed. The manifest fails closed on a missing file, hash
mismatch, duplicate/stale candidate identity, broken evidence link, unknown producer/reviewer,
unsanitized payload, or artifact generated from a different commit/image.

## Traceability closure and Go/No-Go report

Integration/root reconciles every R1 requirement and `AC-001` through `AC-046` against the frozen
candidate. Each row records requirement ID, AC ID, delivery milestone, M0-M13 acceptance reference,
M14 test/review reference, candidate commit/image, status, executor, independent reviewer, date,
defect/variance/waiver, and durable artifact hash. Every R1 Must must be `Verified`; target rows need
measurement and explicit approved disposition. Orphan tests, uncovered Musts, stale links, conflicting
statuses, or evidence from another candidate block closure.

`docs/evidence/M14/release/go-no-go.md` contains:

- candidate/version/commit/tree/tag-plan and release artifact/image/SBOM/checksum identities;
- exact clean-room environment, sole migration head/current results, empty/prior upgrade, startup,
  refusal, backup/restore/rollback, and achieved RPO/RTO results;
- a Pass/Fail/Blocked table for every command, suite, matrix, scanner, walkthrough, performance
  budget, requirement, AC, owner decision, defect, variance, waiver, residual risk, and limitation;
- independent lane sign-offs with conflicts of interest disclosed;
- changelog/release-note completeness, compatibility/upgrade/rollback statements, and artifact
  provenance; and
- one explicit `GO` or `NO-GO` decision, release authority, UTC timestamp, rationale, and required
  next action.

Go requires all prerequisites, tests, reviews, matrices, owner decisions, traceability rows, and
artifacts above to pass for the same candidate with no objective blocker. There is no “Go with hidden
follow-up.” Approved non-Must target variances remain prominent in the report and release notes.

## Objective No-Go and blocking criteria

The decision is No-Go or Blocked if any of these is true:

- M13 is not separately accepted, any M0-M13 task/evidence row is missing or stale, or any R1 Must/
  `AC-001`-`AC-046` row lacks independent candidate-specific evidence;
- release version, OSI license, legal/privacy copy, retention, hostname/origins, S3 provider/region,
  or database/object RPO/RTO and ownership remains unresolved or behavior disagrees with the decision;
- source/tree/artifact/image identity is dirty, mutable, mismatched, irreproducible, unsigned where
  policy requires signing, or lacks checksum/SBOM/provenance;
- Alembic has zero/multiple heads, any tested database current differs from actual sole head `H`,
  empty/prior upgrade or drift/permission test fails, or a speculative/unapproved migration appears;
- clean install/build/start requires an undocumented/local prerequisite, changes a lock/generated
  artifact, uses stale caches as proof, or any production configuration fails to reject unsafe input;
- seed/bootstrap runs implicitly, creates a predictable credential, accepts unsafe production use,
  or leaks a secret; production image is root/writable/overprivileged or fails safe health/startup;
- backup/restore/rollback is incomplete, destructive, cross-store inconsistent, unrepeatable, exceeds
  approved RPO/RTO, uses production data/resources, or cannot return the service to a verified state;
- any required backend/frontend/Storybook/Playwright/API/migration/security/privacy/accessibility/
  performance/docs/link/browser/AT/responsive/theme check fails, is missing, suppressed, quarantined,
  stale, flaky, or has unexplained skip/retry/warning/deselection;
- coverage or frozen performance budget is missed without an allowed target disposition; WCAG 2.2
  AA has an unresolved blocker; a confirmed Critical/High security finding exists;
- secret/PII/private-path evidence is found, a dependency/container/action/base image is unpinned or
  has a blocking vulnerability, a license is unknown/incompatible, or attribution/provenance is absent;
- documentation cannot reproduce install/use/API/operations, contains unsafe or fabricated guidance,
  or the screenshot/evidence/manifest hashes and candidate identities do not reconcile;
- a validator self-accepts their implementation/fix, required independent sign-off is absent, a
  fifth corrective attempt fails, or a gate was weakened to obtain green; or
- the approved tag does not resolve exactly to the Go candidate, artifacts are rebuilt with different
  content after Go, or publication provenance cannot bind source, build, image, SBOM, checksum, tag,
  and report.

M14 passes only when the independent release authority records Go and the post-Go tag/provenance
verification still matches. Until then, the repository has a candidate under qualification, not an
accepted or released R1.
