# Manage project case studies

The Projects workspace lets an administrator build complete case studies, review a private draft,
publish immediately or at a future time, and keep later edits out of the public site until they are
deliberately republished.

## Create and edit a project

1. Sign in and open **Content > Projects** at `/admin/projects`.
2. Choose **New project**, enter the immutable slug and project name, then save.
3. Complete the summary, problem, solution, measurable impact, owner role, architecture,
   technologies, status and dates. Optional repository, demo, SEO, skill, experience, and related
   project fields can be added in the same editor.
4. Save the draft. Field errors remain linked to their controls and other safe input is retained.
5. Use **Preview** to inspect the authenticated, non-indexable draft before publication.

Slugs become lowercase ASCII kebab-case routes and cannot be changed after creation. Status is one
of planned, active, paused, completed, maintenance, or archived. Planned, active, and maintenance
projects cannot have an end date; completed and archived projects require one. Repository, demo,
and canonical URLs must be credential-free HTTPS URLs without fragments.

Case-study sections accept controlled Markdown. Raw HTML and unsafe URL schemes are rejected.
Technologies and relations preserve their entered order and reject duplicates. Related projects
cannot point to the current project or form a cycle.

## Publication, display, and recovery

- **Publish now** freezes the reviewed draft and creates a new editable copy in one transaction.
- **Schedule** interprets the editor value in the configured IANA timezone, converts it to an
  absolute instant, and relies on PostgreSQL time for public eligibility; no worker changes status.
- Editing published content, SEO, or relations produces **Published - changes pending**. The live
  revision stays byte/field-equivalent until **Publish changes** succeeds.
- **Featured** controls curated emphasis; **Hide/Show** controls public visibility independently.
  Reorder controls set the stable collection order.
- **Unpublish** removes eligibility while retaining revisions. **Delete** is a separately confirmed
  soft-delete and keeps audit/reference history.

Every mutation uses a version ETag. If another session writes first, the stale action is rejected
instead of overwriting it. Reload, compare the current server state, and deliberately reapply the
change. Reuse an idempotency key only for an identical create, publish, reschedule, unpublish, or
reorder request.

## Relations and media

Skills and professional experiences are selected through their existing catalogs. Hidden or
nonpublic related content can remain visible to the administrator but is omitted from public
projection. Missing or deleted targets block the mutation safely.

Cover and ordered gallery images use the shared ready-media picker. Each use follows the project
revision lifecycle and keeps its own accessible description. Do not paste storage paths or external
image URLs into project content; public case studies receive only approved responsive renditions.

## Public collection

Visitors browse `/projects` and `/projects/{slug}`. The collection supports search, status, and
technology filters with an exact public result count, clear action, and deterministic pagination.
Only visible, effective frozen publications appear. Draft, future, hidden, unpublished, deleted,
revision, creator, schedule, concurrency, and unavailable relation details never enter the public
API, rendered page, metadata, JSON-LD, or result totals.
