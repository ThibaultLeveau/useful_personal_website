# M14 isolated database and media restore drill

Date: 2026-08-04
Disposition: **Technical restore pass; production objectives/ownership unresolved**

## Procedure

1. Started a fresh digest-pinned PostgreSQL 17 container and empty source database.
2. Applied the complete Alembic chain from base through `20260802_0013`.
3. Ran the explicit fictional demo seed; it changed five aggregates.
4. Produced a custom-format `pg_dump` and restored it with `--exit-on-error` into a new database.
5. Archived and restored a representative managed-media binary.
6. Compared migration revision, database aggregate counts, and media SHA-256 values.
7. Reconciled least-privilege runtime grants and started the current backend/frontend production
   images against the restored database.

## Results

- database backup SHA-256:
  `e82a0beaab4ae24fb66a053b713595206d380443ca1cc6760961f7d1e1493f77`;
- media source/restored SHA-256:
  `4c40649ba6a63794021ed81e4a58cf70b4792eefbf233657e82a37d795a2093d`;
- source/restored migration head: `20260802_0013` / `20260802_0013`;
- source/restored counts:
  profile 1, settings 1, navigation items 3, footer items 2, skill categories 2, skills 5,
  audit entries 1;
- restored production backend liveness/readiness: HTTP 200/200;
- restored production frontend representative routes: 6/6 HTTP 200.

The drill proves local restore consistency and startup compatibility. It does not select a
production backup provider, schedule, retention, encryption key owner, RPO, RTO, or incident owner;
those remain explicit maintainer/operator decisions.
