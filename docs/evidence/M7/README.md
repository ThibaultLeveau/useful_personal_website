# M7 acceptance record

## Decision

M7 is accepted as a complete local Blog vertical slice on 2026-08-04. Controlled content policy,
revision-safe persistence, sole migration, administrator/public APIs, deterministic generated
client, administrator/public UI, lifecycle E2E, privacy, accessibility, SEO, performance, security,
documentation, and fresh runtime gates pass.

## Evidence index

- [Controlled CommonMark security policy](M7-T01-content-security.md)
- [Domain and application lifecycle](M7-T01-domain.md)
- [Persistence and bounded public queries](M7-T01-persistence.md)
- [Migration `0008`](M7-T01-migration.md)
- [Administrator, preview, and export API](M7-T01-admin-api.md)
- [Public projection](M7-T01-public-projection.md)
- [OpenAPI and generated client](M7-T01-generation.md)
- [Administrator frontend](M7-T02-admin.md)
- [Public frontend and B5](M7-T02-public.md)
- [Integrated certification and corrective loop](M7-T03.md)
- [Performance, accessibility, and SEO](performance/README.md)
- [Security certification](security/README.md)
- [Responsive screenshots](screenshots/)

## Frozen candidate

- Backend image: `sha256:b4af3d19e0308557350d35333de024eccb66d84d30f8df2e85b43d917df6ec4f`
  (38,911,582 bytes).
- Frontend image: `sha256:94c993fb23fcab953fe0515f1f1cb3d2b781ce5423383ddd1646ddeecf2ad98c`
  (61,698,482 bytes).
- OpenAPI SHA-256: `e9ce08288cbc17bb643f6369bcc7c7cd0e5737b0fdd4976344ddab622abf05e4`.
- Generated client tree SHA-256:
  `f8dbb2951179efefeee475390ef5edaca88f13a52da1a8fb40bd14416d0a58fe`.
- Database current/head: `20260802_0008`.

## Boundary

This decision releases M8 against the accepted blog safe-content/revision/reference contracts. It
is not a production release: configurable pages, media, contacts, tokens, audit viewer, operator
hardening, the OSI-license decision, and M14 certification remain outstanding. Future AI extension
points stay architectural only; no AI runtime or user-facing AI claim is shipped.
