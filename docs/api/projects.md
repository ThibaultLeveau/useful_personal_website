# Projects API

The project slice is served under `/api/v1`; [OpenAPI](openapi.json) is the canonical schema and
operation contract. This guide explains the lifecycle and constraints consumers must preserve.

## Public operations

`GET /api/v1/public/projects` accepts `page`, `page_size`, `status`, `technology`, `skill`,
`experience_id`, `featured`, `search`, and `sort`. Sort is `default`, `start_date`, or `id`, with
the accepted descending form where applicable. Repeated singleton parameters, unsupported fields,
invalid UUIDs/catalog values, and unbounded text return the shared 422 envelope.

The default order is featured first, curated position, start date descending, then opaque ID. The
response uses the shared list envelope and contains only visible, nondeleted, database-time-
effective frozen revisions. `GET /api/v1/public/projects/{slug}` applies the identical eligibility
rules; every absent or nonpublic slug returns the same safe 404.

```http
GET /api/v1/public/projects?technology=PostgreSQL&status=active&page=1&page_size=20
Accept: application/json
```

Public project data contains case-study content, safe links, display facts, SEO inputs, and only
public-safe relation summaries. It never contains draft/published pointers, revision or creator
IDs, schedules, deletion data, versions, audit facts, storage identifiers, or media URLs.
`gallery_available` is always `false` until the media capability is delivered. Public responses
are immediately revalidated so a cache cannot outlive the next schedule boundary.

## Administrator operations

Every route below requires a full administrator session. Unsafe methods additionally require the
accepted same-origin `Origin` and cookie CSRF header. Reads and preview are private `no-store`.

| Method and path                                      | Purpose                                   | Concurrency/idempotency           |
| ---------------------------------------------------- | ----------------------------------------- | --------------------------------- |
| `GET /api/v1/admin/projects`                         | Filtered/paginated administrator list     | read-only                         |
| `POST /api/v1/admin/projects`                        | Create aggregate and mutable revision 1   | `Idempotency-Key`                 |
| `PUT /api/v1/admin/projects/actions/reorder`         | Replace complete nondeleted order         | `If-Match`, `Idempotency-Key`     |
| `GET /api/v1/admin/projects/{id}`                    | Read draft/publication/lifecycle and ETag | read-only                         |
| `PUT /api/v1/admin/projects/{id}`                    | Replace current mutable draft             | `If-Match`                        |
| `GET /api/v1/admin/projects/{id}/preview`            | Read authenticated draft preview          | `X-Robots-Tag: noindex, nofollow` |
| `PUT /api/v1/admin/projects/{id}/featured`           | Set featured independently                | `If-Match`                        |
| `PUT /api/v1/admin/projects/{id}/visibility`         | Set visibility independently              | `If-Match`                        |
| `PUT /api/v1/admin/projects/{id}/actions/publish`    | Publish now or at `publish_at`            | `If-Match`, `Idempotency-Key`     |
| `PUT /api/v1/admin/projects/{id}/actions/reschedule` | Replace only the publication instant      | `If-Match`, `Idempotency-Key`     |
| `PUT /api/v1/admin/projects/{id}/actions/unpublish`  | Clear public eligibility                  | `If-Match`, `Idempotency-Key`     |
| `DELETE /api/v1/admin/projects/{id}`                 | Confirmed soft delete                     | `If-Match`                        |

Administrator filters are `lifecycle`, `visible`, `featured`, `status`, `skill_id`,
`experience_id`, and `search`. Sort fields are `position`, `name`, `status`, `start_date`,
`updated_at`, and `id`.

## Revision, relation, and input rules

Publishing freezes the draft, assigns it as the publication, and creates an identical mutable copy
atomically. Later draft changes never alter public content, SEO, links, or relations. Scheduling is
an absolute UTC timestamp evaluated with PostgreSQL `now()`. Use the strong response ETag as the
next `If-Match`; stale values fail with the shared precondition error. An idempotency key can replay
only the same canonical request digest.

Skill and experience IDs are resolved through their application facades. Related project IDs are
duplicate-free, cannot self-reference, and are checked transactionally against a bounded directed
graph. Missing/deleted references or cycles return field-addressable safe errors. Input models
forbid undeclared fields, so mass-assignment data is rejected.

All content fields are bounded. Controlled Markdown forbids raw HTML and unsafe destinations.
Optional links are HTTPS-only, credential-free, and fragment-free. `cover_media_id` and ordered
`screenshot_media_ids` accept only ready media assets. Their usages are revision-scoped and public
delivery follows the current visible published project pointer.
