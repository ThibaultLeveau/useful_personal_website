# API documentation

The canonical machine-readable contract is [OpenAPI 3.1 JSON](openapi.json). All current operations
are versioned below `/api/v1` and return request-correlated envelopes.

- [API conventions and consumer examples](conventions.md)
- [Current route, security, filter/sort, and error catalogs](catalogs.md)
- [Liveness, readiness, and administrator health](health.md)
- [Browser administrator authentication](authentication.md)
- [Profile, settings, navigation, footer, and public projections](site-configuration.md)
- [Skills categories, CRUD, ordering, filters, and public projection](skills.md)
- [Professional experience lifecycle and public projection](experiences.md)
- [Project case-study lifecycle, relations, SEO, and public projection](projects.md)
- [Blog lifecycle, controlled content, taxonomy, export, and public projection](blog.md)
- [Secure media upload, library, usage, and public rendition delivery](media.md)
- [Private contact submission and administrator lifecycle](contacts.md)
- [Scoped API-token lifecycle and integration route matrix](api-tokens.md)
- [Protected audit inspection and exact filter contract](audit.md)

The conventions define pagination, filtering/sorting, concurrency, and idempotency. Exact route
catalogs and the generated contract represent shipped behavior only; planned routes never appear as
active operations.
