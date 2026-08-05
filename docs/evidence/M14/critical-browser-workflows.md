# Credentialed critical browser workflows

Date: 2026-08-05
Executor: Codex local release-validation session
Environment: isolated PostgreSQL and current production backend/frontend containers

## Coverage correction

The earlier hosted shell matrix exercised 30 responsive/accessibility route checks, but
credential-gated administrator journeys were skipped because CI did not bootstrap an administrator
or provide application keys. The browser job now creates masked disposable credentials, bootstraps
the administrator through standard input, completes forced password change first, and executes the
stateful critical workflows serially.

New real-stack journeys cover:

- configurable page creation, typed block configuration, media selection, reorder, duplicate,
  hide, preview, export, publish, public render/accessibility, unpublish, and delete;
- verified image upload, rename, usage activation/deactivation, and safe deletion;
- public contact submission plus private read/archive/restore/delete handling;
- scoped API-token create/reveal-once/use/rotate/revoke behavior against the integration API.

## Corrective findings

The browser work found and corrected four product defects: media initial loading could repeat due to
an unstable deferred-load callback; successful asynchronous media/contact submissions could be
misreported because a React event target was read after `await`; and contact/API-token routes had
invalid main-landmark or skip-link targets. Hosted Linux execution also exposed a 320 px project
title overflow caused by a long unbroken segment; the public heading now wraps at arbitrary content
boundaries. Focused lint, strict TypeScript, production build, and the media regression suite passed
after correction.

## Result

Authentication passed against the rebuilt production frontend. The final combined credentialed
phase passed 3/3 in 55.2 seconds: API tokens 12.9 s, contacts 12.7 s, and pages/media 24.1 s. Exact
disposable-project teardown left zero containers, zero volumes, and zero networks.

Hosted CI then executed all 41 browser tests: 30 cross-browser responsive/accessibility shell tests,
authentication, and ten remaining credentialed real-stack workflows. All passed, including the
320 px project regression, on commit `a99b40878ca9a69801eb3d3b9821151268a8bb9d`
([run 30964510984](https://github.com/ThibaultLeveau/useful_personal_website/actions/runs/30964510984)).
