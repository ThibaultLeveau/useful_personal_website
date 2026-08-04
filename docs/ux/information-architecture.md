# Information Architecture

## Purpose and principles

This document defines the R1 navigation, route, content, and permission model for the public portfolio and administration interface. It follows the publication-safe API boundary, the single-administrator R1 policy, and the separate public/admin/integration schemas defined by the architecture.

Principles:

- Public navigation answers, in order: who is this person, what have they done, how do they think, and how can I contact them?
- Administration navigation follows editorial jobs rather than backend module names.
- Draft, visibility, schedule, and featured status are separate concepts everywhere. `Featured` never implies public; public eligibility is published revision + visible + effective publication time + not deleted.
- Sensitive areas (contacts, tokens, audit, sessions, health) never appear in public search, public navigation, sitemap, or public response payloads.
- A route that is unavailable to the current actor behaves as unauthorized or not found according to the security contract; it never reveals protected existence.

Traceability: F1-001-F1-014, F2-001-F2-020, NFR-001-NFR-004; AC-001-AC-026, AC-031-AC-033.

## Public hierarchy and routes

| Level | Route | Purpose | Primary content | Requirement / acceptance |
|---|---|---|---|---|
| 0 | `/` | Establish identity, expertise, evidence, and a next action | Configured home blocks | F1-001, F1-005-F1-006 / AC-001, AC-005-AC-006 |
| 1 | `/about` | Explain background, values, availability, and work preferences | Public profile projection | F1-001, F1-007 / AC-001, AC-007 |
| 1 | `/experience` | Present career progression and outcomes | Published visible experiences | F1-001, F1-009 / AC-001, AC-009 |
| 1 | `/skills` | Show capability by category and supporting evidence | Visible skills and public relations | F1-001, F1-008 / AC-001, AC-008 |
| 1 | `/projects` | Browse and filter case studies | Published visible projects | F1-001, F1-010 / AC-001, AC-010 |
| 2 | `/projects/{slug}` | Explain problem, solution, architecture, and impact | One published project revision | F1-001, F1-010 / AC-001, AC-010 |
| 1 | `/blog` | Browse writing by recency, tag, and category | Effective published posts | F1-001, F1-011 / AC-001, AC-011 |
| 2 | `/blog/{slug}` | Read a safe, portable article | One effective published post revision | F1-001, F1-011-F1-012 / AC-001, AC-011-AC-012 |
| 1 | `/contact` | Start a consented private inquiry | Contact form and public contact preferences | F1-001, F1-013 / AC-001, AC-013 |
| 1 | `/privacy` | Explain privacy and contact-data handling | Owner-supplied legal copy | F1-001 / AC-001 |
| 1 | `/legal` | Provide legal notice | Owner-supplied legal copy | F1-001 / AC-001 |
| 1 | `/{custom-slug}` | Render an administrator-created page | Published page revision and blocks | F1-001, F1-005-F1-006 / AC-001, AC-005-AC-006 |
| system | `/404` behavior | Recover from unknown, deleted, draft, hidden, or unavailable routes | Designed not-found state | F1-003 / AC-001, AC-033 |

Custom pages use one normalized path segment. The reserved registry in `docs/architecture/domain-model.md` is authoritative; the admin slug field checks it before submit and the API remains the concurrency-safe authority.

### Public global navigation

- Desktop order: configurable primary links, optional overflow under "More", then theme selector and one configured contact CTA. The current destination uses both text/shape and `aria-current="page"`.
- Mobile: logo/home link, theme control, and one Menu button opening a modal navigation drawer. The drawer includes every visible primary destination, the contact CTA, social links, and legal links; opening traps focus and closing restores it to Menu.
- Footer: configurable link columns, social links, legal links, copyright, and a compact theme control. Invalid/hidden destinations never render.
- Search is contextual, not a mandatory global feature: project and blog search/filter controls live on their listings. A global public search is added only if a separately approved search contract exists.

## Administration hierarchy and routes

### Authentication boundary

| Route | Purpose | Access |
|---|---|---|
| `/admin/login` | Log in without account enumeration | Signed-out only; signed-in users redirect to dashboard |
| `/admin/change-password` | Replace initial or current password | Signed-in; forced immediately when `must_change_password` |
| `/admin/session-expired` | Explain expiry and preserve a safe return path | Signed-out after expiry; contains no protected data |

When the initial password flag is set, the only permitted destinations are password change, session inspection, and logout. The UI shows a focused setup step, not the ordinary sidebar (F2-001-F2-002 / AC-015-AC-016).

### Signed-in application

| Navigation group | Route | Job |
|---|---|---|
| Overview | `/admin` | See editorial status, recent safe activity, inquiries, and health summaries |
| Website | `/admin/profile` | Manage public/private profile fields |
| Website | `/admin/settings` | Manage identity, brand, locale/timezone, themes, defaults, SEO, and public analytics identifiers |
| Website | `/admin/navigation` | Order, nest, validate, show/hide navigation items |
| Website | `/admin/footer` | Configure footer columns, social, legal, and copyright links |
| Content | `/admin/pages` | Search/filter pages and inspect publication state |
| Content | `/admin/pages/new` | Create a page draft |
| Content | `/admin/pages/{id}/edit` | Edit metadata and typed block composition |
| Content | `/admin/pages/{id}/preview` | Authenticated draft preview shell; private/no-store |
| Content | `/admin/skills` | Manage skills, categories, featured/visibility, relations, and order |
| Content | `/admin/experiences` | Manage experience revisions, relations, order, visibility, and publication |
| Content | `/admin/experiences/{id}/edit` | Edit one experience draft |
| Content | `/admin/projects` | Manage project revisions, media, SEO, relations, and publication |
| Content | `/admin/projects/{id}/edit` | Edit one project draft |
| Content | `/admin/blog` | Manage posts, tags, categories, schedule, and publication |
| Content | `/admin/blog/{id}/edit` | Edit one post draft in controlled Markdown |
| Assets | `/admin/media` | Upload, search, inspect, reuse, and safely delete images |
| Inbox | `/admin/contacts` | Filter private submissions by lifecycle state |
| Inbox | `/admin/contacts/{id}` | Read, mark read, archive/restore, or explicitly delete one submission |
| Developer | `/admin/api-tokens` | Create, copy once, rotate, inspect, and revoke scoped tokens |
| System | `/admin/audit` | Filter append-only safe audit events |
| System | `/admin/health` | View safe liveness/readiness/build summaries |
| Account | `/admin/account` | Inspect session, change password, and log out |

List and detail routes may use drawers for quick inspection at large widths, but every entity has a durable URL so refresh, history, and assistive technology remain predictable. Preview routes are admin-session-only and excluded from discovery.

### Admin sidebar and local navigation

- Expanded sidebar groups use the labels above; badges are reserved for unread contacts and health warnings.
- The footer area contains theme, account, session-expiry context, documentation link, and logout.
- Editors add local tabs only when the content warrants them: `Content`, `Relations`, `SEO`, `Publication`. Tabs are real URL state or preserve draft state safely; required errors are summarized across tabs.
- Breadcrumbs represent location, never action history. The final crumb is plain text. Mobile shows a compact Back link plus current title.

## Findability and command model

- `Ctrl/Cmd+K` opens an admin command menu with navigation, create commands, and current-record actions that the actor may perform. It does not expose contact content, token secrets, or hidden object names in telemetry.
- `/` focuses the current list search when no input/editor is active. `Esc` closes the topmost popover, menu, or dialog.
- Primary create actions are also visible buttons; keyboard commands never become the only path.
- Row overflow menus contain secondary actions. Publish, unpublish, delete, rotate, and revoke always retain explicit text labels and confirmation behavior.
- Filters serialize to the query string so views are shareable within the authenticated session and browser Back works. Sensitive contact query content is never put in the URL; only state/date/sort/page filters are.

## Content vocabulary shown to users

Use these labels consistently:

- `Draft`: never published.
- `Scheduled`: a frozen published revision with a future effective time; not public yet.
- `Published`: effective published revision is public if also visible.
- `Published - changes pending`: the live published revision differs from the editable draft.
- `Unpublished`: a prior revision exists but public eligibility was cleared.
- `Hidden`: visibility gate is off; shown alongside lifecycle status, not instead of it.
- `Featured`: presentation priority only; never a publication indicator.
- `Archived`: reversible contact state; distinct from Delete permanently.

Status labels always include text and an icon/shape; color is supplementary.
