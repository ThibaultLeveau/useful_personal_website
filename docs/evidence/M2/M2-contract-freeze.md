# M2 contract freezes C1 and C2

## Freeze identity

- Requested milestone: M2
- Existing trace milestone alias: M05
- Source of truth: executable FastAPI/Pydantic schemas
- Canonical artifact: `docs/api/openapi.json`
- Generator: OpenAPI Generator 7.17.0
- Recorded UTC: 2026-08-03
- Executor/reviewer: Integration/root

## Deterministic proof

Two consecutive exports, validations, and complete generated-client builds produced identical
results:

| Artifact                       | SHA-256                                                            |
| ------------------------------ | ------------------------------------------------------------------ |
| Canonical OpenAPI schema       | `BF565FB9BCE11C829498FB2CB0B9C9AADDC34761C59283AECB16BCC6BFD90619` |
| Complete generated-client tree | `CFCD37845E49460F50D73F2BEDE61D501B4D7AA9CECADEFFC1004E4CD3AD02BD` |

Validation resolved every reference, found 8 unique operations, retained the same-origin server,
and passed strict TypeScript compilation. The generated directory was not hand-edited.

## C1 - Common conventions

C1 freezes the v1 namespace/audiences; envelopes and request IDs; safe error registry; page-number
pagination; allow-listed filter/sort grammar; temporal/identifier naming; actor context and
authorization ports; integer-version preconditions; and digest-only 24-hour idempotency semantics.
M1 authentication schemas and stable error behavior remain compatible.

## C2 - Health and client boundary

C2 freezes process-only liveness, dependency/revision readiness, authenticated aggregate admin
health, their cache/error/security declarations, and the typed generated health operations. The
handwritten consumer remains same-origin and owns safe error translation; generated transport is
not imported directly by feature components.

## Change policy

Additive compatible changes use the same source/export/validate/generate/compile workflow.
Removal, renaming, or semantic break requires deprecation and CHG-002 impact analysis covering
schema, migration, generated client, consumers, tests, documentation, and acceptance evidence.
