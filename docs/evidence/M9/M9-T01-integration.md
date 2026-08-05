# M9-T01-I integration and client-generation evidence

- The canonical OpenAPI export contains 79 paths and 106 operations; `scripts/validate_openapi.py` passed all operations.
- The pinned OpenAPI Generator 7.17.0 client contains 266 files after repository-owned, exact-count compatibility repairs.
- The multipart media upload contract emits `file: Blob` and uses native `FormData`; the generator's incorrect string/URL-encoded fallback is rejected and repaired fail-fast.
- Strict TypeScript and ESLint passed with Node.js 22.23.2 and pnpm 11.18.0.
- A complete-tree SHA-256 path/content inventory before and after an independent regeneration matched
  across 266 files at `b495c18ccd337ac4a11a3ca4246d462781f77616a414c2f5a349f38be29b66a2`.

The generated client is therefore contract-valid, type-valid, lint-valid, and byte-for-byte deterministic at the S4 boundary.
