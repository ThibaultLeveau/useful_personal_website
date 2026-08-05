# Visual Direction

## Direction: Signal Ledger

Signal Ledger combines an editorial technical journal with the exactness of an engineering instrument. The public experience feels authored, calm, and evidence-led; the admin feels like the control surface behind the same publication. Shared type, rule lines, color, and data labels connect them without making them visually identical.

### Signature elements

- **Ledger rail:** a slim vertical rule with mono section index and outcome label anchors major public sections. On mobile it becomes a horizontal eyebrow, preserving reading order.
- **Evidence plates:** projects, experience, and skills use restrained outlined surfaces with small factual labels (`Impact`, `Role`, `Stack`, `Date`) instead of generic icon cards.
- **Signal cyan + oxidized copper:** cyan marks navigation/action/system precision; copper appears sparsely for editorial emphasis. Neither becomes a page-wide gradient.
- **Editorial contrast:** Newsreader headlines against Instrument Sans body and IBM Plex Mono metadata. Public headings may be asymmetrical; admin headings remain compact.
- **Technical texture:** optional low-contrast 24 px baseline/grid or fine dot registration marks only in hero/section transitions. It is decorative, hidden from assistive technology, and removed under contrast/performance constraints.

## Public composition

Home opens with a concise claim and concrete evidence, not a full-screen portrait or oversized empty hero. One dominant typographic line, short supporting paragraph, primary Contact/Projects action, and a compact evidence strip establish credibility. Subsequent blocks vary rhythm: wide case-study feature, narrow editorial text, structured skill ledger, timeline, and writing list.

Projects emphasize problem -> intervention -> measurable impact. Blog is more typographic and quiet. About uses portrait and biography without a generic centered-card layout. Experience remains readable as a list first; timeline decoration is secondary. Images use deliberate crops, captions, and subtle borders rather than floating glossy mockups.

## Admin composition

Admin density is professional, not sparse: compact sidebar, strong page header, 16-24 px panel spacing, polished tables, and contextual right-hand inspectors. White/dark surfaces sit on a faintly tinted canvas with rules stronger than shadows. Status clusters make lifecycle, visibility, and pending changes legible at a glance. Dashboard cards exist only for actionable information; avoid vanity metrics and empty chart furniture.

The page builder is the flagship admin surface: ledger-like outline at left, true content preview in the center, and structured inspector at right. Selection uses a crisp outline and index marker, not a glowing neon box.

## Theme behavior

Light theme resembles warm technical paper: near-white canvas, graphite text, cool gray rules. Dark theme resembles a deep blue-black studio, not pure black; surfaces remain separable and cyan is softened to avoid glare. Copper becomes a pale amber accent. Both themes keep hierarchy and status semantics identical. Illustrations, logos, and screenshots need theme-aware treatment or a neutral framed surface.

## Iconography, imagery, and data display

- Use one open-source outline icon family at 1.75-2 px stroke. Icons communicate action/domain, not decoration; avoid mixing filled and outline families casually.
- Prefer authentic project screenshots, architecture diagrams, restrained portraits, and process artifacts. Never fabricate testimonials, company marks, metrics, or product imagery.
- Diagrams use labeled nodes, accessible summaries, and the semantic palette. Charts appear only for meaningful data and include direct labels/table alternatives.
- Code samples use IBM Plex Mono, syntax colors verified in both themes, a language label, horizontal scroll, and Copy feedback.

## Motion and micro-interaction

Motion explains state: navigation underline, block insertion, drawer transition, save confirmation, and selection. It is subtle (120-260 ms), never perpetual. Project cards may shift 2 px or reveal a rule on hover; content never jumps. Public scroll animation, parallax, cursor effects, glowing blobs, animated counters, and decorative 3D scenes are excluded from R1.

## Explicit anti-patterns

- No purple-blue gradient hero, glassmorphism stack, giant centered avatar, orbiting technology logos, or wall of identical rounded cards.
- No oversized whitespace that hides useful content below the fold.
- No arbitrary corner radii/shadows, low-contrast gray text, or status conveyed only by colored pills.
- No copied terminal-window gimmick unless showing real, readable code relevant to the content.
- No admin dashboard charts without a defined decision they support.
- No AI/chat affordance in R1 (AI-004 / AC-046).

## Review bar

A visual review passes when: identity is recognizable with logos removed; public evidence appears before decoration; at least three block compositions have distinct rhythm while sharing tokens; admin workflows remain dense and calm; light/dark/mobile views preserve hierarchy; and no template-specific placeholder copy, imagery, or nonfunctional control remains (NFR-001 / AC-031).
