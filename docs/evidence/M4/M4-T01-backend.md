# M4-T01 backend - Skills domain, API, and persistence

## Outcome

Pass. M4 adds category/skill CRUD, deterministic ordering, feature/visibility controls, exact
numeric validation, public projections, bounded filters/sorts, audit/idempotency/concurrency
behavior, and a future-consumer reference facade. No fake project/experience relation storage or
runtime AI behavior was introduced.

## Validation

| Category               | Result                                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ruff / strict Mypy     | Pass; 123 files formatted and 115 source files type-checked                                                                                            |
| Backend tests          | 187 passed; 85.11% total branch-aware coverage                                                                                                         |
| Focused PostgreSQL API | Pass; CRUD, privacy, filters, reassignment, order, ETags, replay/mismatch, audit, mass assignment, slug conflict, relation refusal                     |
| Migration              | Empty/prior upgrades and downgrade pass; one linear head `20260802_0005`; runtime grants pass                                                          |
| OpenAPI                | 22 paths / 32 operations; seven skills path templates; validation passes                                                                               |
| Generated client       | Two complete generations have identical aggregate SHA-256 `c2a1bf76b8929fe778b54af609bab73faf2ee187725cf334731aac938d44ffcf`; strict TypeScript passes |
| Seed                   | First explicit run `changed=5`, immediate second run `changed=0`; 2 categories, 5 skills, 4 public, 1 hidden; no credential/private relation content   |
| Query review           | Public path uses three bounded statements; demo plan 0.605 ms / eight shared hits; all intended indexes present                                        |

The sole migration is `backend/migrations/versions/20260802_0005_skills.py`, directly down from
`0004`. Database constraints independently reject invalid ranges, formats, duplicate slugs, invalid
positions, and orphan categories. Runtime ownership/DDL/temporary-table denial remains enforced by
the common permission gate.

## Security and privacy findings

- Anonymous callers receive only visible fields with public category context; hidden skills and
  empty categories are absent.
- Administrator routes require full sessions; unsafe methods enforce exact Origin and CSRF.
- Unknown filter syntax, unsafe mass-assignment fields, stale writes, incomplete orders, duplicate
  slugs, missing references, and relation-provider absence fail safely.
- Uniqueness mapping uses structured driver diagnostics; errors do not expose SQL, credentials, or
  raw database text.
- The future facade preserves module boundaries and exposes no repository or ORM object.
