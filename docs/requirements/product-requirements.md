# Product Requirements

## Document control

| Field | Value |
|---|---|
| Source of truth | `SPEC.md` |
| Baseline | Initial specification, 2026-08-02 |
| Release | R1 (F1 public website + F2 administration) |
| Status vocabulary | Proposed, Approved, In progress, Implemented, Verified, Deferred, Rejected |

Requirement IDs are permanent. A changed or withdrawn requirement keeps its ID and records the new status; IDs are never reused. “Must” means release-blocking unless the requirement is explicitly marked as a target or recommendation.

## Product outcomes

- Present the owner as a credible technical professional through a premium, accessible public experience.
- Let a non-developer administrator control all public content without source-code changes.
- Expose the same application capabilities through a secure, versioned, documented API.
- Demonstrate production-quality Python/FastAPI, Next.js, security, testing, operations, and open-source practices.
- Preserve clean extension points for real future AI capabilities without shipping fake AI behavior.

## Functional requirements — F1 public experience

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| F1-001 | The product shall provide navigable Home, About, Experience, Skills, Projects, Project Detail, Blog, Blog Post Detail, Contact, Privacy, Legal, and administrator-created public pages. | Must | R1 |
| F1-002 | All public content shall come from the application API or a documented server-side access layer using the same application services; frontend components shall not hard-code public content. | Must | R1 |
| F1-003 | The public experience shall provide responsive desktop/mobile navigation, light/dark/system themes with persistent preference, and not-found, loading, empty, and error states. | Must | R1 |
| F1-004 | Public pages shall support per-page/default SEO metadata, Open Graph metadata, canonical URLs where applicable, sitemap, robots rules, and appropriate structured data. | Must | R1 |
| F1-005 | Home and configurable pages shall render schema-validated blocks for hero, profile summary, CTA, statistics, skills, experiences, projects, latest posts, rich text, image, image-with-text, links, contact callout, testimonial, divider, and spacing. | Must | R1 |
| F1-006 | Each applicable block shall support title, subtitle, description, visibility, order, theme/layout variants, CTA, content references, responsive options, and type-specific validated configuration. | Must | R1 |
| F1-007 | The public profile shall expose only administrator-approved profile fields and shall not expose sensitive personal information by default. | Must | R1 |
| F1-008 | Skills shall be publicly groupable by category, featureable, optionally filterable, and linked to related projects and experiences. | Must | R1 |
| F1-009 | Experiences shall have a polished timeline or equivalent presentation and shall show only visible, published records with valid date combinations. | Must | R1 |
| F1-010 | Projects shall provide listing, filtering, featured presentation, detail pages, screenshots, related skills, and related projects. | Must | R1 |
| F1-011 | The blog shall provide paginated listing, tag/category filters, post details, publication date, reading time, and related posts; only published content due for publication shall be public. | Must | R1 |
| F1-012 | Blog/page rich content shall use a safe portable format with explicit validation/sanitization; raw unsanitized HTML shall never render. | Must | R1 |
| F1-013 | The contact form shall accept name, email, subject, message, and consent; validate input; apply anti-spam and rate limits; and provide success/failure feedback. | Must | R1 |
| F1-014 | Public images shall be optimized and meaningful images shall expose administrator-managed alternative text. | Must | R1 |

## Functional requirements — F2 administration

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| F2-001 | An administrator shall securely log in/out, inspect the current session, change a password, and be denied access to protected routes after session expiration or without authorization. | Must | R1 |
| F2-002 | Initial administrator creation shall use an explicit command, environment-provided credentials, or one-time setup; production shall never enable predictable credentials and an initial password shall require change. | Must | R1 |
| F2-003 | The administrator shall manage profile fields: names/titles, biographies, image, location, availability, email, social profiles, values, work preferences, resume link, and public contact preferences. | Must | R1 |
| F2-004 | The administrator shall create, edit, delete, order, feature, show/hide, categorize, and relate skills to projects and experiences, including all fields defined in `SPEC.md` §5.4. | Must | R1 |
| F2-005 | The administrator shall create, edit, delete, order, show/hide, publish/unpublish, and relate experiences, including all fields in §5.5; inconsistent dates shall be rejected. | Must | R1 |
| F2-006 | The administrator shall create, edit, delete, order, feature, show/hide, publish/unpublish, and relate projects, media, skills, and experiences, including SEO and all fields in §5.6. | Must | R1 |
| F2-007 | The administrator shall create, edit, delete, draft, publish/unpublish, tag, categorize, schedule-ready, and relate blog posts with all fields in §5.7. | Must | R1 |
| F2-008 | The administrator shall list/filter/read, mark read, archive, and delete contact submissions; retention behavior shall be documented. | Must | R1 |
| F2-009 | Contact submissions shall never be exposed by unauthenticated APIs, and sensitive contact content shall not enter application logs. | Must | R1 |
| F2-010 | The media library shall upload, preview, search, paginate, and delete images; capture dimensions/alt/caption/timestamps; track usage; and prevent deletion while in use. | Must | R1 |
| F2-011 | Media uploads shall use safe filenames and validate MIME type, size, and content rather than trusting extensions; storage shall be abstracted for local, S3, and S3-compatible backends. | Must | R1 |
| F2-012 | The administrator shall create, update, delete, duplicate, preview, draft, publish/unpublish, and configure custom pages and their blocks, including reorder/duplicate/hide/delete block operations. | Must | R1 |
| F2-013 | Page slugs shall be unique and shall reject reserved application routes. | Must | R1 |
| F2-014 | The administrator shall configure ordered/visible internal and external navigation, target behavior, supported nesting, footer columns/links, copyright, social, and legal links; unsafe links shall be rejected. | Must | R1 |
| F2-015 | The administrator shall configure site identity, defaults, branding, locale/timezone, themes, contact/social data, SEO, analytics placeholders, and availability; secrets/private analytics credentials shall not be ordinary public settings. | Must | R1 |
| F2-016 | The administrator shall create, name, scope, optionally expire, copy once, inspect metadata for, rotate, and revoke API access tokens. | Must | R1 |
| F2-017 | Initial token scopes shall include `content:read`, `content:write`, `media:read`, `media:write`, `contacts:read`, and `admin:read`; every token operation shall enforce granted scope. | Must | R1 |
| F2-018 | The administrator shall inspect audit records for authentication, security, token, content, publication, settings, and media-deletion events with safe actor/resource/request metadata. | Must | R1 |
| F2-019 | The administration UI shall provide a responsive sidebar, context/title, appropriate breadcrumbs/actions, searchable/filterable lists, polished tables, destructive confirmations, publication states, unsaved-change protection, notifications, accessible forms, and essential mobile workflows. | Must | R1 |
| F2-020 | The administrator shall inspect basic liveness/readiness information without exposing sensitive dependency details. | Must | R1 |

## API and integration requirements

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| API-001 | The system shall use an API-first architecture with versioned initial namespace `/api/v1/`; public/admin clients shall use supported application services and APIs. | Must | R1 |
| API-002 | The OpenAPI contract shall be complete, valid, and compatible with client generation. | Must | R1 |
| API-003 | APIs shall consistently define resource naming, ISO 8601 dates, UTC timestamps, authentication, authorization, validation/domain errors, request IDs, and deprecation behavior. | Must | R1 |
| API-004 | List endpoints shall use one documented pagination strategy consistently and return pagination metadata. | Must | R1 |
| API-005 | Filtering and sorting shall be explicitly allow-listed, documented, and reject unsupported fields and arbitrary database expressions. | Must | R1 |
| API-006 | Errors shall contain a stable code, user-readable message, safe optional details, and request ID; production responses shall never contain stack traces. | Must | R1 |
| API-007 | The service shall expose liveness and readiness endpoints; readiness shall check required dependencies such as database connectivity. Version/build metadata may be exposed safely. | Must | R1 |
| API-008 | API consumers shall authenticate with access tokens and access only resources/actions allowed by unexpired, unrevoked token scopes. | Must | R1 |

## Security and privacy requirements

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| SEC-001 | Security design and review shall consider OWASP ASVS and relevant OWASP Top 10 risks. | Must | R1 |
| SEC-002 | Passwords shall be hashed with Argon2id or an equivalently secure algorithm and shall never be logged or reversibly stored. | Must | R1 |
| SEC-003 | Authentication shall implement expiration, secure cookies where used, brute-force/rate-limit protection, and successful/failed-login audit events. | Must | R1 |
| SEC-004 | Every protected operation shall perform explicit authorization and prevent IDOR and mass assignment. | Must | R1 |
| SEC-005 | Cookie-authenticated state changes shall have CSRF protection; CORS shall be restrictive; secure headers and XSS/content-sanitization controls shall be applied. | Must | R1 |
| SEC-006 | Persistence access shall prevent SQL injection and filtering shall not permit arbitrary expressions. | Must | R1 |
| SEC-007 | Uploads shall be constrained by validated content, MIME, size, safe names, and authorized access. | Must | R1 |
| SEC-008 | API token secrets shall be cryptographically random, shown only at creation, stored only as hashes, revocable/expirable, redacted from logs, and referenced in audit events without the secret. | Must | R1 |
| SEC-009 | Logs, errors, and audit metadata shall redact secrets, full authentication headers, passwords, contact message content, and unnecessary personal data. | Must | R1 |
| SEC-010 | Dependencies and source shall be scanned in CI where practical; a release shall contain no confirmed critical or high-severity security issue. | Must | R1 |

## Quality, architecture, and operational requirements

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| NFR-001 | The public and admin UI shall be premium, modern, credible, calm, consistent, responsive, and distinct from an unmodified template. | Must | R1 |
| NFR-002 | The accessibility target shall be WCAG 2.2 AA, covering keyboard/focus, skip links/landmarks/headings, labels/errors, contrast, reduced motion, screen readers, dialogs/focus restoration, alt text, zoom, and touch targets. | Must | R1 |
| NFR-003 | Automated accessibility testing shall be complemented by manual or browser-assisted review on representative pages and workflows. | Must | R1 |
| NFR-004 | Every asynchronous view shall define initial, loading, success, empty, validation-error, server-error, and applicable unauthorized states. | Must | R1 |
| NFR-005 | Representative public pages shall target Lighthouse performance ≥90, accessibility ≥95, SEO ≥95, and good Core Web Vitals without reducing functionality/accessibility. | Target | R1 |
| NFR-006 | The system shall optimize images/JavaScript/queries, prevent obvious N+1 access, paginate large lists, and index frequently queried fields. | Must | R1 |
| NFR-007 | The backend shall be a modular monolith separating transport, application, domain, persistence, infrastructure, security, and configuration; routes shall not contain complex business logic. | Must | R1 |
| NFR-008 | Frontend components shall not access the database directly; Server Components should be preferred when they reduce unnecessary client JavaScript. | Must | R1 |
| NFR-009 | Runtime baseline shall be Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, Pytest, Ruff, Mypy, structured logging, and OpenAPI. | Must | R1 |
| NFR-010 | Frontend baseline shall be Next.js App Router, React, strict TypeScript, Tailwind, accessible reusable components, React Hook Form, Zod, Playwright, Vitest, Testing Library, and Storybook. | Must | R1 |
| NFR-011 | All database schema changes shall use Alembic migrations; direct unmanaged schema changes are prohibited. | Must | R1 |
| NFR-012 | Delivery shall include Docker, Docker Compose, GitHub Actions, a Makefile/equivalent, environment-based configuration, and production-oriented images. | Must | R1 |
| NFR-013 | CI on pull requests and protected branches shall validate backend/frontend format, lint, types, tests, frontend production build, backend startup, migrations, E2E, security/dependencies, and OpenAPI. | Must | R1 |
| NFR-014 | Required backend, frontend, and end-to-end suites shall cover the categories and critical workflows listed in `SPEC.md` §13. | Must | R1 |
| NFR-015 | Coverage targets are backend ≥85%, backend security/critical domain ≥95%, frontend critical forms/utilities ≥80%, and all critical workflows E2E, without meaningless assertions. | Target | R1 |
| NFR-016 | A feature/release shall pass implementation, acceptance, tests, lint/format/type, migrations, security, accessibility, API, documentation, and container/CI gates; disabling tests or suppressing errors does not satisfy a gate. | Must | R1 |
| NFR-017 | Optional infrastructure/dependencies shall be introduced only for an active justified requirement; R1 shall avoid microservices, premature Kubernetes/distributed systems, fake AI, and needless abstractions. | Must | R1 |
| NFR-018 | Development shall proceed in small validated milestones, and each vertical slice shall include domain, persistence, migration, API, admin UI, relevant public UI, tests, and documentation. | Must | R1 |

## Documentation, open-source, change, and AI-readiness requirements

| ID | Requirement | Priority | Release |
|---|---|---:|---|
| DOC-001 | User documentation shall cover installation through troubleshooting, including administrator/content operations, tokens, backup, restore, and upgrades listed in `SPEC.md` §16.1. | Must | R1 |
| DOC-002 | API documentation shall cover base URL/versioning, authentication/tokens/scopes, pagination/filtering/sorting/errors/rates, examples/cURL, OpenAPI, and revocation. | Must | R1 |
| DOC-003 | Developer documentation shall cover architecture/repository, local development/config/database/migrations, conventions, testing/design system, contributions/releases/security, extension points, and future AI. | Must | R1 |
| OSS-001 | The public repository shall contain README, SPEC, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CHANGELOG, license, issue/PR templates, environment example, setup, roadmap, contribution standards, and UI screenshots when available. | Must | R1 |
| OSS-002 | The repository shall contain no credentials/tokens/private or proprietary data/internal information/machine-specific absolute paths/production database dumps. | Must | R1 |
| CHG-001 | Major technical decisions shall be recorded as ADRs with status, context, options, decision, consequences, and follow-ups. | Must | R1 |
| CHG-002 | Specification changes shall state rationale and implementation/migration/testing impact, update acceptance criteria, and explicitly resolve contradictions. | Must | R1 |
| AI-001 | R1 shall reserve a clean documented boundary for future AI agents, providers, retrieval, embeddings, vector stores, prompts, evaluation, resume, schemas, and services without implementing F3/F4. | Must | R1 |
| AI-002 | Future interfaces shall be able to abstract LLM/embedding providers, vector stores, document sources, retrieval, agent execution, prompt registry, usage, audit, structured outputs, evaluation data, and tracing. | Must | R1-readiness |
| AI-003 | Future AI modules shall be able to consume published profile, skill, experience, project, and blog data through application-service/API boundaries, never by bypassing publication rules. | Must | R1-readiness |
| AI-004 | No fake AI behavior or speculative AI infrastructure shall ship in R1; F3 and F4 remain Deferred unless scope is explicitly changed under CHG-002. | Must | R1 |

## Release acceptance summary

R1 is acceptable only when every R1 “Must” requirement is `Verified`, all release-blocking acceptance criteria pass, migrations succeed from an empty database, production containers build, CI passes, representative pages pass accessibility review, installation succeeds from public documentation, and no confirmed critical/high security finding remains. Target requirements must be measured and reported; a miss requires an explicit disposition rather than silent omission.
