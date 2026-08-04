# Media architecture and security

The media module owns asset, immutable variant, usage, ingestion, deletion, reconciliation, and storage-port
contracts. Owner modules retain their publication rules and transactionally replace canonical `media_usage`
rows through the port; media does not import owner ORM repositories. The database eligibility adapter then
rechecks the exact current public owner pointer before delivery.

Migration `20260802_0010` adds closed-state `media_asset`, `media_variant`, and `media_usage` tables plus
accepted owner foreign keys and revision media relations. Database checks and triggers reject non-ready
references and tombstoning an actively used asset. Repositories never commit; the application service owns
the transaction boundary. When an existing page-block reference is replaced, deletion is flushed before the
same unique role/position is inserted.

## Ingestion pipeline

1. Sanitize the user filename for display only and generate opaque UUID-sharded keys.
2. Stream into private quarantine with a hard byte bound and SHA-256.
3. Detect and fully decode JPEG, PNG, or WebP; reject mismatches, unsupported/animated content, excessive
   dimensions/pixels, malformed/trailing structures, and unsafe metadata cases.
4. Apply orientation/color handling, strip metadata, and re-encode the frozen fallback/WebP width catalog.
5. Store immutable objects, stat and checksum every promoted object, then commit `ready` metadata.
6. On any failure, keep the asset nondeliverable, record a stable safe code, and rely on idempotent cleanup
   and reconciliation for partial object failures.

`MediaStorage` has local and S3-compatible adapters with immutable put, bounded read, stat/list, and
idempotent delete behavior. Local storage is development/single-host only. Production settings reject it and
require an explicit private S3-compatible provider, HTTPS endpoint, region, bucket, managed prefix,
encryption, authentication source, and timeouts. Workload identity is preferred; credentials are environment
or secret-manager inputs, never website settings.

## Extending media

Adding a file format or provider is a security and operations change, not a registry-only edit. Add a real
decoder/encoder or adapter contract, update the closed domain/database catalogs and configuration validation,
extend hostile/failure corpora and migration tests, regenerate OpenAPI/client artifacts, and document backup,
restore, lifecycle, TLS, encryption, least privilege, and public-delivery consequences. Do not add SVG, a
public bucket, mutable user keys, arbitrary transform parameters, permanent signed URLs, or a fake scanner.
