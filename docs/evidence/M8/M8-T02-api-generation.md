# M8-T02 API, public projection, and generated-client evidence

## Frozen API contract

- FastAPI exports 74 paths and 98 unique operations, including the bounded public page-route list used by sitemap generation.
- The page block input discriminator contains exactly the 19 G3 kinds at schema version 1.
- Admin routes cover registry, bounded list, create/get/save/delete, page duplicate, block add/update/duplicate/visibility/delete/complete reorder, preview, export, publish/reschedule/unpublish.
- Public routes expose effective Home and custom pages only, with indistinguishable not-found behavior.
- Unsafe routes reuse the released session, Origin, CSRF, request-ID, `ETag`/`If-Match`, error-envelope, audit, and idempotency conventions.

Create, page duplicate, add block, block duplicate, reorder, publish, reschedule, and unpublish have retry-safe admission. Same-key/same-payload replay returns the one committed effect; mismatches conflict. Block copies receive new IDs and reference rows. Visibility and destructive mutations serialize on the page aggregate and require the current version.

## Provider and privacy boundary

Pages call released provider facades only. Explicit skill, experience, project, post, and internal-page references resolve in bounded sets. Empty collection selections perform at most one bounded public-list call per provider/featured mode and honor `maximum_items`. Provider not-found errors become stable page validation errors rather than internal failures.

Profile-derived blocks receive only the existing public-approved singleton projection. Public rich text uses the M7 sanitizer and exposes only sanitized HTML, policy name/version, and source checksum through a separate public discriminated union. Authored CommonMark source remains confined to administrator detail, preview, and export. Public DTOs contain no draft pointers, creator identities, audit state, raw JSONB shell, or media storage data. M9-required image blocks remain saveable draft intent but cannot publish.

## Deterministic generation

The authoritative schema was exported to `docs/api/openapi.json`, validated, and generated with the pinned OpenAPI Generator 7.17.0 OCI digest. The repository generator includes fail-closed repairs for the pinned generator's collision between a required statistics property named `value` and its decoder parameter, and its duplicate camel-case `blockType` output in strict discriminated-union JSON. The SPEC contracts remain unchanged.

Two clean generations produced identical SHA-256 inventories for all 250 generated files and an unchanged OpenAPI artifact hash. `pnpm --dir frontend typecheck` passed after generation. No generated file was hand-edited.

## Verification summary

- Ruff format/check: passed for page domain, persistence, service, APIs, provider facade additions, tests, and generator script.
- strict Mypy: passed for the affected backend and focused service test.
- focused page tests: 39 unit tests, 2 migration tests, and 2 PostgreSQL integration tests passed.
- OpenAPI validator: passed; 74 paths, 98 operations, exact discriminated input/public unions.
- deterministic generation: passed; 250 files, no hash drift.
- generated/client TypeScript compile: passed.

## G4 decision

G4 is accepted. The API and generated-client writer window is closed, and M8-T03 frontend/admin/public work is released against this contract. G4 does not accept the milestone; G5 and final M8 gates remain pending.
