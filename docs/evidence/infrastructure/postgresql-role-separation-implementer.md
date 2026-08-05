# PostgreSQL owner/runtime separation - infrastructure implementer record

## Identity

- Scope: infrastructure hardening follow-up for administrator identity/audit persistence
- Requirements: SEC-009, SEC-010, NFR-012, NFR-016
- Candidate state: uncommitted working tree; integration acceptance pending
- Environment: Docker Engine 29.2.1, Compose 5.0.2, PostgreSQL 17.10 on the existing pinned image digest
- Executor/reviewer: Infrastructure Agent / independent review pending
- Completed UTC: 2026-08-02

## Delivery

- Added a bootstrap-only cluster administrator, a non-superuser migration owner, and a non-owner runtime login with validated, distinct identifiers and passwords.
- Added idempotent first-volume and existing-volume role reconciliation. Existing public application objects owned by the bootstrap identity are transferred narrowly to the migration owner; system-owned objects are untouched.
- Changed Alembic to use owner credentials and the backend to use runtime credentials.
- Added explicit post-migration grant reconciliation and a read-only fail-closed backend permission dependency.
- Runtime receives ordinary table CRUD without `TRUNCATE`, `REFERENCES`, or `TRIGGER`; Alembic metadata is read-only; `audit_entry` is insert/select-only. Runtime owns no database, schema, table, sequence, or function and cannot create persistent or temporary objects.
- Startup runs no migration, role repair, administrator bootstrap, or seed. Mutating database operations remain behind the `operations` profile.

## Isolated validation

The proof used the task-owned Compose project `upw-role-proof-019fc34f`, a fresh task-owned PostgreSQL volume, synthetic credentials, and loopback backend port `18080`. No shared database or unrelated container was used.

| Check | Result |
|---|---|
| Compose interpolation and default profile | Pass: operations profile resolves; default services exclude `role-init`, `migrate`, and `permissions`. |
| Fresh-volume initialization | Pass: both least-privilege roles created and database/schema ownership transferred before first shutdown. |
| Idempotent role reconciliation | Pass: repeated before and after migrations; passwords were not present in PostgreSQL logs. |
| Fail-closed pre-migration gate | Pass: runtime check exited nonzero because `alembic_version` was absent. |
| Owner migration | Pass: empty database upgraded linearly through `20260802_0001` to `20260802_0002`. |
| Fail-closed pre-grant gate | Pass: runtime check exited nonzero because current tables had not been reconciled. |
| Post-migration reconciliation | Pass: reconnect-as-runtime verification completed successfully. |
| Runtime role attributes and ownership | Pass: runtime and migration roles are login/no-inherit/non-superuser/no-create-role/no-create-db/no-replication/no-bypass-RLS with no memberships; migration role owns database, schema, and current public objects. |
| Legitimate runtime DML | Pass: transactional insert/update/delete on administrator, session, and rate-limit tables; insert/select on audit. |
| Audit mutation denial | Pass: runtime `UPDATE`, `DELETE`, and `TRUNCATE` all failed. |
| DDL/trigger denial | Pass: trigger disable, persistent table create, temporary table create, and ordinary-table alteration all failed. |
| Migration metadata | Pass: runtime could read but could not update `alembic_version`. |
| Future ordinary owner table | Pass: owner-created table inherited runtime insert/update/delete and denied truncate; owner dropped it. |
| Owner rollback/recovery | Pass: owner downgraded `20260802_0002 -> 20260802_0001 -> base`, upgraded back to head, and reran reconciliation. |
| Backend dependency | Pass: permission check completed first; backend then started healthy using only runtime credentials. |
| Cleanup | Pass: task-owned containers, networks, and volumes removed after validation; unrelated containers preserved. |

No database URLs or password values are recorded here.

## Corrective loop

| Finding | Severity | Correction | Retest |
|---|---|---|---|
| Official PostgreSQL entrypoint sourced the init script, so `$0` did not identify the read-only script directory. | High | Use the fixed `/opt/upw/postgres` mount, with an explicit override seam. | Fresh-volume initialization passed. |
| Broad `REASSIGN OWNED` attempted to transfer bootstrap-owned system-required objects. | High | Transfer only application relations, routines, and standalone types in `public`, then transfer database/schema ownership explicitly. | Fresh-volume init and existing-volume idempotence passed. |
| Initial ordinary-table grant also covered Alembic metadata. | Medium | Revoke it and grant `SELECT` only; add a fail-closed check. | Runtime metadata update denied; readiness read and backend health passed. |

## CI and backend-test handoff

CI was intentionally not edited while backend identity tests were active. The CI owner should add a dedicated, isolated PostgreSQL privilege job with an always-run cleanup step that:

1. supplies three synthetic, distinct role names/passwords and a unique Compose project;
2. validates Compose with and without the `operations` profile;
3. starts the pinned PostgreSQL image, proves the permission gate fails before migration, runs `role-init`, owner migration, and `permissions`, then proves the gate passes;
4. executes runtime allow/deny probes for ordinary CRUD, audit insert/select, audit update/delete/truncate, trigger disable, persistent/temp DDL, and Alembic metadata writes;
5. exercises owner downgrade/upgrade and reruns reconciliation;
6. scans captured output for all synthetic passwords and removes only the job-owned project/volumes in `if: always()`.

Backend PostgreSQL fixtures also need an explicit credential split: owner credentials for destructive migration fixtures and runtime credentials for repository/API tests. Do not point the existing downgrade-to-base fixture at the runtime URL, and never inject bootstrap credentials into backend test/application processes.

## Completion decision

- Infrastructure implementation: complete and locally validated.
- Acceptance: not asserted; integration/root and an independent reviewer own the decision.
- Remaining handoff: CI privilege job and backend owner/runtime fixture split described above.
