# Physical accessibility acceptance protocol

This protocol closes the human-only portion of NFR-002. It complements the automated and
browser-assisted evidence; it does not permit a conformance claim by itself.

## Preconditions

1. Record the exact candidate commit and confirm its required hosted CI gate is green.
2. Deploy that commit with fictional content and disposable administrator/contact credentials.
3. Record OS, browser, assistive-technology versions, physical device, viewport/orientation, input,
   theme, executor, and UTC timestamp in `wcag-2.2-aa-matrix.csv`.
4. Never capture real contact data, passwords, session cookies, API tokens, or private endpoints in
   screenshots, recordings, or defect reports.

## Execution rules

- Start each screen-reader journey from the browser address bar; do not rely on memorized element
  positions.
- Navigate by landmarks, headings, links, controls, form fields, and sequential focus. Confirm that
  spoken names, roles, states, errors, and live updates match the visible interface.
- Complete the named journey using only the matrix input method. Keyboard tests must not use a
  pointer; switch, voice, and touch tests must use their actual platform controls.
- For zoom/reflow, test 200% text zoom and 400% browser zoom, or the equivalent 320 CSS-pixel
  viewport. Confirm that content and focus remain visible without two-dimensional page scrolling,
  except for intentionally scrollable data/media regions.
- For forced colors/high contrast, verify visible focus, control boundaries, selected/disabled
  states, errors, status, and destructive actions without relying on color alone.
- Exercise both successful and invalid contact/login forms. Confirm that the error summary is
  announced, identifies every invalid field, and supports recovery without losing valid input.
- Exercise mobile navigation open/close, orientation changes, and representative touch targets.
  Confirm focus restoration and that no action requires a path gesture or multipoint gesture.

## Recording and defect handling

Set `result` to `PASS` only after the full row journey succeeds. Use `FAIL` for a reproducible
barrier and `BLOCKED` only when the named equipment or environment is unavailable. A failed row must
include a defect ID and finding; after correction, retain the original result and link durable retest
evidence. Do not delete or overwrite failed observations.

NFR-002 may move to Verified only when every required matrix row is `PASS`, every failure has passing
retest evidence, the candidate commit is unchanged or fully revalidated, and the reviewer records a
signed acceptance reference. Automated axe or Lighthouse results cannot waive a row.
