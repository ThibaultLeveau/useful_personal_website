# Infrastructure

The root [Compose file](../compose.yaml) is the canonical local container topology. It contains PostgreSQL, the FastAPI backend, the Next.js frontend, explicit operations-profile role/migration/permission jobs, and a read-only runtime-permission gate. PostgreSQL and the named local-media volume are private to the stack; only frontend and backend bind loopback ports.

PostgreSQL uses three distinct identities: a bootstrap-only cluster administrator, a non-superuser migration owner, and a non-owner runtime login. Runtime containers never migrate, bootstrap an administrator, or seed content. Operators explicitly reconcile roles, run Alembic with owner credentials, and reconcile runtime grants before starting the applications. The backend uses only runtime credentials and waits for a read-only permission check; that check never repairs permissions or changes schema.

[`postgres/`](postgres/) contains identifier-validating, idempotent role initialization and post-migration grant reconciliation. These scripts never echo passwords. Reconciliation grants ordinary current tables only `SELECT`, `INSERT`, `UPDATE`, and `DELETE`; Alembic metadata receives only `SELECT`, and `audit_entry` receives only `SELECT` and `INSERT`. It also establishes default privileges, so operators rerun reconciliation after every migration to review and narrow any exceptional table.

See the [container runbook](../docs/development/containers.md) for validated commands, configuration boundaries, and cleanup rules.
