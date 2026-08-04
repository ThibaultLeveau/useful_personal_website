# M7-T02-P - Public blog frontend and B5

## Outcome

Pass. `/blog` and `/blog/{slug}` are Server Components backed by generated public wrappers. The
collection provides labeled search/tag/category/order filters, URL state, exact public totals,
clear action, deterministic pagination, and distinct empty/no-result states. Article pages expose
one `h1`, semantic metadata, controlled content, public taxonomy and related summaries, canonical
and Open Graph metadata, escaped Article JSON-LD, and sitemap integration.

The only HTML sink accepts the generated safe-render DTO and records policy/checksum provenance.
There is no client parser, arbitrary HTML prop, unsafe fallback, image/embed path, or client-derived
reading time. Public APIs, RSC payloads, HTML, metadata, JSON-LD, sitemap, and result totals exclude
draft/future/hidden/unpublished/deleted content and revision internals.

## Verification and B5

Safe-render/component tests, stories, production SSR build, and the eight-width real-stack journey
pass. Every viewport runs Axe and whole-page overflow checks before capturing admin preview, public
list, and public detail. A 1440 px at 400% reflow-equivalent capture uses a 360 CSS-pixel viewport
and repeats both checks. The final evidence set contains 25 sanitized screenshots.

Lighthouse 12.8.2 scores list/detail performance 100/100 desktop and 91/98 mobile, with
accessibility 100, SEO 100, and CLS 0 in all four profiles. A generic synthetic `Read more` link
initially reduced detail SEO; the representative article and browser proof now use descriptive link
text, and repeated profiles pass. B5 is frozen.
