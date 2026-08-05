# PostgreSQL Role Separation - Integration Acceptance

## Identity

- Scope: infrastructure prerequisite for M1 identity/audit and later capabilities
- Requirements: SEC-009, SEC-010, NFR-012, NFR-016
- Reviewer: Integration/root
- Date: 2026-08-02

## Independent review

The Compose topology, role initialization, grant reconciliation, fail-closed
permission check, environment contract, and operator documentation were reviewed
against ADR-0008 and the M1 audit gate. Compose interpolation passes with three
distinct synthetic roles. Scripts validate identifiers and URL-safe secrets,
use quoted PostgreSQL formatting, do not place passwords in repository evidence,
and keep every mutating database operation behind the `operations` profile.

The isolated implementation proof used a task-owned PostgreSQL 17.10 stack and
demonstrated:

- migration and runtime roles are non-superuser, membership-free, and cannot
  create roles or databases;
- the runtime role owns no database, schema, table, sequence, or function;
- ordinary application CRUD and audit insert/select succeed;
- audit update/delete/truncate, trigger alteration, persistent/temporary DDL,
  ordinary-table alteration, and Alembic writes fail;
- owner downgrade/upgrade and repeated role/grant reconciliation succeed;
- backend startup waits for a read-only permission check and then becomes
  healthy using only runtime credentials;
- all proof resources were removed without touching the unrelated container.

## Decision

The local/production-shaped three-role topology passes integration review. The
repository-wide CI gate remains open until CI runs the same isolated privilege
proof and backend fixtures use separate owner migration and runtime application
URLs. Those are integration handoffs, not waivers of the accepted topology.
