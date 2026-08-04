# Experiences API

The experience slice is served under `/api/v1`. The canonical request/response definitions are in
[OpenAPI](openapi.json); this page explains the workflow and invariants a consumer must preserve.

## Public collection

`GET /api/v1/public/experiences` is anonymous and returns only visible, nondeleted, effective,
frozen publications. Supported query parameters are `page`, `page_size`, `current`,
`employment_type`, `remote_status`, `skill`, and `sort`. Filters and sort fields are allow-listed;
unknown or repeated singleton parameters return the standard 422 error envelope.

The default `chronology` sort is current position first, then start date descending, end date
descending with nulls last, curated position, and opaque ID. `id` and `-id` are also supported.
The response uses the shared list envelope and pagination metadata. It intentionally omits draft,
revision, scheduling, creator, deletion, and version fields. Responses are public but immediately
revalidated so a scheduled publication cannot be cached past its effective instant.

Example:

```http
GET /api/v1/public/experiences?current=true&remote_status=hybrid&skill=python&page=1&page_size=20
Accept: application/json
```

## Administrator operations

All routes below require a full administrator session. Unsafe calls also require the accepted
same-origin/CSRF headers. Read responses and preview responses use private `no-store` caching.

| Method and path                                         | Purpose                                      | Concurrency/idempotency                      |
| ------------------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| `GET /api/v1/admin/experiences`                         | Paginated/filterable administrator list      | read-only                                    |
| `POST /api/v1/admin/experiences`                        | Create aggregate plus mutable revision 1     | `Idempotency-Key`                            |
| `PUT /api/v1/admin/experiences/actions/reorder`         | Replace the complete nondeleted order        | `If-Match`, `Idempotency-Key`                |
| `GET /api/v1/admin/experiences/{id}`                    | Read draft, publication, lifecycle, and ETag | read-only                                    |
| `PUT /api/v1/admin/experiences/{id}`                    | Replace the current mutable draft            | `If-Match`                                   |
| `GET /api/v1/admin/experiences/{id}/preview`            | Read a private draft preview                 | read-only; `X-Robots-Tag: noindex, nofollow` |
| `PUT /api/v1/admin/experiences/{id}/visibility`         | Set independent visibility                   | `If-Match`                                   |
| `PUT /api/v1/admin/experiences/{id}/actions/publish`    | Publish now or at `publish_at`               | `If-Match`, `Idempotency-Key`                |
| `PUT /api/v1/admin/experiences/{id}/actions/reschedule` | Change only the schedule                     | `If-Match`, `Idempotency-Key`                |
| `PUT /api/v1/admin/experiences/{id}/actions/unpublish`  | Clear public eligibility                     | `If-Match`, `Idempotency-Key`                |
| `DELETE /api/v1/admin/experiences/{id}`                 | Confirmed soft delete                        | `If-Match`                                   |

Use the strong ETag returned by a read or mutation as the next `If-Match` value. A stale value
returns the shared precondition error. Reusing an idempotency key with different canonical input is
rejected.

## Content and lifecycle rules

Employment type is one of `full_time`, `part_time`, `contract`, `freelance`, `internship`,
`apprenticeship`, `temporary`, `seasonal`, or `volunteer`. Remote status is `onsite`, `hybrid`, or
`remote`. Company URLs must be credential-free HTTPS URLs. Ordered text fields are plain text and
reject empty or duplicate normalized values. Skill IDs are resolved through the skills facade and
stored on the revision.

Publishing freezes the draft, points the aggregate at it, and creates an identical mutable copy in
one transaction. Later draft changes do not mutate the public revision. All errors use the shared
safe envelope and field-addressable issue codes; transport clients should branch on codes, not
message text.
