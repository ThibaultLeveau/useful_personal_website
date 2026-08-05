# Manage professional experience

The Experience workspace lets an administrator prepare, preview, publish, schedule, hide, reorder,
unpublish, and delete professional roles without exposing unfinished edits.

## Create and edit a role

1. Sign in and open **Content > Experience** at `/admin/experiences`.
2. Enter the company, role, and start date, then create the draft.
3. Complete the editor sections for employment type, work style, dates, summary, optional location
   and HTTPS company URL, responsibilities, achievements, technologies, and related skills.
4. Save the draft. Validation errors are shown beside the affected field and do not discard the
   other values.
5. Use **Preview draft** to review the private, non-indexable version before publication.

Dates are calendar dates. A current position cannot have an end date; a past position may have an
unknown end date. Responsibilities, achievements, and technologies preserve the order entered.

## Publication and visibility

- **Publish now** freezes the reviewed draft and makes that revision eligible for the public
  timeline. A fresh editable copy is created automatically.
- **Schedule** accepts an absolute publication instant. Eligibility is evaluated by PostgreSQL
  time, so no background scheduler has to change a status row.
- Editing after publication changes only the draft. The current public revision stays unchanged
  until the next publish.
- **Hide** removes an otherwise published role from the public timeline without changing its
  publication history. **Show** restores eligibility.
- **Unpublish** removes public eligibility and retains all revisions.
- **Delete** is a separate confirmed soft-delete action. It does not erase retained revision and
  audit history.

The list uses text status labels for Draft, Scheduled, Published, Published - changes pending, and
Unpublished. Reorder controls change curated administrator order; the public page remains ordered
by real chronology.

## Public timeline and filters

The public page is `/experience`. Visitors can filter by current role, engagement type, and work
style. Skill links point to the matching entry on `/skills`. Only visible, effective publications
and visible skill summaries appear. Drafts, future schedules, hidden/deleted records, revision
metadata, administrator identifiers, and concurrency data are never included in the public model.

If there are no eligible roles, the page presents an intentional empty state. If the API is
temporarily unavailable, it presents a separate retry message.

## Concurrent edits and recovery

Each record uses a version ETag. If another session changes the record first, a stale save or
lifecycle action is rejected instead of overwriting the newer work. Reload the editor, compare the
new state, and deliberately reapply the intended change. Retrying a publish, schedule, unpublish,
create, or reorder request with the same idempotency key is safe only when its payload is unchanged.
