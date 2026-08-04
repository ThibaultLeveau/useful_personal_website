# M6 PostgreSQL query-plan evidence

## Dataset and protocol

An isolated PostgreSQL 17.10 database was migrated linearly through `20260802_0007` and populated
with deterministic synthetic plan-only data: 10,000 projects, 20,000 revisions, 60,000 technology
rows, and 9,999 related-project draft edges. Visibility, deletion, featured, and future schedules
were distributed across the set. `ANALYZE` ran before `EXPLAIN (ANALYZE, BUFFERS)`.

| Query shape                      |  Execution | Buffers/result                        | Plan disposition                                  |
| -------------------------------- | ---------: | ------------------------------------- | ------------------------------------------------- |
| Default effective page, limit 24 |  44.716 ms | 900 shared hits; top-N 24             | Bounded broad-select hash join/top-N              |
| Technology filter before fix     | 239.550 ms | 13,535 hits; 60,000 technology rows   | Defect: sequential scan over `lower(value)`       |
| Technology filter after fix      | 114.658 ms | 1,455 hits + 63 reads; 10,000 matches | Bitmap expression-index scan selected             |
| Search `%alpha%`, offset 48      | 109.602 ms | 886 hits; top-N 72                    | Expected bounded text scan; no unbounded page     |
| Exact public slug detail         |   0.124 ms | 6 hits; one row                       | `ix_project_slug_lookup` + revision PK            |
| One ordered related summary      |   0.148 ms | 9 hits; one row                       | relation-order index + project/revision PKs       |
| Bounded draft graph scan         |  89.107 ms | 297 hits; 9,695 edges                 | Explicit cap, advisory serialization, fail-closed |

PostgreSQL reasonably chooses sequential scans for broad eligibility joins at this cardinality;
the collection is bounded by exact pagination and top-N sorting. The selective slug and relation
paths use their indexes. The graph path deliberately reads the bounded graph once rather than
issuing N+1 traversal queries.

The first technology plan exposed a mismatch between the case-insensitive predicate and a
plain-value index. Migration/model `0007` now defines
`ix_project_technology_value_revision ON project_technology (lower(value), revision_id)`. A fresh
migration test asserts the physical `indexdef`, all 12 migration tests pass, and the repeated plan
selects the index with roughly 52% lower execution time.

Repository instrumentation separately caps one public page at seven SELECTs regardless of related
row count: page, count, revisions, technologies, skills, experiences, and related projects.
