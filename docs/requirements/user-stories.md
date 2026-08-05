# User Stories

Stories express actor intent; they do not replace the normative product requirements. Each story must be accepted against the linked acceptance criteria in `acceptance-criteria.md`.

## Public visitor

| Story ID | User story | Requirement IDs |
|---|---|---|
| US-VIS-001 | As a visitor, I want to navigate all core and custom pages on any device so that I can understand the owner’s profile and offerings. | F1-001, F1-003, NFR-001 |
| US-VIS-002 | As a visitor, I want the home page to present relevant configurable sections so that I see a curated, current introduction. | F1-002, F1-005, F1-006 |
| US-VIS-003 | As a visitor, I want to read an intentionally public profile without sensitive details leaking so that I can contact the owner appropriately. | F1-007, F2-003 |
| US-VIS-004 | As a visitor, I want to browse and relate skills, experience, and projects so that I can evaluate demonstrated expertise. | F1-008–F1-010 |
| US-VIS-005 | As a visitor, I want to filter projects and inspect rich project details so that I can find relevant evidence of impact. | F1-010 |
| US-VIS-006 | As a reader, I want to browse/filter paginated posts and safely read published content so that I can learn from current writing. | F1-011–F1-012 |
| US-VIS-007 | As a visitor, I want to submit a validated, consented contact request and receive clear feedback so that I know whether it arrived. | F1-013 |
| US-VIS-008 | As a visitor using assistive technology, I want semantic, keyboard-operable, perceivable pages so that I can use the entire public site. | NFR-002–NFR-004 |
| US-VIS-009 | As a visitor, I want my theme preference retained and images/pages to load efficiently so that the experience is comfortable and fast. | F1-003, F1-014, NFR-005–NFR-006 |
| US-VIS-010 | As a search/social visitor, I want accurate metadata and canonical discovery assets so that shared and indexed pages are understandable. | F1-004 |

## Administrator

| Story ID | User story | Requirement IDs |
|---|---|---|
| US-ADM-001 | As the initial administrator, I want a secure explicit bootstrap and forced initial-password change so that production starts without default credentials. | F2-002, SEC-002–SEC-003 |
| US-ADM-002 | As an administrator, I want secure session login/logout/inspection and password change so that I can control access to the dashboard. | F2-001, SEC-002–SEC-005 |
| US-ADM-003 | As an administrator, I want to manage public profile and site settings so that content/branding changes require no source edits. | F2-003, F2-015 |
| US-ADM-004 | As an administrator, I want full skill/category/order/relationship controls so that the skills presentation stays accurate. | F2-004 |
| US-ADM-005 | As an administrator, I want to manage and publish experiences with enforced date rules so that career history is consistent. | F2-005 |
| US-ADM-006 | As an administrator, I want to manage project content, media, relationships, publication, and SEO so that case studies are complete. | F2-006 |
| US-ADM-007 | As an administrator, I want to draft, safely edit, categorize, relate, and publish posts so that the blog is independently maintainable. | F2-007, F1-012 |
| US-ADM-008 | As an administrator, I want to create/duplicate/preview/publish pages and reorder/configure blocks so that I can build pages without code. | F2-012–F2-013, F1-005–F1-006 |
| US-ADM-009 | As an administrator, I want to configure safe navigation and footer links so that visitors can find published content. | F2-014 |
| US-ADM-010 | As an administrator, I want to upload, describe, search, preview, and safely delete reusable media so that assets remain valid and accessible. | F2-010–F2-011, SEC-007 |
| US-ADM-011 | As an administrator, I want to review, filter, mark, archive, and delete private contact submissions so that inquiries are manageable and confidential. | F2-008–F2-009 |
| US-ADM-012 | As an administrator, I want to issue a named, scoped, expiring token and copy its secret once so that an integration can be authorized safely. | F2-016–F2-017, SEC-008 |
| US-ADM-013 | As an administrator, I want to inspect token use, rotate, and revoke tokens so that integrations can be controlled throughout their lifecycle. | F2-016, SEC-008 |
| US-ADM-014 | As an administrator, I want to inspect safe audit events so that security and content changes are attributable without exposing secrets. | F2-018, SEC-009 |
| US-ADM-015 | As an administrator, I want clear, accessible, mobile-capable management states and warnings so that I can complete essential tasks confidently. | F2-019, NFR-002, NFR-004 |
| US-ADM-016 | As an administrator, I want basic health visibility so that I can distinguish a service problem from a content problem. | F2-020, API-007 |

## API consumer and operator

| Story ID | User story | Requirement IDs |
|---|---|---|
| US-API-001 | As an API consumer, I want a versioned OpenAPI-compatible contract with consistent resources/errors/dates so that I can generate and maintain a client. | API-001–API-003, API-006 |
| US-API-002 | As an API consumer, I want documented pagination, filtering, and sorting so that I can retrieve large collections predictably. | API-004–API-005 |
| US-API-003 | As an API consumer, I want unexpired scoped-token authorization so that my integration receives only intended capabilities. | API-008, F2-017, SEC-008 |
| US-OPS-001 | As an operator, I want separate liveness/readiness checks so that orchestration can detect process and dependency health correctly. | API-007 |

## Contributor, reviewer, and maintainer

| Story ID | User story | Requirement IDs |
|---|---|---|
| US-DEV-001 | As a contributor, I want clear modular boundaries and mandated stack/conventions so that changes remain maintainable. | NFR-007–NFR-012 |
| US-DEV-002 | As a contributor, I want repeatable migrations, containers, local tasks, and environment configuration so that development and deployment are reproducible. | NFR-011–NFR-012 |
| US-DEV-003 | As a reviewer, I want CI, tests, coverage evidence, and non-bypassable quality gates so that regressions are caught. | NFR-013–NFR-016 |
| US-SEC-001 | As a security reviewer, I want explicit ASVS-informed controls and redaction so that release risk is visible and bounded. | SEC-001–SEC-010 |
| US-A11Y-001 | As an accessibility reviewer, I want automated and manual WCAG checks so that scores do not substitute for usable behavior. | NFR-002–NFR-003 |
| US-DOC-001 | As a user/API consumer/contributor, I want complete role-specific documentation so that I can install, operate, integrate, and extend the platform. | DOC-001–DOC-003 |
| US-OSS-001 | As an open-source adopter, I want governance files and a repository free of secrets/private artifacts so that adoption and contribution are safe. | OSS-001–OSS-002 |
| US-MNT-001 | As a maintainer, I want decisions and specification changes recorded with impacts so that product intent remains traceable. | CHG-001–CHG-002 |
| US-AI-001 | As a future AI developer, I want published portfolio data and provider/retrieval boundaries without fake R1 behavior so that real F3/F4 work can be added deliberately. | AI-001–AI-004 |
