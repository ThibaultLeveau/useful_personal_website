# M9-T02-L administrator library and picker evidence

- Date/executor: 2026-08-04, Integration/root.
- Environment: built Next.js/FastAPI same-origin stack with isolated PostgreSQL and local private media volume.

`/admin/media` implements accessible file-input upload with truthful server-ready completion, safe failure
states, progress, bounded search/pagination, ready/failed cards, authenticated stripped preview, display-name
editing, exact usage inspection, and active-use delete protection. The shared picker is used by owner editors
and returns only opaque ready asset IDs; it does not expose object URLs, storage coordinates, or credentials.

Browser acceptance uploaded a real JPEG, while a deliberately false `.png`/`image/png` declaration for the
same JPEG bytes was rejected as `UNSUPPORTED_MEDIA_TYPE` and never became public. The ready asset produced
six registered renditions. A transient inspector state discovered during review was corrected so it displays
`Loading usage…` and disables deletion until the usage query resolves rather than briefly claiming the asset
is unassigned. The focused component regression suite passes.
