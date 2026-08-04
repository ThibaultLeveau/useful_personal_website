# M13 release-readiness evidence

Date: 2026-08-04
Environment: local production build, Next.js at `http://127.0.0.1:13013`, API proxy to the isolated local stack
Disposition: **BLOCKED**

M13 is not accepted yet. Product discovery, accessibility automation, cross-browser shells,
frontend and backend quality gates, Lighthouse, repository hygiene, SAST, and dependency audits
pass. Current release-candidate images and secret scans also pass. Owner decisions remain open and
manual assistive-technology/real-device checks have not been performed.

## Current gate summary

| Gate                             | Result                                   | Evidence                                                                                |
| -------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------- |
| Production frontend build        | Pass                                     | Next.js 16.2.12, 28 static outputs, including robots and social image                   |
| Frontend lint/type/unit          | Pass                                     | ESLint, strict TypeScript, 40 files and 156 tests                                       |
| Storybook build                  | Pass with documented build-size advisory | Production static Storybook generated                                                   |
| Browser/axe shell matrix         | Pass                                     | 30/30 across Chromium at 320/360/390/768/1024/1280/1440/1920 and Firefox/WebKit at 1440 |
| Lighthouse                       | Pass                                     | Desktop 100/100/100/100; mobile 94/100/100/100                                          |
| Backend lint/format/type         | Pass                                     | Ruff, Ruff format, strict Mypy across 248 source files                                  |
| Backend functional tests         | Pass                                     | 544/544 passed, zero skips, on a fresh least-privilege PostgreSQL database              |
| Backend coverage                 | Pass                                     | 85.0018% branch-aware coverage; frozen target >=85%; no relaxed exclusions              |
| Bandit                           | Pass                                     | No findings after replacing closed-choice dynamic SQL with static statements            |
| Python dependency audit          | Pass                                     | No known vulnerabilities                                                                |
| Node production dependency audit | Pass with host warning                   | No known vulnerabilities; exact Node 22.23.2 production image separately passes         |
| Project/dependency licenses      | Pass                                     | Canonical MIT License installed; dependency inventories compatible                      |
| Current image/secret scans       | Pass                                     | Gitleaks: zero leaks; Trivy: zero High/Critical findings in both current images         |
| Exact production Node runtime    | Pass                                     | Current frontend image built and ran on Node 22.23.2 as non-root                        |
| Manual AT/real devices           | **Blocked**                              | Requires human/device execution                                                         |

## Defects found and repaired

1. Definition-list context was emitted as an invalid paragraph sibling. It is now contained in the
   `dd` and covered by a structural test.
2. CMS rich-text headings could start at `h3`. Page content now normalizes its heading floor while
   preserving relative hierarchy.
3. Runtime migration compatibility still pointed to the M9 head after M10-M12. The accepted head is
   now `20260802_0013`, the complete linear history is asserted, and clean upgrade/downgrade tests
   pass.
4. API token scopes redundantly declared uniqueness in addition to their composite primary key.
   Model and pre-release migration now match without an autogenerate diff.
5. Two database timestamp methods returned SQLAlchemy `Any`. Explicit safe casts restore strict
   typing.
6. Bandit identified closed-choice string-built SQL. Each website-settings media role now uses an
   explicit static statement.

## Evidence index

- [Accessibility and browser matrix](accessibility.md)
- [Security and supply chain](security-supply-chain.md)
- [Current image and secret scans](security/README.md)
- [Performance](performance/README.md)
- [Coverage and backend test status](coverage.md)
- [Owner decisions](owner-decisions.md)
- [Operations readiness](operations.md)
- [Documentation walkthroughs](walkthroughs.md)
- [Image generation provenance](imagegen.md)
- [Screenshot inventory](screenshots/README.md)
