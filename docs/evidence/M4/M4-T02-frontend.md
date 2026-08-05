# M4-T02 frontend - Public and administrator skills experiences

## Outcome

Pass. `/skills` is a grouped, filterable Server Component backed by the generated public client.
`/admin/skills` provides accessible category and skill CRUD, visibility/featured controls,
reassignment, pagination/filtering, complete-order safety, and explicit unavailable relation state.

## Validation

| Category                              | Result                                                                                                                                                          |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prettier / ESLint / strict TypeScript | Pass                                                                                                                                                            |
| Vitest                                | 20 files, 110 tests, all pass with two constrained workers                                                                                                      |
| Coverage                              | 44.13% statements / 29.21% branches / 41.51% functions / 46.73% lines overall; skills 50.23% statements; generated client materially dilutes aggregate coverage |
| Production build                      | Pass; `/skills` dynamic SSR and `/admin/skills` protected static shell                                                                                          |
| Storybook                             | Pass; skills public/admin states included; generic docs chunk/plugin timing warnings only                                                                       |
| M4 built-stack E2E                    | 4/4 at 320/1440: grouping/filters/privacy/CRUD/reassign/order/filter safety/delete/axe/reflow/screenshots                                                       |
| Full built-stack E2E                  | 16/16 at 320/1440 after correcting an older footer locator for the new Skills link                                                                              |
| Fresh no-seed E2E                     | 2/2 at 320/1440; empty public data/state and protected admin redirect; no bootstrap/seed rows                                                                   |
| Lighthouse desktop                    | Performance 97, accessibility 100, SEO 100; LCP 984 ms, CLS 0, TBT 112 ms, 195,206 bytes                                                                        |
| Lighthouse mobile                     | Performance 70, accessibility 100, SEO 100; LCP 3,112 ms, CLS 0, TBT 1,101 ms, 190,417 bytes                                                                    |

Screenshots:

- [Public skills at 320 px](screenshots/public-skills-320.png)
- [Public skills at 1440 px](screenshots/public-skills-1440.png)
- [Administrator skills at 320 px](screenshots/admin-skills-320.png)
- [Administrator skills at 1440 px](screenshots/admin-skills-1440.png)

Automated axe reports zero violations on public and administrator views at both widths. Manual
in-app browser inspection confirms semantic headings/lists/definitions/progress labels, no hidden
draft text, balanced desktop/mobile layout, and no console warnings or errors.

## Corrective loop and variance

- Direct browser request assertions were corrected to the raw snake_case JSON contract; generated
  client consumers remain camelCase.
- A broad Featured locator was scoped to the filter select after checkboxes made it ambiguous.
- The prior M3 footer E2E locator was scoped because the M4 seed legitimately adds a second link.
- Filtered/paginated admin views now disable only reorder controls, not editing, and mutations reload
  the active page so totals and reassignment remain current.
- Mobile Lighthouse performance 70 remains below the >=90 target on the Windows/Docker throttled
  host. Accessibility/SEO are 100, CLS is zero, desktop is 97, and the variance remains an M17/M20
  optimization target rather than a passing claim.
