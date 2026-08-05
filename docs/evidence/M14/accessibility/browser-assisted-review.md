# M14 browser-assisted accessibility review

Date: 2026-08-04
Target: current local release candidate at `http://127.0.0.1:13008`
Browser surface: Codex in-app Chromium browser
Disposition: **Pass for browser-assisted scope; physical assistive-technology review remains open**

## Representative workflows

### Public About page

- `html[lang]` was `en`; the page exposed a unique main landmark, named primary navigation, one
  level-one heading, ordered level-two section headings, a skip link, and no duplicate IDs.
- All 15 detected interactive elements had accessible names.
- At 320 CSS pixels the document width equalled the viewport width (`320px`) with no horizontal
  overflow. The primary navigation collapsed to a named `Menu` button while the public headings and
  footer navigation remained available.
- Opening the mobile menu exposed a `Navigation` dialog with a level-two heading, named close
  control, named mobile navigation, and theme selector. Initial focus moved to `Close`; closing the
  dialog returned focus to `Menu`.
- The focused skip link rendered a solid `2.67px` outline.

### Administrator sign-in

- The 320 CSS-pixel sign-in page had no horizontal overflow and exposed a unique level-one heading,
  skip link, named main landmark, and live status region.
- Email and password controls had persistent labels, `email`/`password` types, and
  `username`/`current-password` autocomplete purposes. Password reveal was a named non-submit
  button; `Sign in` was the only submit button.
- Empty submission moved focus to a `Check the form` alert. Its two messages linked to the email and
  password controls, and both invalid controls retained adjacent error text.
- Selecting Dark applied `data-theme="dark"`, `color-scheme: dark`, a body background of
  `rgb(9, 14, 22)`, and foreground of `rgb(243, 246, 250)`.
- No browser console errors were emitted during the review.

## Corroborating automated evidence

The browser-assisted observations complement, rather than replace, the M13 30-case Chromium,
Firefox, and WebKit matrix, axe checks, keyboard-order assertions, screenshots, forced-colors and
reduced-motion rules, Lighthouse accessibility scores, and prior zoom coverage documented in
[M13 accessibility evidence](../../M13/accessibility.md).

## Explicit limitation

This review used the browser accessibility tree and interactive browser controls. It is not evidence
of speech output, rotor/landmark navigation, switch control, voice control, OS high-contrast
rendering, or real touch behavior. NFR-002 therefore remains in progress until the owner records the
representative desktop/mobile assistive-technology and physical-device matrix listed in the M13
evidence. No WCAG conformance claim is made.
