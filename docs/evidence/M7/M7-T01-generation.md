# M7-T01-I - OpenAPI and generated-client freeze

## Outcome

Pass. The accepted M7 contract contains 77 unique operations, including 19 blog operations, with
explicit security, errors, ETags, idempotency, filters, sorts, pagination, safe-render provenance,
and source-export content negotiation. The generated TypeScript client contains 168 files and is
consumed behind blog feature wrappers.

## Deterministic proof

- OpenAPI SHA-256: `e9ce08288cbc17bb643f6369bcc7c7cd0e5737b0fdd4976344ddab622abf05e4`.
- Generated client tree SHA-256:
  `f8dbb2951179efefeee475390ef5edaca88f13a52da1a8fb40bd14416d0a58fe`.
- Two clean generations produced the same 168-file tree.
- OpenAPI reference/operation validation, generated formatting, lint, and strict TypeScript pass.
- Handwritten blog transport uses generated clients; the sole safe-render component accepts only
  generated `SafeRenderedContentData`.

B4 is frozen. No generated file was hand-edited and no second transport or Markdown type system is
present.
