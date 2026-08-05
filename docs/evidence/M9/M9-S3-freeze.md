# M9 S3 media domain/storage/data freeze

## Record

- Date: 2026-08-04.
- Executor: Integration/root.
- Requested milestone: M9; trace alias M13.
- Predecessor: accepted M8 and sole prior head `20260802_0009`.
- New sole head: `20260802_0010`.

## Frozen contract

- Logical assets are immutable-bytes records with `quarantined`, `processing`, `ready`, `failed`, `deleting`, and `deleted` states. Only complete verified ready assets are selectable or deliverable.
- Accepted input is single-frame JPEG, PNG, or WebP, at most 10 MiB, 6000 px per dimension, and 36 MP. Declared MIME is a hint that must agree with magic and decoder detection.
- Original uploads remain private and are never a public-delivery source. Public/admin presentation uses orientation-normalized, metadata-stripped responsive WebP plus alpha-aware PNG or opaque JPEG fallback at 320/640/960/1440/1920 without upscaling.
- Storage keys are opaque UUID-derived values under only `quarantine/`, `originals/`, and `variants/`. Display filenames, owner IDs, MIME values, and checksums never form keys.
- Local storage is explicit nonproduction-only. S3-compatible storage requires an HTTPS endpoint, region, private bucket, managed prefix, credential source, encryption mode, and bounded timeouts; production has no fallback.
- Contextual media use is meaningful with nonempty alt text or decorative with empty alt text. Caption and focal data are bounded. Exact owner and role catalogs match the S1 record.
- Deletion takes an asset row lock, rejects active usage, commits a tombstone, removes exact registered objects idempotently, then finalizes the tombstone.
- Reconciliation has a stable one-hour cutoff, 24-hour quarantine threshold, batches of 100, dry-run default, exact apply confirmation, and count-only output.
- Backend-controlled same-origin delivery is the baseline. Public delivery requires ready content plus an active public-effective owner use and returns not-found parity otherwise. Cache authorization cannot exceed five minutes.
- SHA-256 is integrity and search evidence only; no logical deduplication occurs.

## Verification

- Strict Ruff and mypy passed for all 137 backend/application sources and the migration environment.
- Focused M9 and architecture suite: 45 passed in 45.01 seconds.
- Secure storage/image/reconciliation unit subset: 25 passed.
- PostgreSQL migration subset: 2 passed, including upgrade from M8, ready-reference triggers, active-use deletion rejection, downgrade/re-upgrade, and one head.
- PostgreSQL/runtime-role API subset: 2 passed, including multipart upload, ready verification, retry replay and payload conflict, private rendition, public deny-by-default, precondition, tombstone, hostile SVG, and over-limit stream.
- `alembic check`: no new upgrade operations detected.

## Decision

S3 passes for the vendor-neutral implementation and local-development adapter. Production S0 provider, residency, bucket, workload identity, network, KMS, lifecycle/versioning, delivery/CDN, and RPO/RTO owner values remain explicitly open and continue to block S5 and production acceptance.
