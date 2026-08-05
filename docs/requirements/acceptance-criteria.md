# Acceptance Criteria

These criteria are release-level behavioral checks. “Given/When/Then” steps may be implemented as automated tests, manual review protocols, or both as indicated in the traceability matrix. IDs are stable and must not be reused.

## Public experience

### AC-001 — Required public routes (`F1-001`)

- Given published content and an unauthenticated visitor, when each required core route and a published custom-page route is opened on desktop and mobile viewports, then the route is navigable, renders the intended content, and does not require authentication.
- Given an unknown/unpublished route, when requested publicly, then a designed not-found response is returned without leaking draft data.

### AC-002 — API-backed public content (`F1-002`, `API-001`)

- Given a public content value changed through the administration API, when the public page is refreshed, then the new value appears without a frontend source change or rebuild that embeds the content.
- A repository review finds no public business content hard-coded in frontend components and no frontend database access.

### AC-003 — Responsive navigation and theme (`F1-003`)

- Given supported desktop and mobile widths, when primary navigation is used by pointer and keyboard, then all visible destinations are reachable and the mobile navigation opens/closes accessibly.
- Given system/light/dark selection, when the visitor changes and revisits the site, then the applicable preference persists and all themes meet contrast requirements.

### AC-004 — Discoverability metadata (`F1-004`)

- Given a page with overrides and one using defaults, when rendered/crawled, then title, description, Open Graph, canonical (where applicable), sitemap and robots behavior resolve correctly, and appropriate structured data validates without exposing draft URLs.

### AC-005 — Block catalog and rendering (`F1-005`)

- Given one valid example of every required initial block type, when a published page renders, then each block appears in configured order and produces its intended accessible representation.
- Given a hidden block, when the public page renders, then the block and its referenced content do not appear.

### AC-006 — Block schema enforcement (`F1-006`)

- Given valid shared/type-specific options, when saved, then they round-trip and affect the intended rendering.
- Given an unknown type, invalid reference, malformed option, or disallowed variant, when saved through UI or API, then a field-addressable validation error is returned and invalid configuration is not persisted.

### AC-007 — Profile privacy (`F1-007`, `F2-003`)

- Given private and explicitly public profile/contact values, when unauthenticated profile endpoints/pages are inspected, then only approved public values appear; private values are absent from payload, markup, metadata, and logs.

### AC-008 — Skills public/admin slice (`F1-008`, `F2-004`)

- Given skills across categories with featured/visibility/order settings and valid relations, when managed and viewed, then CRUD, category management, bulk ordering, filters, featured selection, and links to related visible projects/experiences behave consistently.

### AC-009 — Experience public/admin slice (`F1-009`, `F2-005`)

- Given valid experiences, when created/edited/ordered/published, then visible published records render in the intended professional presentation with relations.
- Given end-before-start, a current position with an end date, or another declared inconsistent combination, when saved by UI/API, then persistence is rejected with a stable validation error.

### AC-010 — Project public/admin slice (`F1-010`, `F2-006`)

- Given projects with complete fields, media, relations, feature/visibility/publication/order/SEO states, when managed and browsed, then CRUD and public listing/filter/detail/featured/screenshots/related content behave as configured and hidden/draft records remain private.

### AC-011 — Blog lifecycle (`F1-011`, `F2-007`)

- Given draft, published, future-dated, tagged, categorized, and related posts, when lists/filters/details are requested, then only publicly effective posts appear, pagination metadata is correct, and publication date/reading time/related posts render.

### AC-012 — Safe portable content (`F1-012`)

- Given supported formatting, when content is authored, stored, exported/reloaded, and rendered, then formatting remains portable and valid.
- Given script/event-handler/unsafe URL or raw unsanitized HTML input, when saved/rendered, then it is rejected or safely sanitized and cannot execute.

### AC-013 — Contact submission (`F1-013`, `F2-009`)

- Given valid consented input, when submitted below configured limits, then exactly one private submission is stored and accessible only to an authorized administrator, and the visitor sees success feedback.
- Given invalid, non-consented, spam-like, or rate-limited input, when submitted, then safe field/failure feedback is shown and sensitive message data is absent from logs.

### AC-014 — Optimized accessible images (`F1-014`)

- Given meaningful and decorative media, when public pages render, then meaningful images use managed alternative text, decorative images are correctly ignored by assistive technology, and responsive optimized delivery avoids avoidable layout shift.

## Administration and security

### AC-015 — Administrator bootstrap (`F2-002`)

- Given a clean production deployment, when started without an approved bootstrap mechanism, then no predictable administrator is silently enabled.
- Given a valid one-time bootstrap, when the initial administrator logs in, then password change is required; the setup cannot be replayed to take over the account.

### AC-016 — Authentication lifecycle (`F2-001`, `SEC-002`, `SEC-003`)

- Given valid/invalid credentials, when login is attempted, then valid login establishes a protected expiring session, invalid login gives a non-enumerating error, both create safe audit events, and repeated failures trigger configured protection.
- Given logout, expiration, or password change, when a protected route is requested with an invalidated session, then access is denied.
- Stored password inspection confirms an approved Argon2id/equivalent hash and no plaintext/reversible credential.

### AC-017 — Authorization and web controls (`SEC-001`, `SEC-004`, `SEC-005`, `SEC-006`)

- Given an unauthenticated, under-scoped, cross-resource, forged-CSRF, cross-origin, injection, or mass-assignment attempt, when a protected operation is requested, then it is denied safely, no unauthorized mutation occurs, and approved security headers/CORS policies remain present.

### AC-018 — Contact administration and retention (`F2-008`, `F2-009`)

- Given multiple submissions/states, when an administrator lists, filters, reads, marks read, archives, or deletes them, then the state transition is correct and auditable; an unauthenticated request can never list or retrieve submission data.
- Published documentation states retention/deletion behavior and operational configuration.

### AC-019 — Media management (`F2-010`, `F2-011`, `SEC-007`)

- Given a valid image, when uploaded, then a safe name, detected MIME, dimensions, metadata, timestamps, preview, search and pagination behavior are available through the configured storage adapter.
- Given an oversized, mismatched, malformed, or disallowed upload, when submitted, then it is rejected safely regardless of extension.
- Given referenced media, when deletion is attempted, then deletion is blocked with usage information; unreferenced media can be deleted with confirmation.

### AC-020 — Page management and slug safety (`F2-012`, `F2-013`)

- Given page/block operations, when an administrator creates, duplicates, edits, reorders, hides, previews, publishes, unpublishes, or deletes, then persisted/public results match the selected state and destructive/unsaved-change safeguards apply.
- Given a duplicate, reserved, or invalid normalized slug, when saved, then a stable validation error prevents collision.

### AC-021 — Navigation/footer safety (`F2-014`)

- Given valid ordered internal/external/footer/social/legal links, when saved, then labels, visibility, nesting, order, and safe target behavior render as configured.
- Given a disallowed scheme, malformed URL, unsafe target, or invalid internal destination, when saved, then it is rejected.

### AC-022 — Website settings (`F2-015`)

- Given complete settings, when changed, then identity, branding, locale/timezone, theme, contact/social, SEO, analytics placeholders, and availability appear in applicable public/admin surfaces.
- Attempts to store a secret/private analytics credential as a public setting are rejected or stored only through the approved secret mechanism and never returned publicly.

### AC-023 — Token creation and scope (`F2-016`, `F2-017`, `API-008`, `SEC-008`)

- Given a named token with selected initial scopes and optional expiry, when created, then a cryptographically random secret is displayed exactly once, only its hash/metadata is stored, and subsequent views cannot recover it.
- Given valid, missing, under-scoped, expired, revoked, and rotated tokens, when API operations are attempted, then only valid sufficiently scoped tokens succeed; old/invalid secrets authorize nothing.
- Token secrets never appear in logs/audit records, while safe create/use/revoke metadata is recorded.

### AC-024 — Audit events (`F2-018`, `SEC-009`)

- Given every specified authentication/token/content/publication/settings/media/security action, when performed, then an audit entry contains event, actor, resource, UTC timestamp, request ID, and allowed context.
- Inspection confirms no passwords, token secrets, full auth headers, contact bodies, or unnecessary personal data are stored.

### AC-025 — Administration UX (`F2-019`, `NFR-004`)

- Given each essential management workflow at desktop and supported mobile width, when completed by keyboard/pointer, then navigation/context/actions/forms/tables/filters/publication states work, destructive actions require confirmation, unsaved changes warn, and success/failure states are announced accessibly.

### AC-026 — Safe health visibility (`F2-020`, `API-007`)

- Given healthy and database-unavailable conditions, when liveness/readiness/admin health are inspected, then liveness reflects process availability, readiness reflects required dependency readiness, admin view is understandable, and no sensitive internal detail is exposed.

## API contract

### AC-027 — Versioning and OpenAPI (`API-001`, `API-002`)

- Given the running service, when `/api/v1/` and its OpenAPI document are inspected, then all supported public/admin capabilities are represented by stable schemas/security declarations and a standard client generator can consume the document without schema errors.

### AC-028 — API conventions (`API-003`)

- Given representative resources, when requests/responses are inspected, then naming, ISO 8601/UTC dates, authentication/authorization, request IDs, validation/domain distinctions, schemas, and documented deprecation conventions are consistent.

### AC-029 — Pagination/filtering/sorting (`API-004`, `API-005`)

- Given a collection larger than one page, when pagination is traversed with supported filters/sorts, then no item is unintentionally lost/duplicated, metadata is accurate, and behavior matches documentation.
- Unsupported filter/sort fields and arbitrary expression syntax return a safe documented validation error.

### AC-030 — Error contract (`API-006`)

- Given validation, authorization, not-found, conflict, rate-limit, and internal failures, when triggered, then the documented envelope includes stable code, safe message/details, and correlated request ID; production never returns a stack trace.

## Cross-cutting quality and delivery

### AC-031 — Visual/product quality (`NFR-001`)

- A documented cross-device product review confirms the public site is not an unmodified template and the admin experience meets the specified premium, calm, consistent, credible dashboard standard without inconsistent component states.

### AC-032 — WCAG behavior (`NFR-002`, `NFR-003`)

- Automated scans and a documented manual/browser-assisted review of representative public/admin workflows find no unresolved WCAG 2.2 AA blocker across keyboard/focus, structure, labels/errors, contrast, motion, screen reader controls/dialogs, alt text, zoom, and touch targets.

### AC-033 — Complete asynchronous states (`NFR-004`)

- Given each asynchronous view, when its data source is delayed, empty, invalid, failed, or unauthorized, then the specified distinct state is usable, accessible, and does not display stale/privileged data.

### AC-034 — Performance targets (`NFR-005`, `NFR-006`)

- Representative production builds are measured under a documented Lighthouse profile; results target performance ≥90, accessibility ≥95, SEO ≥95 and good Core Web Vitals, with variances recorded.
- Query/profiling evidence shows no obvious N+1 paths; large lists paginate; frequent predicates are indexed; image and client-JavaScript budgets are reviewed.

### AC-035 — Architecture boundaries and stack (`NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`)

- Architecture review confirms modular-monolith/layer boundaries, thin route handlers, no frontend database access, justified Server/Client Component choices, strict TypeScript, and the required backend/frontend technologies and test tooling.

### AC-036 — Migrations and containers (`NFR-011`, `NFR-012`)

- Given an empty PostgreSQL database, when all Alembic migrations run, then the expected schema is created; upgrade validation passes without manual schema edits.
- Docker/Compose and the task runner can execute documented local and production-oriented build/start workflows using environment configuration without embedded secrets.

### AC-037 — CI and tests (`NFR-013`, `NFR-014`)

- Given a pull request/protected branch, when CI runs, then every specified format/lint/type/test/build/startup/migration/E2E/security/OpenAPI job executes and failures block acceptance.
- Test inventory demonstrates every backend/frontend category and every minimum E2E workflow from `SPEC.md` §13.

### AC-038 — Coverage and meaningful assertions (`NFR-015`)

- Coverage reports meet or explicitly disposition backend 85%, critical/security backend 95%, critical frontend 80%, and critical E2E targets; sampled tests assert behavior rather than execution-only lines.

### AC-039 — Non-bypassable completion gates (`NFR-016`, `SEC-010`)

- Given a release candidate, when the release checklist is run, then all listed quality gates provide passing evidence and no test/error suppression or placeholder behavior is used to obtain green status.

### AC-040 — Controlled dependencies and milestone slices (`NFR-017`, `NFR-018`)

- Dependency/architecture review finds no unapproved optional infrastructure, microservice/Kubernetes/distributed/fake-AI implementation, or abstraction without an active requirement.
- Each completed vertical slice has linked domain, persistence, migration, API, admin, applicable public, test, and documentation evidence.

### AC-041 — User documentation (`DOC-001`)

- A clean-environment operator following only published user documentation can install, start, initialize/login/change password, configure/manage each content area/token/contact, back up, restore, upgrade, and resolve documented common failures.

### AC-042 — API documentation (`DOC-002`)

- An API consumer following only API docs can find the base/version/OpenAPI, create and use a scoped token, paginate/filter/sort, interpret errors/rates, run cURL examples, and revoke access successfully.

### AC-043 — Developer documentation (`DOC-003`)

- A new contributor can follow developer docs to understand architecture/repository/config/database/migrations/conventions, run tests/design-system tooling, submit changes, follow release/security practices, and locate extension/AI boundaries.

### AC-044 — Open-source repository hygiene (`OSS-001`, `OSS-002`)

- Repository inspection confirms all required governance/setup/roadmap/template/license/screenshot-when-applicable artifacts exist and secret/private/proprietary/machine-specific/dump scans find no prohibited content.

### AC-045 — Decisions and specification changes (`CHG-001`, `CHG-002`)

- Every major selected candidate decision has an ADR with required sections.
- A sampled specification change includes rationale and implementation/migration/test/acceptance impacts, resolves contradictions, and updates traceability without reusing IDs.

### AC-046 — AI boundary without AI behavior (`AI-001`, `AI-002`, `AI-003`, `AI-004`)

- Architecture/developer documentation identifies replaceable future provider/retrieval/agent/evaluation/tracing/structured-output interfaces and a publication-safe path to profile/skill/experience/project/blog data.
- Runtime/UI/repository inspection finds no fake F3/F4 behavior or speculative AI service dependency; F3/F4 remain marked Deferred unless CHG-002 evidence explicitly changes scope.

## Release acceptance record

For each criterion, the release record shall capture: `Status` (Not run/Pass/Fail/Waived), `Evidence link`, `Build/commit`, `Environment`, `Executor`, `Date`, and `Defect/waiver reference`. A waiver cannot override a critical/high security finding or a normative R1 Must requirement without an approved specification change.
