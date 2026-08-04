# PostgreSQL Database Model

## Database conventions

- PostgreSQL is authoritative; every change is an Alembic migration (`NFR-011`).
- Primary keys are application-generated UUIDv7. Timestamps are `timestamptz` in UTC; date-only domain values are `date`.
- Tables use `created_at`, `updated_at`, and `version` where administrator concurrency matters. Database defaults use `CURRENT_TIMESTAMP`; application serialization is ISO 8601.
- Slugs and normalized names use unique indexes over `lower(value)`. User-facing order is `integer` with a scoped unique constraint.
- JSONB is used only for validated heterogeneous block config, safe audit metadata, and narrowly bounded settings fragments. Core queryable relationships and security state are relational.
- Foreign keys are explicit. `ON DELETE RESTRICT` is the default; owned draft children may use `CASCADE`; security/audit references generally use `SET NULL` plus stable actor snapshots.
- RLS is not the primary authorization mechanism in R1. Application authorization is mandatory; database roles still apply least privilege.

## Identity, sessions, tokens, and abuse controls

### `administrator`

`id`, `email`, `email_normalized`, `display_name`, `password_hash`, `must_change_password`, `is_active`, `password_changed_at`, timestamps, `version`.

Constraints/indexes: unique `email_normalized`; active lookup. R1 supports one active administrator by product policy, not a fragile database singleton constraint, so bootstrap remains operable and future migration is possible.

### `admin_session`

`id`, `administrator_id`, `token_digest`, `created_at`, `last_seen_at`, `idle_expires_at`, `absolute_expires_at`, `revoked_at`, `revocation_reason`, `user_agent_digest`, `ip_pseudonym`, `rotated_from_id`.

Only a SHA-256/HMAC digest of the random 256-bit session secret is stored. Unique digest; indexes on active expiry and administrator. Expiry/revocation is checked on every request. Stale rows are deleted by operator cleanup.

### `api_token`

`id`, `public_id`, `administrator_id`, `name`, `secret_digest`, `created_at`, `expires_at`, `last_used_at`, `revoked_at`, `rotated_from_id`, `version`.

### `api_token_scope`

`api_token_id`, `scope`; composite primary key. `scope` is constrained to the current catalog: `content:read`, `content:write`, `media:read`, `media:write`, `contacts:read`, `admin:read`. Unknown scopes are rejected by both domain validation and a migration-maintained database check/reference table. `public_id` is the safe selector/audit identifier; secret digests are never selected by admin list queries.

### `rate_limit_bucket`

`policy`, `subject_digest`, `window_started_at`, `count`, `blocked_until`, `updated_at`; composite primary key `(policy, subject_digest, window_started_at)`. Subjects are keyed HMACs of normalized identifier/IP combinations, not plaintext email/IP. Atomic upsert/increment implements low-volume R1 limits. Expired buckets are operator-cleaned.

## Public configuration

### `profile`

Singleton ID, complete profile fields, explicit per-field public flags (or a validated `public_field_set`), media FK, timestamps, version. Public query code maps an allow-listed projection and never serializes the row directly.

### `website_settings`

Singleton ID, site identity, locale IETF tag, IANA timezone, theme policy, SEO defaults, contact/social public data, public analytics identifiers, media FKs, timestamps, version. There are no columns for secret analytics credentials.

### Navigation/footer

`navigation_menu`, `navigation_item`, `footer`, `footer_column`, `footer_item`; items contain label, `link_kind`, validated destination, target, visibility, parent ID where applicable, position, timestamps/version. Unique sibling position and a depth check enforced in application/service tests; cycles are prevented by a recursive validation before write.

## Content tables

### Skills

- `skill_category` (M4): ID, name, slug, description, position, timestamps/version.
- `skill` (M4): ID, category ID, name, slug, description, proficiency label, nullable score, exact years, staged icon key, position, featured, visible, timestamps/version.
- `skill_project`, `skill_experience` remain planned for the owning M5/M6 revisioned providers. Their associations include the target revision ID, not merely the aggregate ID, so draft relations cannot leak; M4 creates no placeholder relation table.

Checks cover score 0–100 and years >= 0. Indexes cover category/visible/position, featured/visible/position, and lower slug.

### Revisioned aggregate pattern

`experience`, `project`, `post`, and `page` contain stable identity/slug, visibility, order/featured where relevant, `draft_revision_id`, `published_revision_id`, `publish_at`, `unpublished_at`, timestamps/version, and optional `deleted_at`. Each corresponding revision table contains `id`, aggregate FK, `revision_number`, content fields, `is_frozen`, `created_by`, timestamps. Unique `(aggregate_id, revision_number)`.

Circular pointer integrity is implemented with deferrable foreign keys or by adding revision pointers after both base and revision rows exist. An application invariant plus a database trigger/check migration (where practical) ensures a pointer references a revision belonging to the same aggregate. Frozen published revisions are immutable through repositories; database permissions/triggers may reinforce this after behavior stabilizes.

#### `experience_revision`

Company, company URL, role, employment/remote type, location, start/end dates, current flag, summaries, controlled Markdown detail, responsibilities/achievements structured as ordered child rows or validated arrays, and technologies. Check constraints enforce current/end-date and chronological rules.

#### `project_revision`

Name, short/full description, problem, solution, impact, architecture, URLs, project status, dates, cover media, SEO/canonical values. `project_screenshot` is ordered and revision-scoped. `project_skill`, `project_experience`, and `related_project` are revision-scoped association tables.

#### `post_revision`

Title, excerpt, controlled Markdown body, cover media, author display/reference, derived reading minutes, SEO/canonical values. `post_tag`, `post_category_link`, and `related_post` are revision-scoped. Tags/categories have stable normalized unique slugs.

#### `page_revision` and blocks

`page_revision`: title, description, SEO/canonical values and revision metadata.

`page_block`: ID, page revision FK, `block_type`, `schema_version`, position, visible, nullable title/subtitle/description, theme/layout variants, validated responsive JSON, validated `config JSONB`, timestamps. Unique `(page_revision_id, position)`; indexes on revision/order and block type.

`page_block_reference`: block ID, `reference_kind`, `target_id`, `role`, position; composite uniqueness prevents duplicate roles where prohibited. Because polymorphic SQL foreign keys cannot enforce all target kinds, the block registry resolves each kind through module application facades at save and publish time. Media references are additionally materialized in `media_usage` for deletion protection.

## Media

### `media_asset`

`id`, generated `storage_key`, storage backend identifier, original filename sanitized for display only, detected MIME, byte size, width, height, checksum SHA-256, alt text, caption, status (`pending`, `ready`, `quarantined`), timestamps/version, optional deleted timestamp. Unique storage key; checksum and search indexes. Upload streams to a temporary/quarantine key, validates and extracts metadata, creates DB metadata and promotes to the final immutable key. Compensating cleanup handles storage failure around the database transaction.

### `media_usage`

`media_id`, `owner_type`, `owner_id`, `field`, `owner_revision_id`, `is_active`, timestamps; composite unique on usage identity and indexes on active media. Usage is rebuilt transactionally whenever an owning aggregate changes. Deletion locks the media row and confirms no active usage to avoid a check/delete race.

## Contacts and audit

### `contact_submission`

ID, name, normalized email, subject, encrypted-at-rest expectations delegated to PostgreSQL/disk infrastructure, message, consent timestamp, consent policy version, source, state, read/archive timestamps, created/updated timestamps, version. Indexes cover state/created time and admin filters. There is no public listing foreign path. Application logs never bind body/email values.

### `audit_entry`

ID, event type, actor type (`administrator`, `api_token`, `system`, `anonymous`), nullable actor IDs, safe actor label snapshot, resource type/ID, request ID, occurred-at UTC, outcome, IP pseudonym, `metadata JSONB`, schema version. It has no `updated_at` and no update API. Indexes cover occurred time descending, event type/time, actor/time, resource/time, and request ID. Database application roles receive `INSERT` and `SELECT` but not `UPDATE`; deletion is restricted to a separately authorized retention command/operator role.

## Publication-safe query indexes

Partial/composite indexes support frequent public predicates:

- aggregate `(publish_at desc, id)` where `published_revision_id is not null and visible and deleted_at is null`;
- page/post/project lower slug where not deleted;
- skills `(category_id, position)` where visible;
- featured project/skill `(featured, position)` where visible;
- tags/categories normalized slug;
- contacts `(state, created_at desc)`;
- audit `(occurred_at desc, id desc)`.

Actual query plans are verified with representative data before release (`AC-034`). Indexes are not added speculatively beyond observed/filter contract needs.

## Migration and operational rules

Migrations are forward-only in production practice, deterministic, and safe from an empty database. Destructive transformations use expand/migrate/contract steps and backup verification. Application startup checks that the database revision is compatible but does not mutate it. A dedicated migration identity owns DDL; the runtime identity receives only needed DML. Test CI runs upgrade-from-empty and, for important changes, upgrade from the previous release snapshot.

PostgreSQL backups plus object storage are a single recovery set. Restore testing must verify media metadata/object consistency. Retention commands use batches, stable cutoffs, dry-run output, and audit their aggregate counts without including private payloads.
