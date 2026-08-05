# Operations readiness review

Implemented operational foundations include health/live and health/ready endpoints, authenticated
safe health detail, structured request logging with correlation IDs, linear Alembic migrations,
three-role PostgreSQL separation, bounded contact retention, operator-only bounded audit retention,
local/S3 media adapters, media reconciliation, immutable image builds, explicit environment
validation, and deployment topology ADRs.

M13 repaired the runtime revision expectation from M9 `0010` to the current linear head `0013`.
Clean upgrade, autogenerate parity, readiness, downgrade, and prior-revision upgrade tests pass in
the focused suite.

The M14 isolated database/media restore drill passed, including restored-data startup through the
current production images. Exact Python 3.12.13 and Node 22.23.2 image runtimes were qualified, and
Gitleaks plus Trivy found zero release-blocking findings.

Release operations remain blocked on the owner decisions in `owner-decisions.md`: selected backup
RPO/RTO and restore ownership, the production object-storage provider and controls, and external
TLS/proxy verification against the final hostname. The local drill is technical evidence, not a
substitute for owner acceptance of production recovery objectives.
