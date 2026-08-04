# M5-T01-P - Public experience projection

## Outcome

Pass. `GET /api/v1/public/experiences` returns only visible, nondeleted, due publications whose
pointed revision is frozen. The response is paginated, deterministically ordered, and filterable by
allow-listed current/employment/remote/skill values. Invalid or repeated singleton parameters fail
with stable field-addressable errors.

The public DTO exposes employment content plus visible skill `name`/`slug` summaries only. Hidden
skills and every draft, pointer, schedule, revision, creator, version, deletion, and audit field are
absent. Scheduled eligibility uses PostgreSQL `now()`; cache headers force immediate shared-cache
revalidation so a future publication cannot be held stale. No worker or application-clock decision
is involved.

Integration tests prove hidden/draft/future/deleted exclusion, chronology/filter behavior, safe
allow-list rejection, empty pages, and live-public immutability while a copied draft changes. The
browser lifecycle test independently observes publication, pending edits, republish, hide/show,
unpublish, and delete on the rendered public timeline.
