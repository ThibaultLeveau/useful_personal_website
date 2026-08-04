# Pages and blocks

The Pages workspace manages the public Home route and custom top-level pages. Open **Administration → Pages** to create a page or open its builder. Home is a singleton; custom pages require a lowercase slug that does not collide with the application’s reserved routes.

## Builder

The builder presents the validated block palette, the ordered draft canvas, and the selected block’s properties. At 1440 px and wider these are three panes. Medium layouts use two panes, and narrow layouts put palette, canvas, and inspector into one reading order. Dragging is never required: every block has Move up and Move down controls.

The palette contains exactly these version-1 blocks: hero, profile summary, call to action, statistics, skills grid, featured skills, experience summary, experience list, project grid, featured projects, latest posts, rich text, image, image with text, links collection, contact callout, testimonial, divider, and spacer.

Common properties control title, subtitle, description, layout, theme, visibility, and responsive presentation. The typed configuration field shows the exact per-kind object. It is JSON for precise administrator control, but it is not an escape hatch: the API rejects unknown keys, unsupported versions, unsafe destinations, arbitrary CSS/HTML/code, invalid identifiers, and out-of-bound collections. Rich text is controlled CommonMark and is sanitized by the released content policy.

Image and image-with-text blocks open the shared media picker and require a ready asset. Set meaningful
alt text, an optional caption, and focal position before publishing. Public pages receive responsive
stripped renditions only while the visible published block remains active.

## Preview and publication

**Check preview** resolves public-safe references and lists publication issues. Choosing an issue focuses its owning block. Preview is private and `noindex`; it is not a public route.

Use **Publish now**, **Schedule**, **Reschedule**, or **Unpublish** from the sticky action bar. Scheduling uses an ISO 8601 timestamp with a timezone and becomes effective from PostgreSQL time without a worker. Publishing freezes the selected revision and creates an independent new draft. Later edits remain private until the next publish.

**Export** downloads the canonical private manifest with its integrity checksum. Custom pages can be duplicated to a new reviewed slug. Home cannot be duplicated or deleted.

If another editor changes the page first, the API returns a version conflict. The builder keeps local form values so they can be compared or copied before reloading. Mutations use the signed-in session, same-origin CSRF protection, `If-Match`, and retry-safe request keys where required.
