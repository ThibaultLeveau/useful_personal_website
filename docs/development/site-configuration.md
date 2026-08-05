# Site configuration architecture

M3 is a complete modular-monolith slice for profile, website settings, navigation, and footer.
Domain and application code lives under `backend/app/modules/{profile,site_settings,navigation}`;
SQLAlchemy records and adapters remain under `backend/app/infrastructure/database`; HTTP schemas
and routes translate through application facades and never import repositories directly.

## Persistence and transactions

Alembic revision `20260802_0004` creates the singleton aggregates and ordered child tables. The
runtime role receives ordinary DML through the existing permission-reconciliation flow but owns no
object. Repositories may flush and never commit; the unit of work commits the resource mutation,
idempotency result, and append-only audit fact together or rolls all of them back.

Profile and settings reads are one aggregate query each. Navigation uses two bounded queries (menu
plus all items). Footer uses at most three (footer, all columns, then all items). The child queries
use observed menu/parent/position and footer/column/position indexes; adding a child must not add a
query. Complete tree replacement is intentional because validation, order normalization, and audit
must be atomic.

## Public projection and frontend boundary

Public transport schemas are distinct types built from explicit domain projection functions. They
do not serialize administrator records and then redact fields. Public Server Components call the
generated `PublicSiteApi` only through `features/site-configuration/public-api.ts`, using a
server-only upstream origin, omitted credentials, 60-second revalidation, and scoped cache tags.
There is no frontend database dependency.

The public layout and pages also declare a route revalidation interval. This matters when an image
is built without an API: the resilient fallback is prerendered but becomes eligible for runtime
regeneration. Authenticated editor Server Actions validate the session, expire the relevant data
tag, and invalidate affected public routes so the first post-save read is fresh even when the
build-time fallback had no recorded tag dependency.

The public header is the only substantial public client island because it owns current-route state,
the responsive dialog, focus restoration, and scroll lock. Theme selectors are small client
islands. Profile content, site identity, navigation data, footer data, and metadata remain
server-rendered and appear in initial HTML with JavaScript disabled.

## Extending routes and settings

Add a core internal destination to the backend route catalog and its tests before allowing it in
navigation. Later published pages integrate through the documented published-page facade; they do
not query page tables from navigation validation.

New settings require an explicit typed field, validation and boundary tests, a safe public/private
decision, migration review where storage changes, OpenAPI regeneration, and UI/error mapping.
Never add generic key/value settings, script blobs, secret fields, arbitrary analytics payloads, or
storage/database configuration.

Profile image, logo, favicon, and social-image identifiers accept only ready M9 assets. The owner
save and canonical usage replacement share one transaction; arbitrary image URLs and fake upload
paths remain prohibited.

## Demo data

`seed-demo` is an explicit development operation, separate from migration, startup, and
administrator bootstrap. It writes fictional M3 site configuration and the M4 skills catalog in one
transaction, is idempotent, refuses production, and creates no administrator, credential, token,
session, private contact value, media object, relation target, or secret setting. See the container
runbook for invocation.
