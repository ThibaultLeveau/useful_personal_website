# M7-T01-R - Blog PostgreSQL persistence

## Result

The blog repository persists stable post/taxonomy identities, canonical revision values and
derivation provenance, ordered revision-owned tag/category/related-post links, copy-on-write
publication, PostgreSQL-time eligibility, soft deletion, visibility, scheduling, and optimistic
versions without owning commits.

Public list/detail predicates select only visible, nondeleted, pointed publications whose
`publish_at <= now()`. Tag/category filters join only the published revision and visible,
nondeleted taxonomy. Draft edits therefore cannot affect live source, title, SEO, reading time,
facets, or relations. A public page uses exactly six statements regardless of result size: bounded
page/count, pointed revisions, and the three ordered relation collections.

## Verification

Ruff and strict Mypy pass the ORM/repository and database tests. Four isolated PostgreSQL tests pass
against a clean schema through `0008`: rollback/commit ownership and exact round trip;
copy-on-write/frozen-row enforcement; future scheduling plus draft/public taxonomy separation; and
the fixed six-statement public page contract. Final result: `4 passed in 24.86s`.

No repository imports transport/frontend code, calls commit, performs unbounded recursive loading,
stores rendered HTML, or persists a media placeholder.
