# M9-T01-A administrator and delivery API evidence

The authenticated media API provides multipart upload, exact pagination/search, detail, display-name update with `If-Match`, safe usage summaries, delete, and stripped admin preview. Upload requires trusted Origin, CSRF, a bounded `Idempotency-Key`, and independently enforces the stream cap. Responses exclude storage keys, bucket/endpoint, checksums, signed values, raw metadata, and originals.

The public same-origin route returns stripped registered variants only after application eligibility and otherwise uses not-found parity. The current owner facade deliberately denies all public use until the post-S4 owner activation lanes materialize exact public-effective usages.

The PostgreSQL-backed API tests passed upload, replay, mismatch conflict, library listing, stripped WebP preview, public deny-by-default, missing precondition, tombstone, SVG rejection, 10 MiB cap rejection, and sanitized audit records.
