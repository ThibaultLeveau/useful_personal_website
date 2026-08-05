# M12 protected audit query

Date: 2026-08-04

The read-only administrator API exposes event catalog, newest-first paginated list, and durable detail operations. Exact filters cover event, actor type/ID, resource type/ID, outcome, half-open timezone-aware UTC interval, and request ID. Page size is capped at 100. Unknown, repeated, malformed, metadata-search, and sort parameters are rejected; SQL uses bound typed expressions and deterministic `(occurred_at DESC, id DESC)` ordering.

A PostgreSQL-backed runtime protocol returned list `200`, detail `200`, 9 rows and 79 catalog events, with `private, no-store`. Unit/API tests cover authorization at the application service, query ambiguity, safe correlation/envelopes, detail not-found behavior, pagination, and exclusion of IP pseudonyms. No audit export or web mutation route exists.
