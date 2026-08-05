# Screen Inventory

## State contract used by every screen

Every data-backed screen specifies: initial, loading, success, empty, validation error, server error, and unauthorized/session-expired state where applicable (NFR-004 / AC-033). Loading preserves the final geometry; errors retain safe user input where possible; unauthorized states clear protected data before offering login.

## Public screens

| Screen | Route | Core composition | Distinct states | Traceability |
|---|---|---|---|---|
| Home | `/` | Public header, ordered block renderer, footer | No configured blocks; referenced item unavailable; API error; theme initialization | F1-001-F1-006 / AC-001-AC-006 |
| About | `/about` | Editorial intro, portrait, biography, values, availability, public links | Optional field absent; image unavailable; no public profile configured | F1-007, F1-014 / AC-007, AC-014 |
| Experience | `/experience` | Intro, filter if useful, accessible timeline/list, related evidence links | No published experiences; filtered zero state | F1-009 / AC-009 |
| Skills | `/skills` | Category navigation, filter/search, skill groups, related evidence | No visible skills; category empty; filtered zero state | F1-008 / AC-008 |
| Projects | `/projects` | Featured area, query/filter bar, paginated project cards | No projects; filtered zero; page beyond last; image fallback | F1-010, API-004-API-005 / AC-010, AC-029 |
| Project detail | `/projects/{slug}` | Case-study header, problem/solution/impact, architecture, gallery, relations | Not found for draft/hidden; missing optional repo/demo; gallery error | F1-010, F1-014 / AC-010, AC-014 |
| Blog | `/blog` | Intro, search/filter controls, post list, pagination | No posts; filter zero; page beyond last | F1-011 / AC-011, AC-029 |
| Post detail | `/blog/{slug}` | Article header, safe Markdown, reading metadata, related posts | Not found for draft/future/hidden; content render failure | F1-011-F1-012 / AC-011-AC-012 |
| Contact | `/contact` | Contact preferences, labeled form, privacy/consent note | Client validation; submitting; accepted; generic spam success; rate limit with retry; server failure | F1-013 / AC-013 |
| Privacy | `/privacy` | Owner-supplied legal content and effective date | Missing content uses unavailable page, never invented legal text | F1-001 / AC-001 |
| Legal | `/legal` | Owner-supplied legal notice | Missing content uses unavailable page | F1-001 / AC-001 |
| Custom page | `/{custom-slug}` | Page header and schema-driven ordered blocks | Hidden block omitted; missing optional reference; route not found | F1-001, F1-005-F1-006 / AC-001, AC-005-AC-006 |
| Not found | route-level | Concise explanation, Home, Projects, Blog actions | Same treatment for unknown and nonpublic resources | F1-003, SEC-004 / AC-001, AC-017 |
| Public error | error boundary | Safe message, retry, request ID, alternate navigation | Full-page and section-level variants | API-006, NFR-004 / AC-030, AC-033 |

## Authentication and account screens

| Screen | Route | Core composition | Distinct states | Traceability |
|---|---|---|---|---|
| Login | `/admin/login` | Brand mark, email, password, show/hide, submit, security note | Invalid non-enumerating credentials; throttled; offline/server error; return path | F2-001, SEC-003 / AC-016 |
| Forced password change | `/admin/change-password` | Setup explanation, current/new/confirm fields, requirements, logout | Common/compromised password; mismatch; expired session; success then re-auth if required | F2-002, SEC-002 / AC-015-AC-016 |
| Session expired | `/admin/session-expired` | Expiry explanation, Login, safe return destination | Expired vs signed out intentionally; no cached private UI | F2-001 / AC-016, AC-033 |
| Account and sessions | `/admin/account` | Identity, current session, expiry, password change, logout | Save/revoke errors; upcoming expiry warning | F2-001 / AC-016 |

Login permits paste, password managers, and reveal controls; it never adds a cognitive puzzle or discloses whether an email exists (NFR-002, WCAG 3.3.8; SEC-003).

## Administration screens

| Screen | Route(s) | Primary actions and content | High-value states | Traceability |
|---|---|---|---|---|
| Dashboard | `/admin` | Continue drafts, create content, recent safe activity, unread count, publication/health summary | First-run onboarding; partial widget failure; health warning | F2-019-F2-020 / AC-025-AC-026 |
| Profile | `/admin/profile` | Edit identity, biographies, public flags, media, links, contact preferences | Public/private preview; invalid URL; version conflict | F2-003 / AC-007 |
| Settings | `/admin/settings` | Brand, locale/timezone, theme, SEO defaults, analytics identifiers | Invalid timezone/URL; secret-like value rejected; version conflict | F2-015 / AC-022 |
| Navigation editor | `/admin/navigation` | Tree/list reorder, nesting <=2, labels, destinations, visibility, target | Unsafe link; invalid destination; cycle/depth; unsaved order | F2-014 / AC-021 |
| Footer editor | `/admin/footer` | Columns, links, legal/social, copyright, order | Unsafe link; empty column; unsaved order | F2-014 / AC-021 |
| Pages list | `/admin/pages` | Search, filter by lifecycle/visibility, create, duplicate, row actions, pagination | No pages; filtered zero; stale page; bulk/order errors | F2-012-F2-013, F2-019 / AC-020, AC-025 |
| Page create/editor | `/admin/pages/new`, `/admin/pages/{id}/edit` | Metadata, slug, SEO, outline, canvas summary, inspector, add/reorder/duplicate/hide/delete blocks, save/preview/publish | Invalid/reserved slug; invalid block; missing reference; dirty; conflict; published changes pending | F1-005-F1-006, F2-012-F2-013 / AC-005-AC-006, AC-020 |
| Draft preview | `/admin/pages/{id}/preview` and equivalent entity previews | Exact draft renderer, preview banner, viewport controls, return to editor | Expired session; unresolved required reference; renderer error | F2-012 / AC-020 |
| Skills manager | `/admin/skills` | Category filter/tree, skill table/cards, edit sheet/page, bulk reorder, relations, feature/visibility | No categories; no skills; invalid score/years; media missing | F2-004 / AC-008 |
| Experiences list/editor | `/admin/experiences`, `/{id}/edit` | Search/filter, revision editor, ordered achievements, skills/projects, preview/publication | Invalid dates; current/end conflict; draft/live divergence | F2-005 / AC-009 |
| Projects list/editor | `/admin/projects`, `/{id}/edit` | Search/filter, case-study fields, gallery, relations, SEO, preview/publication | Invalid dates/URLs; missing required public media; self relation; conflict | F2-006 / AC-010 |
| Blog list/editor | `/admin/blog`, `/{id}/edit` | Search/filter, controlled Markdown editor/preview, taxonomy, relations, SEO, schedule/publication | Unsafe Markdown/URL; scheduled; reading time recalculation; render error | F1-012, F2-007 / AC-011-AC-012 |
| Media library | `/admin/media` | Upload dropzone/button, search, grid/list toggle, metadata editor, usage list, picker mode | Upload progress; invalid type/size/dimensions; quarantine/failure; empty; in-use conflict | F2-010-F2-011, SEC-007 / AC-019 |
| Contact inbox | `/admin/contacts` | State/date filters, safe list columns, read/unread, archive | Empty inbox; filtered zero; unread count sync; unauthorized | F2-008-F2-009 / AC-018 |
| Contact detail | `/admin/contacts/{id}` | Sender, subject, timestamp, consent evidence, message, archive/restore, permanent delete | Mark-read failure; stale version; deleted elsewhere; session expiry | F2-008-F2-009 / AC-018 |
| API tokens | `/admin/api-tokens` | Token table, create, one-time reveal, rotate, revoke, metadata/scopes/expiry | No tokens; secret reveal; copy success/failure; expired/revoked; rotation error | F2-016-F2-017, SEC-008 / AC-023 |
| Audit log | `/admin/audit` | Filter by event/actor/resource/outcome/date/request ID; safe detail | Empty; no matches; redacted metadata; server error | F2-018, SEC-009 / AC-024 |
| Health | `/admin/health` | Liveness/readiness/build/last checked; refresh | Ready; degraded/not ready; stale/unknown; refresh failure | F2-020 / AC-026 |

## Screen-level action placement

- Desktop page header: breadcrumb, title/context, status cluster, secondary actions, then one primary action.
- Mobile: title/status first; primary action remains visible in a bottom-safe sticky action bar only on long editors. Secondary actions move into a labeled More menu.
- List creation is top-right on desktop and first action after the title on mobile. Filters follow in a toolbar; active filters repeat as removable chips below.
- Edit screens use explicit `Save draft`; publication is a separate command. Save status is textual (`Unsaved changes`, `Saving`, `Saved at 14:32`, `Save failed`).
- No shipping screen contains a nonfunctional control, fake statistic, or AI affordance (AI-004 / AC-046).
