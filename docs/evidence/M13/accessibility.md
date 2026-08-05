# Accessibility and browser matrix

## Automated result

The production build passed 30 Playwright cases in 2.2 minutes:

- Chromium: public and login shells plus dark-theme control at 320, 360, 390, 768, 1024, 1280,
  1440, and 1920 CSS pixels;
- Firefox: the same three journeys at 1440 pixels;
- WebKit: the same three journeys at 1440 pixels;
- every shell run checks horizontal overflow, a visible main landmark, the expected heading,
  axe-core violations, and a full-page screenshot;
- Chromium and Firefox verify the skip link is first in sequential keyboard order;
- WebKit verifies the same visible focus state programmatically because Playwright WebKit mirrors
  Safari's OS-level default that omits links from sequential focus unless full keyboard access is
  enabled. This limitation is explicit in the test rather than treated as a browser pass-through.

Lighthouse accessibility scored 100 on desktop and mobile. Automated checks found no heading-order
or definition-list violations after the M13 repairs.

## Additional covered states

- light and dark theme selection;
- mobile navigation at 390 pixels;
- protected admin redirect to the sign-in route;
- labelled email/password inputs and password semantics;
- forced-colors and reduced-motion CSS rules are present in the design system;
- prior milestone evidence includes 400% zoom and broader light/dark route captures.

## Manual blockers

The [M14 browser-assisted review](../M14/accessibility/browser-assisted-review.md) independently
confirmed representative public/admin structure, names, focus management, validation errors, theme
state, and 320 CSS-pixel reflow. NFR-003 is therefore verified. Complete WCAG 2.2 AA acceptance
under NFR-002 still requires a human to perform and record:

- NVDA + Firefox and NVDA + Chromium on Windows;
- VoiceOver + Safari on macOS/iOS;
- TalkBack + Chrome on Android;
- real-device reflow, orientation, zoom, switch/voice control, and high-contrast checks;
- content review for link purpose, alternative text quality, error recovery, and reading order.
