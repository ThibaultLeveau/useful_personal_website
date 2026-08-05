# R1 Implementation Plan

## Planning contract

This plan converts the accepted requirements, architecture, ADRs, and UX specification into the requested delivery sequence `Milestone 0` through `Milestone 14`. Stable requirement IDs (`F1-*`, `F2-*`, `API-*`, `SEC-*`, `NFR-*`, `DOC-*`, `OSS-*`, `CHG-*`, `AI-*`) and acceptance IDs (`AC-*`) are never renumbered. The existing traceability matrix's historical `M01`-`M20` values are preserved as aliases in `milestone-plan.md`; delivery evidence records both the requested milestone (`M0`-`M14`) and the existing trace milestone(s).

The implementation remains a FastAPI/Next.js modular monolith in one repository. Work is delivered as vertical slices: invariant and service, migration and repository, versioned API, generated client, admin workflow, relevant public rendering, tests, documentation, and evidence. No slice closes on one layer alone (`NFR-018`, `AC-040`). F3/F4 and runtime AI infrastructure remain deferred.

## Delivery flow

1. **M0 establishes executable foundations and contracts.** Pin runtimes and package managers, create repository/application skeletons, configuration, PostgreSQL/Alembic baseline, test harnesses, container/task runner, CI, OpenAPI artifact/generator pipeline, documentation/governance skeleton, and architecture-boundary tests.
2. **M1-M2 establish security and API contracts.** Identity/session/bootstrap is first because all admin work depends on it. API envelopes, errors, pagination, concurrency, idempotency, request IDs, health, and generated-client checks stabilize before feature teams fan out.
3. **M3 establishes the public/admin shell.** Profile, site settings, navigation, footer, theme, and layout primitives provide the shared page chrome and editor patterns.
4. **M4-M12 deliver complete product slices.** Skills, experiences, projects, blog, pages/blocks, media, contact, tokens, and audit/system administration each close with backend, frontend, E2E, security, accessibility, API, and documentation evidence.
5. **M13 consolidates product quality.** Cross-device visual polish, complete states, onboarding/initial-content experience, SEO/performance, security, and manual accessibility reviews close gaps accumulated across slices.
6. **M14 validates a release candidate from clean environments.** The validator performs clean install/build/migrations, upgrade and restore tests, complete suites/reviews, traceability audit, screenshots, and release reporting.

## Contract-first dependency order

The minimum ordering is:

```text
runtime/config pins
  -> repository and app skeletons
  -> PostgreSQL/Alembic base + test database
  -> auth/session contract
  -> API envelope/error/pagination/concurrency conventions
  -> committed OpenAPI artifact + generated client
  -> shared public/admin shells
  -> independently owned vertical slices
  -> cross-slice relations/pages/media integration
  -> polish/security/a11y consolidation
  -> clean release validation
```

Before a frontend implementation starts for an endpoint, the endpoint's Pydantic schemas, operation ID, envelope, errors, authentication/security declaration, examples, and filter/sort catalog must be reviewed and committed. Before another backend module consumes a capability, the provider's application facade/port must be explicit; importing its repository or ORM type is prohibited.

## Parallel delivery lanes

M0 work is serialized where files overlap, then parallelized as follows after contracts exist:

| Lane | Safe work after prerequisite | Owned areas | Coordination boundary |
|---|---|---|---|
| Backend | Approved API/domain contract and migration slot | `backend/app/modules/<capability>`, capability tests, its migration | One migration owner/sequence at a time; peers use application facades only |
| Frontend | Committed OpenAPI artifact and regenerated client | `frontend/features/<capability>`, routes, components, stories/tests | Generated output is integration-owned; feature agents do not hand-edit it |
| Infrastructure | Runtime/config contract and stable commands | containers, Compose, CI, scripts, deployment docs | Does not change app contracts without routing back through the owning task |
| Integration | Backend schema is runnable | OpenAPI snapshot, generated client, contract/E2E fixtures | Sole owner of regeneration commits during concurrent slices |

Safe concurrent examples after M2: backend skills and frontend design-system primitives; backend profile/settings and infrastructure CI hardening; frontend work on an already generated project contract while backend works on the next independent contract. Unsafe concurrency includes two agents editing the same Alembic head, two generators updating the client, or page/media/project agents changing shared reference schemas without a coordinated integration task.

## OpenAPI generated-client workflow

1. Backend authors explicit Pydantic request/response models, stable operation IDs, `{data,meta}`/error envelopes, security schemes, examples, and declared error responses.
2. Contract tests start FastAPI and export deterministic `docs/api/openapi.json`; schema lint validates references, operation-ID uniqueness, envelope/security consistency, and generator compatibility.
3. A pinned generator version/config produces `frontend/src/generated/api` (exact path fixed by M0). Generated files carry a generated header and are never edited manually.
4. Frontend feature wrappers under `frontend/src/features/<feature>/api` map generated transport types to UI/domain view types and centralize cookie/CSRF/request-ID behavior. Upload streaming is the only planned handwritten transport and must reuse generated schemas.
5. CI regenerates from the committed OpenAPI artifact and fails on a diff. Backend contract changes and regenerated output land in the same integration change; breaking changes require CHG-002 handling.
6. Each slice adds a backend schema/contract test, a wrapper test, and at least one integration/E2E path through the generated client.

## Migration and data initialization order

Alembic revisions are linear until a deliberate branch/merge is approved. M0 creates the baseline/configuration; subsequent logical order is identity/session/rate-limit/audit foundations, shared settings/navigation/profile, skills, revision infrastructure plus experiences/projects/blog/pages, media/usage references, contacts, API tokens, and final operational indexes/constraints. If a later milestone needs a table earlier (for example audit at authentication), create the minimal durable schema early and extend it forward; never create a parallel temporary table.

Every migration must pass upgrade from empty, schema-model comparison, and (when it transforms existing data) previous-release upgrade with representative data. Use expand -> backfill/idempotent data command -> compatibility deploy -> contract for destructive changes. Production startup checks revision compatibility but never runs migrations; a release job runs exactly once before application rollout.

**Bootstrap and seed data are separate paths.** `bootstrap-admin` is security-sensitive, idempotent, refuses takeover when an administrator exists, consumes secret input without logging it, and sets `must_change_password`. `seed-demo` is development/test-only, deterministic and idempotent, creates non-secret sample content, never creates credentials/tokens, and is rejected in production mode. Application startup runs neither.

## Slice completion and gates

Each task uses the record in `task-catalog.md`. A milestone gate requires:

- all scheduled Must requirements implemented and linked to acceptance evidence;
- format, lint, static type, backend, frontend, integration, relevant E2E, migration, OpenAPI generation/diff, security, and accessibility checks passing;
- no confirmed Critical/High finding and no placeholder/mock production path;
- docs, ADR/change records, test inventory, and traceability evidence updated;
- visual/browser evidence for user-facing behavior and measured evidence for performance targets.

A target requirement that misses its threshold is not silently passed: record measurement, cause, disposition, owner, and approved follow-up. A blocked item rolls forward explicitly with impact; it cannot be hidden by marking the milestone complete.

## Corrective loop

Corrections require new evidence: failed test, reproducible defect, security/a11y/API finding, requirement gap, integration failure, or measured performance regression. Triage records the acceptance/requirement IDs, severity, reproduction, root-cause hypothesis, owner, and affected regression scope. Apply the smallest corrective task, rerun the failed check plus every impacted gate, and attach before/after evidence. Do not weaken tests, types, scanners, or thresholds to obtain green status.

Maximum attempts per root cause are five. After the fifth failed attempt, stop changes in that area, preserve diagnostics, document attempts and likely root cause, identify the safest next action, and continue only independent work. Critical/High security or release-blocking Must failures stop downstream release validation.

## Clean-release validation

M14 uses a fresh checkout/worktree, empty dependency caches where practical, newly built production images, a new PostgreSQL database and media store, and only published documentation/config examples. It verifies bootstrap, forced password change, seed separation, migration from empty, previous-release upgrade, backup/restore consistency, production startup/readiness, the full backend/frontend/E2E suites, OpenAPI regeneration with no diff, security/container/dependency scans, representative manual WCAG review, Lighthouse profiles, screenshots, repository hygiene, and every R1 Must row in `traceability-matrix.md` as `Verified` with durable evidence.

## Dispatch policy

The dispatcher selects only tasks whose dependencies are evidenced, reserves shared files (lockfiles, Alembic head, OpenAPI/generated client, global UI tokens, Compose/CI), and prefers a complete small slice over starting multiple incomplete layers. The first dispatch-ready tasks are `M0-T01` (toolchain/lock contract) and the non-overlapping governance/documentation portion of `M0-T02`; `M0-T02` consumes the pins before closure. Then `M0-T03` and `M0-T04` can establish backend/frontend skeletons in parallel, followed by coordinated database, contract, and Infrastructure lanes.
