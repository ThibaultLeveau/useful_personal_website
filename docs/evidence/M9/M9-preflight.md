# M9 preflight: S0-S2 and owner handoff

## Record

- Date: 2026-08-04.
- Executor: Integration/root.
- Requested milestone: M9; trace alias M13.
- Accepted predecessor: M8, migration head `20260802_0009`.

## S0 production decision status

The vendor-neutral adapter and application contracts are released for implementation. Production acceptance remains blocked because no deployment owner has selected a storage provider/service, region/residency, private bucket/namespace, workload identity, network endpoint, encryption/KMS policy, lifecycle/versioning behavior, CDN/signature policy, or coordinated backup/restore owners and targets. Code must have no production defaults for these values.

Development explicitly uses the local private adapter rooted at the dedicated mounted media volume. Production configuration must reject that adapter and must fail closed when any selected S3-compatible requirement is absent. Public delivery uses the backend authorization proxy by default; a signed-redirect mode remains unavailable until an owner records its exact provider and revocation budget.

## S1 accepted owner-field handoff

The following existing SPEC-backed fields/roles are released to migration `0010` and later serialized owner windows:

| Owner | Stable reference scope | Released media roles and intent |
| --- | --- | --- |
| Profile singleton | `profile.id` | optional `profile_image_id`; one contextual meaningful/decorative use with explicit effective alt |
| Website settings singleton | `website_settings.id` | optional `logo_media_id`, `favicon_media_id`, `social_image_media_id`; no navigation/footer media role |
| Project revision | immutable `project_revision.id` | optional cover plus ordered screenshots; per-use meaningful/decorative, alt, caption, focal intent; publication/copy-on-write owns activation |
| Blog revision | immutable `blog_post_revision.id` | optional cover; per-use meaningful/decorative, alt, caption, focal intent; publication/copy-on-write owns activation |
| Page revision/block | immutable `page_revision.id` + `page_block.id` | existing `image` and `image_with_text` config `media_id`, purpose, alt, caption, focal point, order; normalized `media_primary` reference |

Skill `icon_key` is not an accepted staged media identifier and is not silently converted. No new owner field is inferred. Existing frozen revisions are not mutated or backfilled; administrators select assets in a mutable draft/new revision.

Media consumes owner application facades/usage facts only. It may not import owner repositories or ORM. Owner commands validate ready assets and transactionally rebuild their own draft/current-published usages.

## S2 threat, limits, and recovery freeze

- Accepted inputs: single-image JPEG, PNG, and WebP only. GIF, animated images, SVG/XML, HTML, PDF, archives, audio/video, executable formats, ambiguous/mismatched containers, trailing polyglot payloads, and every other format are rejected.
- Limits: streamed hard cap 10 MiB independent of `Content-Length`; width/height at most 6000 px; at most 36 MP; one frame; bounded 1 MiB chunks; 30-second request/processing budget; at most two concurrent processors per application process.
- Originals: retained privately for administrator-authorized recovery/reprocessing and never publicly served. Raw EXIF/IPTC/XMP/GPS/comments/thumbnails and arbitrary profiles are not persisted or published.
- Variants: metadata-stripped, orientation-normalized, sRGB responsive widths 320/640/960/1440/1920 without upscaling. WebP quality 85 plus a safe alpha-aware PNG or JPEG quality-88 fallback. Variant identity is closed and immutable.
- Integrity: SHA-256 is integrity/search evidence only. Logical assets are not automatically merged by checksum.
- Keys: generated opaque UUID-based keys under closed quarantine/original/variant namespaces. User filenames, owner IDs, slugs, MIME strings, and checksums never form paths.
- Quarantine: private and nondeliverable; rejected/canceled objects are removed immediately when possible. Reconciliation treats quarantine older than 24 hours as stale with a stable one-hour run cutoff/grace.
- Failure behavior: ready is committed only after all required promoted objects pass stat/checksum verification. Every DB/object boundary has idempotent compensation or a reconciliation-visible nonready/tombstoned state.
- Delete: row lock, same-order active-usage check, immediate tombstone, then idempotent object removal. Uncertain or partially failed objects are never silently destroyed.
- Reconciliation: explicit operator command, dry-run by default, batches of 100 under a stable cutoff, apply requires explicit confirmation. Reports only safe IDs/categories/counts.
- Delivery: backend proxy of stripped registered variants, five-minute browser/shared authorization cache maximum, `nosniff`, exact detected content type, bounded range behavior, and not-found parity after owner eligibility checks.
- Backup/restore: implementation must provide coordinated database/object manifest and isolated restore verification. Production RPO/RTO, provider snapshots, encryption locations, and named drill owner/date remain S0 blockers.

Decoder validation is not described as antivirus scanning. No fake scanner/provider is introduced.

## Preflight decision

S1 and S2 pass. S0 passes only for vendor-neutral/local-development implementation; production acceptance and S5 remain blocked on the explicit deployment-owner decisions above. The sole migration reservation is `20260802_0010_media.py` with revision `20260802_0010` on `20260802_0009`.
