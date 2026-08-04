# M5 performance and query evidence

## Profile

- Candidate: exact production images recorded in [M5 acceptance](../README.md), local loopback
  Compose stack on Windows/Docker Desktop.
- Lighthouse: 12.8.2, headless Chrome cold launch, `performance,accessibility,seo`; desktop preset
  and default simulated mobile profile.
- Page/data: `/experience`, five seeded skills and lifecycle-created synthetic experience records;
  the E2E cleanup left four soft-deleted aggregates and no public result at final measurement.
- Targets: performance >=90, accessibility >=95, SEO >=95; CLS 0 target.

## Results and disposition

| Profile          | Performance | Accessibility | SEO |    FCP |    LCP |      TBT | CLS |
| ---------------- | ----------: | ------------: | --: | -----: | -----: | -------: | --: |
| Desktop          |          87 |           100 | 100 |  0.5 s |  1.2 s |   260 ms |   0 |
| Simulated mobile |          66 |           100 | 100 | 1.06 s | 3.38 s | 1,461 ms |   0 |

The accessibility and SEO targets pass. Performance remains a documented target variance. The
root document response was about 100 ms and total transfer was 186 KiB; the mobile trace attributes
most delay to simulated main-thread work in the shared Next.js runtime/shell. The M4 route on the
same runner measured 97 desktop/70 mobile, so the mobile result is consistent with the known local
simulation constraint while the desktop result is seven points lower. This is not waived as a
release target: M13/M14 must repeat on the frozen release candidate and optimize the shared shell if
the variance persists. Security, semantics, theme controls, and functionality were not reduced.

Four attempted repeat launches are excluded: Lighthouse failed before navigation with
`NO_NAVSTART` and a locked temporary Chrome profile. Only the two reports with complete categories
are authoritative. The invalid generated reports were removed; the corrective-loop finding remains
recorded here.

## Server, bundle, and database observations

- `/experience` performs one server-side public API request plus the two parallel public-shell API
  requests; the timeline itself has no client fetch or hydration boundary.
- The production build succeeds and classifies `/experience` as dynamic SSR. Its network trace is
  186 KiB total; the largest script transfer is about 70 KiB.
- Public repository loading is capped by regression test at seven SELECTs for a page, independent
  of relation count. No unbounded page size is accepted.
- On the tiny final browser dataset, the effective-public plan completes in 0.274 ms with 15 shared
  buffer hits. PostgreSQL reasonably chooses sequential scans for four aggregates; partial public
  and frozen chronology indexes are installed for production-shaped cardinalities.
- Schedules are query-time predicates using PostgreSQL `now()` and zero shared-cache TTL. There is
  no polling worker or status-flip write load.
