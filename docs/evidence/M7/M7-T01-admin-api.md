# M7-T01-A - Blog administrator, preview, export, and taxonomy API

## Result

The authenticated `/api/v1/admin/blog` surface provides closed post list/create/get/update/order,
visibility, publish/reschedule/unpublish/delete, private preview, exact source export, and
tag/category list/create/update/order/delete operations. Mutable requests reject extra fields;
reading time, checksum, and policy provenance are never client inputs. Unsafe operations consume
the accepted Origin/CSRF/session boundary, ETags use `If-Match`, and retryable creates/orders/
publication actions use idempotency keys.

Preview is `private, no-store` plus `X-Robots-Tag: noindex, nofollow`. Export is authenticated
`text/markdown`, attachment-safe, exact normalized source with matching checksum/policy/reading
headers, and the same no-store/noindex treatment. Field/relation errors contain stable path/code
facts without rejected source or identifiers. Taxonomy-in-use is an explicit conflict.

## Verification

Ruff and strict Mypy pass all transport source/tests. The focused unit transport suite is part of a
49-test green policy/domain/service/transport gate. A real FastAPI/PostgreSQL lifecycle test passes
create/replay, malicious raw-HTML rejection, taxonomy linking, preview, export equivalence,
publication, safe public filtering/detail, frozen live content during draft edits, and visibility
privacy: `1 passed in 5.50s`.
