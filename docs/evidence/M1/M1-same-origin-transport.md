# M1 - Same-origin API transport integration

## Identity

- Requested milestone: M1
- Existing trace milestone alias(es): M02 authentication foundation
- Requirement IDs: SEC-004, SEC-005, SEC-010, NFR-012, NFR-014
- Acceptance IDs: AC-016, AC-017, AC-039
- Build/commit: uncommitted integration working tree
- Executor/reviewer: Integration/root; real-browser review completed under M1-T03
- Completed UTC: 2026-08-03

## Delivery

- Goal and outcome: browser calls remain relative `/api/v1` requests on the public origin. The Next.js 16 fallback proxy rewrites only that versioned boundary to a validated server-only backend origin for local/container operation.
- Files/modules changed: `frontend/src/proxy.ts`, its focused test, local Compose injection, environment example, and configuration/container documentation.
- Security/privacy consequences: the upstream value is never browser-visible, contains no secret, and is restricted to an exact HTTP(S) origin without credentials, path, query, fragment, wildcard, whitespace, or controls. Production refuses a missing value. The proxy adds no authorization and does not copy request headers into a client response.
- Deployment consequence: Compose supplies `http://backend:8000`. A standalone non-production Next.js process may use `http://127.0.0.1:8000`. The preferred production TLS edge continues to route `/api/v1` before Next.js.

## Validation

| Category                       | Command/protocol                                                                                                                              | Result                                                                                                               | Repository-relative artifact      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| Matcher and rewrite unit tests | `vitest run src/proxy.test.ts`                                                                                                                | Pass: 13 tests; exact matcher, path/query rewrite, development fallback, production refusal, and adversarial origins | `frontend/src/proxy.test.ts`      |
| Frontend format/lint/type      | Prettier 3.9.6, ESLint 9.39.5 with zero warnings, TypeScript 5.9.3                                                                            | Pass                                                                                                                 | `frontend/src/proxy.ts`           |
| Compose expansion              | default and operations `docker compose config --quiet` with distinct synthetic roles                                                          | Pass                                                                                                                 | `compose.yaml`                    |
| Production build               | Node.js 22.23.2; pnpm 11.18.0; Next.js 16.2.12                                                                                                | Pass: all static-generation units and one Proxy boundary                                                             | `frontend/`                       |
| Real browser/API               | explicit bootstrap, login, forced rotation, session refresh, missing/forged CSRF, logout, back/reload through the relative `/api/v1` boundary | Pass: 8 Playwright tests at 320/1440 plus manual forced-change proof                                                 | `frontend/tests/e2e/auth.spec.ts` |

## Completion decision

- Static integration gate: Pass.
- Real same-origin cookie/Origin/CSRF/Set-Cookie proof: Pass under M1-T03.
- Production topology: final hostname/TLS edge and trusted origins remain operator-owned release inputs; no insecure default is introduced.
