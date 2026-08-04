# Pages API

Pages are exposed under `/api/v1/admin/pages` and `/api/v1/public/pages`. The generated OpenAPI contract is authoritative; examples here summarize the lifecycle rather than replacing it.

Administrator operations cover the registry, paginated list, create/get/replace/delete, custom-page duplication, block add/replace/duplicate/visibility/delete/complete reorder, private preview, canonical export, publish, reschedule, and unpublish. Unsafe operations require an authenticated administrator session, trusted `Origin`, CSRF header, current `If-Match`, and an idempotency key on retry-sensitive commands. Successful aggregates return an `ETag` derived from their version.

Block input is a closed discriminator union on `block_type`. It contains exactly 19 version-1 kinds. Every kind has a strict config model; unknown fields, versions, presentation tokens, reference forms, and unsafe URLs fail validation. References are derived server-side from typed configs and stored in normalized rows. Clients cannot assign reference rows or renderer keys.

`GET /api/v1/public/pages/home` and `GET /api/v1/public/pages/{slug}` expose only the effective visible published revision. Missing, hidden, future, unpublished, deleted, and reserved targets are indistinguishable `404` results. `GET /api/v1/public/pages` returns a bounded route summary for sitemap composition. Public page data excludes versions, draft pointers, audit facts, author identities, raw JSON shells, source CommonMark, media storage details, and unresolved private targets.

Rich-text public config contains only sanitized HTML plus policy name, policy version, and source checksum. The browser’s only HTML sink accepts that generated safe DTO. Image kinds require a ready media asset and expose only responsive delivery descriptors and authored per-use metadata.

Publishing and scheduling use immutable revisions and database time. A publish copies a new mutable draft; edits cannot mutate the frozen live tree. Complete reorder is atomic. Provider collections are bounded and batched, and optional unavailable targets are omitted rather than widening visibility.

See `docs/api/openapi.json` for schemas, response envelopes, operation IDs, error codes, pagination, and exact headers.
