# Milestone 10 Dispatch

## Dispatcher status

This document prepares `M10-T01` through `M10-T03`. It does not release implementation, record acceptance, authorize M11, or claim that M9 has passed.

M10 remains blocked until Integration/root records the separate M9 acceptance decision, confirms the accepted single database head, resolves the contact-policy decisions below, and releases every shared/provider surface named in this dispatch.

| Task      | Current state | Release condition                                                                                                                                              |
| --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M10-T01` | Blocked       | M9 passes; one Alembic head is `20260802_0010`; gates C0-C2 pass; the sole `0011` reservation and disjoint backend/provider writers are recorded.              |
| `M10-T02` | Blocked       | `M10-T01` backend/API/security evidence passes; Integration/root records contract freeze C4 and generates a clean client.                                      |
| `M10-T03` | Blocked       | `M10-T02` public/admin UI evidence passes; retention/privacy and operator inputs remain approved; Integration/root records vertical-slice readiness freeze C5. |

M10 maps to trace milestone `M14`. It delivers only the private Contact vertical slice: unauthenticated submission, authenticated administrator triage and lifecycle, anti-abuse controls, retention purge, accessible public/admin UX, documentation, and verification. It does not add public contact queries, outbound email, notifications, CRM/webhooks, CAPTCHA vendors, Redis, workers/schedulers, exports, bulk destructive actions, API-token contact access, or M11/M12 feature work.

## Blocking inputs and decisions

### C0 - Separate M9 acceptance and foundation release

Before any M10 write, Integration/root must record:

- a separate accepted M9 gate with `M9-T01` through `M9-T03` evidence, no unresolved Critical/High finding, and no active M9 writer on a file M10 needs;
- exactly one Alembic head at `20260802_0010` from `20260802_0010_media.py`, with current/head equality in the accepted environment;
- clean OpenAPI export and deterministic generated-client regeneration at the M9 baseline;
- accepted M1/M2 provider contracts for administrator sessions, actor context, CSRF/Origin, request IDs, safe errors, PostgreSQL rate limiting, minimal append-only audit, idempotency, pagination/filter/sort, `ETag`/`If-Match`, and same-origin transport;
- the actual released backend/frontend router, model, configuration, central API wrapper, admin-shell/navigation, public route, privacy-page, command, and E2E fixture files that later single-writer windows may touch.

M10 consumes those contracts through their public facades. It does not duplicate identity, audit, rate-bucket, idempotency, request-context, error, pagination, or transport implementations.

### C1 - Owner privacy, consent, retention, and lifecycle decision

The Maintainer/Privacy-Legal owner, Product/Architecture owner, Security owner, and Operations owner must record all of the following before T01 starts:

- reviewed public privacy text for `/privacy`, its stable non-secret policy version identifier and effective time, and the exact contact-data purposes disclosed next to the form;
- whether the architecture default of 365 days from database `created_at` is lawful and operationally appropriate for the deployment, including treatment of all states and residual encrypted backups;
- named authority for manual hard deletion and operator purge, the production purge cadence/runbook despite R1 having no worker, batch size/timeout/lock policy, dry-run review/approval, and incident hold procedure;
- data-subject/privacy request handling and the rule for a legal/incident hold. No hold feature or indefinite retention is invented unless separately specified and designed;
- approved source-form identifiers and the rule binding each identifier to its server-owned route/form context;
- the exact state machine after resolving a source conflict: architecture defines `unread -> read -> archived` and `archived -> read`, while UX also mentions mark read/unread. No `read -> unread`, archive-from-unread shortcut, or other transition may be implemented until Product/Architecture records the accepted transition table and updates impacted contracts through change control.

Placeholder legal text, a free-form client policy version/source, an unowned purge, silent indefinite retention, or treating a planning dispatch as legal approval blocks C1 and M10 acceptance.

### C2 - Anti-abuse, trusted-proxy, and validation freeze

Security/Operations/Integration must freeze:

- the public request body limit and exact normalized character/UTF-8 byte limits for name, email, subject, message, idempotency key, form-start proof, honeypot, policy version, and source; source requirements currently demand strict validation but do not authorize guessed limits;
- Unicode normalization, whitespace/newline rules, prohibited control/bidi/null characters, plain-text rendering/escaping, email parser/normalization behavior, and stable field error codes without ASCII-only human-name assumptions or speculative email deliverability checks;
- consent as an explicit unchecked boolean, a server-recorded consent timestamp, and exact match to the currently effective reviewed policy version; stale/missing/false consent is not persisted;
- the server-owned source allow-list and signed/bound minimum-completion proof. Browser timestamps, hidden fields, `Referer`, and client-supplied source labels are not trusted facts;
- PostgreSQL-authoritative contact limits of 5 distinct attempts per 15 minutes per IP pseudonym and 20 per day per IP pseudonym, including database-UTC window boundaries, atomic accounting, replay behavior, failure policy, cleanup retention, indexes, and load target;
- raw-client-IP derivation: exact production proxy hop count or CIDR allow-list, canonical IPv4/IPv6 handling, and a fail-closed startup/readiness rule. Forwarded headers are honored only from an explicitly trusted immediate peer; otherwise the socket peer is authoritative. Trust-all proxies, guessed hops, arbitrary `X-Forwarded-For`, and localhost/example production defaults are forbidden;
- a dedicated versioned rotating-key HMAC pseudonym contract and overlap/rotation behavior that cannot casually reset both rate windows. Raw IP is transient and is never persisted or placed in audit, logs, URLs, traces, analytics, screenshots, or idempotency rows;
- generic anti-spam response semantics for honeypot, too-fast, and classified spam paths, including indistinguishable safe status/body/schema/cache behavior where disclosure would help attackers; ordinary field validation remains actionable, and an actual rate limit follows the accepted `429` plus `Retry-After` contract without echoing contact content;
- the exact public idempotency scope and canonical request fingerprint using the accepted M2 store without persisting submitted values or response bodies. Same key plus same normalized request replays one generic result; the same key with a different request conflicts safely; concurrent duplicates have one effect.

Production configuration fails closed if proxy trust, HMAC key/version, current policy version, allowed sources, retention, or rate policy is missing or invalid. Edge throttling may supplement PostgreSQL for volumetric protection but cannot replace or weaken the authoritative two-window policy.

## Scope reservations and excluded files

### Existing and active work is excluded

Until C0 and explicit release, no M10 lane may edit, delete, move, format, or regenerate:

- `backend/app/modules/media/**`, media storage/usage/owner integrations, `backend/migrations/versions/20260802_0010_media.py`, M9 routes/configuration/commands/tests/evidence, or M9 frontend/E2E files;
- any still-active M0-M9 evidence, migration, provider, shared router, wrapper, shell/navigation, privacy-page, infrastructure, CI, documentation, or generated-contract surface;
- `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator scripts, root manifests/locks, `.github/workflows/**`, `compose.yaml`, `.env.example`, shared scanner/coverage settings, or deployment configuration except during a separately named Integration/Infrastructure single-writer window;
- requirements, architecture, ADR, UX, traceability, risk, and prior dispatch sources. A contradiction or missing decision is returned to its owner through change control, not silently edited by a feature lane.

M10 introduces no unrequested dependency. No task may add a CAPTCHA/anti-spam SaaS, Redis, queue, worker, notification service, encryption scheme, or PII analytics/error-reporting integration as a convenience.

### Shared single-writer surfaces

Integration/root records an exact file manifest before fan-out. The sole migration, contact ORM registration, rate-limit/provider changes, privacy/config schema, backend/public/admin router composition, purge-command registration, audit event catalog integration, central handwritten wrapper, public route/navigation, admin route/sidebar/unread badge, generated artifacts, E2E fixtures, and privacy/redaction corpus each have one named writer window. Lanes may propose diffs or consume released facades; they do not create competing helpers or edit a shared file concurrently.

## Owner-safe M10 lanes

| Lane                                        | Owner                             | Exclusive write area                                                                                                                                                                                                                        | Boundary and handoff                                                                                                                                                                                        |
| ------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M10-T01-D` contact domain/application      | Backend Contact Domain Agent      | New contact domain/application code under `backend/app/modules/contacts/**`: validation, acceptance/lifecycle/delete/purge use cases, ports, DTOs/errors/events, and focused unit/application tests; `docs/evidence/M10/M10-T01-domain.md`. | Starts after C2. No ORM/migration/router/provider/generated/config/shared audit files. Emits safe facts only and never receives a logger capable of binding contact values.                                 |
| `M10-T01-R` persistence/query/purge         | Backend Contact Persistence Agent | Dedicated contact ORM/repository/admin query/purge adapters and PostgreSQL tests in Integration-reserved contact infrastructure files; `docs/evidence/M10/M10-T01-persistence.md`.                                                          | Starts after contact model freeze C3. Repositories never commit. Reuses accepted UoW, DB time, idempotency, rate, and audit ports; no duplicate persistence.                                                |
| `M10-T01-M` sole migration                  | Backend Migration Agent           | `backend/migrations/versions/20260802_0011_contacts.py`, dedicated migration fixtures/tests, and `docs/evidence/M10/M10-T01-migration.md`.                                                                                                  | Starts only after C3 and root reservation. Sole `0011` writer; no mutation of `0001`-`0010`, second revision, merge head, rate/idempotency/audit duplicate, or production data dump.                        |
| `M10-T01-S` anti-abuse/provider integration | Security plus M1 Provider Owner   | Only C2-approved extensions to the existing rate-limit/IP-pseudonym/config/audit-provider facades and dedicated tests/evidence named in the root manifest; `docs/evidence/M10/M10-T01-security.md`.                                         | Serialized after active owners release exact files. Contact lanes cannot fork shared security behavior. Infrastructure alone writes deployment/edge/env surfaces if a separately approved change is needed. |
| `M10-T01-A` public/admin API                | Backend Contact API Agent         | Dedicated contact public-submit and authenticated-admin route/schema/dependency modules plus API/security tests; `docs/evidence/M10/M10-T01-api.md`.                                                                                        | Starts after C3. Calls application services only. Does not add public reads, token authorization, raw repository access, generated artifacts, or shared router edits outside its named integration window.  |
| `M10-T01-I` contract integration            | Integration/root                  | Sequential router/model/command/event-catalog composition, reviewed OpenAPI diff, `docs/api/openapi.json`, `frontend/src/generated/api/**`, generation reports, contract/security review, C4, and final T01 decision.                       | Starts after D/R/M/S/A evidence. Integration/root alone exports/generates and writes shared composition. All other lanes pause those surfaces.                                                              |
| `M10-T02-P` public contact frontend         | Frontend Public Contact Agent     | `frontend/src/features/contacts/public/**`, the released `/contact` page slot, form-specific stories/tests/wrapper, and `docs/evidence/M10/M10-T02-public.md`.                                                                              | Starts after C4. Uses generated schemas through the accepted wrapper; no raw fetch, public query, analytics payload, legal-copy invention, or shared route/navigation edit without a reserved window.       |
| `M10-T02-A` private admin frontend          | Frontend Admin Contact Agent      | `frontend/src/features/contacts/admin/**`, released `/admin/contacts` list/detail slots, contact-specific stories/tests/wrapper, and `docs/evidence/M10/M10-T02-admin.md`.                                                                  | Starts after C4, file-disjoint from T02-P. Shared admin shell/sidebar/badge work is a later serialized owner window. No contact values in URL, toast, telemetry, persistence, or screenshot fixtures.       |
| `M10-T02-I` UI/shared integration           | Integration/root                  | Sequential public/admin route/navigation/sidebar/unread-badge/wrapper composition, cross-UI contract/privacy/a11y review, C5, and final T02 decision.                                                                                       | Runs after P/A evidence. It reconciles shared changes and generated-client use; it does not hide behavioral defects or claim M10 acceptance.                                                                |
| `M10-T03-I` integration/E2E/docs            | Integration/root                  | Contact-only E2E/security/privacy/load/retention fixtures and reports, sanitized screenshots/traces, user/API/developer/operator docs, `docs/evidence/M10/M10-T03.md`, trace links, and final M10 gate preparation.                         | Starts after C5. Defects return to named owners. No M11 work or final acceptance without independent privacy/security/operations/a11y review.                                                               |

No two lanes edit the same file concurrently. Backend authors executable Pydantic contracts, Integration/root alone exports and generates, and frontend lanes consume only the C4 generated client through handwritten wrappers.

## Sole migration reservation

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0011_contacts.py
revision: 20260802_0011
down_revision: 20260802_0010
owner: M10-T01-M only
```

The revision adds only the accepted contact persistence required by C1-C3:

- `contact_submission` with opaque ID, strictly bounded name, normalized email, subject, plain-text message, consent timestamp, consent policy version, server-owned source, accepted lifecycle state, nullable read/archive timestamps consistent with state, database UTC created/updated timestamps, and integer version;
- constraints for nonempty/bounded normalized values, allowed state/source/policy shapes, consent/state timestamp consistency, and indexes supporting the frozen admin state/date filters and stable allowed sorts with opaque-ID tie-breakers;
- privileges consistent with runtime least privilege and the separately authorized operator purge path.

Contact rows and their backups remain inside the accepted private PostgreSQL/network boundary and use the deployment's approved encryption-at-rest and encrypted-backup controls. Application-layer field encryption is neither improvised nor claimed by this milestone.

It does not store raw IP, forwarded headers, user agent, honeypot value, form-start proof, idempotency key/fingerprint, spam classification, arbitrary metadata JSON, HTML, URL/query data, audit payload copies, or a public foreign/query path. It does not recreate or alter the accepted rate-limit, idempotency, or audit tables unless Integration/root dispatches an unavoidable compatible extension to their original provider owner within this same sole revision.

Migration evidence requires empty upgrade, upgrade from accepted `0010`, current/head equality, one head, schema-model/constraint/index/grant parity, representative contact states, and the project-approved downgrade check. Production startup checks compatibility and never migrates or purges.

## Backend contract to freeze

### C3 - Contact domain and persistence contract

Integration/root records C3 after T01-D review and tests, before R/M/S/A fan-out. C3 freezes the following behavior.

#### Strict public input and acceptance

- The public API exposes a bounded submit mutation only. There is no unauthenticated list, detail, count, status, search, export, or ID-based lookup, and public OpenAPI schemas never reuse private administrator projections.
- Request parsing rejects oversized bodies before full buffering. Unknown/duplicate/mass-assigned fields fail according to the frozen safe validation contract; transport/header/query values cannot become contact fields.
- Name is normalized and validated as human text without an ASCII-only or word-shape guess. Email uses the frozen standards-aware parser and deterministic normalization. Subject and message remain bounded plain text, normalize line endings as specified, reject prohibited controls/markup assumptions, and are escaped at every render boundary. None is interpreted as HTML, Markdown, a link, a header, or log template.
- Consent must be explicitly true and never inferred from submitting the form. The server records database time and the exact currently effective reviewed policy version; stale or unknown versions require safe re-consent and create no submission.
- Source is derived from a server-bound allowed form context. Client-provided route, campaign, referrer, or source text cannot be persisted by mass assignment.
- Honeypot and minimum-completion evidence are defense-in-depth signals, not accessibility barriers or sole security controls. The minimum time uses a server-issued authenticated proof and server time; a missing/invalid/expired proof follows frozen anti-spam behavior without trusting the browser clock.

#### Anti-abuse, rate accounting, and exact-one storage

Processing is ordered and bounded: request-size/content parsing, trusted source-IP derivation/pseudonym, atomic rate admission, safe normalization/validation, server-owned form-context/consent checks, anti-spam classification, idempotency admission, and one transaction for the accepted write plus safe audit/idempotency outcome as permitted by the existing providers. The exact ordering and what consumes rate capacity are fixed in C2 and tested; no rejected contact values are retained accidentally.

- PostgreSQL is authoritative for both 5 distinct attempts per C2-frozen 15-minute window and 20 per database-UTC day per IP pseudonym. Updates are atomic under concurrency, indexed, bounded, and use the established rate port. An edge limiter is supplementary only.
- HMAC pseudonyms are purpose-separated/versioned. Raw IP and forwarded-header chains exist only long enough to derive the pseudonym and are then discarded. Rotation preserves the C2 abuse window semantics and documented incident correlation without storing raw addresses.
- A valid accepted request stores exactly one private row. Same-key/same-normalized-request retries, simultaneous duplicates, timeout-after-commit retry, refresh/back, and transport replay return the approved safe result without a second row or second logical event. Same-key/different-request never exposes the first request.
- Honeypot/too-fast/classified-spam paths store no contact row and return the frozen generic response. They do not disclose the classification through response schema, status, request timing targets, headers, cookies, IDs, logs, audit, or browser copy. Genuine field errors remain correctable; actual rate-limit feedback uses safe `Retry-After` and never echoes submitted content.
- Accepted public responses contain no contact ID, email, body, normalized payload, classification, bucket detail, pseudonym, or administrative link. All public-submit responses use `Cache-Control: no-store` and appropriate referrer/search indexing protections.

#### Private lifecycle, queries, concurrency, and audit

- New rows begin `unread`. Only the C1-approved transition table is implemented. Detail loading has no mutation; an explicit version-guarded command marks read only after detail succeeds. Archive is reversible and restore returns to `read` under the accepted architecture. Hard delete is permitted from any accepted state only through an administrator session and explicit confirmation.
- At M10, administrator sessions are the only admin contact actor. Cookie-authenticated unsafe methods enforce exact Origin and signed CSRF. API tokens and the future `contacts:read` scope are M11 work; token-shaped actors cannot hard-delete and gain no implied access now.
- List/detail/selectors are authenticated before resource lookup, use dedicated private projections, return `Cache-Control: private, no-store`, and never leak existence through public or under-authorized paths. Allowed filters are state and frozen date boundaries; allowed sorts use explicit mappings and deterministic ID tie-breakers. Sensitive name/email/message/subject search or URL filters are excluded unless separately approved.
- Inbox defaults to unread then newest according to the frozen sort definition. Pagination is bounded and stable under concurrent inserts/state changes; no unbounded collection, arbitrary SQL field, N+1 detail loading, or body preview is allowed.
- Every mutable lifecycle command requires accepted `If-Match`/version behavior, row locking or equivalent atomic predicates, and one UoW. Concurrent read/archive/restore/delete produces one valid transition or safe conflict, never resurrection, lost updates, partial timestamps, or duplicate audit.
- Hard delete atomically appends a controlled audit event and removes the contact row. Audit metadata contains only event/outcome, actor, contact resource ID, prior state, request ID, UTC time, and explicitly allow-listed operational facts. It never contains name, email, subject, message/body, consent text, raw IP, form proof, source URL, or arbitrary client metadata.
- Application logs, exception messages, traces/spans, metrics labels, profiler output, analytics, error reporting, SQL-bind logging, URLs/query strings, response caches, screenshots, fixtures, and evidence never contain contact email or body. The stronger evidence rule uses synthetic values and avoids all real submitted personal data.

#### Retention purge

- Default eligibility is database `created_at < database_now - interval '365 days'` for every state, unless C1 records a reviewed different policy before release. Application-server clocks and last-read/archive time do not silently extend retention.
- A dedicated operator command defaults to dry-run and reports safe aggregate counts by state/cutoff only. Apply requires explicit authorization, an explicit apply flag plus reviewed cutoff/run identity, and the C1 policy gate; ordinary application/admin UI roles cannot invoke it.
- Selection and deletion are bounded by batch size/time, deterministic, lock-safe with concurrent lifecycle activity, resumable, and idempotent. A dry run never mutates. Apply deletes only rows older than its frozen database-time cutoff and creates controlled aggregate and/or per-resource audit facts according to the approved event catalog, without PII.
- Failure mid-batch rolls back the affected transaction and resumes safely; repeated apply does not double-count/delete/audit logical effects. The command provides safe exit status, request/run correlation, progress counts and final reconciliation without IDs or values in ordinary logs unless the restricted operator evidence policy explicitly allows sanitized opaque IDs.
- Privacy/operations documentation explains database deletion, audit separation, idempotency/rate-record expiry, encrypted-backup residual lifetime and restore handling. Restoring an older backup requires re-running purge before normal service so expired contacts are not accidentally re-exposed.

## API and generated-client handoff

The backend contract submitted to `M10-T01-I` includes only:

- one unauthenticated public submit operation with bounded request fields, idempotency requirements, generic accepted behavior, safe validation/rate errors, and `no-store` response headers;
- authenticated administrator list/detail operations with opaque IDs, page metadata, explicit state/date filters and allowed sorts, private projections, and `private, no-store`;
- authenticated administrator mark-read plus any C1-approved mark-unread operation, archive, restore, and hard-delete mutations with CSRF/Origin, `If-Match`, stable validation/domain/conflict/precondition errors, and no contact value in error details;
- no public GET/HEAD detail/list/count/status route, no contact body in OpenAPI examples, and no production-looking email/name/message fixture.

Integration/root records C4 only after T01-D/R/M/S/A pass. It reviews the OpenAPI diff, checks unique stable operation IDs, validates schemas/security/cache/errors/idempotency/rates/pagination/filter/sort/concurrency, exports, generates, formats only as configured, strictly compiles, regenerates, and obtains no diff. Only Integration/root writes `docs/api/openapi.json` and `frontend/src/generated/api/**`.

C4 releases T02. Frontend cannot compensate with raw fetch, duplicated request/response types, `any`, hand-built authentication/CSRF/idempotency, body-in-query transport, or client-only security rules.

## Frontend behavior to freeze

### Public contact form

- `/contact` explains the private purpose, displays only owner-approved contact preferences/legal copy, links `/privacy` beside a separate unchecked consent control, and submits the exact effective policy version and server-bound source context through the generated contract.
- Name, email, subject, and message use persistent labels, correct autocomplete/input type/mode, descriptions, counts/limits where useful, and linked inline errors plus a focused summary. Validation preserves entered values locally for correction but never writes them to URL, history state, Web Storage, IndexedDB, Cache Storage, service worker queues, analytics, telemetry, error reporting, or console.
- The honeypot is unavailable to keyboard and assistive-technology users and cannot disturb autocomplete; the signed start proof is not a user task. JavaScript-disabled behavior remains a usable server-rendered form where the accepted architecture supports it, with the same server authority.
- Submit has one clear pending state and prevents accidental local double activation without relying on the button for exactly-once behavior. Network ambiguity offers an idempotent retry. Refresh/back after success does not resubmit; success replaces the form with a concise confirmation and explicit next action.
- Correctable validation identifies fields without disclosing anti-spam internals. Generic anti-spam success uses the same visitor-facing confirmation. A rate limit provides an accessible safe retry time; server/offline/internal errors retain input only in current volatile component state and include no echo in toast/URL/log.
- Initial, ready, invalid, submitting, success/generic-success, rate-limited, offline, server-error, policy-changed/re-consent, and retry states are distinct, keyboard usable, announced without noisy duplication, and safe at narrow/zoomed layouts.

### Private administrator inbox and detail

- `/admin/contacts` defaults to unread/newest, provides accessible state/date filters, allowed sort and pagination, announces result counts, and distinguishes empty inbox from no matches. Desktop semantic table and equivalent mobile cards expose safe list fields only; the message body never appears in a row preview, URL, notification, command palette, badge, or browser title/metadata.
- A durable `/admin/contacts/{id}` detail displays sender, subject, submission time, consent policy evidence, source label and plain-text message only after authorization and successful private fetch. Loading detail does not mark read. Explicit mark-read follows success; archive/restore reflect the C1 transition table.
- Safe reversible actions may be optimistic only with immediate rollback, version-conflict handling and announcement. The UI never silently overwrites a concurrent transition. It does not retain stale contact data while navigating between records.
- Permanent delete waits for server confirmation and uses a high-friction dialog naming the record only by safe synthetic subject/date presentation, explaining irreversibility and audit behavior, requiring an explicit checkbox/confirm, initially focusing the heading or least destructive action, and restoring focus. It never echoes email/body. After success, detail/query caches and DOM are cleared and focus moves to the next logical row or list heading.
- Session expiry, logout, unauthorized response, route change, delete, and component disposal immediately clear protected detail from DOM, memory, query caches, history-sensitive state, print preview, clipboard helpers, and any client persistence, then use the accepted safe expired-session path. `private, no-store` and bfcache tests prevent Back from revealing prior detail.
- Every initial/loading/success/empty/no-result/unauthorized/expired/offline/server-error/not-found/deleted-elsewhere/version-conflict/action-failure state is explicit. Toasts/badges contain safe counts, IDs/subject/date only where approved, never email/body.

Integration/root records C5 after T02-P/A/I pass generated-wrapper, component, Storybook, privacy, accessibility, responsive, state-clearing, and built-app browser tests. C5 is a readiness freeze for T03, not M10 acceptance.

## Ordered dispatch

1. **Blocked - Integration/root:** record separate M9 acceptance, verify sole head `0010`, release active/shared files, and assign C0 owners.
2. **Blocked - Privacy/Product/Security/Operations:** resolve C1 lifecycle/legal/privacy/retention/source/purge decisions and C2 validation/proxy/pseudonym/rate/idempotency/anti-spam details.
3. **After C2 - `M10-T01-D`:** implement and review the contact domain/application contract; Integration/root records C3.
4. **After C3 - Integration/root:** reserve sole `0011` on `0010` and publish exact disjoint R/M/S/A plus shared-provider writer manifests.
5. **After C3 - `M10-T01-R/M/S/A`:** implement persistence/purge, migration, provider integration, and APIs in disjoint files with serialized shared windows.
6. **After T01 evidence - `M10-T01-I`:** integrate routes/models/commands/event catalog, export/generate twice, compile/review, and record C4.
7. **After C4 - `M10-T02-P/A`:** implement public form and private inbox/detail in disjoint areas; Integration/root serializes shared UI/wrapper changes and records C5.
8. **After C5 - `M10-T03-I`:** run complete privacy/abuse/lifecycle/retention vertical-slice verification and prepare the M10 gate record without releasing M11.

## Exact acceptance, security, quality, and evidence gates

All evidence follows `docs/plan/delivery-evidence-template.md`, maps both M10 and trace M14, records commit/worktree/environment/tool versions/commands/results/defects/retests, and uses repository-relative artifact links. Only synthetic contact records are permitted. Evidence artifacts are scanned before retention or commit; no real or test email/body may appear in logs, audit output, URLs, caches, traces, screenshots, videos, reports, command lines, shell history excerpts, database dumps, or machine-specific paths.

### `M10-T01` backend, data, security, API, and contract evidence

Evidence must include:

- table-driven/property validation for boundary and over-bound name/email/subject/message, Unicode normalization, whitespace/newlines, controls/null/bidi, malformed/internationalized email cases, consent false/missing, stale/unknown policy, unknown/tampered source, unknown/duplicate fields, body caps, and plain-text output escaping;
- honeypot empty/filled, signed minimum-time proof valid/too-fast/missing/tampered/expired/replayed, generic-response equivalence, no storage, and accessibility-neutral field behavior without documenting an evasion recipe in public evidence;
- PostgreSQL rate tests for 5/15-minute and 20/day windows at before/exact/after boundaries using database UTC, IPv4/IPv6 canonicalization, atomic concurrent requests, two-window interaction, cleanup/key rotation/failure behavior, and indexed load/contention evidence at the C2 target;
- trusted-proxy tests for direct clients, approved one/multiple-hop topologies, untrusted immediate peers, too few/many hops, spoofed/malformed/duplicate forwarding headers, IPv4-mapped IPv6, production missing/trust-all configuration refusal, and absence of raw IP from persistence/log/audit/trace;
- idempotency tests for first accept, same replay, changed-payload conflict, concurrent duplicate, timeout after commit, refresh/back/network retry, expiry, pseudonym/key isolation, and safe records with exactly one contact row/logical audit effect;
- domain/state tests for the C1 transition matrix, timestamp/version invariants, invalid/repeated transitions, detail-no-side-effect, hard delete from every allowed state, and safe stable errors;
- PostgreSQL repository/query tests for deterministic pagination under concurrent inserts/transitions, state/date filters and each sort, rejected arbitrary/SQL-like fields, no body preview, bounded selects/no N+1, row-lock/concurrency behavior, transaction rollback, database-time cutoffs, and realistic query plans;
- purge tests proving 365-day exact cutoff, every applicable state, dry-run zero mutation, explicit apply authorization, batching/resume/idempotency, concurrent update/delete/new insert, injected mid-batch/DB/audit failure rollback, safe counts, event redaction, restored-backup re-purge, and operator-role separation;
- public/admin API tests for method/path matrix, no public reads, unauthenticated/expired/under-authorized/IDOR denial, CSRF/Origin/CORS, mass assignment/injection, body size, idempotency, `429 Retry-After`, pagination/filter/sort, `ETag`/`If-Match`, lifecycle conflicts, hard-delete confirmation contract, cache/referrer/security headers, safe envelopes/request IDs, and identical protected existence behavior;
- audit/log/cache/trace/metrics/error-reporting/OpenAPI example inspection proving no name/email/subject/message/contact body/raw IP/forwarded header/form proof/idempotency payload appears, while safe required contact events contain controlled IDs/state/outcome/request IDs only;
- migration evidence for empty/`0010` upgrade, one head/current equality, schema/model/constraint/index/grant parity, representative states, no prior revision mutation and no duplicate rate/idempotency/audit table;
- OpenAPI lint/reference/operation-ID/security/cache/error/example/idempotency/rate/pagination/filter/sort/concurrency review, two deterministic generations/no diff, strict generated compile, and wrapper-boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest suites, meaningful backend overall and >=95% contact security/critical-domain coverage evidence, architecture-boundary checks, dependency/container/secret/privacy scans, and no disabled/suppressed test or unexplained warning.

Any public contact query, duplicate accepted row, rate bypass/race, forged client IP/source/policy, raw IP storage, spam oracle, consent failure storage, invalid state transition, unaudited/partial hard delete, unsafe purge, PII in a forbidden sink, generated drift, second migration head, or confirmed Critical/High finding blocks C3/C4 and T01.

### `M10-T02` frontend and UX evidence

Evidence must include:

- generated-wrapper/component tests for all public fields and server errors, consent initially unchecked, privacy link/policy change, honeypot/valid timing integration, pending/double activation, idempotent retry, success/back/refresh, generic spam response, rate retry, offline/server failure, and volatile-only value retention;
- public form assertions that email/message never enter URL/history/storage/cache/service-worker/analytics/telemetry/console/error output and that no hidden anti-spam mechanism excludes keyboard, screen reader, autofill, paste, zoom, or JavaScript-disabled users;
- admin tests for default unread/newest, state/date filter/sort/page URL rules, table/mobile parity, detail-load-before-mark-read, every C1 state transition, optimistic rollback, stale `If-Match`, archive/restore, concurrent deletion, irreversible confirmation, focus after delete, and unread badge synchronization;
- protected-state tests for session expiry/logout/unauthorized/navigation/delete/bfcache/back/print/error boundaries proving immediate removal of private detail from DOM/memory/query cache/client persistence and no body/email in toast/title/URL/command menu/notification;
- Storybook interaction, axe, and manual keyboard/screen-reader tests for persistent labels, autocomplete, error summary/focus links, descriptions/counts, status/live regions, semantic table/sort/pagination, mobile cards, dialogs/focus restore, contrast/forced colors, reduced motion, touch targets, 200% text, and 400% zoom;
- Prettier, ESLint, strict TypeScript, affected Vitest/Testing Library/Storybook/Playwright, production build, >=80% meaningful critical contact-form/business-utility coverage, and bundle/render checks with no raw transport or duplicate model.

Evidence must cover 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px in light/dark/system as relevant. Screenshots and traces use conspicuously synthetic non-address contact values, redact request/response payloads, and include public ready/validation/submitting/success/rate/error plus admin empty/list/filter/detail/state/conflict/delete/session-expiry views without body/email.

An inaccessible consent/error/rate/confirmation flow, hidden-field interference, repeat submission, email/body in a forbidden client sink, stale protected detail, misleading state, silent concurrency overwrite, responsive loss, unresolved WCAG blocker, or unexplained bundle/performance regression blocks C5/T02.

### `M10-T03` vertical-slice, privacy, retention, and M10 gate evidence

Integration/E2E uses built Next.js/FastAPI through the same-origin edge and a fresh PostgreSQL database migrated through `0011`, with isolated workers and no demo/production contact data. It must prove:

- J1: reviewed privacy copy/version is visible; a visitor corrects strict validation, explicitly consents, submits once, receives safe confirmation, and refresh/back/network retry does not create another row;
- abuse paths: honeypot/too-fast/tampered proof receive generic safe behavior and no row; exact dual rate boundaries enforce atomically with safe `Retry-After`; spoofed proxy headers cannot rotate identity; raw IP and submitted values do not escape;
- J8: an authenticated administrator sees stable unread/newest pagination, loads detail before explicit read, performs every approved lifecycle transition, archives/restores, encounters a real stale-version conflict safely, and permanently deletes with confirmation/audit/focus/cache clearing;
- unauthenticated, expired, forged-CSRF, untrusted-Origin, token-shaped, IDOR, guessed-ID, mass-assignment, SQL/filter/sort injection, method confusion, and cache/bfcache attempts never list, retrieve, mutate, or reveal contact existence/data;
- injected DB/rate/idempotency/audit failures and concurrent duplicate/state/delete/purge requests produce no false public success for a failed valid write, duplicate row, rate-accounting corruption, partial transition/delete, missing required audit fact, or unbounded retry;
- a dataset spanning the 365-day cutoff yields an accurate sanitized dry run, unchanged rows, approved batched apply, resumable failure recovery, correct safe audit/counts, no over-cutoff deletion, and zero eligible rows afterward; an isolated old-backup restore is purged before contact access;
- HTTP/RSC/HTML, headers, browser/Next/FastAPI/PostgreSQL logs, audit queries, traces, metrics, caches, URLs/history, analytics/error reports, OpenAPI examples, test artifacts, coverage reports, screenshots and repository scans contain no email/body/raw IP and no real contact data;
- query/load/browser performance meets recorded budgets for submit contention, inbox pagination/filter/sort, detail, lifecycle, purge batches, public form render and admin bundle; representative Lighthouse performance remains >=90 and accessibility >=95 unless a measured owner disposition exists, with good CWV and no N+1/unbounded path;
- full affected backend/frontend/migration/contract/E2E/build/security/privacy/a11y/performance suites pass, generated output is clean, `0011` is the sole head, and no active/shared writer overlap occurred.

Documentation/evidence must include:

- a visitor/admin user guide for collected fields, consent/privacy link, validation, success/rate/retry behavior, inbox filters/sorts/pagination, read/archive/restore/delete, confirmations, concurrency and session expiry without exposing anti-spam evasion detail;
- an API guide for public submit and authenticated admin operations, schemas/errors/request IDs/idempotency/rates/`Retry-After`/pagination/filter/sort/ETag/cache/security, using synthetic redacted examples and no public read implication;
- a developer/security guide for strict normalization, source/policy binding, trusted proxy derivation, HMAC pseudonyms/key rotation, dual PostgreSQL rate buckets, honeypot/minimum-time/generic responses, exactly-one transaction/idempotency, lifecycle/audit redaction, private caching, and safe extension points;
- an operator/privacy guide for approved policy owner/version/effective date, 365-day rationale/configuration, purge dry-run review/apply/batches/resume/permissions/cadence, incident hold decision, rate/idempotency cleanup, proxy topology, key rotation, monitoring without PII, backup residual lifetime, restore-then-purge, privacy requests and incident response;
- sanitized command records, query plans/load reports, database/log/audit/cache/URL/privacy scans, coverage/security/accessibility/performance reports, the responsive screenshots above, defect/retest links, and independent Privacy-Legal, Security, Operations, API, Architecture, and UX/a11y reviews.

Passing lane evidence does not authorize M11 until Integration/root records the separate M10 acceptance decision. The M10 gate remains blocked by open C1/C2 ownership, placeholder/unreviewed privacy text, unresolved lifecycle conflict, indefinite or unsafe retention, untrusted proxy ambiguity, insecure/default HMAC/configuration, public reads, weak consent/source binding, anti-spam oracle, incorrect dual rate behavior, duplicate storage, PII leakage, unaudited/partial deletion, unsafe purge/restore, generated drift, multiple migration heads, parallel migration/generated/provider/shared writers, active earlier-milestone overlap, unsanitized evidence, failed Must requirement, missing independent retest, unresolved WCAG blocker, unexplained target regression, or any confirmed Critical/High finding.
