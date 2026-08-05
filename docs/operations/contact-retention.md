# Contact retention

Contact submissions use a 365-day default retention window. Preview eligible rows without changing data:

```shell
python -m app.commands.purge_contacts
```

After reviewing the aggregate count and confirming a recoverable database backup exists, apply bounded batches:

```shell
python -m app.commands.purge_contacts --apply --batch-size 100
```

Restore drills must restore the database to an isolated environment, run migrations to the recorded revision, verify private inbox counts through an authenticated session, and destroy the isolated copy under the operator’s data-handling procedure. The command reports only cutoff and aggregate counts.
