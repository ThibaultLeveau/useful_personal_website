# Accessibility Checklist

Target: WCAG 2.2 AA. This checklist is a design and verification contract, not a claim of conformance. A release needs automated scans plus manual/browser-assisted evidence on representative public and admin workflows (NFR-002-NFR-003 / AC-032).

## Structure and semantics

- [ ] One descriptive `h1`; headings form a meaningful hierarchy independent of visual size.
- [ ] `header`, `nav`, `main`, complementary regions, and `footer` have unique labels where repeated.
- [ ] First focusable item is a visible Skip to main content link; admin editors also provide Skip to editor when useful.
- [ ] Lists, timelines, cards, quotes, article metadata, tables, and pagination use native semantics.
- [ ] Page titles, language, link purpose, status, and route changes are announced meaningfully.
- [ ] Draft/hidden resources never leak through headings, metadata, live regions, or cached unauthorized UI.

## Keyboard, focus, and input

- [ ] Every action works with keyboard alone; no keyboard trap outside deliberate modal focus containment.
- [ ] Focus order follows reading/task order. Focus-visible ring is at least 3 px, high contrast, and never clipped.
- [ ] Sticky headers/action bars, drawers, and virtual keyboards do not obscure the focused item (WCAG 2.4.11/2.4.12).
- [ ] Dialogs/sheets set initial focus deliberately, contain focus, close with Escape when safe, and restore the invoker.
- [ ] Drag/reorder/gallery gestures have buttons or keyboard equivalents (WCAG 2.5.7).
- [ ] Touch targets are designed at 44 x 44 px and never below WCAG 2.5.8's minimum without an applicable exception.
- [ ] No action depends on hover, path-based gesture, device motion, orientation, or multipoint input.
- [ ] Single-character shortcuts are disabled while typing and can be discovered/turned off where applicable.

## Forms and authentication

- [ ] Every field has a persistent programmatic label; instructions precede input; required/optional state is textual.
- [ ] Correct `autocomplete`, input type/mode, and accessible name/description/error relationships are present.
- [ ] Error summary receives focus after failed submit and links to inline errors; errors explain correction and do not rely on color.
- [ ] Entering data once is not required again unnecessarily; selections survive validation errors (WCAG 3.3.7).
- [ ] Login/password change permits paste, password managers, and reveal; no memory/transcription/puzzle test is imposed (WCAG 3.3.8).
- [ ] Destructive/security-sensitive submissions provide review, confirmation, and reversal where appropriate (WCAG 3.3.4/3.3.6).
- [ ] Session expiry warning gives enough time/action where feasible and never leaves private content visible.
- [ ] Contact consent is separate, plain language, not preselected, and linked to privacy information.

## Visual and responsive

- [ ] Normal text contrast >=4.5:1; large text >=3:1; controls/focus/status boundaries >=3:1 in light and dark themes.
- [ ] Meaning never depends on color; status uses text plus icon/shape.
- [ ] Content remains usable at 200% text zoom and 400% browser zoom without two-dimensional page scrolling except contained data/media regions.
- [ ] Text spacing overrides do not clip or overlap content.
- [ ] Light/dark/system initialization avoids a disorienting flash; forced-colors/high-contrast modes retain controls and focus.
- [ ] Reduced-motion preference removes nonessential transform, shimmer, parallax, counters, and smooth scroll.
- [ ] Responsive order matches DOM/reading order; CSS does not create a misleading focus sequence.

## Images, media, and rich content

- [ ] Meaningful images use administrator-managed purpose-specific alt text; decorative images use empty alt and are ignored.
- [ ] Image picker distinguishes missing alt from intentionally decorative usage; filenames are never default alt text.
- [ ] Captions are associated; galleries identify position and offer named previous/next controls.
- [ ] Screenshots remain legible or open at a usable size; no critical meaning is encoded only inside an image.
- [ ] Markdown output has safe heading hierarchy, named links, code labels/copy feedback, and scrollable tables with context.
- [ ] No autoplaying audio/video; any future time-based media requires captions/transcript/control.

## Components and dynamic states

- [ ] Loading skeletons are hidden from assistive tech; one concise status describes loading.
- [ ] Empty, error, unauthorized, offline, conflict, save, upload, copy, and reorder outcomes are announced without repetitive noise.
- [ ] Toasts are dismissible/persistent enough and never the only place for critical information.
- [ ] Tables expose captions/headers/sort via `aria-sort`; responsive cards carry equivalent labels/actions.
- [ ] Tabs, comboboxes, menus, tooltips, tree/outline, command menu, pagination, and disclosure follow established ARIA patterns.
- [ ] Disabled controls remain understandable; an explanation exists when the reason is not evident.
- [ ] Publication, visibility, featured, token, health, and contact lifecycle states have explicit text.

## Manual verification matrix

Test at minimum:

| Workflow | Keyboard + focus | Screen reader | Zoom/reflow | Themes/motion |
|---|---:|---:|---:|---:|
| Public Home/nav/theme/custom blocks | Yes | Yes | 320 px + 400% | Light/dark/system/reduced |
| Projects filter/detail/gallery | Yes | Yes | Yes | Both themes |
| Blog filter/article/Markdown | Yes | Yes | Yes | Both themes |
| Contact validation/rate/error/success | Yes | Yes | Yes | Both themes |
| Login/forced password/session expiry | Yes | Yes | Yes | Both themes |
| Admin table/filter/form/error/conflict | Yes | Yes | Yes | Both themes |
| Page block add/reorder/preview/publish | Yes | Yes | Yes | Reduced motion + touch |
| Media upload/picker/in-use delete | Yes | Yes | Yes | Both themes |
| Token one-time copy/rotate/revoke | Yes | Yes | Yes | Both themes |
| Contact read/archive/delete | Yes | Yes | Yes | Both themes |

Record tool/version, browser, viewport, theme, assistive technology, result, screenshot/video where useful, defect ID, and retest evidence. Automated axe/Lighthouse results cannot waive a manual blocker.
