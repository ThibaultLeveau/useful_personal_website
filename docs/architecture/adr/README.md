# Architecture Decision Record Index

ADRs are immutable decision history. Superseding a decision adds a new ADR and updates status/link; numbers are never reused. Statuses: Proposed, Accepted, Superseded, Rejected.

| ADR | Decision | Status | Requirements |
|---|---|---|---|
| [0001](0001-modular-monolith-and-monorepo.md) | Modular monolith and monorepo | Accepted | NFR-007–NFR-012, NFR-017 |
| [0002](0002-authentication-and-api-tokens.md) | Opaque admin sessions and scoped API tokens | Accepted | F2-001–002, F2-016–017, SEC-002–008 |
| [0003](0003-api-envelope-and-pagination.md) | API envelopes and page pagination | Accepted | API-003–006 |
| [0004](0004-typed-page-block-storage.md) | Relational block shell plus validated JSONB | Accepted | F1-005–006, F2-012–013 |
| [0005](0005-controlled-markdown.md) | Controlled CommonMark Markdown | Accepted | F1-012, SEC-005 |
| [0006](0006-media-storage-abstraction.md) | Private media through storage port | Accepted | F2-010–011, SEC-007 |
| [0007](0007-publication-revisions-and-scheduling.md) | Immutable revisions and time-gated scheduling | Accepted | F1-009–011, F2-005–007, F2-012 |
| [0008](0008-audit-and-retention.md) | Append-only safe audit and bounded retention | Accepted | F2-008–009, F2-018, SEC-009 |
| [0009](0009-no-redis-or-worker-in-r1.md) | No required Redis/worker in R1 | Accepted | NFR-017, AI-004 |
| [0010](0010-openapi-generated-frontend-client.md) | OpenAPI-generated frontend client | Accepted | API-001–002, NFR-008 |
| [0011](0011-future-ai-boundary.md) | Publication-safe future AI boundary | Accepted | AI-001–004 |
| [0012](0012-production-deployment-topology.md) | Two web containers, PostgreSQL, private object storage | Accepted | NFR-012, API-007, OSS-002 |
