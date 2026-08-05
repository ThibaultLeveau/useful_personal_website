# M6 performance, metadata, and bundle evidence

## Profile

- Candidate: production Compose images on loopback; Lighthouse 12.8.2 with headless Chrome,
  `performance,accessibility,seo`; desktop preset and default simulated mobile profile.
- Data: two synthetic API/UI-created public project proofs for measurement; no private draft text or
  credentials are present in reports.
- Targets: performance >=90, accessibility >=95, SEO >=95; CLS 0 target.

## Results

| Route/profile      | Performance | Accessibility | SEO | FCP   | LCP   | TBT      | CLS |
| ------------------ | ----------: | ------------: | --: | ----- | ----- | -------- | --: |
| Collection desktop |          90 |           100 | 100 | 0.3 s | 0.8 s | 260 ms   |   0 |
| Collection mobile  |          66 |           100 | 100 | 1.0 s | 3.1 s | 1,980 ms |   0 |
| Detail desktop     |          98 |           100 | 100 | 0.4 s | 0.8 s | 80 ms    |   0 |
| Detail mobile      |          75 |           100 | 100 | 1.4 s | 2.9 s | 840 ms   |   0 |

Accessibility and SEO pass every profile. Both desktop performance profiles pass. Simulated mobile
remains below target, consistent with the known shared Next.js main-thread variance recorded at M5;
no security, SSR, metadata, or accessibility behavior was weakened to raise it. M13/M14 retain the
release-wide optimization/retest obligation.

One initial detail desktop report scored SEO 90 because Next.js streamed dynamic description tags
after the head. `htmlLimitedBots: /.*/` now keeps dynamic public metadata in the initial head; exact
production build and HTTP inspection pass, and both repeated detail profiles score SEO 100. A
separate mobile launch failed before navigation with `NO_NAVSTART`; its incomplete report was
overwritten and is not evidence.

The optimized production build succeeds under Node 22.23.2, emits 19 static pages plus dynamic
project collection/detail routes, and reuses one React-cached detail projection across metadata and
page rendering. Initial project content is SSR; there is no project-only client fetch/hydration
boundary. Raw reports are the four JSON files in this directory. Database evidence is in
[query-plans.md](query-plans.md).
