# M12 audit retention and permissions

Date: 2026-08-04

The operator command defaults to a 400-day cutoff computed once from PostgreSQL time, dry-runs by default, requires an exact apply confirmation, and deletes oldest-first through a security-definer function in batches capped at 1,000. It refuses a reused runtime URL, requires a bounded operator identifier, prints aggregate facts only, and appends `audit.retention_executed` without deleted metadata.

Against the disposable PostgreSQL database, dry-run found exactly 2 expired synthetic rows and changed none. Apply with batch size 1 deleted exactly 2. The dedicated synthetic operator could execute the bounded function but a direct table `DELETE` was denied. Container provisioning creates a distinct no-inherit/no-superuser operator; reconciliation grants only database connect, schema use, audit select/insert, and execution of the bounded function, with a dedicated permission verifier.

Production execution remains blocked until the owner approves retention, backup implications, operator identity/secret injection, scheduling/monitoring, and recovery procedure.
