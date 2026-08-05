# M7-T01-C - Controlled content security and B3a freeze

## Identity

- Requested milestone: M7; trace alias: M11
- Requirements: F1-011 and the applicable SEC-004-SEC-006, NFR-006-NFR-008,
  NFR-014-NFR-018 contracts
- Executor/reviewer: Integration/root
- Environment: Windows development shell, Python 3.12.13
- Completed UTC: 2026-08-04

## Frozen policy

`upw-commonmark` version `1.0.0` is the sole controlled-content policy. It canonicalizes UTF-8
Unicode to NFC and newlines to LF, validates a bounded CommonMark AST, renders the reviewed table,
strikethrough, task-list, fenced-code, and autolink extensions, then sanitizes through a fixed nh3
allow-list. Raw HTML, Markdown images, embeds, protocol-relative links, credentials, unsafe schemes,
encoded scheme bypasses, controls, and bidi overrides fail closed with stable issue codes.

Only HTTPS and root-relative links are accepted. Article headings are deterministically demoted and
receive collision-safe IDs. Code is escaped and its optional language belongs to a closed catalog.
Tables have a labeled scroll container and task lists render as disabled controls. The safe output
DTO carries the exact source checksum plus policy name/version. Reading time is server-derived at
225 words per minute, rounded up and bounded to 240 minutes.

The source is capped at 100,000 characters, 4,000 lines, 12,000 parsed tokens, 64 nesting levels,
and 2,000 table cells. Sanitized HTML is a derivation, never an independently editable source.

## Malicious corpus and verification

The versioned corpus contains 12 reviewed raw-HTML, event-handler, SVG, Markdown-image, encoded and
plain JavaScript/data URL, protocol-relative, credential, bidi, iframe, and comment cases. Focused
tests also prove supported-format preservation, heading collision behavior, Unicode/newline export
stability, checksum and reading-time determinism, unknown-language degradation, parser limits,
ordinary comparison characters, and escaped hostile-looking code.

The final focused gate passed:

```text
ruff format --check ...  2 files already formatted
ruff check ...           All checks passed
mypy --strict ...        Success: no issues found in 2 source files
pytest ... --no-cov      13 passed in 0.26s
```

Dependencies are exactly pinned and locked as markdown-it-py 4.2.0, mdit-py-plugins 0.6.1, and nh3
0.3.6. No CSP, router, generated-client, migration, frontend, or earlier-milestone file changed in
this lane.

## Decision

B3a passes. The policy, safe-render DTO, limits, extensions, URL rules, provenance, and malicious
corpus are frozen for M7 blog domain, API, SSR boundary, export/reload, and browser verification.
Any incompatible change reopens this gate before downstream acceptance.
