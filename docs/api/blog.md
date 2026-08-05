# Blog API

The blog slice is served under `/api/v1`; [OpenAPI](openapi.json) is the canonical schema and exact
operation contract.

## Public operations

`GET /api/v1/public/blog/posts` accepts `page`, `page_size`, `tag`, `category`, `search`, and
`sort`. Repeated singleton parameters, unsupported sorts, malformed values, and unbounded text
return the shared 422 envelope. `GET /api/v1/public/blog/posts/{slug}` requires the normalized
lowercase slug; missing and every nonpublic state return the same safe 404.

Public DTOs contain the frozen title, excerpt, author display, safe rendered HTML with policy name,
policy version, and source checksum, server-derived reading time, publication date, public SEO,
visible taxonomy references, and effective related summaries. They never contain source Markdown,
drafts, creators, pointers, revision/version/deletion facts, future schedules, hidden taxonomy, or
nonpublic related-target clues. Cache revalidation is bounded by the next schedule instant.

## Administrator operations

All routes require a full administrator session. Unsafe methods additionally require the accepted
same-origin `Origin` and cookie CSRF token. Reads, preview, and export are private `no-store`.

| Method and path                                            | Purpose                                   | Concurrency/idempotency       |
| ---------------------------------------------------------- | ----------------------------------------- | ----------------------------- |
| `GET /api/v1/admin/blog/posts`                             | Filtered administrator list               | read-only                     |
| `POST /api/v1/admin/blog/posts`                            | Create stable slug and revision-one draft | `Idempotency-Key`             |
| `PUT /api/v1/admin/blog/posts/actions/reorder`             | Replace complete post order               | `If-Match`, `Idempotency-Key` |
| `GET /api/v1/admin/blog/posts/{id}`                        | Read complete lifecycle and ETag          | read-only                     |
| `PUT /api/v1/admin/blog/posts/{id}`                        | Replace mutable draft                     | `If-Match`                    |
| `GET /api/v1/admin/blog/posts/{id}/preview`                | Server-render private draft               | `noindex`, `no-store`         |
| `GET /api/v1/admin/blog/posts/{id}/source`                 | Exact normalized Markdown export          | `text/markdown`, `no-store`   |
| `PUT /api/v1/admin/blog/posts/{id}/visibility`             | Set visibility independently              | `If-Match`                    |
| `PUT /api/v1/admin/blog/posts/{id}/actions/publish`        | Publish now or schedule                   | `If-Match`, `Idempotency-Key` |
| `PUT /api/v1/admin/blog/posts/{id}/actions/reschedule`     | Replace publication instant               | `If-Match`, `Idempotency-Key` |
| `PUT /api/v1/admin/blog/posts/{id}/actions/unpublish`      | Remove public eligibility                 | `If-Match`, `Idempotency-Key` |
| `DELETE /api/v1/admin/blog/posts/{id}`                     | Soft-delete post                          | `If-Match`                    |
| `GET /api/v1/admin/blog/taxonomies/{kind}`                 | List tags or categories                   | read-only                     |
| `POST /api/v1/admin/blog/taxonomies`                       | Create taxonomy identity                  | `Idempotency-Key`             |
| `PUT /api/v1/admin/blog/taxonomies/{id}`                   | Update label/slug/visibility              | `If-Match`                    |
| `PUT /api/v1/admin/blog/taxonomies/{kind}/actions/reorder` | Replace kind order                        | `If-Match`, `Idempotency-Key` |
| `DELETE /api/v1/admin/blog/taxonomies/{id}`                | Delete unused taxonomy                    | `If-Match`                    |

Administrator post filters are `lifecycle`, `visible`, `tag_id`, `category_id`, and `search`; the
OpenAPI catalog defines the accepted sort values. Request bodies forbid unknown fields. Non-null
cover media accepts only a ready media asset. Usage is revision-scoped and becomes publicly eligible
only for the current visible published post.

## Lifecycle and content rules

Publishing freezes the draft and creates an identical mutable copy atomically. Later source,
taxonomy, relation, SEO, render, checksum, or reading-time changes cannot affect the live revision
until another publish succeeds. `publish_at` and reschedule values are absolute UTC instants tested
against PostgreSQL time; there is no scheduler endpoint or worker.

The server canonicalizes source newlines, renders controlled CommonMark, sanitizes output, and
derives checksum/policy/reading-time fields. Raw HTML, images, embeds, unsafe URLs, duplicate/self/
deleted relations, wrong taxonomy kinds, duplicate slugs, and undeclared fields return bounded
field-addressable errors. Taxonomy deletion while retained revisions still use it returns
`RESOURCE_VERSION_CONFLICT` with reason `taxonomy_in_use`.

Use the response ETag as the next `If-Match`; a stale value returns the shared version conflict
without a partial write. Reuse an idempotency key only with the exact same canonical payload.

```http
GET /api/v1/public/blog/posts?tag=engineering&sort=-published_at&page=1&page_size=20
Accept: application/json
```
