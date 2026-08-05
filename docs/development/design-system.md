# Design-System Development

The [UX design system](../ux/design-system.md) is the normative visual specification. The [component inventory](../ux/component-inventory.md), [interaction states](../ux/interactions-and-states.md), [responsive rules](../ux/layouts-and-responsive-rules.md), and [accessibility checklist](../ux/accessibility-checklist.md) define required behavior.

## Implementation contract

- Implement semantic tokens before feature-local styling.
- Keep public and admin presentation coherent while respecting their different density and workflow needs.
- Reuse accessible primitives; do not recreate native behavior without a demonstrated need.
- Cover interactive, hover, focus-visible, disabled, busy, invalid, success, destructive, empty, and error states where applicable.
- Support light and dark themes, reduced motion, high zoom/reflow, keyboard navigation, and touch targets from the start.
- Treat Storybook as component documentation and interaction evidence, not as a substitute for integrated pages.

## Change review

A token or shared primitive change must identify downstream components, responsive/theme impact, accessibility impact, screenshots or browser evidence, and migration guidance for consumers. Visual changes require inspection of rendered output; code review alone is insufficient.

The implementation path, Storybook commands, and screenshot protocol will be added after the frontend foundation is validated.
