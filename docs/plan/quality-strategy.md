# R1 Quality Strategy

## Quality model

Quality is a completion gate throughout M0-M14, not a final hardening phase (`NFR-016`). Evidence must prove behavior, not merely tool execution. A milestone closes only when the applicable requirement/AC links are current, automated checks pass, rendered behavior has been reviewed where relevant, documentation is updated, and no confirmed Critical/High defect remains.

## Required gates

| Gate | Every task/slice | Milestone close | Release close |
|---|---|---|---|
| Contract | Explicit schemas/errors/security; generated client compiles | OpenAPI regenerates with no diff; API review | Consumer walkthrough; all capabilities represented/rationalized |
| Code | Format, lint, strict types, focused tests | Full affected backend/frontend suites; boundary review | Full repository suites and production builds |
| Data | Migration for schema change; transaction/invariant tests | Empty-DB upgrade and important prior-state upgrade | Clean/upgrade migration plus backup/restore drill |
| Security | Threat consequences, authz/redaction negatives | Scanner + reviewer findings triaged | No confirmed Critical/High; ASVS/API report passes |
| UX/a11y | Required states, keyboard/focus and stories | Browser review at relevant widths/themes | Manual WCAG matrix plus automated evidence |
| Performance | Pagination/index/bundle implications reviewed | Query/bundle checks for changed hot paths | Lighthouse/CWV, query-plan, N+1 and budget report |
| Documentation | User/API/developer impact updated | Traceability and milestone evidence linked | Clean docs-only install/operator/consumer walkthrough |

Target measurements: backend overall coverage >=85%; critical/security backend >=95%; critical frontend forms/utilities >=80%; critical workflows E2E; representative Lighthouse performance >=90, accessibility >=95, SEO >=95, with good CWV. A miss needs measured evidence and explicit disposition; targets do not justify reducing security/accessibility/functionality.

## Review routing

- Code review: correctness, boundaries, transactions, typing, errors, performance, dead/placeholder code.
- Security review: OWASP/ASVS controls, secrets, authn/authz, CSRF/CORS/headers, content/upload safety, privacy/redaction, dependencies.
- API review: coverage, names, envelopes, versioning, pagination/filter/sort, idempotency, schemas/examples, security/scopes, client generation.
- UX/a11y review: actual pages using browser/screenshots, all states, responsive behavior, keyboard/focus, screen reader, zoom, contrast, motion.
- Defect triage: deduplicate, reproduce, assign severity/root cause/AC, reject unsupported findings, route minimal correction.

## Corrective loop

1. Capture reproducible evidence and affected requirement/AC.
2. Classify severity and root cause; assign owner and regression scope.
3. Implement the smallest corrective task without weakening a control/test.
4. Rerun the failed check and all affected gates; record before/after evidence.
5. Update docs/traceability and close only after independent retest.

Maximum five failed correction attempts per root cause. On the fifth, stop that area, document diagnostics/attempts/likely cause/safest next action, and proceed only with independent work. Critical/High security or an R1 Must failure blocks release. Waivers cannot override them without an approved CHG-002 specification change.

## Evidence integrity

Evidence records commit, environment, tool/version, command or manual protocol, date, executor, result, artifact path, and defect/waiver. Never store credentials, tokens, contact content, private data, machine-specific absolute paths, or production dumps in evidence. Screenshots/traces must be sanitized.
