# Backend coverage and test status

## Authoritative result

The final clean run used a freshly recreated PostgreSQL database whose `PUBLIC` database and schema
privileges were revoked before the runtime role received only its required grants.

- 544 tests collected;
- 544 passed;
- 0 failures, errors, or skips;
- 892.347 seconds (14m52s);
- 12,787 of 14,560 statements covered;
- 1,614 of 2,382 branches covered;
- **85.0018% combined branch-aware coverage**;
- frozen required target: **>=85%**.

The gate passes without lowering the threshold or broadening coverage exclusions. The permanent
regression suite now includes complete API-token service authentication/lifecycle branches, contact
submission and retention behavior, administrator error catalogs, media storage failure boundaries,
demo-seed convergence/refusal, and executable typed port contracts.

## Machine-readable reports

- `reports/backend-tests.xml` — JUnit result with exact count, duration, and zero skips;
- `reports/backend-coverage.xml` — Cobertura statement and branch totals.

The reports contain no production credentials. Database URLs used only synthetic local passwords
against the disposable M13 container.
