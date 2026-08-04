# M7-T01-D - Blog domain/application and B3 freeze

## Identity

- Requested milestone: M7; trace alias: M11
- Requirements: F1-011; applicable API-001-API-006, SEC-004-SEC-006,
  NFR-006-NFR-008, NFR-014-NFR-018
- Executor/reviewer: Integration/root
- Environment: Windows development shell, Python 3.12.13
- Completed UTC: 2026-08-04

## Frozen blog contract

- Post slugs normalize to immutable ASCII lowercase kebab case, are bounded to 80 characters, and
  reserve a case-insensitive unique route identity.
- Title, excerpt, author display, SEO, and canonical URL are bounded and safe. Canonical URLs are
  credential-free, fragment-free HTTPS. SEO falls back to the frozen public title/excerpt.
- Canonical CommonMark source, reading minutes, checksum, policy name/version, tag/category links,
  and ordered related-post links belong to the revision. Client-supplied derivations are always
  replaced by `upw-commonmark` 1.0.0 output.
- Cover media remains nullable and every non-null value fails with `capability_unavailable` until
  the accepted M9 provider exists. M7 adds no media URL, key, filename, blob, storage, or request.
- Tags and categories have separate stable kinds, normalized unique slugs, bounded labels,
  visibility, deterministic order, optimistic versions, and soft deletion. A retained draft or
  frozen revision blocks taxonomy deletion.
- Relation lists reject duplicates, over-limit input, wrong taxonomy kinds, unavailable targets,
  and self-related posts. Related posts are one bounded level; no artificial graph-cycle rule is
  imposed. Public projection independently omits every hidden/deleted/non-effective target.
- Publication freezes the current draft and creates one identical mutable copy atomically.
  Scheduling uses PostgreSQL time without a worker. Save, publish, reschedule, unpublish,
  visibility, order, and deletion are independent actions with shared ETag/idempotency rules.
- Preview renders only the current draft through the frozen policy. Export returns the exact
  normalized draft source plus matching provenance, reading time, safe filename, and Markdown
  content type. Both are authenticated private boundaries intended for `private, no-store` and
  `noindex` transport handling.
- Public DTOs contain sanitized rendered content and allow-listed labels only. They never contain
  CommonMark source, revision/pointer/version/creator data, hidden taxonomy, future timing, or
  sanitizer internals.

## Verification

Ruff format/check and Mypy 2.3.0 strict pass the policy, domain, ports, application service, and
tests. Pytest 9.1.1 passes 44 focused tests covering the malicious corpus, supported rendering,
normalization, server-owned derivation, stable errors, taxonomy kinds/usage, relation privacy,
copy-on-write publication/replay, future/visibility eligibility, independent unpublish, and exact
preview/export provenance.

## Decision

B3 passes and reserves the sole migration `backend/migrations/versions/20260802_0008_blog.py` with
`revision = 20260802_0008` and `down_revision = 20260802_0007`. Persistence, migration, admin API,
and public projection may now consume this contract. Any incompatible change reopens B3.
