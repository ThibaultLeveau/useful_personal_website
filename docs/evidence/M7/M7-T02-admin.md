# M7-T02-A - Administrator blog frontend

## Outcome

Pass. `/admin/blog`, `/admin/blog/new`, and `/admin/blog/{id}/edit` provide post search/filtering,
responsive lifecycle/visibility facts, taxonomy maintenance, complete source/SEO/relation fields,
private server preview, exact source export, publish/schedule/reschedule/republish, hide/show,
unpublish, and confirmed deletion through the generated-client wrapper.

The editor offers keyboard-operable CommonMark helpers without a raw-HTML or WYSIWYG escape hatch.
It explains null-only cover media, server-derived reading time, immutable live revisions, database
time scheduling, and ETag conflict recovery. Preview carries a persistent private banner and uses
the sole typed safe-render boundary.

## Verification and corrective loop

Component tests and stories cover manager/editor, taxonomy, preview, lifecycle, and error states.
The complete frontend suite passes 133/133 in 31 files; Prettier, ESLint, strict TypeScript,
production Next build, and Storybook build pass. A full-coverage run exposed one asynchronous test
race; awaiting the API-loaded post and taxonomy corrected it, and the complete rerun passed.

Real-stack Playwright passes at 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px with zero Axe
violations and no page overflow. Browser review corrected a mobile table overflow, pending-republish
copy/action, and a preview save-bar overlap before the final eight-width run.
