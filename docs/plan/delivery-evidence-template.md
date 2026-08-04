# Delivery Evidence Template

Copy this record to `docs/evidence/<requested-milestone>/<task-id>.md`. Evidence uses repository-relative links and records both milestone schemes.

```markdown
# <Task ID> - <title>

## Identity
- Requested milestone: M<0-14>
- Existing trace milestone alias(es): M<01-20>
- Requirement IDs:
- Acceptance IDs:
- Build/commit:
- Branch/PR:
- Environment/image digests:
- Executor/reviewer:
- Started/completed UTC:

## Delivery
- Goal and outcome:
- Files/modules changed:
- Migration revision/data action (or N/A):
- OpenAPI/client change and regeneration result (or N/A):
- Security/privacy consequences:
- Accessibility/UX consequences:
- Documentation changed:

## Validation
| Category | Command/protocol + tool version | Result | Repository-relative artifact |
|---|---|---|---|
| Backend format/lint/type | | | |
| Backend unit/service/repository/API | | | |
| Migration/empty DB/upgrade | | | |
| OpenAPI/generator diff | | | |
| Frontend format/lint/type/build | | | |
| Frontend unit/component/Storybook/a11y | | | |
| E2E/integration | | | |
| Security/privacy | | | |
| Manual UX/a11y/browser | | | |
| Performance/coverage | | | |
| Documentation/link walkthrough | | | |

## Acceptance record
| AC ID | Status (Not run/Pass/Fail/Waived) | Evidence | Defect/waiver |
|---|---|---|---|
| | | | |

## Findings and corrective loop
| Finding | Severity | Reproduction | Root cause | Attempt # | Correction | Retest |
|---|---|---|---|---:|---|---|
| | | | | | | |

## Completion decision
- Gate: Pass / Fail / Blocked
- Remaining risks/targets and disposition:
- Traceability matrix rows updated:
- Independent reviewer sign-off:
```

Do not attach raw secrets, auth headers, cookies, token reveal screens, contact content/email, private data, absolute local paths, or production dumps. Sanitize browser traces, screenshots, logs, database samples, and API transcripts before committing.
