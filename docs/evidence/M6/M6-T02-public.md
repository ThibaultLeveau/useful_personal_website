# M6-T02-P - Public projects frontend and P5 freeze

## Outcome

Pass. `/projects` and `/projects/{slug}` are Server Components whose initial content and metadata
come from generated server-only API wrappers. The collection provides labeled search/status/
technology filters, URL state, exact public count, active-filter summary, clear action,
deterministic pagination, distinct no-match/unavailable states, and focusable results heading.

The detail has one `h1`, semantic case-study sections, status/date/role facts, controlled Markdown,
safe external links, ordered public relations, escaped JSON-LD, canonical metadata, and an
intentional reserved-geometry gallery fallback. It never invents imagery, outcomes, links, or
relation summaries.

## Verification and P5

Public project unit/component tests pass 9/9; the complete frontend candidate passes 130 tests in
29 files. Generated-wrapper, list/card, empty/error, link safety, lifecycle privacy, and rendering
behavior are covered. The production build emits dynamic SSR routes for both collection and detail.

Playwright passes 2/2 real-stack lifecycle projects. Axe reports zero violations. Layout has no
horizontal overflow at 320, 360, 390, 768, 1024, 1280, 1440, or 1920 px in light/dark themes; the
320 CSS-pixel reflow proof covers the 1280 px at 400% equivalent. Integration/root additionally
inspected the live collection/detail at desktop and 390 px in the in-app browser.

Lighthouse collection/detail accessibility and SEO are 100 in every complete profile. Desktop
performance is 90 and 98. Throttled mobile is 66 and 75 with zero CLS, retained as the known shared
runtime target variance for M13/M14. Dynamic metadata streaming initially caused Lighthouse to
miss the detail description; blocking head delivery corrected detail SEO from 90 to 100. P5 is
frozen after that retest.
