# Skills vertical-slice architecture

M4 implements skills as a modular-monolith slice. Persistence-neutral invariants, public
projections, application commands, and `SkillReferenceFacade` live in
`backend/app/modules/skills`. SQLAlchemy records/repositories and transaction composition remain in
`backend/app/infrastructure/database`; HTTP schemas and routes translate through the service and do
not import repositories.

## Persistence and query shape

Alembic revision `20260802_0005` is the sole head and descends directly from `0004`. It creates
`skill_category` and `skill` with database checks for normalized slugs, score/year ranges, versions,
positions, and icon keys; deferrable unique order constraints make atomic reorder possible. The
skill-to-category foreign key uses `RESTRICT`, while application deletion normalizes remaining
positions.

The public list is three bounded SQL statements regardless of item count: an exact count, one
joined page, and the ordered category catalog used for grouping. The admin list is count plus page.
Purpose-built indexes cover global category order, per-category skill order, visible category/order,
visible featured/order, and case-insensitive slug uniqueness. On the five-row demo catalog,
PostgreSQL correctly chose two tiny sequential scans and a hash join (0.605 ms, eight shared-buffer
hits); forcing an index on that cardinality would be slower. The index set is retained for production
growth and is migration-tested.

## Transactions and concurrency

Repositories flush and never commit. `SkillsService` owns authorization, validation, locks,
idempotency, optimistic concurrency, audit facts, and commit. Complete order payloads must contain
exactly the current IDs once each. Resource mutation, order normalization, idempotency completion,
and append-only audit facts commit together or roll back together.

Infrastructure maps PostgreSQL uniqueness failures through structured driver diagnostics and never
parses database error text. Public projections are separate immutable shapes with no IDs, versions,
timestamps, hidden rows, or administrator metadata.

## Frontend and cache boundary

`/skills` is a Server Component. Its server-only wrapper uses generated `PublicSkillsApi`, sends no
browser credential, and applies a bounded cache tag/revalidation policy. Search, category, and
featured filters come from URL parameters; the page ships only the small existing header/theme
client islands. `/admin/skills` is a protected client workspace that uses only generated
`SkillsApi` methods through `admin-api.ts`, including cookie CSRF, Origin, ETags, idempotency keys,
pagination, and typed queries.

The administrator reloads the active filtered page after skill create/update/delete so category
reassignment and pagination cannot leave stale privileged state. Reorder is disabled unless the UI
holds the full, unfiltered position view; ordinary edits remain enabled on filtered pages.

## Future relation consumers

M4 exposes `SkillReferenceFacade.reference_summaries(ids)`. It rejects duplicates and missing
targets and returns only stable ID/name/slug/visibility facts in caller order. M5 and M6 must depend
on that application facade, never import skills repositories or ORM records, and own their
revision-scoped relation rows. Until those providers exist, non-empty relation writes fail closed and
the UI presents a disabled explanatory fieldset.

Regenerate the contract with the locked workflow in [API client generation](api-client.md). The M4
aggregate artifact digest and verification commands are recorded in [M4 backend evidence](../evidence/M4/M4-T01-backend.md).
