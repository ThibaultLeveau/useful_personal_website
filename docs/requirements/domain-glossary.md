# Domain Glossary

| Term | Definition / rule |
|---|---|
| Administrator | The privileged human operator who manages content, settings, tokens, contacts, and audits. R1 specifies a single administrator role conceptually; multi-role administration is not promised. |
| API consumer | An external integration using a scoped API access token, distinct from a browser administrator session. |
| API access token | A named bearer credential with explicit scopes and optional expiration. Its secret is shown once and only a hash is stored. |
| Application service | The reusable layer that coordinates domain rules and persistence for API, public server access, and admin workflows. |
| Archive | A reversible or logically retained contact-submission state, distinct from permanent deletion. Exact retention duration is a policy decision. |
| Audit event | An immutable security/operational record containing safe actor, resource, time, request, and limited contextual metadata, never credential secrets. |
| Block | A typed, schema-validated, ordered page section. A block has shared presentation fields and type-specific configuration. |
| Canonical URL | The preferred URL supplied to search engines for duplicate/related content resolution. |
| Configurable page | An administrator-created page composed of blocks and governed by draft/publication, slug, navigation, and SEO rules. |
| Content reference | A validated relation from a block or entity to reusable content such as skills, projects, experiences, posts, or media. |
| Draft | Authenticated-previewable content that is not available through ordinary public retrieval. |
| Featured | An editorial flag that elevates otherwise visible/published content; it does not itself publish hidden content. |
| F1 | R1 public personal website capability. |
| F2 | R1 administration and CMS capability. |
| F3 | Deferred agentic RAG portfolio assistant. Not an R1 feature. |
| F4 | Deferred AI resume generator. Not an R1 feature. |
| Initial password | A credential established during secure bootstrap that must be changed by the administrator before ordinary administration continues. |
| Liveness | A shallow health signal that the application process can respond; it should not fail solely because a dependency is unavailable. |
| Media in use | A media record referenced by any retained content/settings record; destructive deletion is blocked until references are removed. |
| Modular monolith | One deployable backend organized into cohesive modules and layered boundaries, without independent microservices. |
| Page slug | A unique, URL-safe public-page identifier that cannot collide with reserved application routes. |
| Personal Platform | The production-grade, open-source public portfolio, CMS, and API described by `SPEC.md`. |
| Publication date | The effective public release time for published content. Stored as UTC; presentation uses configured locale/timezone. |
| Publication status | A domain state controlling eligibility for ordinary public retrieval. Visibility and schedule conditions still apply. |
| Published data | Content satisfying publication status, visibility, and effective-time rules; future AI access is limited to this set. |
| Readiness | A health signal that required dependencies, especially PostgreSQL, permit the service to handle requests. |
| Reserved route | A platform-owned path (for example administration, API, or required public route) unavailable as a custom-page slug. The exact registry must be documented. |
| R1 | The first product release comprising F1, F2, API, security, documentation, tests, CI/CD, and containerization. |
| Safe portable content | Sanitized rich text, controlled Markdown, or validated structured JSON whose storage/rendering is not tied to unsafe raw HTML. |
| Scope | A token permission string authorizing a bounded resource/action family; scope does not bypass resource-level authorization. |
| Sensitive personal information | Personal data not intentionally approved for public display, including contact submission data and private settings. |
| Structured data | Machine-readable page metadata, typically schema.org JSON-LD, used only where appropriate to content type. |
| Theme preference | Light, dark, or system-derived display mode, persisted for repeat visits while retaining sufficient contrast. |
| Usage tracking (media) | References/usage locations used to find assets and enforce in-use deletion protection; it is not visitor analytics. |
| Vertical slice | A capability delivered through domain rules, persistence/migration, API, admin UI, relevant public UI, tests, and documentation. |
| Visibility | An editorial display gate independent of draft/published lifecycle. Public exposure requires all applicable gates to permit it. |

## State rules

- Publicly retrievable content = `published` AND `visible` AND publication time (if present) is effective.
- `featured` never overrides publication or visibility.
- `current-position = true` implies no end date; a non-current experience with a known end date must not end before it starts.
- Revoked, expired, or unknown API tokens authorize nothing.
- Hidden blocks remain stored and editable but do not render publicly.
- Archived contact submissions remain authenticated-only and follow the documented retention policy.
