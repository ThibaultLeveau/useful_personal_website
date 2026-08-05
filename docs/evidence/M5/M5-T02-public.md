# M5-T02-P - Public experience UI

## Outcome

Pass. `/experience` is a dynamic Server Component route that obtains its initial data through the
generated public client on the server. Semantic headings, an ordered chronology, native GET
filters, text labels, real DOM reading order, visible focus treatment, intentional empty/error
states, and skill links are present without a client-only timeline or unnecessary data fetch.

Automated axe checks report zero violations at 320 and 1440 px. The browser matrix verifies no
horizontal overflow at 320, 390, 768, 1024, 1440, and 1920 px in light and dark themes. Manual
in-app inspection covered the populated timeline and independent 390 px dark empty state. The
public component has 100% test coverage in the final report.

Lighthouse 12.8.2 returned desktop 87/100/100 and mobile 66/100/100 for
performance/accessibility/SEO. Accessibility and SEO exceed target; performance misses the target
and is explicitly retained as a target variance, not a pass. Server response was about 100 ms,
transfer 186 KiB, CLS 0, and desktop LCP 1.2 s; simulated shared-shell main-thread work dominates.
See [performance evidence](performance/README.md). No feature or accessibility behavior was removed
to inflate the score.
