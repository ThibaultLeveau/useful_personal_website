# Audit retention operations

The R1 default retains audit entries for 400 days. This is a deployment-policy default, not jurisdiction-specific legal advice; the owner must approve it before production acceptance.

Retention uses a dedicated PostgreSQL login that can connect, use the schema, select/insert audit rows, and execute only the bounded `purge_audit_entries_before` function. It has no direct `UPDATE`, `DELETE`, `TRUNCATE`, object-creation, migration, or ordinary application-table permissions. Do not inject `APP_AUDIT_RETENTION_DATABASE_URL` into the web application, and never reuse the runtime or migration-owner credential.

Run a dry review first:

```text
python -m app.commands.purge_audit --operator-id <safe-deployment-operator>
```

The output contains only the fixed cutoff, eligible aggregate count, retention days, and a run correlation ID. After reviewing the cutoff and ensuring the coordinated backup policy is current, execute explicitly:

```text
python -m app.commands.purge_audit --operator-id <safe-deployment-operator> --apply --confirm delete-expired-audit-entries
```

Deletion proceeds oldest-first in batches of at most 1,000, uses one database-time cutoff for the run, is safe to retry, and emits one aggregate `audit.retention_executed` event after commit. The command returns non-zero for missing/unsafe configuration, reused runtime credentials, invalid confirmation, or database failure. It never prints deleted event metadata.

External platform scheduling is optional; the application contains no scheduler. Monitor command exit status and aggregate counts without attaching database URLs, operator credentials, or audit payloads. Because deletion is permanent, recovery requires the owner-approved coordinated backup process. M14 owns the independent restore drill.
