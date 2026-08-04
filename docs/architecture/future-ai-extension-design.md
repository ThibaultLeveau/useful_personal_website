# Future AI Extension Design (R1 Boundary Only)

## R1 rule

F3/F4 remain deferred. R1 ships no chat endpoint/UI, generated resume, LLM/embedding/vector dependency, prompt stub, fake response, worker, or AI database table (`AI-004`). It documents publication-safe ports so a later approved scope can add real behavior.

## Boundary

```text
backend/app/ai/
  ports.py                 # future protocols only when F3/F4 begins
  schemas/                 # versioned structured I/O
  providers/               # LLM/embedding adapters
  retrieval/ vectorstores/
  agents/ prompts/ evaluation/ resume/ services/
```

Future implementations depend on interfaces, not vendor SDK types:

- `PublishedContentSource.snapshot(cursor) -> PublishedDocumentPage`;
- `LLMProvider.generate(request) -> StructuredResult`;
- `EmbeddingProvider.embed(texts) -> vectors`;
- `VectorStore.upsert/delete/search`;
- `RetrievalService.retrieve(query, policy) -> citations`;
- `AgentExecutor.run(input, limits) -> structured output`;
- `PromptRegistry.get(name, version)`;
- `AIUsageRecorder`, `AITraceSink`, and evaluation dataset/run repositories.

Provider adapters own authentication, retries, limits, content-policy mapping, and vendor data conversion.

## Publication-safe document source

The source calls a content application facade or `/api/v1/public`-equivalent internal query; it never imports content repositories or ORM tables (`AI-003`). Documents contain stable document ID (`type:id`), revision ID, canonical URL, title, sanitized plain/Markdown text, typed metadata, `published_at`, and source checksum. Allowed types are public profile, skill, experience, project, and post. Private profile fields, contacts, drafts, audit, admin identity, tokens, and storage keys cannot be mapped.

R1 can exercise the ordinary public facade without an AI-specific projection. When a real ingestion requirement is approved, an initial snapshot builds the index and publication events keep it current.

## Future durable events/read model

At AI-scope entry, add a transactional `outbox_event` written with publication transactions:

- `content.published.v1` with type, ID, revision ID, checksum, occurred time;
- `content.unpublished.v1` / `content.deleted.v1` with stable IDs;
- `public_profile.changed.v1`, `skill.visibility_changed.v1`.

Payloads contain identifiers and public-safe metadata, not full private content. An idempotent indexer reads by outbox ID, re-fetches through `PublishedContentSource`, upserts/deletes the vector/read model, and records a checkpoint. At-least-once delivery is assumed; `(event_id, consumer)` is deduplicated. Rebuild always remains possible from the snapshot API, preventing the vector index from becoming authoritative.

The future `published_ai_document` read model may store source/revision/checksum/text/metadata and indexing state. The vector store contains document/chunk IDs and public content only. Unpublish/delete must remove all chunks and caches; retrieval rechecks current publication eligibility before returning citations.

## Security, privacy, quality gates for future scope

Before implementation, CHG-002 requires approved user stories/ACs, threat/privacy model, provider data-retention decision, prompt-injection/data-exfiltration controls, cost/rate limits, abuse policy, human-review rules for resume output, model/provider fallback behavior, and accessibility UX. Generated statements must cite source revisions; structured outputs use versioned Pydantic/JSON Schema and reject invalid provider output.

Observability separates operational traces from user content, redacts prompts where needed, tracks model/prompt versions, tokens/cost/latency, safety outcomes, and consent. Evaluation uses versioned datasets, retrieval relevance, groundedness/citation checks, refusal/safety cases, regression thresholds, and recorded model/prompt versions (`AI-001`, `AI-002`).

## Entry sequence

1. Approve scope/change record and threat/evaluation plan.
2. Implement/test `PublishedContentSource` privacy contract.
3. Add outbox migration and idempotent indexer only if incremental ingestion is needed.
4. Select provider/vector/worker through ADRs based on measured requirements.
5. Implement one vertical slice with structured outputs, citations, limits, audit, evaluations, docs, and rollback/unpublish behavior.
