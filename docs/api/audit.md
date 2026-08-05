# Audit inspection API

Audit inspection is read-only and accepts only an active administrator cookie session. Bearer API tokens, including tokens carrying the reserved `admin:read` scope, cannot access these routes. Every response is `Cache-Control: private, no-store`.

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/admin/audit/events` | Return the exact event identifiers accepted by the current catalog. |
| `GET /api/v1/admin/audit` | Return a newest-first page ordered by `(occurred_at DESC, id DESC)`. |
| `GET /api/v1/admin/audit/{entry_id}` | Return one durable safe event projection. |

The list supports page-number pagination (`page=1`, `page_size=20`, maximum `100`) and exact filters for `event_type`, `actor_type`, `actor_id`, `resource_type`, `resource_id`, `outcome`, `request_id`, `occurred_from`, and `occurred_to`. Date intervals are half-open: `occurred_from` is inclusive and `occurred_to` is exclusive. Dates must include a timezone. Unknown, repeated, malformed, or unsupported parameters are rejected; metadata search and arbitrary sort expressions do not exist.

Responses expose the event identifier, safe actor/resource identifiers and label, UTC occurrence time, outcome, request correlation, schema version, and event-specific allow-listed metadata. They never expose IP pseudonyms, administrator email, contact identity or body, content bodies, token selectors/digests/secrets, authentication material, storage keys, infrastructure addresses, SQL, or exception details. Forbidden values are absent rather than replaced with a redaction marker.

There is deliberately no audit create/update/delete/export web API. Retention is an operator-only command documented separately.
