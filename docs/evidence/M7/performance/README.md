# M7 performance, accessibility, and SEO evidence

Lighthouse 12.8.2 measured the production Compose frontend on loopback. The detail fixture was
created and published through authenticated APIs with descriptive links, then soft-deleted after
measurement. Reports contain only synthetic public content.

| Route/profile   | Performance | Accessibility | SEO | FCP   | LCP   | TBT    | CLS |
| --------------- | ----------: | ------------: | --: | ----- | ----- | ------ | --: |
| Blog desktop    |         100 |           100 | 100 | 0.3 s | 0.6 s | 10 ms  |   0 |
| Blog mobile     |          91 |           100 | 100 | 1.0 s | 2.6 s | 290 ms |   0 |
| Article desktop |         100 |           100 | 100 | 0.3 s | 0.5 s | 10 ms  |   0 |
| Article mobile  |          98 |           100 | 100 | 0.9 s | 1.8 s | 150 ms |   0 |

All targets (performance >=90, accessibility >=95, SEO >=95) pass. Initial content is SSR and
detail metadata shares the server projection through React request caching. Raw reports are the
four JSON files in this directory.
