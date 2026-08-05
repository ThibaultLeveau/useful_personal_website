# Design System

## System character

The system is named **Signal Ledger**: an editorial portfolio paired with a precise instrument-panel admin. Public pages use expressive serif headlines, measured rules, evidence labels, and asymmetric but disciplined composition. Admin surfaces use the same color and typography DNA at higher information density. It must not resemble an unmodified component-library dashboard.

## Color tokens

Tokens describe roles, not fixed component colors. The listed foreground/background pairs target at least 4.5:1 for normal text and 3:1 for large text/UI boundaries; rendered combinations still require automated and manual verification (NFR-002 / AC-032).

| Token | Light | Dark | Use |
|---|---|---|---|
| `canvas` | `#F6F7F9` | `#090E16` | Page background |
| `surface-1` | `#FFFFFF` | `#111927` | Cards, sidebar, popovers |
| `surface-2` | `#EEF1F5` | `#192435` | Subtle sections, selected rows |
| `surface-inverse` | `#111827` | `#F3F6FA` | Deliberate inverse panels |
| `text` | `#18202B` | `#F3F6FA` | Primary text |
| `text-muted` | `#52606D` | `#B0BAC8` | Secondary text |
| `text-subtle` | `#667085` | `#98A6B8` | Metadata; not for small critical copy |
| `border` | `#CBD2DC` | `#344054` | Dividers/nonessential boundaries |
| `border-strong` | `#7D8999` | `#667085` | Inputs, controls, selected outlines |
| `brand` | `#075985` | `#7DD3FC` | Links, primary signal, selected state |
| `brand-hover` | `#0C4A6E` | `#BAE6FD` | Brand interaction |
| `brand-on` | `#FFFFFF` | `#082F49` | Text on brand-filled control |
| `accent` | `#9A3412` | `#FDBA74` | Sparse editorial highlights |
| `success` | `#166534` | `#86EFAC` | Success/status foreground |
| `warning` | `#92400E` | `#FCD34D` | Warning/scheduled foreground |
| `danger` | `#B42318` | `#FDA29B` | Errors/destructive foreground |
| `focus` | `#0369A1` | `#7DD3FC` | 3 px focus ring |
| `selection` | `#DFF3FC` | `#123A50` | Selected surface behind normal text |

Status fills use tinted surfaces plus icon/text: light `success #ECFDF3`, `warning #FFFAEB`, `danger #FEF3F2`; dark `#12351F`, `#3B2A0B`, `#411817`. Never place the pale status foreground on white or the dark foreground on dark. Data visualization colors require per-chart contrast review and a pattern/label alternative.

## Typography

Self-host, subset, preload only critical faces, and retain metrics-compatible fallbacks.

- Public display: `Newsreader`, Georgia, serif; weight 500-650.
- UI/body: `Instrument Sans`, `Segoe UI`, sans-serif; weight 400-700.
- Code/data labels: `IBM Plex Mono`, `Cascadia Mono`, monospace; use sparingly.

| Token | Size / line-height | Typical use |
|---|---|---|
| `text-xs` | 12 / 16 px | Compact metadata, never sole critical instruction |
| `text-sm` | 14 / 20 px | Admin labels, secondary copy |
| `text-base` | 16 / 24 px | Body/forms |
| `text-lg` | 18 / 28 px | Lead text |
| `text-xl` | 20 / 28 px | Card/section title |
| `text-2xl` | 24 / 32 px | Admin page title/mobile public heading |
| `text-3xl` | 32 / 38 px | Section display |
| `text-4xl` | 40 / 46 px | Public page title |
| `text-5xl` | 56 / 60 px | Desktop hero |
| `text-6xl` | 72 / 74 px | Large-screen hero maximum |

Body measure is 60-72 characters; long-form article measure is 68 characters. Uppercase mono labels use at least 12 px, letter spacing `0.06em`, and short phrases only. Admin numeric columns use tabular figures.

## Spacing and sizing

Base unit is 4 px. Tokens: `0, 1(4), 2(8), 3(12), 4(16), 5(20), 6(24), 8(32), 10(40), 12(48), 16(64), 20(80), 24(96), 32(128)`. Public sections use 64/80/96 px vertical spacing by breakpoint; admin panels use 16/24/32 px. Do not invent intermediate values unless a platform control requires one.

- Control height: 40 px compact desktop, 44 px default/touch; textarea minimum 120 px.
- Icon sizes: 16, 20, 24 px; stroke 1.75-2 px.
- Content widths: reading 720 px; form 760 px; public content 1200 px; public shell/admin wide 1440 px.
- Touch target: minimum 44 x 44 px by design, even when visible icon is smaller.

## Shape, borders, and elevation

| Token | Value | Use |
|---|---|---|
| `radius-sm` | 6 px | Tags, compact fields |
| `radius-md` | 10 px | Buttons, inputs, cards |
| `radius-lg` | 16 px | Dialogs, editorial media |
| `radius-xl` | 24 px | Rare hero/feature surface |
| `radius-pill` | 999 px | Status/filter chips only |
| `shadow-1` | `0 1px 2px rgb(9 14 22 / .08)` | Menus and low lift |
| `shadow-2` | `0 12px 32px rgb(9 14 22 / .14)` | Dialogs/drawers |
| `shadow-focus` | `0 0 0 3px` focus color | Keyboard focus |

Most hierarchy comes from spacing, tone, and 1 px rules, not shadows. Dark theme uses lower-opacity black shadows plus stronger borders.

## Motion

Tokens: `instant 0 ms`, `fast 120 ms`, `base 180 ms`, `slow 260 ms`; easing `standard cubic-bezier(.2,.8,.2,1)` and `exit cubic-bezier(.4,0,1,1)`. Animate opacity/transform only; avoid layout/height animation for content-heavy regions. No animation exceeds 300 ms in routine UI. Reduced motion removes transform, parallax, shimmer, animated counters, and smooth scrolling while retaining immediate state changes.

## Interaction styling

- Hover is enhancement only. Focus-visible is a 3 px ring with 2 px offset and must remain visible against both control and surrounding surface.
- Disabled controls retain readable labels and include adjacent explanation when the reason is not obvious; read-only and disabled are visually distinct.
- Links in prose are underlined. Navigation links may omit underline when current/hover/focus treatment is explicit.
- Primary buttons use brand fill; danger fill is reserved for final destructive confirmation, not the first Delete entry point.
- Dark/light/system themes share semantic tokens; theme change does not alter spacing, hierarchy, or status meaning.

Traceability: NFR-001-NFR-002, F1-003, F2-019; AC-003, AC-025, AC-031-AC-032.
