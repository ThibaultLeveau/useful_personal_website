# Operate media storage

Development selects `APP_MEDIA_STORAGE_KIND=local` and mounts the dedicated `local-media` volume at the
absolute `APP_MEDIA_LOCAL_ROOT`. A deliberate single-host production deployment may select the same
private adapter only with `APP_MEDIA_LOCAL_PRODUCTION_ACKNOWLEDGED=true`. The one-shot initializer
assigns the non-root backend user least access. Do not point this root at the repository, a home
directory, or a shared host path.

Production must explicitly record provider/service ownership and coordinated database/media RPO/RTO.
S3 deployments additionally record region/residency, private bucket/prefix, identity, encryption,
versioning/lifecycle, delivery, and monitoring. Local production records its single-host limitation,
persistent-volume ownership, capacity monitoring, backup mechanism, and migration trigger. Startup
fails closed unless local production is explicitly acknowledged or the selected S3 configuration is
complete. The remaining owner-specific decisions are tracked in
[M9 preflight](../evidence/M9/M9-preflight.md); adapter validation is not production acceptance.

Run reconciliation first in dry-run mode:

```console
docker compose --profile operations run --rm backend \
  python -m app.commands.reconcile_media
```

Review stable-cutoff missing, orphan, stale-quarantine, and incomplete-delete counts. Apply only with the
command's explicit confirmation option after preserving the report and confirming the namespace. Never delete
an uncertain object solely because it appeared in one eventually consistent listing.

A recovery set always contains PostgreSQL plus the corresponding private object/volume snapshot. Record one
cutoff, capture both sides, preserve object versions/checksums, and restore into an isolated environment. Before
serving traffic: migrate to the expected head, run dry-run reconciliation, verify ready asset and variant
checksums/counts, verify usage pointers, sample authenticated preview and eligible public delivery, and stop
safely on missing/corrupt/orphan drift. Database-only or object-only recovery is incomplete.

Alerts should cover storage permission/capacity, upload rejection/failure rate, checksum or promotion failure,
missing registered objects, reconciliation drift, and repeated delete cleanup failures. Logs and evidence may
contain request IDs, safe aggregate counts, and opaque asset IDs; they must not contain credentials, bucket or
object keys, signed URLs, raw EXIF, private filenames, or image bodies.
