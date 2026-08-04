# Configurable page architecture

The page slice is a bounded module under `backend/app/modules/pages`. Stable page identity, route ownership, revision pointers, blocks, and normalized references live in relational tables introduced by migration `20260802_0009`. Authored kind-specific config is bounded JSONB validated by the frozen Python registry; it is never treated as an executable renderer/query/CSS description.

## Immutability and persistence

Home is a database-enforced singleton. Retained custom slugs are case-insensitively unique and checked against the reserved route catalog. Draft and published pointers belong to the same page and cannot alias. Publication freezes a revision and its block/reference descendants; PostgreSQL triggers reject every frozen-tree mutation direction. A new independent draft is flushed before its copied children.

Block positions are contiguous application-managed order. Repository mutations use positive scratch positions above the current maximum so uniqueness and non-negative constraints remain valid throughout add, copy, delete, and full reorder transactions. Page list pagination and counts run in SQL. Reference and public-route resolution uses bounded set queries rather than per-block aggregate loads.

## Registry and providers

`registry.py` is the only backend block catalog. It maps the exact 19 `BlockType` values at schema version 1 to strict config models, renderer keys, groups, media requirements, and trusted reference extractors. Pages call only released profile, skills, experience, projects, and blog application facades. Empty automatic collections use one bounded public-list call per provider/featured mode.

The frontend consumes only the generated client. `PAGE_BLOCK_TYPES` and `BLOCK_TYPES` are parity-tested against the frozen count, and `PageRenderer` dispatches exhaustively by the generated discriminator. Public rich text reuses the M7 `SafeRenderedContent` boundary. Unknown kinds have no renderer fallback and therefore fail closed.

The pinned OpenAPI generator currently needs two fail-closed repairs: required `StatisticItem.value` decoding, and removal of generator-added camel-case `blockType` keys from strict union wire JSON. Both repairs assert exact expected patterns/counts and abort generation if the pinned templates change. Generated files are never hand-edited.

## SSR, security, and extension

Home, custom pages, About, and sitemap are explicit dynamic server routes because their public APIs use no-store reads and the production container has a read-only root filesystem. Compose mounts only the actual standalone cache directory at `/app/frontend/.next/cache`. Metadata derives from the same public page projection; sitemap consumes the bounded public route list.

To add a future block version, add a new explicit registry model/upgrader decision, reference extractor, migration/backfill if required, OpenAPI fixture, generated union, administrator template/inspector behavior, public renderer, malicious-input tests, and story/render fixtures in one reviewed change. Never silently reinterpret stored config or reuse an existing version number.

M9 owns media tables, usage rows, validation/storage adapters, asset delivery, and the now-active
`media_id` references. Image blocks require a ready asset, persist per-use alt/caption/focal metadata,
and become publicly deliverable only through a visible current published revision; frozen revisions
are never patched in place.
