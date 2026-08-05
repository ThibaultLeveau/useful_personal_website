# Component Inventory

## Component contract

Every reusable component ships with Storybook examples for default, hover, focus-visible, disabled, loading, error, high-contrast theme, long content, zoom, and narrow width where applicable. Interactive primitives use an accessible foundation and expose semantic names, descriptions, state, and deterministic focus behavior.

## Foundations and primitives

| Component | Required variants/states | Accessibility contract |
|---|---|---|
| Text / heading | display, page, section, body, label, metadata, code | Semantic element is selected separately from visual style; heading order is never chosen for appearance |
| Link | inline, navigation, quiet, external | Underlined in prose; external target is announced in accessible name/help and uses safe rel attributes |
| Button | primary, secondary, quiet, danger, icon+label | 44 px touch size; icon-only requires accessible name and tooltip; loading preserves label width |
| Icon | 16/20/24 px, decorative/status | Decorative icons hidden; status icon paired with text |
| Badge | neutral, draft, scheduled, published, hidden, warning, danger | Never color-only; compact but readable at 200% zoom |
| Divider | horizontal/vertical | Decorative unless it separates named regions |
| Surface/Card | flat, outlined, raised, selected | Selection has non-color indicator and `aria-selected` where appropriate |
| Skeleton | line, card, table, media | `aria-hidden`; surrounding region has one concise loading status; no shimmer under reduced motion |
| Spinner/Progress | indeterminate, percent | Used only when duration/progress warrants it; accessible status avoids repeated announcements |
| Tooltip | help only | Never contains essential or actionable content; keyboard/pointer dismissible |

## Navigation and discovery

| Component | Use | Key behavior |
|---|---|---|
| Skip link | Public/admin first focus | Moves focus to `main`; admin may add `Skip to editor` |
| Public header | Global public nav | Desktop links; mobile modal drawer; current route; theme control |
| Admin sidebar | Signed-in global nav | Expanded, rail, and drawer modes; group headings; unread/health badges |
| Breadcrumbs | Deep admin context | Ordered nav; final item text; collapses middle items on small screens |
| Tabs | Editor subareas | Arrow-key navigation; URL/state persistence; error counts in accessible labels |
| Pagination | Public/admin lists | First/previous/page/next/last; current page announced; disabled is not a dead link |
| Command menu | Admin navigation/actions | `Cmd/Ctrl+K`; search, grouped results, no secret/contact indexing |
| Search field | Lists/catalog | Submit and clear controls; debounced suggestion status only where useful |
| Filter bar | Lists | Explicit Apply on complex filters; active chips; Clear all; query-string persistence |
| Theme selector | Public/admin | System/light/dark; current state announced; no flash of wrong theme |

## Forms

| Component | Required behavior |
|---|---|
| Field shell | Persistent label, optional/required cue, hint, error, character count; `aria-describedby` composes these IDs |
| Text input | Text/email/url/slug variants; autocomplete attributes; leading/trailing adornments never replace labels |
| Textarea | Visible minimum size; character/word guidance; resize remains available |
| Password field | Show/hide with pressed state; paste/password-manager support; requirements remain visible |
| Checkbox / radio | Entire label clickable; 24 px control within 44 px touch row; native-like semantics |
| Switch | Only for immediate binary settings such as visibility; label expresses state and effect |
| Select / combobox | Native select when practical; accessible search/listbox for large relations; clear no-result state |
| Date/time input | Configured timezone shown next to control; keyboard entry; UTC conversion explained |
| Slug field | Generated suggestion, manual override, normalized preview, reserved/collision errors |
| Markdown editor | Source and preview modes; format toolbar; keyboard operable; raw HTML warning; code/table overflow preview |
| Relation picker | Search, selected tokens/list, visibility/publication warnings; does not silently drop unavailable references |
| Media picker | Searchable grid/list, metadata, usage intent, upload entry; selection name announced |
| Form error summary | Appears on submit failure, receives focus, links to fields, includes cross-tab counts |
| Save bar | Dirty/saving/saved/failed status, Save draft, contextual secondary actions; never relies on toast alone |

Validation occurs on blur for locally knowable issues and on submit for the full contract. Errors persist until resolved; server field paths map to controls. Destructive or publication actions are never triggered by pressing Enter in an unrelated field.

## Data display and management

| Component | Required behavior |
|---|---|
| Data table | Semantic table, sortable header buttons with `aria-sort`, selectable rows only when bulk action exists, responsive alternative |
| Mobile record list | Labeled key/value card rows with same actions/status as table, not a visual truncation of critical fields |
| Empty state | Explains whether collection is empty or filters have no match; one relevant action, no decorative dead end |
| Status cluster | Lifecycle + visibility + featured as separate labeled facts |
| Overflow menu | Secondary row actions; destructive group separated and labeled |
| Detail drawer | Quick inspect only; durable route; focus trap/restore; close does not discard edits silently |
| Audit event row | Event, outcome, safe actor/resource, UTC/local time, request ID; redaction is explicit, not blank ambiguity |
| Health status | Text/icon status, last check, stale marker; no raw dependency detail |
| Toast | Noncritical confirmation only; no secrets/contact data; live region; action remains elsewhere for critical recovery |
| Inline alert | Info/success/warning/error with heading and action; errors include request ID when useful |

## Public content components

- `HeroBlock`: focused identity statement, supporting copy, one primary and optional secondary CTA, optional portrait/diagram.
- `ProfileSummaryBlock`: public biography excerpt and intentional links.
- `StatisticsBlock`: evidence labels, values, and context; no animated counters by default.
- `SkillsGridBlock` / `FeaturedSkillsBlock`: category, skill, experience/proficiency text, related evidence links.
- `ExperienceSummaryBlock` / `ExperienceListBlock`: semantic list/timeline; dates readable without spatial interpretation.
- `ProjectGridBlock` / `FeaturedProjectsBlock`: case-study card with outcome-led summary and meaningful image handling.
- `LatestPostsBlock`: article list with date, reading time, category.
- `RichTextBlock`: controlled Markdown renderer with prose, table scroll region, code copy action.
- `ImageBlock` / `ImageWithTextBlock`: meaningful/decorative contract, caption, responsive aspect ratio.
- `CallToActionBlock` / `ContactCalloutBlock`: clear destination and privacy-aware contact wording.
- `LinksCollectionBlock`: semantic named list; external destination cues.
- `TestimonialBlock`: quote, attribution, relationship/context; never fabricated placeholder content.
- `DividerBlock` / `SpacerBlock`: bounded responsive sizes and decorative semantics.

All block renderers have missing optional-reference behavior and fail closed for an invalid/unknown type. Unknown blocks in public content produce an observable section error or omit safely according to the API contract; they never render raw config.

## Page-builder components

| Component | Responsibilities |
|---|---|
| Block catalog | Search and group all required block types; description and mini-preview; keyboard selection |
| Block outline | Ordered blocks, type/title, visibility, issue count, drag handle, selection |
| Block inspector | Schema-specific Content/References/Appearance/Responsive fields; field errors |
| Block action menu | Duplicate, hide/show, move, delete; safe action ordering |
| Reorder control | Pointer drag plus keyboard lift/move/drop and explicit Move controls; live announcement |
| Preview canvas | Accurate renderer at selected viewport; selection outline never changes rendered spacing |
| Publication panel | Live/draft comparison, visibility, publish time/timezone, validation issues, publish/unpublish |

Traceability: F1-005-F1-006, F2-012, F2-019, NFR-002-NFR-004; AC-005-AC-006, AC-020, AC-025, AC-032-AC-033.
