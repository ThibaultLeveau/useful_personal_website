# Milestone 9 Dispatch

## Dispatcher status

This document prepares `M9-T01` through `M9-T03`. It does not release implementation, record acceptance, or authorize M10.

M9 remains blocked until Integration/root records the separate M8 acceptance decision and staged-media handoff, confirms the sole database head, resolves production storage ownership decisions, and releases every shared/provider surface required below.

| Task     | Current state | Release condition                                                                                                                             |
| -------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `M9-T01` | Blocked       | M8 passes; one Alembic head is `20260802_0009`; storage/owner/provider gates S0-S2 pass; sole `0010` reservation is recorded.                 |
| `M9-T02` | Blocked       | `M9-T01` domain/storage/persistence/API evidence passes and media contract freeze S4 is recorded with a clean generated client.               |
| `M9-T03` | Blocked       | `M9-T02` library/owner/public integration evidence passes, coordinated backup/restore inputs exist, and integration readiness S5 is recorded. |

M9 maps to trace milestone `M13` and delivers the Media vertical slice: secure image ingestion, private replaceable storage adapters, metadata/variants, active usage, deletion/reconciliation, admin library/picker, activation of staged owner references, authorized optimized public delivery, contract generation, tests, documentation, and evidence. It does not authorize contact, tokens, arbitrary files/video/audio/SVG, a public bucket, a worker/scheduler, speculative malware/AI services, or acceptance of a later milestone.

## Strict dependency and owner-decision gates

### S0 - Foundation, deployment, and operator decision record

Before any M9 write, Integration/root confirms accepted foundation contracts for authentication/authorization, CSRF/Origin, request IDs, rate limits, audit facts, API envelopes/errors/pagination/filter/sort, `ETag`/`If-Match`, idempotency, generated clients, database UoW, configuration validation, same-origin edge, security headers, and production startup/readiness.

The deployment owner must assign and record the following decisions. Values may remain open while generic adapters are implemented, but production acceptance and S5 remain blocked; code must not substitute defaults:

| Decision                            | Required owner record                                                                                         | Forbidden fallback                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Production storage service/provider | Named provider/service class, compatibility target, account/project owner, support/escalation owner           | Local filesystem, development MinIO/localhost, public bucket, or an unreviewed vendor          |
| Region and residency                | Exact region, residency/legal owner, transfer/replication decision                                            | SDK implicit region, `us-east-1` guess, cross-region replication by default                    |
| Bucket/container and namespace      | Exact private bucket/container, environment/prefix isolation, ownership and deletion policy                   | Shared unscoped bucket, user-controlled prefix, world-readable ACL/policy                      |
| Authentication and authorization    | Workload identity or secret-manager reference, rotation owner, least-privilege actions on exact bucket/prefix | Embedded/example/static default credentials, browser credentials, wildcard account permissions |
| Network and TLS                     | Private endpoint/egress policy, exact HTTPS endpoint, certificate verification, proxy/DNS owner               | Plain HTTP, disabled verification, arbitrary request-supplied endpoint                         |
| Encryption                          | At-rest mode and key/KMS owner/rotation/recovery decision                                                     | Provider-unknown or disabled encryption in production                                          |
| Object behavior                     | Versioning/lifecycle/multipart-abort policy, immutability/no-overwrite semantics, checksum support            | Mutable public filenames or destructive lifecycle shorter than recovery policy                 |
| Delivery                            | Backend proxy or short-lived signed redirect, maximum signature/cache lifetime, CDN/purge owner               | Permanent signed URL, public ACL, origin key in ordinary public metadata                       |
| Backup/restore                      | Coordinated PostgreSQL/object RPO/RTO, snapshot mechanism, manifest/integrity procedure, drill owner/date     | Database-only backup, object-only backup, undocumented best-effort restore                     |

Production configuration fails closed at startup/readiness when the selected adapter lacks required provider/region/bucket/endpoint/encryption/auth configuration. Health output exposes only a safe dependency category/status, never endpoint, bucket, region if sensitive, credentials, key IDs, or object keys. No provider decision is inferred from a development Compose volume.

Development may explicitly select the local adapter. Its absolute media root is configuration-owned, resolves beneath the dedicated private mounted volume, is created with least permissions by the deployment path, and is rejected in production mode. User filenames and request values never form directories or keys.

### S1 - Separate M8 acceptance and media reference registry handoff

Integration/root must record the separate M8 acceptance decision and prove:

- exactly one Alembic head exists at `20260802_0009` from `20260802_0009_pages_blocks.py`;
- the M8 catalog discrepancy is resolved, its registry/reference extraction/serializer/public renderer contracts pass, and no unresolved Must failure is being deferred into media;
- M3 profile/settings/navigation/footer, M6 project, M7 post, and M8 page/block owners publish exact staged media field/role/cardinality/alt/caption/focal/ordering and revision-ownership handoff manifests;
- owner application facades can validate/mutate draft or singleton references and expose active draft/current-published usage facts without media importing owner repositories/ORM;
- the M8 migration/module/API/frontend/E2E/evidence, shared configuration/router/generated/public-image/render files required by M9 are released;
- no unresolved prior defect can corrupt revision immutability, public eligibility, reference extraction, cache privacy, metadata, or generated contracts.

M4 skill-icon or another earlier staged media field joins `0010` only if its accepted handoff manifest exists at S1; it is not silently inferred or omitted. New owner fields outside accepted SPEC require CHG-002.

### S2 - Storage threat, limits, and recovery freeze prerequisites

Before implementation fan-out, Security/Operations/Integration record:

- accepted R1 input formats are JPEG, PNG, and WebP; GIF remains disabled, SVG and all other formats are rejected;
- hard upload limit 10 MiB, each dimension <=6000 px, total pixels <=36 MP, plus decoder memory/time/frame/nesting limits frozen at S3;
- original-byte retention/private-access policy, metadata stripping policy, derivative format/quality/width catalog, color/orientation handling, checksum/deduplication policy, and quarantine retention/cutoff;
- upload and delivery rate/timeout/concurrency limits, temporary-space budget, failure behavior, and operator alert ownership;
- reconciliation dry-run/apply authority, grace window, batch/lease semantics, evidence redaction, and coordinated backup/restore protocol owner.

An unselected optional antivirus service is not simulated. Decoder/magic/structural validation is not documented as malware detection. Adding scanning/quarantine services later requires a real provider contract and threat/operations review.

## Active-file exclusions and ownership

### Earlier milestone/provider files

M9 must not edit, move, delete, format, regenerate, or claim ownership of M1-M2 auth/common/API/health/client files, M3-M8 provider modules/routes/frontends/tests/evidence, migrations `0002` through `0009`, or shared accepted contracts until S1 and a named owner-integration window.

Media never imports profile/settings/navigation/skills/experience/project/blog/page repositories or ORM. Owner modules call `MediaReferenceFacade`/usage commands, or expose owner-side reference facts through application ports. Reverse usage is materialized through controlled facts/registry roles, not cross-module table crawling.

### Infrastructure/shared files

M9 feature lanes must not edit `backend/migrations/env.py`, shared database runtime/session/UoW/readiness or database-role/grant files, existing `infrastructure/**`, Compose/environment/Docker files, root manifests/locks, task-runner/CI/scanner/deployment files, security-header configuration, or current Infrastructure evidence. Storage/config/volume/backup/permission work receives its own Infrastructure owner window after S0; media feature agents only provide reviewed requirements and adapter/application code.

### Integration/root single-writer surfaces

Integration/root alone writes `docs/api/openapi.json`, `frontend/src/generated/api/**`, generator/export/validator configuration, final cross-owner usage/contract/trace reports, and final M9 decisions. Requirements, architecture, ADR, UX, prior dispatches, and planning sources remain read-only unless an approved change is separately dispatched.

The migration, storage configuration schema, local/S3 adapter registration, usage role registry, generated artifacts, backend router/model composition, central upload wrapper, public image component/loader, metadata/owner integration, Compose volume, `.env` examples, backup docs/scripts, and shared fixtures/corpus each have exactly one named writer window. No parallel adapter, migration, generated, usage-registry, or owner-file writers are allowed.

## Owner-safe M9 lanes

| Stage                                     | Owner                          | Exclusive write area                                                                                                                                                                                                                                                                                                    | Gate and handoff                                                                                                                                                                |
| ----------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M9-T01-D` media domain/application       | Backend Media Domain Agent     | Media asset/variant/usage lifecycle, upload/delete/replace/reconcile commands, validation/metadata/alt/caption policies, storage/reference ports, DTOs/errors/audit facts, unit/service tests under `backend/app/modules/media/**`; `docs/evidence/M9/M9-T01-domain.md`. Excludes persistence/delivery filenames below. | Starts after S2. Produces S3. No adapter/migration/artifact/frontend/Infrastructure/provider files or final acceptance.                                                         |
| `M9-T01-S` storage and image security     | Storage Adapter/Security Agent | Dedicated local and S3-compatible adapters, streaming/quarantine/sniff/decode/re-encode/checksum/variant services, malicious corpus and adapter/failure tests in newly reserved backend infrastructure paths; `docs/evidence/M9/M9-T01-storage.md`.                                                                     | Starts after S3. Does not edit global config/Compose/secrets/CI; those requirements go to Infrastructure. One implementation of `MediaStorage`, no vendor logic in domain.      |
| `M9-T01-R` persistence/usage/reconcile    | Backend Persistence Agent      | Dedicated media ORM/repositories, usage registry adapter, deletion locks, reconciliation query adapters/command implementation and PostgreSQL tests in media-owned files; `docs/evidence/M9/M9-T01-persistence.md`.                                                                                                     | Starts after S3 and may run beside T01-S only in disjoint files. Repositories never commit; command wiring is a later single-writer handoff.                                    |
| `M9-T01-M` sole migration                 | Backend Migration Agent        | `backend/migrations/versions/20260802_0010_media.py`, dedicated migration fixtures/tests, and `docs/evidence/M9/M9-T01-migration.md`.                                                                                                                                                                                   | Starts after S3 and Integration/root reservation. Serialized with model/owner-field registration; no other M9 revision or merge head.                                           |
| `M9-T01-A` admin/delivery API             | Backend Media API Agent        | Dedicated admin upload/list/detail/metadata/usage/replace/delete/preview/reconcile-status and public/admin delivery route/schema modules, API/security tests, and `docs/evidence/M9/M9-T01-api.md`.                                                                                                                     | Starts after S3; calls application services only. Public delivery is separate from admin/original access. Does not generate client artifacts.                                   |
| `M9-T01-I` OpenAPI/client generation      | Integration/root               | Cross-lane contract/security/storage reports, `docs/api/openapi.json`, `frontend/src/generated/api/**`, deterministic generation evidence, S4, and final T01 decision.                                                                                                                                                  | Starts after D/S/R/M/A evidence. Sole artifact/generated-code writer; all other lanes pause those surfaces.                                                                     |
| `M9-T02-L` admin library/picker frontend  | Frontend Media Agent           | `frontend/src/features/media/**`, `/admin/media`, media list/grid/upload/metadata/usage/delete/picker components/stories/tests/wrappers, and `docs/evidence/M9/M9-T02-library.md`.                                                                                                                                      | Starts after S4. Progress transport uses the Integration-approved wrapper; no duplicate API types/auth/error logic.                                                             |
| `M9-T02-O3` M3 owner activation           | M3 Provider Owner              | Only released M3 profile/settings/navigation/footer backend/frontend fields, forms, projections, tests, and `docs/evidence/M9/M9-T02-owner-m3.md` named in S1.                                                                                                                                                          | Serialized after S4. Activates exact accepted roles through media facade/usage commands; no other M3 behavior or migration.                                                     |
| `M9-T02-O6` project owner activation      | M6 Project Owner               | Only released project cover/screenshot revision fields, gallery/editor/public renderer/query/tests and `docs/evidence/M9/M9-T02-owner-m6.md` named in S1.                                                                                                                                                               | Serialized after S4. Existing frozen revisions remain immutable; activation uses a new draft/copy-on-write publication path.                                                    |
| `M9-T02-O7` blog owner activation         | M7 Blog Owner                  | Only released post cover reference/editor/public article/list/query/tests and `docs/evidence/M9/M9-T02-owner-m7.md` named in S1.                                                                                                                                                                                        | Serialized after S4. CommonMark policy remains unchanged; arbitrary inline image URLs stay prohibited unless a separately approved media-reference syntax exists.               |
| `M9-T02-O8` page/block owner activation   | M8 Page Registry Owner         | Only released media reference roles/config schemas/registry fixtures, image renderers/builder integration/queries/tests and `docs/evidence/M9/M9-T02-owner-m8.md` named in S1.                                                                                                                                          | Serialized after S4. Registry version/adapter impact is explicit; no silent reinterpretation or mutation of frozen page revisions.                                              |
| `M9-T02-P` public image delivery frontend | Frontend Public Image Agent    | One shared optimized public image component/loader in an Integration-reserved file, media-specific fallback/tests/stories, performance/layout evidence, and `docs/evidence/M9/M9-T02-public.md`.                                                                                                                        | Starts after S4 and owner DTO fixtures. It accepts public delivery DTOs only, never keys/buckets/admin URLs. Shared renderer edits remain serialized with O3/O6/O7/O8.          |
| `M9-T03-I` integration/E2E/docs           | Integration/root               | Adapter/owner/API/browser/failure/backup-restore fixtures/specs, sanitized reports/screenshots, user/API/developer/operator docs, traceability links, `docs/evidence/M9/M9-T03.md`, S5, and final M9 gate record.                                                                                                       | Starts after all T02 owners pass. Defects return to owners. It does not start M10 or mark M9 accepted without independent security/operations review and owner-decision record. |

Owner activation lanes do not run in parallel when they touch shared media wrappers/renderers/fixtures/router/model composition. Each provider owns its semantic validation/publication transaction; media owns storage identity, readiness, usage contract, and delivery authorization.

## Sole linear migration policy

Integration/root reserves exactly:

```text
file: backend/migrations/versions/20260802_0010_media.py
revision: 20260802_0010
down_revision: 20260802_0009
owner: M9-T01-M only
```

The revision implements only the accepted S3 schema and staged owner activation:

- `media_asset`: opaque ID, generated unique immutable original storage key, closed backend identifier, sanitized display filename only, detected MIME, byte size, width/height, SHA-256 checksum, bounded default alt/caption, closed `pending`/`quarantined`/`ready` status, timestamps/version, and nullable deletion tombstone;
- `media_variant`: asset FK, closed purpose/format/width-density key, generated unique immutable storage key, detected MIME, byte size, dimensions, checksum, timestamps, and uniqueness on asset+variant identity;
- `media_usage`: asset FK, closed owner type/field/role, stable owner ID, nullable owner revision/block ID as required, active flag, ordered position, per-use meaningful/decorative intent, bounded alt/caption override/focal/crop tokens where applicable, timestamps/version, and composite uniqueness/indexes;
- upload/reconciliation indexes for status/age/checksum/search, active usage/delete checks, public delivery lookup, and owner usage pages based on measured query contracts;
- nullable FK/reference structures for the exact S1 handoffs: M3 singleton fields, M6 revision-scoped project cover/ordered screenshots, M7 revision-scoped post cover, and M8 page-block media references/usage materialization; other handoffs only when accepted at S1;
- no object bytes, presigned URL, credential/endpoint/bucket, raw EXIF, arbitrary metadata JSON, SVG/GIF/file kind, provider mirror data, contact/token table, worker/outbox, or second migration.

Where prior frozen revision tables gain nullable media references, `0010` does not backfill or mutate existing frozen content. Existing staged null/unresolved intent is converted only by a reviewed deterministic rule with validation evidence; otherwise it remains absent and an administrator creates a new draft revision to select media. No dangling staged UUID becomes a valid asset by coincidence.

Owner-table FK direction is owner -> `media_asset` with `ON DELETE RESTRICT`, or owner references materialize solely through the accepted normalized usage/reference model. `media_usage` is not user-authored generic polymorphic input: closed registry roles and owner application commands create it. Database constraints/indexes enforce shape/uniqueness; application ports validate owner/revision/publication semantics.

Migration evidence requires empty upgrade, upgrade from accepted `0009` with representative M3/M6/M7/M8 staged data, current/head equality, one-head proof, schema/model parity, constraints/indexes/FKs, no frozen-row mutation, owner-role registry parity, ready-only references, usage rebuild comparison, deletion restrict/race support, rollback/UoW, runtime/migration role isolation, and production startup without migration/reconcile/upload. Schema changes after S3 return to the sole migration owner; no merge head.

## Storage abstraction and configuration contract

### `MediaStorage` port

The inward-facing asynchronous/bounded port freezes typed operations for quarantine write, validated-object promotion/copy, open/read, stat/checksum, delete, existence/list-by-managed-prefix for reconciliation, and optional short-lived signed delivery. Results use controlled errors/capabilities; they do not leak SDK exception text, endpoint, bucket, credentials, signed query parameters, or arbitrary provider metadata.

- Keys are application-generated UUID-based opaque values under closed environment/state/purpose prefixes. Original filename, owner ID, email, slug, MIME extension, checksum, path input, or request header never forms a key.
- Final original/variant keys are immutable and created with conditional no-overwrite semantics. “Replace” creates a new asset and owner reference swap; it never overwrites bytes/key/checksum for an existing asset.
- Quarantine keys are unguessable, outside all delivery namespaces, private, short-lived, and never returned to clients. Local and S3 adapters implement identical path/key normalization and traversal defenses.
- Local adapter uses safe descriptor/path operations beneath the resolved root, rejects symlink/reparse escape, uses atomic same-volume rename where supported, fsync/close semantics as frozen at S3, and private permissions. It is development/single-host only.
- S3-compatible adapter requires explicit provider capabilities and S0 config, private bucket/public-access block, TLS verification, least privilege, server-side encryption, checksum/conditional operations, bounded timeouts/retries with jitter, multipart abort, and no browser-facing credentials. It never enables public ACL or trusts request-provided bucket/endpoint/region.
- Adapter contract tests run against local and the selected compatible S3 test service/provider behavior, including pagination, missing object, transient/timeout/permission/quota, partial stream, promotion conflict, checksum mismatch, delete retry, signed expiry, and list-prefix isolation.

### Fail-closed configuration

- Adapter selection is a closed enum. Local requires an explicit nonproduction environment and root. S3-compatible requires explicit endpoint/provider mode, region, bucket, auth source, encryption mode, managed prefix, delivery mode/TTL, timeouts, and capability checks.
- Secrets are injected by the deployment secret manager/workload identity, never website settings, `NEXT_PUBLIC_*`, image URLs, logs, traces, health, OpenAPI examples, `.env.example` values, screenshots, or repository evidence.
- Startup validates safe syntax/mode but does not create buckets, weaken policies, migrate data, or perform destructive reconciliation. Readiness performs a bounded least-privilege capability probe selected at S3 without revealing configuration; liveness remains dependency-free.
- Development examples use unmistakably synthetic values and local-only selection. Production mode has no fallback region, bucket, endpoint, credential, encryption, signing, or local root.

## Secure upload, validation, variants, and lifecycle contract

### Streaming quarantine and validation

1. Authenticate/authorize the actor, enforce CSRF/Origin and the media upload rate/concurrency policy, validate multipart structure/declared length where present, and allocate an unguessable upload attempt/idempotency scope.
2. Stream once to a quarantine key with a hard 10 MiB cap independent of `Content-Length`, bounded chunks/time/temp space, incremental SHA-256, cancellation handling, and no full-file request buffering.
3. Inspect magic bytes/container structure and decoder-detected format; declared MIME/extension are hints only. Require exact allowed JPEG/PNG/WebP agreement under S3 policy and reject empty/truncated/malformed/multi-image/animated/ambiguous inputs.
4. Fully decode under hard pixel/dimension/frame/memory/time/nesting limits, apply orientation safely, validate color/profile constraints, reject decompression/image bombs and parser errors, and ensure no trailing/embedded executable/polyglot payload survives accepted structural checks.
5. Explicitly reject GIF, SVG/XML, HTML, PDF, archives, video/audio, scripts, executable headers, double-extension tricks, mismatched/polyglot formats, external-resource references, and unsupported chunks/features. Never rasterize SVG in R1.
6. Extract only allow-listed technical metadata; do not persist/publish raw EXIF/IPTC/XMP, GPS, thumbnails, comments, device/author identifiers, paths, or arbitrary profiles. Re-encode public variants with metadata stripped and deterministic bounded parameters.
7. Create bounded responsive variants frozen at S3 (including WebP and a safe compatible fallback where required), preserving aspect ratio and recording exact dimensions/bytes/checksum. Upscaling is prohibited; orientation and color output are consistent.
8. Create/update pending DB metadata and promote immutable original/variants according to the failure-safe protocol; mark `ready` only after every required object/stat/checksum exists. Only `ready`, nondeleted assets can be selected or delivered.

Filename sanitation produces a bounded human display label only: strip paths/control/bidi-dangerous characters, normalize Unicode, collapse whitespace, and supply a generic label if empty. It is not a key, URL, alt text, or trust signal. Error/audit/log output never reflects malicious bytes or an unsafe filename unescaped.

### Alt, caption, and accessible-use rules

- Asset default alt/caption are bounded plain text conveniences, never derived from filename, OCR, AI, EXIF, or page title. Caption is optional and not a substitute for alt.
- Every owner usage explicitly chooses `meaningful` or `decorative`. Meaningful use requires nonblank contextual per-use alt or an explicitly accepted asset default; decorative use emits empty `alt` and presentation semantics and cannot carry conflicting descriptive alt.
- The same asset may have different per-use alt/caption/focal/crop intent. Public delivery DTOs contain the effective use-specific text/intent and dimensions, not storage metadata. Editor validation blocks missing meaningful alt at owner save/publish as frozen by that owner.
- Captions are associated with the rendered image/figure. Project galleries expose image position and named navigation. No filename, storage key, checksum, MIME string, or generic “image” becomes alt text.

### Non-atomic DB/object failure protocol

- Upload uses a recorded pending asset/attempt and quarantine objects. Promotion is conditional and idempotent. Required objects are verified before the short DB transaction marks ready; failure leaves no ready row pointing at missing content.
- Every boundary has compensation: canceled/rejected uploads remove or age out quarantine; DB failure after promotion records/reconciles managed orphan candidates; promotion/variant failure keeps the asset nonready and schedules no public path; retry with the same idempotency key cannot create duplicate ready assets.
- Automatic checksum deduplication, if selected at S3, never merges logical assets/usages/alt metadata across actors without explicit semantics. Otherwise checksum is integrity/search evidence only.
- No request performs an unbounded bucket scan. Reconciliation is an explicit idempotent operator command, dry-run by default, paginated/batched under a stable cutoff/grace period and optional lease. Apply mode requires explicit authority/confirmation.
- Reconciliation compares DB pending/ready/deleted rows, variant manifests, managed-prefix objects, checksums, and usage rebuild facts. It reports stale quarantine, orphan objects, missing/corrupt originals/variants, incomplete promotions/deletes, and usage drift with safe asset IDs/counts—not credentials, signed URLs, private content, keys in public evidence, or raw filenames.
- Repair actions quarantine/restore/rebuild/delete only according to a reviewed class-specific policy; uncertain objects are not silently destroyed. Runs are audited with cutoff/mode/aggregate counts/outcome/request/run ID and produce sanitized operator evidence.

## Usage registry, replacement, deletion, and audit contract

### Active usage and deferred owner activation

- `MediaReferenceFacade` validates ready/nondeleted assets, returns admin picker summaries or public-safe delivery descriptors according to actor/context, and never exposes storage adapter/backend/key/bucket/checksum/quarantine/deletion internals.
- Owner save/publish/unpublish/delete/visibility commands rebuild their usage rows transactionally from canonical owner references. Active usage covers mutable active drafts, current frozen published revisions, M3 singleton/direct fields, navigation/footer, and direct entity/block references as frozen at S3.
- Draft and published usages remain distinct by owner revision. Editing a project/post/page draft cannot change live delivery/alt/crop. Publishing activates the new frozen revision and deactivates the superseded live usage atomically while retaining any still-active draft usage.
- M3 activation covers only accepted profile/settings/navigation/footer roles. M6 activates project cover and ordered screenshots. M7 activates post cover. M8 activates block media roles and turns accepted unresolved draft intent into validated selected assets only through an administrator command; no ID coincidence/backfill.
- Usage location summaries are allow-listed safe admin navigation labels/routes. They never include draft prose, contact/private values, raw config, hidden target details beyond the authorized owner, or storage values. Unauthorized callers cannot learn whether an asset or usage exists.

### Replace and delete

- Asset metadata update requires `If-Match`; absent is 428 and stale conflicts. Replacing bytes uploads a new ready asset, then each owner changes its reference under the owner aggregate `If-Match`/copy-on-write rules. No global silent replacement of all usages exists.
- Delete is explicit and irreversible for ready/unreferenced assets. The application starts a transaction, locks the media row `FOR UPDATE`, rejects nonready/already-deleted state, checks active usage under the same lock/order protocol, and returns `MEDIA_IN_USE` with authorized safe usage summaries if any exist.
- Owner reference creation/activation locks or validates the same asset in the documented lock order so it cannot race between delete check and tombstone. Deadlock/serialization retries are bounded and tested.
- If unused, deletion writes an immediate DB tombstone/audit intent so new selection and public/admin delivery fail, commits, then idempotently removes original/variant objects. Object deletion failure leaves a recoverable tombstone for reconciliation/retry, never a row that appears ready/public while bytes are partially missing.
- Completion records safe audit outcome. A tombstoned asset is omitted from lists by default but remains available to authorized reconciliation/audit paths. Retention/purge of tombstones and quarantine is an explicit operator policy, not startup cleanup.
- Audit covers upload accepted/rejected/quarantined/ready, metadata change, selection/reference activation, replacement reference change, delete blocked/requested/completed/failed, reconciliation, and delivery authorization failures with safe actor/asset/owner/request/outcome/reason/size-dimension-format categories. It never stores bytes, filenames if unsafe, alt/caption, storage keys, endpoints, signed URLs, credentials, EXIF, or private owner content.

## Admin/public API and delivery contract

### Admin API

- `/api/v1/admin/media` provides multipart upload, paginated/searchable/filterable/sortable list, ready detail, metadata update, authorized preview/content, usage list, replace-as-new flow, and delete. Reconciliation apply remains an operator command, not a general browser endpoint; UI may show safe last-run status only if authorized.
- List filters/sorts are a closed catalog for detected format, readiness, usage state, dimensions/size ranges, created/updated time, display filename/alt search, and deterministic ID tie-breaker. Bound expressions reject arbitrary fields/operators.
- Upload accepts `Idempotency-Key` without retaining file bytes in the idempotency store; replay/mismatch behavior is frozen at S4. Metadata/delete require asset `ETag`/`If-Match`. Owner selection/replacement uses the owner aggregate version too.
- Admin schemas include safe media ID, display metadata, dimensions/size/detected MIME, readiness, timestamps/version, variant/picker facts, and authorized usage summaries. They exclude keys/backend/bucket/endpoint/quarantine path/checksum where not operationally necessary, signed secrets, raw metadata, and deletion internals.
- Unsafe cookie methods require exact trusted Origin/CSRF and application authorization. Upload/preview/admin delivery/list/detail/use are `private, no-store`; errors are stable/safe and never contain SDK/decoder stack, filesystem path, object key, endpoint, multipart bytes, or request-provided raw filename.

### Public delivery privacy, cache, and headers

- Public content APIs return an owner-use image descriptor with opaque media/use/variant identifiers, same-origin delivery URL, intrinsic dimensions/aspect, effective alt/decorative/caption intent, responsive variant widths/formats, and cache validator—never a storage key/backend/bucket/checksum/admin URL.
- A public delivery request succeeds only for a ready/nondeleted variant with at least one currently active public usage whose owner is public-effective under that owner's facade. Supplying admin cookies/tokens to the public route does not widen it; draft-only/hidden/future/unpublished/deleted usage returns the same not-found response.
- Original uploaded bytes are never publicly served. Public responses use validated/re-encoded stripped variants. Admin original access, if S3 permits it at all, is separately authorized, `private, no-store`, attachment-safe, and absent from public DTOs.
- Backend-controlled streaming is the privacy baseline. A selected signed-redirect mode must use an opaque immutable key, HTTPS, least permissions, short expiry no longer than the S0 revocation/cache budget, content headers, no public ACL/listing, and no referrer/analytics leakage; public APIs still return only the same-origin URL.
- Public image responses set exact detected `Content-Type`, `X-Content-Type-Options: nosniff`, restrictive content disposition, ETag from safe variant identity, bounded `Cache-Control`/`Vary`, CSP-compatible behavior, range policy, and no user-controlled header reflection. Error responses are no-store.
- Cache/signature lifetime and CDN purge/invalidation must bound stale delivery after unpublish/hide/reference removal/delete. The owner decision record states the maximum revocation window; tests prove it. “Immutable object” does not mean authorization can be cached forever.
- Delivery prevents path traversal/key guessing, IDOR, hotlink policy bypass, variant amplification, arbitrary resize/transcode parameters, cache-key poisoning, content sniffing, SSRF/open redirects, and unbounded range/request work. Only registry variants can be requested.

## Contract freeze points

### S3 - Media domain/storage/data freeze

Integration/root records S3 only after T01-D review/tests and S0-S2 inputs pass. S3 freezes:

- asset/variant/usage lifecycle, accepted formats and every byte/pixel/dimension/decode/time/metadata/variant limit;
- generated immutable key/quarantine/promotion/compensation/reconcile/delete/replace semantics and adapter capabilities;
- alt/caption/per-use intent, owner role registry, lock order, active draft/current-published usage, staged-field conversion, and public authorization rules;
- configuration requirements and provider capability assumptions without choosing missing owner values;
- command/query DTOs, authorization/audit/concurrency/idempotency, persistence/storage ports, and proposed `0010` schema/index/owner-field contract.

S3 releases S/R/M/A. Incompatible format/storage/schema/owner decisions return to T01-D before migration/generation.

### S4 - Media API and generated-client freeze

Integration/root records S4 only after T01-D/S/R/M/A pass and generation is clean. S4 freezes:

- admin upload/list/detail/update/preview/usage/replace/delete operation IDs, multipart/request/response schemas, readiness/errors/security/rate declarations;
- public/admin delivery DTOs/routes, variant registry, authorization/not-found/cache/header behavior, and owner reference DTOs;
- `ETag`/`If-Match`, idempotency, limits/content types, alt/caption/use intent, pagination/filter/sort, examples, and deprecation metadata;
- deterministic generated TypeScript client plus approved streaming-progress wrapper seam and public image descriptor/component contract.

Integration/root exports, validates, generates, strictly compiles, regenerates, and obtains no diff. S4 releases T02. Frontend cannot compensate with raw untyped fetch, hand-auth/CSRF, duplicate models, `any`, blob URLs that outlive protected state, direct S3 credentials/URLs, or client-trusted MIME/dimensions.

### S5 - Owner/frontend/operations readiness

Integration/root records S5 only after T02-L/O3/O6/O7/O8/P pass focused tests, shared files are released, and Operations supplies a runnable coordinated backup/restore/reconciliation protocol. S5 freezes owner role/field parity, library/picker/public renderer behavior, responsive/a11y states, safe progress/error handling, public image performance/layout, sanitized fixtures, and final evidence interfaces.

S5 releases T03. S5 is not M9 acceptance and does not resolve open S0 production decisions by implication.

## Frontend behavior contract

### Accessible upload, library, picker, usage, replace, and delete

- `/admin/media` provides button and optional drag/drop upload, independent per-file queued/uploading/validating/processing/ready/rejected/canceled states, overall safe limits/help, search, closed filters, page pagination, grid/list modes, metadata edit, preview, usage detail, replace-as-new guidance, and delete.
- The file input remains the canonical accessible mechanism; drag/drop is optional. Keyboard and pointer users can choose/cancel/retry files. Progress uses native/ARIA semantics without noisy announcements, never claims success before `ready`, and distinguishes upload from server validation/promotion.
- Client prechecks improve feedback but do not claim security. Server reason codes map to actionable safe errors retaining only the display filename locally; the browser never parses content as trusted, embeds a rejected SVG, or previews unvalidated bytes as executable content.
- Successful upload opens labeled metadata. Meaningful/decorative choice is explicit per use; filenames never prefill alt. Alt/caption validation, character guidance, crop/focal preview, variant dimensions and effective use are understandable without color.
- Picker mode is searchable/paginated grid/list with selection announcement, readiness/usage/alt facts, keyboard listbox/grid behavior, upload entry, and intentional cancel. It returns opaque generated DTOs and use intent to the owner editor; no object URL/key/provider details.
- Usage detail exposes authorized safe owner locations and draft/live labels. In-use delete is disabled with links; unused delete uses irreversible confirmation. Replace explains that a new asset is created and each selected owner reference changes independently—never a silent global byte swap.
- Initial/loading/success/empty/no-result/upload/validation/processing/server/offline/unauthorized/session-expired/version-conflict/in-use/delete-failure states are explicit. Session expiry cancels safe requests where possible and clears previews/blobs/protected metadata from DOM, memory, caches, object URLs, and history-sensitive storage.
- Upload progress transport is the approved wrapper around S4 schemas/security/error/request IDs. It scopes retries/idempotency per file, bounds parallelism, handles abort, and does not log bodies/filenames or queue offline uploads.

### Owner editors and public images

- M3/M6/M7/M8 editors use one shared picker/use-intent component through generated wrappers. Existing lifecycle/dirty/conflict/preview semantics remain authoritative; selecting media never bypasses owner save/publish/`If-Match`/reference validation.
- Project cover/gallery, blog cover, profile/site/nav roles, and page image blocks expose contextual meaningful/decorative/alt/caption/focal fields exactly as their S1 manifests require. Ordered galleries retain non-drag controls and position announcements.
- Public renderers accept only owner-public image descriptors. They use intrinsic width/height/aspect to prevent layout shift, bounded responsive `srcset`/`sizes` variants, lazy loading except measured LCP candidates, correct fetch priority, effective per-use alt/decorative/caption, and a stable intentional fallback on delivery failure.
- Public components do not build storage URLs, request arbitrary transforms, leak keys/query signatures through logs/analytics, render filenames as alt, or encode critical meaning only in an image. Screenshots can open at a legible size; galleries provide position and named controls.
- Removing/hiding/unpublishing/replacing a usage updates public HTML/RSC/cache/delivery authorization according to the frozen revocation window. Stale DOM does not retain a private admin preview URL after session/owner state changes.

## Dispatch order

1. **Blocked - Integration/root/owner:** record separate M8 acceptance, verify head `0009`, resolve its catalog gate, publish S1 manifests, assign S0 decisions/owners, and release shared files.
2. **After S0-S2 - `M9-T01-D`:** implement/review media lifecycle, validation/variants, usage/alt/caption, failure/reconcile/delete/replace, storage/config ports and `0010` proposal; record S3.
3. **After S3 - Integration/root:** reserve sole `0010` on `0009` and name adapter/config/model/router writers.
4. **After S3 - `M9-T01-S/R/M/A`:** storage-security, persistence/reconcile, migration, and API work only in disjoint files with serialized registration.
5. **After T01 evidence - Integration/root `M9-T01-I`:** review storage/data/security/contracts, export/generate twice, compile, and record S4.
6. **After S4 - `M9-T02-L/O3/O6/O7/O8/P`:** library and owner/public activation proceed only in disjoint files and serialized shared windows.
7. **After T02 evidence - Integration/root/Operations:** run owner parity, public privacy/performance, accessibility and runnable recovery review; record S5.
8. **After S5 - `M9-T03-I`:** execute malicious/failure/J6/owner/public/backup-restore integration, docs/evidence, and prepare the M9 gate record without releasing M10.

## Exact acceptance, security, quality, and evidence gates

All records follow `docs/plan/delivery-evidence-template.md`, identify requested milestone `M9` and trace alias `M13`, and include date, executor, environment/adapter, commit/worktree identity, tool/decoder/SDK versions, exact command/manual protocol, result, repository-relative artifact, finding, correction, and independent retest. Corpus objects, filenames, DB/object samples, API transcripts, screenshots, and traces are sanitized and contain no credentials, endpoints/buckets/keys/signed URLs, cookies/CSRF/auth headers, private/draft content, raw EXIF, production data, or machine-specific absolute paths.

### `M9-T01` backend/storage/data/API evidence

Evidence must include:

- domain/property tests for status transitions, immutable keys/replace-new, filename display sanitation, SHA-256/dimensions/metadata, default/per-use alt/caption/decorative contradictions, variant catalogs, readiness, stable errors, audit redaction, and idempotency;
- versioned malicious image corpus with genuine allowed JPEG/PNG/WebP plus empty/truncated/malformed, extension/MIME/magic mismatch, double extension, GIF/animated, SVG/XML/HTML/PDF/archive/video/audio/executable, polyglot/trailing payload, decompression/zip/image bombs, huge dimensions/pixels, ICC/EXIF/XMP/GPS/thumbnail/comment, orientation/color, parser edge and timeout/memory cases;
- corpus assertions for bounded streaming/full decode/re-encode, rejection before ready/public, quarantine/private state, no execution/external request, metadata stripping, safe error/log/audit, temporary cleanup, and unaffected supported images; tool/name-only scanner output is insufficient;
- local and selected S3-compatible adapter contract suites for traversal/symlink escape, generated/conditional immutable keys, quarantine isolation, stream abort, stat/open/list pagination, checksum, promote conflict, permission/quota/timeout/transient retry, multipart abort, delete idempotency, signature expiry, private policy, TLS and prefix isolation;
- failure injection at each DB/object boundary: before/during/after quarantine, decode/variant, pending-row write, each promote/stat/checksum, ready commit, owner usage commit, tombstone, each object delete, reconciliation/backup listing; prove compensation/retry and no ready-public missing object;
- migration tests for empty/`0009` upgrade, one head/current equality, schema-model parity, owner handoff/FK/usage role constraints/indexes, frozen revision nonmutation, staged data disposition, variant/usage/delete races, rollback/UoW and production roles/startup;
- repository/application tests for ready-only selection, draft/live usage transitions, owner rebuild parity, row-lock order, concurrent reference/delete, replace/publish/unpublish, tombstone/object failure, authorized usage summaries, no cross-module repository reach-through, and bounded transaction duration;
- reconcile dry-run/apply tests for cutoff/batches/lease/idempotency, stale quarantine/orphan/missing/corrupt/incomplete delete/variant/usage drift classes, uncertain-object safety, aggregate audit, and redacted output;
- admin/public API tests for upload/list/filter/sort/pagination/detail/update/preview/usage/replace/delete/delivery, multipart caps, rate/concurrency, CSRF/Origin/auth/IDOR/mass assignment/injection, ETag/If-Match, idempotent replay/mismatch, range/cache/header/error behavior and no configuration/key leakage;
- OpenAPI multipart/binary/schema/security/error/example/filter/sort/deprecation review, unique operation IDs, reviewed diff, two deterministic generations/no diff, strict generated compile, and upload-wrapper/public-descriptor boundary scan;
- Ruff format/lint, strict Mypy, full affected Pytest and meaningful overall/critical coverage, dependency/container/secret scans, no disabled test/corpus omission/unexplained warning.

Accepted hostile/polyglot/SVG/executable content, unbounded stream/decode, filename/path/key influence, public original/quarantine/key access, missing ready object, DB/object inconsistency without recovery, mutable replacement, usage/delete race, unsafe alt fallback, credential/config leak, adapter divergence, preview/public IDOR, generated drift, second migration head, failed Must requirement, or Critical/High finding blocks S3/S4.

### `M9-T02` frontend/owner/public evidence

Evidence must include:

- generated-wrapper/component tests for independent upload progress/abort/retry/idempotency, server validation stages/reasons, grid/list/search/filters/pagination, metadata/version conflicts, picker keyboard behavior, meaningful/decorative/alt/caption, usage links, replace-as-new, in-use/unused delete, protected state clearing, and every async/error state;
- Storybook interaction/axe/manual tests for dropzone+file-input equivalence, progress announcements, safe rejected preview, picker grid/list, metadata forms, usage dialog, delete confirmation/focus restore, mobile cards, long labels, 200% text/400% zoom, light/dark/forced-colors/reduced-motion/touch;
- owner contract tests for every S1 field/role: select/save/preview/publish/edit-live/unpublish/hide/remove/replace/delete interactions, draft vs current-published usage, per-use semantics, immutable revisions, cache/delivery invalidation, unavailable/corrupt fallback, and no staged-ID/config/storage leak;
- public rendered tests for intrinsic geometry/no CLS, responsive formats/width selection, meaningful/decorative/caption semantics, lazy/LCP priority, gallery position/control, delivery failure fallback, no filename alt, no arbitrary transform/key/provider URL, and JavaScript-disabled SSR usefulness;
- public privacy/security tests for draft/future/hidden/unpublished/deleted owners, admin-only/original/quarantine assets, guessed media/variant/use IDs, stale signed URLs/cache windows, hotlink/cache poisoning/content sniffing/range amplification, CSP/referrer/analytics/log/trace leakage;
- Prettier, ESLint, strict TypeScript, full affected Vitest/Testing Library/Storybook/Playwright, production build and focused performance/a11y evidence with no raw untyped transport or direct storage access.

Broken progress/readiness truth, inaccessible picker/delete/gallery, filename-derived alt, owner lifecycle bypass, frozen revision mutation, usage drift, original/key/provider leak, public layout shift, stale private preview, unresolved WCAG blocker, or unexplained bundle/image/performance regression blocks S5/T02.

### `M9-T03` vertical-slice, recovery, and M9 gate evidence

Integration/E2E uses built Next.js/FastAPI through the same-origin edge, a fresh PostgreSQL database migrated through `0010`, isolated local and selected S3-compatible test namespaces, and no demo seed dependency. It must prove:

- administrator uploads valid JPEG/PNG/WebP via button and drag/drop, sees truthful independent progress, server-detected metadata/variants, sets default and per-use meaningful/decorative alt/caption, searches/pages/previews, and selects through owner editors;
- invalid/mismatched/oversized/dimension-bomb/SVG/GIF/polyglot/malicious corpus files never become ready/public, execute, make attacker requests, retain unsafe metadata, leak paths/keys, or leave unreconciled state;
- M3 profile/site roles, M6 project cover/gallery, M7 post cover, and M8 image/image-with-text/block roles activate from staged contracts through owner save/publication without frozen-row mutation or public draft leakage;
- public pages use optimized stripped variants, responsive geometry and correct per-use semantics; originals/admin previews remain private; hide/unpublish/remove/replace/delete revoke delivery within the recorded cache/signature bound;
- replace creates a new immutable asset and atomic owner reference change; old asset remains protected while used; concurrent selection/delete locks safely; in-use delete returns authorized usages; unlink then confirmed delete tombstones and removes objects or reconciles retry;
- local and S3-compatible paths produce the same observable contract across injected quarantine/promote/DB/usage/delete/reconcile failures, with no false success and one idempotent effect;
- unauthorized/expired actor, forged/missing CSRF, untrusted Origin, IDOR, mass assignment, filename/filter/header injection, path/key/variant guessing, stale `If-Match`, idempotency mismatch and rate/concurrency abuse fail safely;
- API/RSC/HTML/image responses/cache/log/audit/trace/screenshot/backup artifacts contain no credentials, bucket/endpoint/key/signed secret, raw EXIF, unsafe filename, draft/private owner content, or admin/original URL;
- full affected backend/frontend/contract/migration/adapter/E2E/build/scan commands pass, generated output stays clean, revision remains one head, S0 decisions are recorded, and no Critical/High finding remains.

Backup/restore evidence must use a coordinated PostgreSQL/object recovery set and prove:

- recorded provider/region, encrypted backup locations/access, RPO/RTO target, cutoff/snapshot ordering, object version/lifecycle assumptions, and named backup/restore/incident owners;
- a manifest mapping safe asset IDs to status/original+variant identity/checksums without publishing credentials/keys, plus counts for usages, tombstones and quarantine exclusions;
- restore into an isolated environment, migrate/check revision, restore objects/DB in the documented order, run dry-run reconciliation and checksum/variant/usage/public-delivery verification before serving traffic;
- missing/corrupt/orphan/object-version/DB rollback failure drills produce a safe stop/recovery report rather than silently serving broken/private media;
- local-volume and selected S3 production strategy differences are documented and at least their supported restore protocols are exercised or explicitly blocked with owner/date—no untested production readiness claim.

Documentation/evidence must include:

- user guide for formats/limits, upload/progress/rejection, library/search/pagination/preview, metadata/default/per-use alt/caption/decorative/focal behavior, picker/owner roles, replace, usage, in-use/unlink/delete, and recovery-facing error guidance;
- API guide for admin/public delivery operations, multipart/idempotency, schemas/errors/auth/CSRF/rates, filters/sorts/pagination, ETag/If-Match, readiness/variants/use descriptors, cache/range/headers/not-found privacy, and sanitized examples/cURL without storage internals;
- developer/security guide for threat model/corpus, `MediaStorage`/config adapters, quarantine/decode/variant/checksum/promotion/compensation, `0010` model/usage locks, owner activation/facades, delete/reconcile state, delivery authorization/cache, and extension rules for a real new format/provider;
- operator guide for S0 provider/region/bucket/auth/TLS/encryption/lifecycle/signing/CDN decisions, local volume, least privilege, capacity/rate/alerts, reconciliation dry-run/apply, quarantine/tombstone retention, key/credential rotation, coordinated backup/restore/RPO/RTO, disaster/partial-failure runbooks;
- sanitized screenshots at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px plus 400% zoom for upload/progress/rejections/library grid-list/filter/pagination/metadata/picker/usage/replace/in-use-delete/error states, every owner integration, public responsive images/galleries/fallbacks in light/dark; attach malicious-corpus, adapter/failure/reconcile, backup/restore, performance/image/CLS/bundle, accessibility, security/privacy, API, coverage, traceability and independent-review reports.

Passing lane evidence does not authorize M10 until Integration/root records the separate M9 acceptance decision. The M9 gate remains blocked by any open required S0 production owner decision, failed Must requirement, disabled/suppressed check, insecure/default provider/region/credential/bucket/TLS/encryption behavior, fake adapter/scanner, hostile file acceptance, public original/key/quarantine/private usage leak, DB/object/usage inconsistency without tested recovery, mutable replacement, deletion race, broken backup/restore, generated drift, multiple migration heads, parallel migration/generated/adapter/usage/shared writer, earlier-provider or Infrastructure overlap, unsanitized evidence, missing independent retest, unresolved WCAG blocker, unexplained target regression, or confirmed Critical/High finding.
