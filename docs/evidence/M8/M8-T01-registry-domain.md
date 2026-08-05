# M8-T01 registry and domain evidence

## Record

- Requested milestone: `M8`; trace milestone: `M12`.
- Date: 2026-08-04.
- Executor: Integration/root.
- Repository identity: `8f6a5e1a4c9ffb894260103cb105d43f21d41fca`; the workspace has no tracked baseline, so evidence identifies exact paths and commands rather than claiming a clean Git diff.
- Runtime: Python 3.12.13, Pydantic 2.13.4, uv 0.12.1.

## G0-G2 reconciliation

- The separate M7 decision is accepted in `docs/evidence/M7/README.md`.
- `uv run --frozen alembic -c backend/alembic.ini heads` returned exactly `20260802_0008 (head)`.
- Released application-facing public/reference boundaries exist for profile, skills, experiences, projects, and posts. Page references are page-owned and do not import provider persistence.
- SPEC section 5.2 is authoritative: the catalog contains exactly 19 kinds. Prior references to 20 were transcription errors. No alias or placeholder kind was introduced.
- The M8 exclusion holds: no media storage/resolver, contact submission, token, worker, scheduler, AI behavior, raw renderer selection, CSS, HTML, query, or code field was added.

## Frozen G3 catalog

The canonical `BlockType`, strict Pydantic models, deterministic serializer, reference extractor, renderer keys, groups, versions, and staged-media facts live in `backend/app/modules/pages/registry.py`. The exact canonical names are:

`hero`, `profile_summary`, `call_to_action`, `statistics`, `skills_grid`, `featured_skills`, `experience_summary`, `experience_list`, `project_grid`, `featured_projects`, `latest_posts`, `rich_text`, `image`, `image_with_text`, `links_collection`, `contact_callout`, `testimonial`, `divider`, and `spacer`.

All entries use schema version 1. Renderer keys equal the canonical discriminants. Media is required only for `image` and `image_with_text`, and remains unresolved draft intent until M9. M7 CommonMark parsing is reused by `rich_text`.

Normalized reference kinds are closed to `profile`, `skill`, `experience`, `project`, `post`, `page`, and `media`. Config-derived references are ordered, typed, role-labelled, and never client mass-assigned. Singleton profile blocks use the released singleton projection instead of inventing a target identifier. Custom-page action targets may use a page-owned opaque ID; direct destinations remain restricted to reviewed internal paths or HTTPS.

## Frozen page/domain contract

- Home is a singleton with no slug. Custom slugs normalize to one ASCII lowercase kebab-case segment, reserve the platform/public route catalog, and remain case-insensitively unique including retained soft-deleted identities.
- Page metadata and canonical URLs are bounded and validated.
- Block common fields use closed theme/layout/responsive tokens; type-specific config rejects extra fields.
- Revisions own ordered blocks and derived references. Published revisions and children are immutable; publish uses copy-on-write.
- Lifecycle is derived from pointers and PostgreSQL time; there is no mutable status row or scheduler.
- Add/duplicate/hide/show/delete and complete-list reorder operate only on the mutable draft, require contiguous positions, and preserve independent copies.
- Publish blocks required unavailable references and all M9-staged media. Hidden blocks are omitted before reference resolution.
- Export is a bounded canonical JSON manifest with checksums and no resolved provider/admin/internal payloads.

## Verification

Commands:

```text
uv run --frozen ruff format backend/app/modules/pages backend/tests/unit/test_pages_registry.py backend/tests/unit/test_pages_domain.py
uv run --frozen ruff check backend/app/modules/pages backend/tests/unit/test_pages_registry.py backend/tests/unit/test_pages_domain.py
uv run --frozen pytest backend/tests/unit/test_pages_registry.py backend/tests/unit/test_pages_domain.py -q --no-cov
uv run --frozen mypy backend/app/modules/pages backend/tests/unit/test_pages_registry.py backend/tests/unit/test_pages_domain.py
uv run --frozen alembic -c backend/alembic.ini heads
```

Result after correction: Ruff format/check passed; 33 focused tests passed; strict Mypy passed; Alembic reported one head at `20260802_0008`.

The focused suite covers every catalog fixture, exact count/name/renderer parity, deterministic JSON/checksums, version failure, unknown fields, unsafe URL, raw HTML, CSS/query/renderer injection, prototype-shaped keys, depth/string/Unicode/nonfinite bounds, typed ordered references, duplicate references, Home/custom identity, reserved slugs, common/type config validation, contiguous block ownership/order, immutable revisions, and database-time lifecycle.

## G3 decision and migration reservation

G3 is accepted. It releases page persistence and the sole migration reservation:

```text
file: backend/migrations/versions/20260802_0009_pages_blocks.py
revision: 20260802_0009
down_revision: 20260802_0008
owner: M8-T01-M only
```

Any incompatible registry, provider, lifecycle, schema, or query decision returns to this gate before API/client generation. G3 does not accept M8 or release frontend work.
