# M13 Lighthouse performance evidence

Local production build measured on 2026-08-04 with Chrome and Lighthouse against
`http://127.0.0.1:13013/`.

| Profile | Performance | Accessibility | Best practices | SEO |   FCP |   LCP |    TBT | CLS |
| ------- | ----------: | ------------: | -------------: | --: | ----: | ----: | -----: | --: |
| Desktop |         100 |           100 |            100 | 100 | 0.3 s | 0.6 s |  20 ms |   0 |
| Mobile  |          94 |           100 |            100 | 100 | 0.9 s | 2.5 s | 220 ms |   0 |

Both profiles meet the frozen thresholds: performance >=90, accessibility >=95, and SEO >=95.
The JSON reports are `lighthouse-home-desktop.json` and `lighthouse-home-mobile.json` in this
directory. Results are local lab measurements, not field Core Web Vitals; production RUM remains an
operator follow-up.

The Storybook production build reported large documentation-only chunks containing Storybook and
axe. Those chunks are not part of the public Next.js route bundles; the advisory is recorded rather
than suppressed.
