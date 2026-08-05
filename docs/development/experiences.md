# Experience slice architecture

The experience feature is a complete modular-monolith slice. Domain and application code lives in
`backend/app/modules/experiences`; SQLAlchemy adapters live in
`backend/app/infrastructure/database/experiences_uow.py`; transport adapters live in the dedicated
admin/public API modules. Frontend admin and public code lives under
`frontend/src/features/experiences` and consumes the generated OpenAPI client.

## Invariants and persistence

`experience` is the stable aggregate. `experience_revision` and its ordered responsibility,
achievement, technology, and skill rows own the content. The aggregate points to one mutable draft
and optionally one frozen published revision. Same-aggregate deferrable foreign keys protect the
pointers, and PostgreSQL triggers reject updates/deletes to a frozen revision or its owned rows.

Publishing performs copy-on-write in one unit of work. Repositories flush but never commit; the
application service owns the transaction, authorization, optimistic concurrency, idempotency, and
controlled audit facts. The skills dependency is the application-facing `SkillReferenceFacade`;
experience code never imports skills ORM or repository types.

Scheduled effectiveness is a query predicate using PostgreSQL `now()`. Do not add a worker that
mutates lifecycle status. Public reads join only the frozen published pointer and finish chronology
with the opaque aggregate ID for deterministic order. Related rows are loaded in bounded batches;
the repository regression test caps a public page at seven SELECT statements.

## Schema and contract changes

The sole migration is `backend/migrations/versions/20260802_0006_experiences.py`, directly after
`20260802_0005`. Any future schema change needs a new linear revision; never edit an applied
migration. Run empty and prior-head upgrade tests, model/schema comparison, constraint/index,
frozen-row, downgrade, and role-isolation tests.

Pydantic schemas are executable API source. After an intentional contract change, export
`docs/api/openapi.json`, run `scripts/validate_openapi.py`, regenerate
`frontend/src/generated/api`, regenerate a second time, and require no diff. Handwritten frontend
code must use the generated boundary instead of raw response casts or database access.

## Validation

Run the canonical repository gates from [Testing](testing.md). The focused files are:

- backend domain/service: `backend/tests/unit/test_experiences_domain.py` and
  `backend/tests/unit/test_experiences_service.py`;
- PostgreSQL adapter and migration: `backend/tests/database/test_experiences_repository.py` and
  `backend/tests/migrations/test_0006_experiences.py`;
- API: `backend/tests/integration/test_experiences_api.py`;
- frontend components: tests beside `frontend/src/features/experiences`;
- vertical browser flow: `frontend/tests/e2e/experiences.spec.ts`.

Use a fresh database and create test-owned fixtures through APIs/factories. Do not make application
startup migrate, seed demo data, bootstrap an administrator, or run a scheduler. Evidence and the
accepted behavior boundary are indexed in [M5 acceptance](../evidence/M5/README.md).
