# M7-T01-M - Sole linear blog migration

## Result

`20260802_0008_blog.py` is the only M7 revision and points directly to accepted `20260802_0007`.
Alembic reports exactly `20260802_0008 (head)`. The migration creates stable `post`, `tag`, and
`post_category` identities; `post_revision`; ordered `post_tag`, `post_category_link`, and
`related_post` relations; deferrable same-owner publication pointers; case-insensitive expression
indexes; public/admin query indexes; bounds/checks; and database triggers that reject update/delete
of frozen revisions and their relations.

It creates no rendered-HTML source of truth, media/storage table or key, worker/scheduler/outbox,
page/block/contact/token table, or second head.

## Verification

Ruff and strict Mypy pass the ORM, migration, Alembic composition, and migration tests. Two isolated
PostgreSQL migration tests pass (`2 passed in 12.69s`) for upgrade from accepted `0007`, empty
upgrade, one current head, provider preservation, pointer/self/duplicate constraints,
case-insensitive taxonomy identity, frozen scalar/relation mutation rejection, downgrade cleanup,
and `alembic check` schema/model parity.
