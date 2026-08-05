# M8-T03 frontend, renderer, and integration evidence

## Record

- Date: 2026-08-04.
- Executor: Integration/root.
- Environment: fresh production-shaped Compose stack `upw-m8-final`, loopback-only frontend/backend ports, fresh PostgreSQL volume migrated through `20260802_0009`, explicit permission reconciliation, fictional demo seed, and one disposable administrator.
- Credentials, cookies, CSRF values, database URLs, and private manifests were not logged or committed.

## Delivered surface

The administrator Pages workspace provides list/create, Home/custom routing, SEO and visibility metadata, a grouped exact 19-kind palette, ordered canvas, selected-block inspector, strict config editing, Move up/down controls, duplicate/hide/show/delete, page settings, linked preview issues, export, duplicate custom page, publish/schedule/reschedule/unpublish, and protected delete. Three panes activate at 1440 px; the measured 1280 px two-pane layout has `scrollWidth == innerWidth`, and the sub-768 px stylesheet is linear.

The public renderer covers all 19 kinds from the generated discriminator. It preserves DOM order, uses semantic headings/lists/definitions/figures/links/separators, resolves only safe public references, and routes rich HTML exclusively through `SafeRenderedContent`. Home and custom routes derive metadata from the public projection. Sitemap consumes the bounded public route list and includes published custom-page modification time.

## Independent runtime workflow

Using the built same-origin UI, the reviewer completed forced-password setup, created the Home singleton, confirmed the 19-item registry, added and configured hero/statistics/automatic project/post/rich-text/testimonial blocks, ran a clean private preview, and published. The anonymous Home route immediately rendered the frozen ordered projection.

The reviewer then created `/principles`, added rich text, call-to-action, contact-callout, and divider defaults, ran a clean preview, published, and confirmed the anonymous semantic output and sitemap entry. The 1280 px builder screenshot showed no horizontal overflow after the responsive threshold correction. Home/custom/About smoke checks passed after the final container start, and the frontend log contained zero `Error`, `EROFS`, `ENOENT`, or static-to-dynamic findings.

The browser gate found and independently retested three defects:

1. Create sent an empty description against the strict minimum-length schema. The template now supplies valid neutral copy and requires the metadata field.
2. OpenAPI Generator appended camel-case `blockType` after correctly encoding `block_type`. The deterministic generator now removes exactly 19 overlays from each of three unions; a wrapper regression test proves strict wire JSON.
3. Build-time fallback routes changed to no-store reads under a read-only runtime. Home, custom, About, and sitemap are explicitly dynamic, and the cache tmpfs targets the standalone runtime path.

## Automated verification

- Focused backend page suites: 43 passed (domain, registry, transport, service, migration, PostgreSQL API integration).
- Frontend page suites: 3 files / 4 tests passed, including all-19 renderer mount parity, safe-rich-text policy marker, all-19 administrator templates, and strict generated wire serialization.
- Strict TypeScript: passed.
- Repository ESLint: passed.
- Production Next.js build: passed; `/`, `/[slug]`, `/about`, and `/sitemap.xml` are dynamic.
- OpenAPI validation: passed at 74 paths / 98 operations.
- Two clean generations: identical SHA-256 inventory and unchanged OpenAPI hash across 250 generated files.
- Fresh container migration/permission/readiness: passed; backend and frontend healthy.

## Security and privacy observations

Public API/browser inspection exposed no draft pointer, aggregate version, author/admin identity, raw CommonMark source, raw config shell, storage key, cookie, or unresolved media identifier. Public rich text contained the sanitizer policy marker and sanitized HTML only. Preview remained behind the administrator shell. The backend integration suite covers forged/missing CSRF, missing/stale preconditions, idempotent replay/mismatch, public `404` equivalence, immutable live/draft isolation, and hidden/unpublished behavior.

## Decision

G5 is accepted and M8 is accepted. No unresolved Critical/High defect remains in the slice. M9 receives the frozen 19-kind registry, normalized media-reference roles, immutable revision ownership, exact generated contracts, and staged image/image-with-text draft intent. M9 must activate real validated media usage/delivery and remove the publication issue; it must not introduce a fake storage path or mutate frozen revisions.
