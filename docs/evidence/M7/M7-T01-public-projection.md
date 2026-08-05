# M7-T01-P - Public blog projection

## Result

`GET /api/v1/public/blog/posts` supports exact page pagination and allow-listed tag/category/search
filters with newest/oldest/title order. `GET /api/v1/public/blog/posts/{slug}` returns one effective
article or indistinguishable not-found. Both use frozen published revisions and PostgreSQL time.

The public schema includes title/excerpt/author, publication time, server reading time, SEO and
canonical inputs, public tag/category/related summaries, and sanitized HTML carrying source
checksum plus renderer policy provenance. It excludes CommonMark source, revision IDs/pointers,
creator/version/deletion data, hidden taxonomy/relations, future schedule facts, and media/storage
identifiers. Public caching remains revalidation-only at the current accepted boundary.

## Verification

The PostgreSQL repository gate proves future exclusion, published-revision facet isolation, hidden
related/taxonomy omission, and a fixed six statements per public page. Transport tests prove the
allow-list cannot accept internal mass assignment and OpenAPI carries no public source property.
The real API lifecycle confirms a draft/future article is absent, publication appears under its
public tag, draft content/taxonomy changes leave the live article byte/field-equivalent, and hiding
returns public 404.
