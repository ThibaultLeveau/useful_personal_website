# M9 S4 media API and generated-client freeze

## Record

- Date: 2026-08-04.
- Executor: Integration/root.
- Predecessor: accepted M9 S3 and sole migration head `20260802_0010`.

## Frozen contract

- Administrator upload is multipart and requires a `Blob`, trusted Origin, CSRF token, and bounded idempotency key.
- Administrator library operations expose exact pagination/search, safe detail, optimistic metadata update, active-use-protected deletion, and stripped registered renditions.
- Public delivery remains deny-by-default until an exact active, public-effective owner usage exists; unauthorized and absent media have not-found parity.
- Storage coordinates, managed keys, checksums, raw metadata, originals, and credential-bearing values are absent from API responses and audits.
- The OpenAPI document is the only client contract. Repository-owned generator repairs are exact-count, pinned-version, fail-fast transforms rather than hand-edited generated output.
- The media upload compatibility repair is narrowly frozen to one generated `file: string` to `file: Blob` replacement and one multipart selector replacement with native `FormData`.

## Verification

- Canonical OpenAPI: 79 paths and 106 validated operations.
- Generated TypeScript client: 266 files.
- Strict TypeScript: passed on Node.js 22.23.2/pnpm 11.18.0.
- ESLint: passed on Node.js 22.23.2/pnpm 11.18.0.
- Independent regeneration inventory: byte-for-byte path/content match across 266 files at
  `b495c18ccd337ac4a11a3ca4246d462781f77616a414c2f5a349f38be29b66a2`.

## Decision

S4 passes. T02 frontend media-library, picker, optimized rendering, and transactional owner-activation lanes are released. S0 production infrastructure choices remain open and continue to block S5 and production acceptance.
