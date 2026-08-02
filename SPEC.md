# Personal Platform — Product and Engineering Specification

## 1. Document purpose

This document defines the functional, technical, architectural, security, quality, testing, and documentation requirements for the Personal Platform project.

It is the primary source of truth for:

* product requirements;
* technical decisions;
* implementation planning;
* agentic development workflows;
* acceptance criteria;
* quality validation;
* future AI integrations.

All contributors and automated development agents must read this document before implementing or modifying the application.

When implementation and this specification differ, the discrepancy must be documented and resolved explicitly.

---

# 2. Product vision

Personal Platform is a production-grade, open-source personal website and content management system designed for software engineers, AI engineers, consultants, and technical professionals.

The product combines:

* a premium public portfolio;
* a fully configurable administration interface;
* an API-first backend;
* reusable page-building capabilities;
* strong developer experience;
* future-ready AI integration points.

The public website must communicate technical expertise, credibility, business impact, and product thinking.

The administration interface must allow a non-developer administrator to manage all public content without editing source code.

The product must be credible as:

* an open-source portfolio project;
* a production-ready web application;
* a demonstration of advanced Python and FastAPI engineering;
* a foundation for future agentic AI features.

---

# 3. Project scope

## 3.1 Current implementation scope

The first implementation phase includes:

* F1 — Public personal website;
* F2 — Configurable administration interface;
* complete REST API;
* API access token management;
* authentication and authorization;
* documentation;
* automated testing;
* CI/CD validation;
* local and production-ready containerization.

## 3.2 Future scope

The architecture must prepare for:

* F3 — Agentic RAG portfolio assistant;
* F4 — AI resume generator;
* LangChain integration;
* LangGraph integration;
* vector databases;
* embeddings;
* multiple LLM providers;
* structured AI output;
* AI observability;
* AI evaluation;
* background jobs.

F3 and F4 must not be fully implemented during the first phase unless explicitly added to the project scope.

No fake AI functionality should be created.

---

# 4. Primary users

## 4.1 Public visitor

A public visitor may:

* discover the profile owner;
* browse professional experiences;
* browse projects;
* inspect technical skills;
* read blog posts;
* submit a contact request;
* navigate the website on desktop and mobile;
* access public content without authentication.

## 4.2 Administrator

An administrator may:

* authenticate securely;
* configure the website;
* edit profile information;
* manage pages;
* manage configurable blocks;
* manage skills;
* manage professional experiences;
* manage projects;
* manage blog posts;
* manage media;
* manage contact submissions;
* manage navigation;
* manage footer content;
* manage SEO metadata;
* preview unpublished content;
* publish and unpublish content;
* create and revoke API access tokens;
* inspect audit logs;
* inspect basic system health.

## 4.3 API consumer

An API consumer may:

* authenticate using an API access token;
* access authorized API resources;
* use documented pagination, filtering, and sorting;
* integrate external services with the platform;
* operate only within the scopes granted to its token.

---

# 5. Functional requirements

# 5.1 Public website

The public website must include the following pages or equivalent navigable sections:

* Home;
* About;
* Professional experience;
* Skills;
* Projects;
* Project details;
* Blog;
* Blog post details;
* Contact;
* Privacy policy;
* Legal information;
* custom pages created through the administration interface.

The website must support:

* responsive layouts;
* desktop navigation;
* mobile navigation;
* dark mode;
* light mode;
* SEO metadata;
* Open Graph metadata;
* semantic HTML;
* accessible keyboard navigation;
* sitemap generation;
* robots configuration;
* structured data where appropriate;
* optimized images;
* loading states;
* error states;
* not-found pages.

All public content must come from the application API or a documented server-side data access layer built on top of the same application services.

Public content must not be hard-coded into frontend components.

---

# 5.2 Home page

The home page must support configurable blocks.

Supported initial block types must include:

* hero;
* profile summary;
* call to action;
* statistics;
* skills grid;
* featured skills;
* professional experience summary;
* professional experience list;
* project grid;
* featured projects;
* latest blog posts;
* rich text;
* image;
* image with text;
* links collection;
* contact callout;
* testimonial;
* section divider;
* spacing block.

Each block must support, where relevant:

* title;
* subtitle;
* description;
* visibility;
* display order;
* theme variant;
* layout variant;
* call-to-action configuration;
* content references;
* responsive options;
* block-specific configuration.

Each block configuration must be validated against an explicit schema.

---

# 5.3 About profile

The administrator must be able to manage:

* full name;
* professional title;
* short biography;
* full biography;
* profile image;
* location;
* availability;
* email address;
* social links;
* GitHub profile;
* LinkedIn profile;
* personal values;
* preferred working arrangements;
* downloadable resume link;
* public contact preferences.

Sensitive personal information must not be exposed by default.

---

# 5.4 Skills

Each skill must support:

* name;
* slug;
* category;
* description;
* proficiency label;
* optional proficiency score;
* years of experience;
* icon;
* display order;
* featured status;
* visibility status;
* associated projects;
* associated professional experiences;
* creation timestamp;
* update timestamp.

The public website must support:

* skill grouping by category;
* featured skills;
* skill filtering where useful;
* links from skills to related projects and experiences.

The administration interface must support:

* skill creation;
* skill editing;
* skill deletion;
* bulk ordering;
* visibility controls;
* featured controls;
* category management.

---

# 5.5 Professional experiences

Each professional experience must support:

* company name;
* company URL;
* role title;
* employment type;
* location;
* remote status;
* start date;
* end date;
* current-position flag;
* short summary;
* detailed description;
* responsibilities;
* achievements;
* technologies;
* related skills;
* display order;
* visibility;
* publication status;
* creation timestamp;
* update timestamp.

The application must prevent inconsistent date combinations.

The public website must support a polished timeline or equivalent professional presentation.

---

# 5.6 Projects

Each project must support:

* name;
* slug;
* short description;
* full description;
* business or user problem;
* implemented solution;
* measurable impact;
* technical architecture;
* technologies;
* screenshots;
* cover image;
* repository URL;
* live demo URL;
* project status;
* featured status;
* start date;
* end date;
* related skills;
* related professional experiences;
* display order;
* visibility;
* publication status;
* SEO title;
* SEO description;
* canonical URL;
* creation timestamp;
* update timestamp.

The public website must support:

* project listing;
* project filtering;
* featured projects;
* individual project pages;
* project screenshots;
* related skills;
* related projects.

---

# 5.7 Blog

Each blog post must support:

* title;
* slug;
* excerpt;
* body;
* cover image;
* author;
* tags;
* categories;
* draft status;
* published status;
* publication date;
* scheduled publication architecture;
* reading time;
* SEO title;
* SEO description;
* canonical URL;
* related posts;
* creation timestamp;
* update timestamp.

The editor must use a safe and portable content format.

Acceptable formats include:

* sanitized rich text;
* Markdown with controlled extensions;
* structured JSON document format with explicit validation.

Raw unsanitized HTML must not be rendered.

The public blog must support:

* post listing;
* pagination;
* tag filtering;
* category filtering;
* individual post pages;
* publication dates;
* reading time;
* related posts.

---

# 5.8 Contact

The public contact form must support:

* visitor name;
* visitor email;
* subject;
* message;
* consent confirmation;
* validation;
* anti-spam controls;
* rate limiting;
* successful submission feedback;
* failure feedback.

The administration interface must support:

* listing submissions;
* filtering submissions;
* reading submission details;
* marking submissions as read;
* archiving submissions;
* deletion;
* retention documentation.

Contact submissions must never be available from unauthenticated APIs.

Sensitive contact data must not appear in application logs.

---

# 5.9 Media library

The media library must support:

* image upload;
* safe filename generation;
* MIME type validation;
* file size validation;
* image dimension extraction;
* alternative text;
* caption;
* creation timestamp;
* update timestamp;
* usage tracking;
* deletion protection for media currently in use;
* preview;
* search;
* pagination.

The storage implementation must use an abstraction allowing future support for:

* local filesystem storage;
* Amazon S3;
* S3-compatible object storage.

Uploaded files must never be trusted solely based on their extension.

---

# 5.10 Page management

Administrators must be able to:

* create pages;
* update pages;
* delete pages;
* duplicate pages;
* define page titles;
* define slugs;
* define navigation visibility;
* define SEO metadata;
* save drafts;
* publish pages;
* unpublish pages;
* preview pages;
* reorder page blocks;
* duplicate blocks;
* hide blocks;
* configure blocks;
* delete blocks.

Slugs must be unique.

Reserved application routes must not be usable as custom page slugs.

---

# 5.11 Navigation and footer

The administrator must be able to configure:

* navigation items;
* item labels;
* internal links;
* external links;
* item order;
* visibility;
* link target behavior;
* nested navigation where supported;
* footer columns;
* footer links;
* copyright text;
* social links;
* legal links.

Invalid or unsafe links must be rejected.

---

# 5.12 Website settings

The administrator must be able to configure:

* website name;
* default title;
* default description;
* logo;
* favicon;
* default social image;
* default locale;
* timezone;
* theme preferences;
* primary branding settings;
* contact details;
* social links;
* default SEO metadata;
* analytics integration placeholders;
* public availability information.

Secrets and private analytics credentials must not be stored as ordinary public settings.

---

# 5.13 Authentication

The administration interface must provide:

* secure login;
* logout;
* password change;
* current-session inspection;
* session expiration;
* protected routes;
* brute-force protection;
* failed-login audit events;
* successful-login audit events.

Passwords must be hashed using Argon2id or an equivalently secure password hashing algorithm.

Production credentials must never be predictable.

A default administrator must be created using one of the following secure mechanisms:

* explicit initialization command;
* environment-provided initial credentials;
* one-time setup workflow.

Development-only credentials may be documented but must not be enabled implicitly in production.

An administrator using an initial password should be required to change it.

---

# 5.14 API access tokens

The administration interface must allow an administrator to:

* create an access token;
* name the token;
* define scopes;
* define an optional expiration;
* copy the token once;
* inspect creation metadata;
* inspect last-used metadata;
* revoke the token;
* rotate the token.

Initial supported scopes should include:

* `content:read`;
* `content:write`;
* `media:read`;
* `media:write`;
* `contacts:read`;
* `admin:read`.

Tokens must:

* contain cryptographically secure random values;
* be stored only as hashes;
* support revocation;
* support expiration;
* never be displayed after initial creation;
* be excluded from logs;
* be included in audit records without storing the secret value.

---

# 5.15 Audit logs

Audit logs must cover:

* successful authentication;
* failed authentication;
* logout;
* password changes;
* API token creation;
* API token revocation;
* content creation;
* content editing;
* content deletion;
* publication changes;
* website settings changes;
* media deletion;
* administrator security actions.

Audit entries should contain:

* event type;
* actor identifier;
* resource type;
* resource identifier;
* timestamp;
* request identifier;
* safe metadata;
* IP information where legally and operationally appropriate.

Audit metadata must not contain passwords, API tokens, full authentication headers, or unnecessary personal data.

---

# 6. API requirements

## 6.1 API strategy

The application must follow an API-first architecture.

All business capabilities required by the public website and administration interface should be accessible through application services exposed by versioned APIs.

The initial API namespace must be:

```text
/api/v1/
```

The API must be compatible with OpenAPI client generation.

## 6.2 API conventions

The API must provide consistent conventions for:

* resource naming;
* pagination;
* filtering;
* sorting;
* authentication;
* authorization;
* validation errors;
* domain errors;
* request identifiers;
* date and time formats;
* deprecation;
* response schemas.

Dates and times must use ISO 8601 representations.

Timestamps must be stored in UTC.

## 6.3 Pagination

List endpoints must use a documented pagination strategy.

The default strategy may use:

* page and page size; or
* cursor-based pagination.

The selected strategy must be consistent.

Responses must include pagination metadata.

## 6.4 Filtering and sorting

Filtering and sorting parameters must:

* be explicitly allow-listed;
* reject unsupported fields;
* be documented in OpenAPI;
* avoid arbitrary database expressions.

## 6.5 Error format

The API must use a consistent error response.

Example:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "The requested project was not found.",
    "details": {},
    "request_id": "01J..."
  }
}
```

Errors must contain:

* a stable machine-readable code;
* a user-readable message;
* safe optional details;
* a request identifier.

Internal stack traces must never be returned in production.

## 6.6 Health endpoints

The application must expose:

* liveness endpoint;
* readiness endpoint;
* optional version or build information endpoint.

Readiness must validate required dependencies such as database connectivity.

---

# 7. Technical stack

## 7.1 Backend

Required technologies:

* Python 3.12 or later;
* FastAPI;
* Pydantic;
* SQLAlchemy 2;
* Alembic;
* PostgreSQL;
* Argon2id password hashing;
* Pytest;
* Ruff;
* Mypy;
* structured logging;
* OpenAPI.

Optional backend technologies:

* Redis;
* Celery, Dramatiq, Arq, or equivalent background execution system;
* object storage SDK;
* rate-limiting middleware.

Optional technologies must only be added when justified by a current requirement.

## 7.2 Frontend

Required technologies:

* Next.js;
* React;
* TypeScript with strict mode;
* Next.js App Router;
* Tailwind CSS;
* an accessible reusable component system;
* React Hook Form;
* Zod;
* Playwright;
* Vitest;
* Testing Library;
* Storybook.

TanStack Query may be used for client-side server state where it improves behavior.

Server Components should be preferred where they reduce unnecessary client-side JavaScript.

## 7.3 Database

PostgreSQL is the primary relational database.

Database changes must use Alembic migrations.

Direct schema changes without migrations are prohibited.

## 7.4 Infrastructure

Required tooling:

* Docker;
* Docker Compose;
* GitHub Actions;
* Makefile or an equivalent task runner;
* environment-variable-based configuration;
* production-oriented container images.

---

# 8. Architecture

## 8.1 Architecture style

The backend should use a modular monolith.

The architecture must separate:

* API transport;
* application services;
* domain rules;
* persistence;
* infrastructure;
* security;
* configuration.

Route handlers must not contain complex business logic.

Frontend components must not access the database directly.

## 8.2 Suggested backend modules

```text
backend/app/
├── api/
│   └── v1/
├── auth/
├── users/
├── profile/
├── website_settings/
├── pages/
├── page_blocks/
├── navigation/
├── skills/
├── experiences/
├── projects/
├── blog/
├── media/
├── contacts/
├── api_tokens/
├── audit/
├── health/
├── common/
├── infrastructure/
└── ai/
```

## 8.3 Suggested frontend areas

```text
frontend/
├── app/
│   ├── (public)/
│   ├── admin/
│   └── api/
├── components/
│   ├── public/
│   ├── admin/
│   ├── blocks/
│   └── ui/
├── features/
├── lib/
├── hooks/
├── styles/
├── tests/
└── stories/
```

## 8.4 Repository structure

Recommended initial structure:

```text
personal-platform/
├── backend/
├── frontend/
├── docs/
├── scripts/
├── infrastructure/
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── SPEC.md
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── docker-compose.yml
├── .env.example
├── .editorconfig
├── .gitignore
└── pre-commit-config.yaml
```

---

# 9. Security requirements

The implementation must consider the OWASP Application Security Verification Standard and relevant OWASP Top 10 risks.

Required controls include:

* secure password hashing;
* explicit authorization checks;
* CSRF protection where cookie-based authentication requires it;
* XSS prevention;
* content sanitization;
* SQL injection prevention;
* upload validation;
* secure cookies;
* restrictive CORS;
* secure headers;
* rate limiting;
* brute-force protection;
* secret redaction;
* dependency scanning;
* prevention of insecure direct object references;
* prevention of mass assignment;
* audit logging;
* safe error handling;
* API token hashing;
* API token revocation.

No confirmed critical or high-severity security issue may remain in a release.

---

# 10. User interface requirements

## 10.1 Design principles

The product must appear:

* premium;
* modern;
* credible;
* technically precise;
* calm;
* consistent;
* responsive;
* accessible.

The public website must not look like an unmodified portfolio template.

The administration interface must be comparable in quality to mature SaaS dashboards and modern content-management products.

## 10.2 Required interface states

Every asynchronous view must define:

* initial state;
* loading state;
* successful state;
* empty state;
* validation-error state;
* server-error state;
* unauthorized state where applicable.

## 10.3 Administration experience

The administration interface must include:

* responsive sidebar;
* page title and context;
* breadcrumbs where appropriate;
* contextual actions;
* searchable and filterable lists;
* polished tables;
* confirmation for destructive actions;
* clear publication states;
* unsaved-change protection;
* success notifications;
* accessible forms;
* keyboard navigation;
* mobile-compatible essential workflows.

## 10.4 Theme

The application must support:

* light mode;
* dark mode;
* operating-system preference;
* persistent user preference;
* sufficient contrast in all themes.

---

# 11. Accessibility requirements

The target is WCAG 2.2 AA.

The implementation must support:

* keyboard navigation;
* visible focus states;
* skip links;
* semantic landmarks;
* correct heading hierarchy;
* form labels;
* accessible validation messages;
* sufficient contrast;
* reduced-motion preferences;
* screen-reader-compatible controls;
* accessible dialogs;
* focus trapping in modal interfaces;
* focus restoration;
* meaningful alternative text;
* responsive zoom;
* touch-friendly targets.

Automated accessibility testing must be complemented by manual or browser-assisted review.

---

# 12. Performance requirements

Representative public pages should target:

* Lighthouse performance score of 90 or higher;
* Lighthouse accessibility score of 95 or higher;
* Lighthouse SEO score of 95 or higher;
* good Core Web Vitals;
* optimized images;
* minimal unnecessary JavaScript;
* efficient database queries;
* no obvious N+1 queries;
* paginated large lists;
* indexed frequently queried fields.

Performance targets are goals, not reasons to hide functionality or skip accessibility.

---

# 13. Testing strategy

## 13.1 Backend tests

The backend test suite must include:

* unit tests;
* application-service tests;
* repository tests;
* API integration tests;
* authentication tests;
* authorization tests;
* API token tests;
* migration tests;
* validation tests;
* domain-error tests;
* audit-log tests;
* file-upload tests.

## 13.2 Frontend tests

The frontend test suite must include:

* component tests;
* form tests;
* validation tests;
* state tests;
* accessibility tests;
* page behavior tests;
* reusable component stories;
* Storybook interaction tests where useful.

## 13.3 End-to-end tests

The end-to-end suite must cover at minimum:

* administrator bootstrap;
* administrator login;
* invalid login;
* password change;
* protected route access;
* skill creation and public rendering;
* experience creation and public rendering;
* project creation and public rendering;
* blog post creation and publication;
* configurable page creation;
* block creation and reordering;
* draft preview;
* publication;
* unpublication;
* media upload;
* contact form submission;
* contact submission review;
* API token creation;
* authenticated API usage;
* API token revocation;
* unauthorized API access.

## 13.4 Coverage targets

Recommended targets:

* backend overall coverage: at least 85%;
* backend security and critical domain logic: at least 95%;
* frontend critical forms and business utilities: at least 80%;
* all critical workflows covered by end-to-end tests.

Coverage targets must not encourage meaningless assertions.

---

# 14. Quality gates

A feature is complete only when:

* its requirements are implemented;
* acceptance criteria are met;
* unit tests pass;
* integration tests pass;
* relevant end-to-end tests pass;
* linting passes;
* formatting passes;
* static typing passes;
* database migrations succeed;
* security review succeeds;
* accessibility review succeeds;
* API review succeeds;
* documentation is updated;
* no confirmed critical or high-severity issue remains.

A green build obtained by disabling tests or suppressing errors is invalid.

---

# 15. Continuous integration

GitHub Actions must run on pull requests and protected branches.

The CI pipeline must include:

* backend formatting validation;
* backend linting;
* backend static typing;
* backend tests;
* frontend formatting validation;
* frontend linting;
* frontend static typing;
* frontend tests;
* production frontend build;
* backend application startup validation;
* migration validation;
* end-to-end tests;
* dependency vulnerability checks where practical;
* security static analysis;
* OpenAPI schema validation.

CI jobs should be separated where this improves diagnostic clarity.

---

# 16. Documentation requirements

## 16.1 User documentation

User documentation must explain:

* installation;
* first startup;
* administrator initialization;
* first login;
* password change;
* website configuration;
* page management;
* block management;
* skill management;
* experience management;
* project management;
* blog management;
* media management;
* contact management;
* API token management;
* backup;
* restore;
* upgrades;
* troubleshooting.

## 16.2 API documentation

API documentation must explain:

* base URL;
* versioning;
* authentication;
* token creation;
* token scopes;
* pagination;
* filtering;
* sorting;
* errors;
* rate limits;
* endpoint examples;
* cURL examples;
* OpenAPI access;
* token revocation.

## 16.3 Developer documentation

Developer documentation must explain:

* architecture;
* repository structure;
* local development;
* configuration;
* database setup;
* migrations;
* backend conventions;
* frontend conventions;
* testing;
* design system;
* contribution process;
* pull request expectations;
* release process;
* security reporting;
* extension points;
* future AI integration.

---

# 17. Open-source requirements

The repository must include:

* `README.md`;
* `SPEC.md`;
* `CONTRIBUTING.md`;
* `SECURITY.md`;
* `CODE_OF_CONDUCT.md`;
* `CHANGELOG.md`;
* an open-source license;
* issue templates;
* pull request template;
* environment example;
* local setup instructions;
* screenshots when the UI exists;
* roadmap;
* contribution standards.

The repository must not contain:

* credentials;
* API tokens;
* private data;
* proprietary source code;
* internal company information;
* machine-specific absolute paths;
* production database dumps.

---

# 18. Future AI architecture

The project must reserve a clean architectural boundary for future AI capabilities.

Suggested structure:

```text
backend/app/ai/
├── agents/
├── providers/
├── retrieval/
├── embeddings/
├── vectorstores/
├── prompts/
├── evaluation/
├── resume/
├── schemas/
└── services/
```

Future interfaces should support:

* LLM provider;
* embedding provider;
* vector store;
* document source;
* retrieval service;
* agent execution;
* prompt registry;
* AI usage tracking;
* AI audit events;
* structured outputs;
* evaluation datasets;
* tracing.

Future AI modules must be able to consume published:

* profile information;
* skills;
* professional experiences;
* projects;
* blog posts.

The initial implementation should provide documented extension boundaries but must avoid speculative over-engineering.

---

# 19. Development workflow

Development must proceed through small, validated milestones.

Recommended order:

1. repository foundation;
2. backend and frontend skeletons;
3. database and migrations;
4. administrator authentication;
5. API conventions;
6. website settings;
7. navigation and footer;
8. skills vertical slice;
9. experiences vertical slice;
10. projects vertical slice;
11. blog vertical slice;
12. configurable pages and blocks;
13. media library;
14. contact workflow;
15. API access tokens;
16. audit logs;
17. product polish;
18. security validation;
19. accessibility validation;
20. release validation.

Each vertical slice must include:

* backend domain logic;
* persistence;
* migration;
* API;
* administration UI;
* public UI where relevant;
* automated tests;
* documentation.

---

# 20. Agentic implementation graph

Automated development agents must follow this workflow:

```text
Requirements analysis
        |
Architecture review
        |
UX and interface design
        |
Technical planning
        |
Task implementation
        |
Automated testing
        |
Integration review
        |
Code review
        |
Security review
        |
API review
        |
Accessibility and UX review
        |
Defect triage
      /   \
Defects   Accepted
   |         |
Correction  Documentation
   |         |
   +----> Release validation
```

Corrections must be based on observable evidence such as:

* failed tests;
* reproducible defects;
* security findings;
* accessibility findings;
* API contract issues;
* requirement gaps;
* performance measurements.

Agents must not loop based only on subjective requests to “improve” the result.

---

# 21. Acceptance criteria

The first product release is accepted only when:

* the complete public website is operational;
* all public content is configurable;
* administrator authentication is secure;
* configurable pages and blocks work;
* skills CRUD works;
* experiences CRUD works;
* projects CRUD works;
* blog CRUD works;
* media management works;
* contact submissions work;
* API access tokens work;
* public and admin interfaces consume supported application APIs;
* OpenAPI documentation is complete;
* user documentation exists;
* developer documentation exists;
* API documentation exists;
* tests pass;
* migrations pass from an empty database;
* production containers build;
* CI passes;
* no critical or high security issue remains;
* representative pages pass accessibility review;
* the application can be installed from the public documentation.

---

# 22. Definition of done

A task is done only when:

* implementation is complete;
* behavior is validated;
* error cases are handled;
* tests are written;
* tests pass;
* types pass;
* lint passes;
* documentation is updated;
* migrations are included where required;
* security consequences are reviewed;
* accessibility consequences are reviewed;
* no placeholder behavior remains.

---

# 23. Initial release constraints

The initial release should prioritize:

* correctness;
* security;
* maintainability;
* visual quality;
* testability;
* clear documentation.

The initial release should avoid:

* microservices;
* unnecessary event-driven infrastructure;
* premature Kubernetes configuration;
* speculative distributed systems;
* fake AI capabilities;
* excessive dependencies;
* complex abstractions without an active use case.

---

# 24. Decision recording

Major technical decisions must be recorded as Architecture Decision Records under:

```text
docs/architecture/decisions/
```

ADRs should include:

* decision title;
* status;
* context;
* considered options;
* decision;
* consequences;
* follow-up actions.

Initial ADR candidates include:

* monorepo structure;
* authentication strategy;
* API pagination strategy;
* page-block storage model;
* rich-text format;
* media storage abstraction;
* frontend API client generation;
* API token scopes;
* future AI integration boundary.

---

# 25. Change management

Changes to this specification must:

* be explicit;
* explain the reason;
* describe implementation impact;
* describe migration impact;
* describe testing impact;
* update acceptance criteria where necessary.

Unresolved contradictions must not be silently implemented.

---

# 26. Current status

Initial status:

* specification defined;
* repository foundation pending;
* F1 implementation pending;
* F2 implementation pending;
* F3 deferred;
* F4 deferred.

This section must be updated as the project progresses.
