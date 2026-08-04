# Layouts and Responsive Rules

## Breakpoints and test widths

Design mobile-first. Breakpoints are `sm 640`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536` px. Required review widths: 320, 360, 390, 768, 1024, 1280, 1440, and 1920 px, plus 400% browser zoom at 1280. Components respond to available container width when nested; breakpoints are shell rules, not device names.

## Public shell

- Outer gutter: 16 px below 640, 24 px at 640-1023, 32 px at 1024-1279, max 48 px above 1280.
- Header: 64 px mobile, 72 px desktop; sticky only when it does not obscure focused content. Skip-link and anchor offsets include header height.
- Full primary navigation appears at `lg`; below `lg`, use one modal drawer. Never hide destinations solely because width is small.
- Main content max 1200 px; display compositions may reach 1440 px. Long-form stays 720 px.
- Home blocks stack at small widths. Two-column image/text and case-study layouts start at `md` only when each column remains >=320 px. Grid defaults: 1 column, 2 at `md`, 3 at `xl`; cards may span for editorial rhythm.
- Hero typography uses `clamp(2.5rem, 5vw, 4.5rem)` and never forces a viewport-height panel. Primary content appears without scrolling on common laptop heights.
- Project galleries use one large media item plus thumbnails at `lg`; on small widths use a labeled horizontal scroller with scroll-snap and next/previous controls.
- Timeline becomes a semantic vertical list on all widths; alternating spatial placement is optional at `lg` but reading/DOM order remains chronological.

## Admin shell

| Width | Sidebar | Main region |
|---|---|---|
| `<1024` | Hidden; 320 px max modal drawer from Menu button | Full width; 16-24 px gutter |
| `1024-1279` | 72 px icon rail with tooltips and accessible labels | Remaining width; 24 px gutter |
| `>=1280` | 272 px expanded, fixed/sticky | Remaining width; 24-32 px gutter |

Sidebar state can persist per administrator, but an expanded preference must collapse safely when space is insufficient. Drawer opening traps focus and locks background scroll; closing restores Menu focus.

Page header actions wrap below title before truncating. On editor screens below `lg`, primary Save/Publish access uses a bottom bar respecting `env(safe-area-inset-bottom)`; it must not cover the focused field or error summary.

## Admin lists, forms, and tables

- Table mode begins when required columns fit at >=960 px container width. Below it, render equivalent record cards; do not make touch users pan through primary data.
- Tables may horizontally scroll only for genuinely wide audit/technical data; first column and row action may be sticky, with a visible scroll hint.
- Filters: single row at wide width, disclosure panel below `lg`. Active filter chips remain visible outside the panel.
- Pagination never collapses to unlabeled arrows only; mobile shows Previous, `Page x of y`, Next.
- Forms use a 760 px reading/form column. Related sidebar help begins at `xl`; otherwise appears inline or in a disclosure.
- Two-column fields begin at `md`, but long text, URLs, Markdown, errors, and relation pickers always span full width.
- Dialog max widths: 480 px confirmation, 640 px form, 960 px media picker. Below 640 they become near-full-screen sheets with safe-area padding.

## Page builder

| Width | Composition |
|---|---|
| `>=1440` | Three panes: 280 px outline, fluid preview/canvas >=560 px, 360 px inspector |
| `1280-1439` | 240 px outline, fluid canvas, 320 px inspector |
| `1024-1279` | Canvas + 320 px inspector; outline opens as drawer |
| `768-1023` | Canvas full width; outline and inspector are separate modal sheets |
| `<768` | Linear editor: outline list then selected block form; preview opens full-screen; Move controls replace drag as primary reorder |

Canvas viewport controls simulate 375/768/1440 px without scaling text below readable size. At narrow host widths, preview uses a separate full-screen route rather than a scaled illegible miniature.

## Overflow and content resilience

- Text wraps; IDs/URLs/code may break or scroll within their own region. Never clip focus rings.
- Support user text resize and 400% zoom without two-dimensional page scrolling, except code, tables, and media where WCAG permits contained scrolling.
- Images reserve aspect-ratio space. Meaningful crops keep configurable focal point; never crop screenshots so key UI becomes unreadable.
- Sticky regions must account for on-screen keyboards and use `scroll-padding` so focus is not obscured (WCAG 2.4.11).
- Orientation is never locked. Pointer drag always has a non-drag alternative.

Traceability: F1-003, F2-019, NFR-001-NFR-004; AC-003, AC-025, AC-031-AC-033.
