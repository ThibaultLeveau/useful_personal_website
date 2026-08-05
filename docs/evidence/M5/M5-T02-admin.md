# M5-T02-A - Administrator experience UI

## Outcome

Pass. `/admin/experiences` provides responsive create, filter, pagination, lifecycle actions, and
ordering controls. `/admin/experiences/{id}/edit` exposes all frozen contract fields and skill
relations with field-level validation, status text, safe destructive confirmations, scheduling,
and conflict recovery. The preview route is session-only and visually distinguishes draft state.

The UI uses generated API classes behind a typed feature boundary. It does not access PostgreSQL,
cast raw transport responses, or ship hard-coded business content. Initial auth and data states,
loading, empty, validation, API error, stale conflict, and success feedback are covered by component
tests and Storybook stories.

Formatting, ESLint, strict TypeScript, 121/121 Vitest tests, the production Next.js build, and the
Storybook 10.5.5 static build pass. Tooling reported only nonblocking Storybook plugin-timing and
catalog chunk-size warnings. Browser screenshots are indexed by [M5 acceptance](README.md).
