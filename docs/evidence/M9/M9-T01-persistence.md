# M9-T01-R persistence, usage, delete, and reconciliation evidence

Media ORM composition lives under infrastructure and repositories never commit. Assets, immutable variants, and contextual usages use closed database constraints and indexes. Owner usage rebuild verifies every referenced asset is ready in the same transaction. Deletion locks the asset, locks/checks active use, commits `deleting`, and finalizes only after object removal.

Database triggers reject nonready profile/settings/project/blog/page/media-usage references and reject direct tombstoning while an active usage exists. Reconciliation compares registered and observed keys under a stable cutoff, reports missing registered objects, and deletes only reviewed stable orphan/stale-quarantine candidates with explicit confirmation.
