# M6-T02-A - Administrator projects frontend

## Outcome

Pass. `/admin/projects`, `/admin/projects/new`, edit, and preview expose every active project field,
provider relations, SEO, configured-timezone scheduling, reorder, feature/show-hide, publication,
reschedule, unpublish, and confirmed deletion through the generated client wrapper.

The manager has pending/applied filters, exact result status, clear action, responsive table/cards,
and non-drag reorder controls. The editor retains safe input, presents linked validation issues,
uses server ETags/idempotency, applies authoritative returned aggregates, and distinguishes Draft,
Scheduled, Published, Published - changes pending, and Unpublished. Media controls truthfully report
the unavailable capability. Preview is private and non-indexable.

## Corrective loop and verification

Browser testing found and corrected a narrow-toolbar overflow, an invalid preview status role, a
same-route stale editor after save, and the missing `Publish changes` action for pending revisions.
Focused admin unit tests pass 7/7, including 2 editor lifecycle regressions. Project stories cover
manager/editor states and provider/media/SEO/lifecycle surfaces. Prettier, ESLint, strict
TypeScript, production build, and the Node 22 Storybook build pass.

The real-stack lifecycle suite passes at 320 and 1440 px with zero axe violations, explicit status
announcements, private preview denial for anonymous requests, and responsive screenshots.
