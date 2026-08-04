# ADR-0005: Controlled Markdown

- **Status:** Accepted
- **Date:** 2026-08-02

## Context

Blog and rich text need a safe portable authoring format; raw HTML is prohibited (`F1-012`).

## Options considered

Sanitized HTML; editor-specific structured JSON; controlled Markdown.

## Decision

Store UTF-8 CommonMark Markdown with a fixed extension allow-list (tables, strikethrough, task lists, fenced code, autolinks). Disable embedded raw HTML and unsafe URL schemes. Render through one pinned policy and sanitize the resulting HTML as defense in depth.

## Consequences

Content is portable, diffable, and easy to export. Complex WYSIWYG layouts are limited; pages use typed blocks instead. Renderer policy changes can affect output and therefore require regression tests/version notes.

## Follow-up

Add malicious-content corpus tests, link/image resolver tests, policy documentation, and export/reimport acceptance coverage.
