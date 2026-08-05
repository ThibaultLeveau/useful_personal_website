# Milestone 13 Dispatch

## Dispatcher status

This document prepares `M13-T01` through `M13-T04`. It does not release implementation, record
M12 or M13 acceptance, choose an owner/legal/hosting value, authorize a production deployment, or
replace the independent M14 release-validation gate.

| Task      | Current state | Release condition                                                                                                                                           |
| --------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M13-T01` | Blocked       | Integration/root separately accepts M12, verifies its actual sole Alembic head and released contracts, closes T0-T2, and publishes the exact file manifest. |
| `M13-T02` | Blocked       | T01 public/admin polish and complete-state evidence passes at T4; the accessibility environment and assistive-technology matrix is available.               |
| `M13-T03` | Blocked       | T01 candidate and frozen route/capability/data-flow inventories are available; independent Security/API/Privacy reviewers are assigned.                     |
| `M13-T04` | Blocked       | T01-T03 corrective loops pass, owner decisions in T1 are recorded, and production-shaped performance/operations/documentation fixtures are ready.           |

M13 maps to trace milestones `M17`, `M18`, and `M19`. Its outcome is a coherent, complete,
accessible, secure, private, discoverable, documented, and measured R1 candidate. It prepares a
frozen candidate and reproducible inputs for M14; it does not perform or claim M14's independent
clean-checkout, upgrade, coordinated restore, or final release acceptance.

## Blocking predecessor and release-owner decisions

### T0 - Separately accepted M12 and actual-head freeze

Before any M13 implementation write, Integration/root must record all of the following in a
separate accepted M12 gate:

- `M12-T01` through `M12-T03` pass with no unresolved Critical/High defect and no active M12 writer
  on a file M13 needs;
- the actual single Alembic head at the accepted M12 commit, current/head equality, empty-database
  upgrade, accepted prior-head upgrade, downgrade policy, schema drift result, and runtime/operator
  grant evidence. No M13 lane may infer the head or revision number from `dispatch-m12.md`;
- the released OpenAPI artifact/generated client, route-operation inventory, browser-session and
  API-token authorization matrices, audit catalog, safe health contract, retention command, public
  projection/publication rules, media-storage contract, contact privacy contract, and demo-seed
  contract;
- passing M12 backend/frontend/contract/browser/security/accessibility/coverage evidence with every
  expected test executed and no unexplained skip, retry, suppression, placeholder, or generated
  diff; and
- an exact shared-surface manifest covering routers, app layouts, metadata roots, navigation,
  wrappers, generated output, configuration, Compose/CI, documentation indexes, screenshots, E2E
  fixtures, and evidence indexes, with all earlier writer reservations released.

An accepted M12 plan or implementer claim is not acceptance evidence. A second head, unknown head,
unreleased contract, active shared-file writer, or unresolved Critical/High finding keeps every M13
lane blocked.

### T1 - Owner/legal/hosting decisions that agents must not invent

The Maintainer, Legal/Privacy owner, Product owner, and Operator must record explicit values or an
approved release-blocking disposition for each item below before T04 can pass:

1. the repository's OSI-approved license and attribution/notice obligations, including dependency,
   font, icon, image, demo-content, and screenshot provenance;
2. reviewed privacy, cookie/analytics, contact-consent, terms/legal, retention/deletion, and public
   footer copy appropriate to the selected jurisdiction and actual deployed behavior;
3. final contact and audit retention periods, including explicit acceptance or change control for
   the current 365-day contact and 400-day audit defaults, backup-retention interaction, deletion
   limitations, and operator ownership;
4. production public/admin/API hostnames, canonical origin, TLS edge, trusted exact origins, proxy
   hops, cookie domain behavior, callback/public-media hosts, and sitemap/robots/feed base URLs;
5. the private S3-compatible provider, region/data-residency decision, bucket names/ownership,
   endpoint style, credentials/secret-manager owner, encryption/versioning/lifecycle choices, and
   backup responsibility; and
6. documented database/object-storage RPO and RTO targets, backup frequency/retention, restore
   authority, restore-test cadence, and incident escalation owner.

These are release blockers under `R-018`. Agents may create decision templates, compare already
approved choices, and test supplied values, but may not select a license, write legal assurances,
choose a jurisdiction/provider/region/hostname, silently accept retention, or invent RPO/RTO.
Production examples use reserved example domains and redacted placeholders until owners decide.

### T2 - Candidate inventory and measurable budgets

Integration/root freezes one machine-readable candidate inventory before fan-out. It contains:

- every public, authentication, administrator, integration API, health, sitemap, robots, and
  approved feed route; its audience, authorization/cache policy, data owner, canonical URL rule,
  metadata source, empty/loading/error/not-found behavior, and E2E journey;
- every back-office capability mapped to an API operation and application authorization point, or a
  documented rationale for its absence. A UI-only capability, raw frontend database/storage access,
  or undocumented operator mutation blocks the inventory;
- every public-discovery source: title/description, canonical, language/locale, Open Graph/social
  image, structured data type, sitemap inclusion, robots directive, feed inclusion, pagination,
  publication-time behavior, and exclusion of drafts/previews/private identifiers/storage keys;
- representative public/admin/API datasets at minimum, typical, large-but-bounded, empty, invalid,
  unavailable, unauthorized, expired, conflict, and rate-limited states;
- a privacy data-flow register for contact data, administrator identity, sessions/tokens, IP
  pseudonyms, audit, uploads/metadata, logs/traces/metrics, analytics if owner-approved, backups,
  screenshots, and support artifacts; and
- numeric budgets and measurement profiles. Normative Lighthouse targets are performance `>=90`,
  accessibility `>=95`, and SEO `>=95`. Core Web Vitals target the current Good bands at the
  documented 75th-percentile profile (`LCP <=2.5s`, `INP <=200ms`, `CLS <=0.1`). Product and
  Performance owners must additionally freeze per-route JavaScript, image/font, request-count,
  API-latency, query-count, query-plan, and server-start/readiness budgets from measured baselines;
  lanes do not invent favorable limits after measurement.

The performance profile records hardware/runner, OS/browser/version, viewport, network/CPU
throttling, cold/warm cache, dataset size, build mode, sample count, median/p75 selection, variance,
and commit. Lab Lighthouse data is not represented as field data. Any target variance needs an owner
disposition and remains visible to M14.

## Schema and migration rule

M13 reserves **no migration**. Visual polish, metadata, documentation, security review,
accessibility fixes, observability redaction, performance tuning, backup runbooks, and owner
decisions do not justify a speculative schema revision.

If a reproducible M12 acceptance gap proves that the accepted schema, index, constraint, or grant
cannot satisfy an existing R1 Must requirement, all affected lanes stop. Integration/root opens an
explicit CHG-002 record containing the defect, requirement/acceptance impact, query/schema evidence,
data/rollback/backup consequences, security/privacy review, and alternatives. Database and
Integration owners then decide whether a migration is necessary and, only after re-verifying the
actual accepted M12 sole head, reserve exactly one named successor and one writer. No lane guesses a
revision, edits a prior migration, creates a merge head, combines unrelated cleanup, or treats a
performance hunch as migration evidence.

## Scope reservations and single-writer surfaces

Until T0-T2 pass, no M13 lane may edit, move, delete, format, regenerate, or relabel accepted M0-M12
implementation/evidence, any migration, normative requirement/ADR/UX source, root manifest/lock,
CI/Compose/deployment configuration, generated client, shared router/layout/navigation/wrapper, or
evidence index. Corrections to normative scope require CHG-002 and the owning reviewer.

Integration/root publishes exact file lists for each lane. The root layout/metadata composition,
robots/sitemap/feed composition, admin navigation/dashboard, shared error/not-found surfaces,
OpenAPI/generated client, configuration/environment examples, root manifests/locks, CI/Compose,
documentation indexes, screenshot fixtures, E2E fixtures, and evidence manifest are serialized
single-writer windows. Feature lanes submit narrow handoffs and do not edit these surfaces in
parallel.

M13 adds no analytics, telemetry, consent, SEO, accessibility, chart, performance, storage, scanner,
legal-copy, or monitoring dependency merely to obtain a score. A new dependency requires an active
requirement, license/security/privacy review, exact pin/lock update, architecture impact, and
Integration-owned write window. F3/F4 remain deferred; no fake AI behavior or service is added.

## Disjoint M13 lanes

| Lane                                      | Owner                                       | Exclusive write area                                                                                                                           | Boundary and handoff                                                                                                                                                                                                           |
| ----------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `M13-T01-PU` public/SEO polish            | Frontend Public + SEO Agent                 | Exact T2-reserved public route/components, route-local metadata/structured-data helpers and tests, `docs/evidence/M13/M13-T01-public.md`       | Completes public routes/states/discovery without shared root metadata, sitemap, robots, feed, generated client, admin, or legal copy. Publishes route-level metadata fixtures to root.                                         |
| `M13-T01-AD` admin/onboarding polish      | Frontend Admin Product Agent                | Exact T2-reserved dashboard/onboarding/route-local admin components, stories/tests, `docs/evidence/M13/M13-T01-admin.md`                       | Completes first-run and all async/session/conflict states. No shared navigation/layout/wrapper, backend, demo seed, or screenshots.                                                                                            |
| `M13-T01-SE` SEO/discovery composition    | Integration/root SEO window                 | Root metadata composition, canonical base, sitemap, robots and owner-approved feed composition/tests, `docs/evidence/M13/M13-T01-discovery.md` | Runs after PU and T1 hostname decision. No feature UI fixes. Proves public-only discovery and deterministic production output. An unapproved feed format/path is omitted and remains an explicit scope decision, not invented. |
| `M13-T01-DM` clean demo/onboarding data   | Backend Demo Data + Privacy Agent           | Existing accepted demo command/factories and their focused tests only, `docs/evidence/M13/M13-T01-demo.md`                                     | Deterministic/idempotent, refuses production, creates no users/tokens/secrets/PII, uses provenance-safe content/assets, and never runs at startup. No feature/domain redesign or migration.                                    |
| `M13-T02-A` accessibility review/fixes    | Accessibility Agent with feature owners     | Defect-proven route-local UI/test/story fixes and `docs/evidence/M13/accessibility/**`                                                         | Starts after T4. Automated and manual findings are mapped to WCAG 2.2 AA success criteria. Shared-shell defects return to root's serialized window. No design rewrite or score-only workaround.                                |
| `M13-T03-S` application security/API      | Independent Security + API Reviewers        | Security/API tests, sanitized reports, defect-proven fixes returned to owning feature lanes, `docs/evidence/M13/security/**`                   | Read-only review first. Covers route/use-case authorization and all adversarial boundaries. Reviewers do not self-accept their fixes. Contract changes use root's contract window.                                             |
| `M13-T03-SC` supply chain/repository      | Security + Dependency + OSS Reviewers       | Scanner configurations only in an explicitly released root/Infrastructure window; otherwise reports under `docs/evidence/M13/supply-chain/**`  | Audits pins, locks, install scripts, dependencies, images, SBOM/provenance, secrets, licenses, repository hygiene, and deferred-AI boundary. No floating upgrade or gate suppression.                                          |
| `M13-T03-PR` privacy/legal verification   | Privacy/Security Reviewer + owner           | Privacy data-flow/retention/copy checklists and `docs/evidence/M13/privacy/**`; owner-supplied copy only in exact released files               | Verifies behavior against T1 decisions. It does not author legal advice, select retention, enable analytics, or expose private test data.                                                                                      |
| `M13-T04-BP` backend/query performance    | Backend Performance + Database Reviewer     | Query/load fixtures, measured application/query fixes, route-local repository/service tests, `docs/evidence/M13/performance/backend/**`        | Uses accepted facades/UoWs and T2 budgets. No migration absent explicit change control; no unsafe cache, denormalization, unbounded query, or skipped authorization/audit.                                                     |
| `M13-T04-FP` frontend/runtime performance | Frontend Performance Agent                  | Route-local image/font/loading/hydration/bundle fixes and tests, `docs/evidence/M13/performance/frontend/**`                                   | Measures production builds. No accessibility/SEO/privacy regression, raw client secret, hidden content prefetch, or new dependency without review. Shared config belongs to root.                                              |
| `M13-T04-OP` operator/S3/backup readiness | Infrastructure + Operations Agent           | Operator runbooks, redacted validation scripts/reports in an explicit Infrastructure window, `docs/evidence/M13/operations/**`                 | Prepares production-shaped backup/restore/S3/deploy inputs for M14. Does not choose T1 values, run destructive production actions, claim a clean restore drill, or expose credentials/endpoints.                               |
| `M13-T04-DU` user documentation           | Documentation Agent - User                  | User guides and route-local sanitized illustrations reserved by root, `docs/evidence/M13/docs/user-walkthrough.md`                             | Covers actual behavior only. No legal copy, operator secrets, fake screenshots, or undocumented capability.                                                                                                                    |
| `M13-T04-DA` API documentation            | Documentation Agent - API                   | API consumer guides/examples and `docs/evidence/M13/docs/api-walkthrough.md`                                                                   | Uses canonical generated contract; examples use reserved domains/redacted tokens. No contract edits or hand-written generated schemas.                                                                                         |
| `M13-T04-DD` developer documentation      | Documentation Agent - Developer             | Architecture/repository/contribution/testing/extension docs and `docs/evidence/M13/docs/developer-walkthrough.md`                              | Documents accepted code/tooling only, including future-AI boundary. No root manifests/locks or normative architecture changes.                                                                                                 |
| `M13-T04-DO` operator documentation       | Documentation Agent - Operator              | Deployment/config/secret/migration/backup/restore/S3/monitoring/incident runbooks and `docs/evidence/M13/docs/operator-walkthrough.md`         | Uses T1 owner decisions or explicit blockers. No real credentials, production addresses, destructive execution, or unsupported guarantees.                                                                                     |
| `M13-I` integration/contract/shared UI    | Integration/root                            | Serialized shared layouts/navigation/metadata/wrappers/config, any authorized contract generation, full-suite integration, T3-T7 decisions     | Sole shared writer. Defects return to lanes; generated artifacts are never hand-edited. Root cannot accept its own work without independent retest.                                                                            |
| `M13-E` evidence/screenshots/final review | Integration/root with independent reviewers | Evidence index, sanitized screenshot/trace window, traceability preparation, `docs/evidence/M13/M13-gate.md`                                   | Runs last with product writers paused. Records results and blockers; it cannot declare M14 or release acceptance.                                                                                                              |

## Required behavior and test matrices

### Product completeness, responsive behavior, and discovery

T01 must prove every T2 route at `320`, `360`, `390`, `768`, `1024`, `1280`, `1440`, and
`1920` CSS px, plus 400% zoom where applicable, portrait/landscape touch behavior, light/dark/system,
reduced motion, forced colors/high contrast, long localized text, minimum/typical/large data, and
loading/empty/validation/error/offline/unauthorized/expired/conflict/rate-limited states. Shared
headers, navigation, dialogs, drawers, tables/cards, editors/builders, media, contacts, tokens,
audit, health, and destructive confirmations retain visible focus, usable reflow, and protected-state
clearing.

Browser evidence records OS and exact versions for current stable Chromium, Firefox, and WebKit,
plus owner-available real Safari/iOS and Chrome/Android checks for touch-sensitive journeys. An
emulated viewport is labeled as emulation and does not masquerade as a real-device result.

Discovery tests assert deterministic canonical URLs, unique bounded titles/descriptions, correct
language/locale, Open Graph/social fallbacks, valid allow-listed structured data, public-only
sitemap/feed entries, robots policy, pagination/canonical behavior, status codes, publication-time
boundaries, and no draft/preview/admin/contact/audit/token/session/storage-key/private identifier in
HTML, RSC payloads, metadata, structured data, sitemap, robots, feeds, cache, or logs. The production
hostname decision blocks canonical/sitemap/robots/feed acceptance.

### Accessibility WCAG 2.2 AA

T02 combines axe/component/browser automation with manual keyboard, screen-reader, zoom/reflow,
contrast, motion, touch-target, pointer-cancellation/drag alternative, focus-order/visibility,
semantic structure, landmarks/headings, names/roles/values, labels/instructions/errors, status/live
regions, dialogs, menus, tables, authentication, timeout/session-expiry, alt text, and cognitive
consistency review. The matrix records exact WCAG 2.2 success criterion, route/journey, browser,
assistive technology/version, viewport/zoom/theme, result, finding, owner, fix, and independent
retest.

At minimum, the owner freezes and supplies a desktop screen-reader pair and a real mobile
screen-reader pair; recommended representative pairs are NVDA with Firefox/Chrome and VoiceOver
with Safari, with TalkBack/Chrome where available. Missing required equipment is recorded as a
blocker, not a synthetic pass. Automated score, `aria-*` addition, or test exclusion cannot waive a
manual failure.

### Security, API, privacy, and observability

T03 executes the complete route-to-actor/action matrix for missing, wrong, expired, revoked,
rotated, under-scoped, cross-resource, forced-change, and ordinary/operator identities. Adversarial
tests cover IDOR, mass assignment, injection/filter expressions, XSS/controlled Markdown, CSRF,
Origin/CORS, open redirects, SSRF/unsafe URLs, cache/draft/preview leakage, request smuggling-relevant
edge assumptions, upload bombs/mismatch/path traversal/metadata, storage authorization, token/session
recovery, rate/idempotency concurrency, error/health disclosure, security headers/CSP, and bootstrap,
seed, migration, retention, and backup separation.

Privacy inspection covers database rows, object metadata, browser DOM/storage/history/cache, HTML/RSC,
API/OpenAPI/examples, logs, audit, traces/spans, metrics labels, profiler/error reporting, analytics,
screenshots/videos, test fixtures/reports, support bundles, backups, and repository history. Passwords,
session/token/CSRF/idempotency secrets or digests, Authorization/cookies, database/storage URLs,
contact name/email/message/body, raw IP, private drafts, upload bytes/EXIF, SQL/binds, stack traces,
environment dumps, production hostnames, and unnecessary personal data are forbidden. Observability
uses bounded event names, request/operation IDs, safe actor/resource identifiers, aggregate counts,
latency/status categories, and approved pseudonyms only; it never places untrusted or sensitive
payloads in logs, traces, metrics, or alerts.

Every finding has severity, CWE/ASVS/API category where applicable, reproduction, affected commit,
owner, correction attempt, retest, and disposition. Confirmed Critical/High findings block M13; a
scanner false positive needs documented technical evidence and independent review, not suppression.

### Performance and production-shape evidence

T04 runs production builds against T2 datasets. Backend evidence includes request/SQL counts,
bounded pagination, pool/timeout behavior, `EXPLAIN (ANALYZE, BUFFERS)` for frequent/large-list
queries, lock/contention behavior for rates/idempotency/publication/contact/media/audit retention,
startup/readiness time, memory/CPU profile, and a no-N+1 assertion. Bound SQL parameters and
authorization/publication/privacy/audit semantics remain unchanged by optimization.

Frontend evidence includes per-route build output, first-load and route JS, hydration boundaries,
image/font dimensions/formats/preload behavior, request waterfalls, cache headers, server/client
component rationale, long-task/input response, layout shift, and Lighthouse samples for home,
representative public detail/list, authentication, dashboard, complex admin editor/builder, media,
contacts, tokens, audit, and health. It records each T2 budget and before/after result. A score gained
by removing content, accessibility, security headers, validation, tests, or representative data is
invalid.

### Backup, restore, S3, containers, and operator readiness

The Operations lane prepares, without claiming the M14 drill:

- a production topology manifest with immutable image references, non-root/read-only/no-new-privilege
  posture, private PostgreSQL/S3 networks, TLS edge, exact-origin/proxy/secret injection, one-shot
  owner migration, runtime role, health, resource limits, rollout/rollback, and no worker/Redis;
- coordinated PostgreSQL and private-object backup procedures with timestamps/checksums, encryption,
  access control, retention/lifecycle, versioning if owner-approved, consistency point/order,
  restore order, migration compatibility, orphan reconciliation, and partial-failure handling;
- S3 adapter/provider compatibility, path-style/virtual-host behavior as selected, region/endpoint
  validation, multipart/size/MIME/private-delivery behavior, least privilege, key rotation, failure
  injection, and no public bucket/object listing;
- bootstrap, demo seed, migration, audit/contact retention, media reconciliation, backup, restore,
  and incident commands with explicit environment refusal, dry-run/confirmation where required,
  idempotent/replay behavior, operator identity, and sanitized output; and
- monitoring/alert guidance for availability, readiness, backup age/result, restore-test age,
  storage/database capacity, rate-limit pressure, migration mismatch, and error categories without
  payloads, identities, credentials, endpoints, or high-cardinality untrusted labels.

M14 alone performs the independent clean coordinated restore and measures the owner-approved RPO/RTO.
Until provider/region, RPO/RTO, hostname/origins, secrets, and retention are decided, Operations may
validate adapters/examples with synthetic values but cannot mark production readiness complete.

### Dependencies, containers, supply chain, secrets, and licenses

T03/T04 evidence runs exact frozen-install and lockfile-integrity checks; Ruff/Mypy/Bandit/pip-audit;
Prettier/zero-warning ESLint/strict TypeScript/Vitest/Storybook/build; Gitleaks full-history and
working-tree scans with redaction; dependency/license inventory for Python, Node, container OS,
fonts/icons/assets; blocking Trivy Critical/High scans for every production image; Dockerfile/Compose
non-root/read-only/capability/network/health/history/environment/context review; action pin/digest
validation; generated OpenAPI/client deterministic no-diff; and SBOM/provenance output if the
existing approved toolchain supports it.

No scan uploads a credential, proprietary/private data, absolute developer path, raw environment,
contact content, or protected browser trace. Reports use short retention and sanitized repository
summaries. The unresolved top-level OSI license blocks repository/release readiness even if all
dependency licenses are compatible; no agent creates a placeholder `LICENSE`.

## Ordered integration, evidence, and screenshot windows

1. **T0:** Integration/root records separate M12 acceptance, actual sole head, released contracts,
   clean tests, and exact shared-file releases.
2. **T1:** Maintainer/Legal/Product/Operations record every owner decision or blocker; no
   implementation lane substitutes a choice.
3. **T2:** Integration/root publishes route/capability/discovery/privacy inventories, datasets,
   performance budgets/profile, lane manifests, and the no-migration decision.
4. **T3:** PU, AD, and DM run in parallel only on disjoint manifests. Root then owns serialized
   discovery/shared-layout/navigation/wrapper/contract integration and deterministic regeneration if
   required.
5. **T4:** Root runs full affected backend/frontend/contract/browser suites and freezes the T01
   candidate. Product/UX independently reviews complete states before T02/T03 begin.
6. **T5:** Accessibility and Security/API/Privacy/Supply-chain reviewers run read-only matrices in
   parallel. Findings return to exact owners; shared/config/dependency fixes are serialized by root.
   Independent reviewers retest every blocker.
7. **T6:** Backend and frontend performance lanes measure the corrected candidate in parallel;
   Operations and four documentation lanes use frozen behavior. Root serializes shared performance,
   configuration, and documentation-index changes, then reruns security/accessibility/contract
   regressions.
8. **T7:** With product writers paused, root opens the sole screenshot/trace window. Screenshots use
   clean provenance-safe demo data and synthetic identities; private payloads, tokens, contact data,
   infrastructure values, and machine paths are excluded. Root creates the evidence index and
   requests independent Product, Accessibility, Security, Privacy, API, Operations, Performance,
   Documentation, and OSS reviews.
9. **T8:** Integration/root records the M13 gate outcome. A passing implementer lane or dispatch
   document cannot release M14. Only a separate accepted M13 record and frozen candidate commit can
   be handed to M14.

## Exact command and artifact inventory

Integration/root records exact pinned versions, commands, exit codes, environment class, commit,
and sanitized report paths. At minimum M13 evidence contains:

- `docs/evidence/M13/predecessor.md`: accepted M12 record, actual sole head/current, released
  contract hashes, zero-skip inventory, and shared-file manifest;
- `docs/evidence/M13/owner-decisions.md`: each T1 owner/value/date/reference or explicit blocker;
- `docs/evidence/M13/product/**`: route/state/discovery/demo matrices and cross-device review;
- `docs/evidence/M13/accessibility/**`: axe results, manual WCAG criterion matrix, AT/browser/device
  versions, findings, fixes, and independent retests;
- `docs/evidence/M13/security/**`, `privacy/**`, and `supply-chain/**`: authorization/adversarial/API,
  redaction/data-flow, findings/triage, dependency/container/secret/license/pin reports;
- `docs/evidence/M13/performance/**`: production build/bundle outputs, Lighthouse raw JSON and
  summaries, Core Web Vitals profile, query/EXPLAIN/request-count/load reports, budgets, variance,
  before/after evidence;
- `docs/evidence/M13/operations/**`: redacted topology, S3 compatibility/least-privilege/failure
  reports, backup/restore rehearsal preparation, monitoring and incident checklists, open T1 values;
- `docs/evidence/M13/docs/**`: clean-reader user, API consumer, contributor, and operator
  walkthroughs with every defect/retest;
- `docs/evidence/M13/screenshots/**`: sanitized required-width/theme/state manifest with provenance,
  not raw protected traces; and
- `docs/evidence/M13/M13-gate.md`: requirement/AC mapping, commit/environment/executor/date, tool
  versions, report hashes, defects/waivers, target variances, residual risks, and independent
  reviewer decisions.

Required command families, using the repository's canonical wrappers where available, are:

```text
repository/pre-commit/format/whitespace/link/secret/private-path checks
Ruff format + lint; strict Mypy; full PostgreSQL Pytest with branch coverage; Bandit; pip-audit
one Alembic head/current; empty + accepted-prior upgrade; schema drift; runtime/operator permissions
frozen pnpm install; Prettier; zero-warning ESLint; strict TypeScript; full Vitest coverage
Storybook build + interaction/a11y; production Next build; generated-client compile/wrapper tests
deterministic OpenAPI export/validation/regeneration with clean diff
Playwright Chromium/Firefox/WebKit route/journey/adversarial/responsive matrix
manual keyboard/screen-reader/zoom/touch/contrast/motion WCAG 2.2 AA matrix
Lighthouse production profiles; bundle/image/font/request budgets; backend query/load/EXPLAIN checks
Gitleaks, dependency/license inventory, Trivy for every production image, pin/lock/context/SBOM review
production-shape Compose/container/security/health/startup and synthetic S3/backup preparation checks
documentation consumer walkthroughs and evidence sanitization/hash/link validation
```

All expected suites execute with zero unexplained skip/deselection/retry. Coverage targets are
backend `>=85%`, critical/security backend `>=95%`, critical frontend `>=80%`, and the frozen
critical E2E target. A target miss, flaky result, unavailable manual environment, or tool limitation
is recorded as Fail/Blocked or an explicit owner variance; it is never converted to Pass by lowering
a gate.

## M13 completion blockers

M13 remains blocked by any of the following:

- M12 is not separately accepted, its actual head is unknown/non-single, a contract is unreleased,
  or an M12 writer still owns a required surface;
- any T1 owner decision is missing: OSI license, legal/privacy copy, retention, hostname/origins, S3
  provider/region, or RPO/RTO;
- an unapproved migration, second head, prior-migration edit, generated-client hand edit, floating
  action/image/dependency, unreviewed package, or shared-file ownership collision;
- incomplete public/admin route/state/API mapping, fake/template/AI/legal/demo content, missing
  provenance, draft/private discovery, incorrect canonical/sitemap/robots/feed behavior, or stale
  protected data;
- unresolved WCAG 2.2 AA blocker, missing required manual AT/browser/device/zoom evidence, or
  score-only accessibility treatment;
- confirmed Critical/High security/privacy/supply-chain/container/dependency finding, authorization
  gap, secret/token/contact/private-content leak, unsafe upload/storage behavior, or scanner/gate
  suppression;
- failed Lighthouse/Core Web Vitals/route budget without disposition, obvious N+1/unbounded query,
  unexplained regression/variance, or optimization that weakens behavior/security/accessibility;
- unprepared coordinated database/object backup and restore inputs, unverified private S3 adapter,
  unsafe operator command, missing secret/rollout/rollback/monitoring guidance, or sensitive
  observability;
- incomplete or inaccurate user/API/developer/operator documentation, failed clean-reader
  walkthrough, missing sanitized screenshots, broken evidence links/hashes, prohibited evidence
  content, unexplained skips/flakes, or a reviewer accepting their own corrective work.

No waiver can override a Critical/High security finding or normative R1 Must requirement without an
approved specification change.

## M14 handoff criteria

Only Integration/root may create the M14 handoff after a separate accepted M13 gate. The handoff
must freeze and identify:

1. the exact candidate commit/tree, actual sole Alembic head, immutable production image digests,
   lockfile and generated-contract hashes, and zero-diff/zero-skip suite inventory;
2. all T1 owner decisions and deployed configuration expectations, with no secret values: license,
   reviewed legal/privacy copy, retention, hostnames/origins/proxy/TLS, S3 provider/region/endpoint
   class, secret-manager ownership, and RPO/RTO;
3. clean-install prerequisites, previous-release fixture, empty and upgrade migration protocols,
   synthetic bootstrap/demo data, production build/start/readiness protocol, and coordinated
   PostgreSQL/object backup set plus restore-order/consistency assertions;
4. the complete M14 minimum E2E journey list, manual WCAG/browser/device matrix, security/API/privacy
   matrix, performance profiles/budgets, query/load fixtures, scanner commands, and documentation
   consumer walkthroughs;
5. sanitized evidence/report/screenshot manifest with hashes, tool/browser/AT/OS versions,
   environments, dates, executors, defects/retests, coverage and target variances, limitations,
   accepted owner risks, and no prohibited content; and
6. explicit confirmation that M14 uses a fresh checkout, clean dependency caches where practical,
   fresh secrets, fresh database/media namespaces, newly built images, only shipped documentation,
   independent validators, and no inherited developer services/data/caches.

M13 does not pass merely because this package is prepared. M14 independently reproduces install,
build, migration, previous-release upgrade, production startup, backup/restore consistency, full
suites/scans/reviews, API/documentation consumer flows, traceability, and release reporting. Any M14
failure returns through a triaged corrective task and a new frozen candidate; it is not patched
silently inside the validation environment.
