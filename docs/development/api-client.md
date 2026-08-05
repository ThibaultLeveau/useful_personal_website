# OpenAPI and Generated Client

FastAPI is the single source of truth for the public contract. Integration/root
alone exports `docs/api/openapi.json` and commits
`frontend/src/generated/api/**`; generated files are never hand-edited.

Run from the repository root with Docker available:

```console
python -m uv run --frozen python scripts/export_openapi.py
python scripts/generate_api_client.py
```

The generator script uses the F0-pinned OpenAPI Generator 7.17.0 OCI digest,
cleans only the exact generated-client directory, exports the schema first, and
removes generator bookkeeping. A clean regeneration must produce no diff.

Application code imports handwritten wrappers from `frontend/src/lib/api`, not
generated modules directly. Wrappers own base URL, credentials, request IDs,
safe error translation, and test seams; generated code owns transport models
and operation signatures.

The M2 wrapper uses relative same-origin paths by default, `credentials:
"same-origin"`, caller-supplied `X-Request-ID`, an injectable `fetch`, and
`cache: "no-store"` for health. Unsafe administrator-session operations obtain
the readable CSRF cookie and send `X-CSRF-Token`; feature components do not
reimplement that transport logic. `ApiError` retains only status, stable code,
safe details, request ID, and optional retry timing. It never exposes a raw
response body, nested transport cause, or credential-bearing header.

`createApiClient()` exposes the public live/ready boundary and authenticated
administrator-health boundary. The health UI consumes only the latter. A 401
must clear privileged feature state through the shared auth context before
navigation; a 403 password-change requirement routes to the forced-change flow.

M3 adds two feature-owned wrappers while preserving this boundary. The administrator
site-configuration wrapper uses relative same-origin paths, cookies, CSRF/Origin, `If-Match`, and
idempotency headers with `cache: "no-store"`. The public wrapper is server-only, uses the validated
internal upstream origin with no credentials, and attaches projection-specific cache tags. Public
Server Components import that wrapper; client editors never import public transport code and no
feature imports generated runtime internals outside its wrapper.

Contract changes require explicit response schemas, stable operation IDs,
security declarations, examples where useful, a regenerated schema and client,
strict TypeScript compilation, wrapper tests, and API review.
