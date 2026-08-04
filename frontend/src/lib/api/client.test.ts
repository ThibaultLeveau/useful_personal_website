import { describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient } from ".";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json", ...init.headers },
    ...init,
  });
}

describe("official API client", () => {
  it("uses same-origin cookies, forwards request IDs, and returns generated health types", async () => {
    const fetchApi = vi.fn<typeof fetch>(async (input) =>
      String(input).endsWith("/ready")
        ? jsonResponse({ data: { status: "ready" }, meta: { request_id: "response-ready" } })
        : jsonResponse({ data: { status: "ok" }, meta: { request_id: "response-live" } }),
    );
    const client = createApiClient({ fetch: fetchApi });

    await expect(client.health.live({ requestId: "request-live" })).resolves.toEqual({
      data: { status: "ok" },
      meta: { requestId: "response-live" },
    });
    await expect(client.health.ready()).resolves.toEqual({
      data: { status: "ready" },
      meta: { requestId: "response-ready" },
    });

    expect(fetchApi).toHaveBeenNthCalledWith(
      1,
      "/api/v1/health/live",
      expect.objectContaining({ credentials: "same-origin", method: "GET" }),
    );
    const firstRequest = fetchApi.mock.calls[0];
    expect(firstRequest).toBeDefined();
    const firstHeaders = new Headers(firstRequest?.[1]?.headers);
    expect(firstHeaders.get("accept")).toBe("application/json");
    expect(firstHeaders.get("x-request-id")).toBe("request-live");
  });

  it("translates a documented non-2xx envelope without exposing the response body", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      jsonResponse(
        {
          error: {
            code: "DEPENDENCY_UNAVAILABLE",
            message: "A required dependency is unavailable.",
            details: { dependency: "database", status: "not_ready" },
            request_id: "request-error",
          },
          private_debug_value: "must-not-escape",
        },
        { status: 503, headers: { "retry-after": "20" } },
      ),
    );

    const error = await createApiClient({ fetch: fetchApi })
      .health.ready()
      .catch((value: unknown) => value);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      code: "DEPENDENCY_UNAVAILABLE",
      details: { dependency: "database", status: "not_ready" },
      message: "A required dependency is unavailable.",
      requestId: "request-error",
      retryAfter: "20",
      status: 503,
    });
    expect(JSON.stringify(error)).not.toContain("must-not-escape");
    expect(error).not.toHaveProperty("response");
  });

  it("returns typed private admin health over the same-origin cookie boundary", async () => {
    const checkedAt = "2026-08-03T08:00:00Z";
    const fetchApi = vi.fn<typeof fetch>(async () =>
      jsonResponse({
        data: {
          status: "operational",
          application_status: "operational",
          database_status: "operational",
          migration_status: "current",
          build_version: "1.2.3",
          build_commit: "abcdef1",
          checked_at: checkedAt,
        },
        meta: { request_id: "admin-health-response" },
      }),
    );

    const result = await createApiClient({ fetch: fetchApi }).adminHealth.get({
      requestId: "admin-health-request",
    });

    expect(result.data).toMatchObject({
      status: "operational",
      applicationStatus: "operational",
      databaseStatus: "operational",
      migrationStatus: "current",
      buildVersion: "1.2.3",
      buildCommit: "abcdef1",
      checkedAt: new Date(checkedAt),
    });
    expect(fetchApi).toHaveBeenCalledWith(
      "/api/v1/admin/health",
      expect.objectContaining({ cache: "no-store", credentials: "same-origin", method: "GET" }),
    );
    const headers = new Headers(fetchApi.mock.calls[0]?.[1]?.headers);
    expect(headers.get("x-request-id")).toBe("admin-health-request");
  });

  it("rejects a malformed successful admin health response without exposing it", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      jsonResponse({
        data: {
          status: "internal-database-hostname",
          application_status: "operational",
          database_status: "operational",
          migration_status: "current",
          build_version: "1.2.3",
          build_commit: "abcdef1",
          checked_at: "not-a-date",
        },
        meta: { request_id: "malformed" },
      }),
    );

    const error = await createApiClient({ fetch: fetchApi })
      .adminHealth.get()
      .catch((value: unknown) => value);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "API_INVALID_RESPONSE", status: 0 });
    expect(JSON.stringify(error)).not.toContain("internal-database-hostname");
  });

  it.each([
    {
      name: "non-JSON",
      response: new Response("internal stack and secret", {
        headers: { "content-type": "text/plain", "x-request-id": "header-request" },
        status: 502,
      }),
    },
    {
      name: "malformed JSON envelope",
      response: jsonResponse({ error: { message: "unsafe incomplete payload" } }, { status: 500 }),
    },
  ])("uses a safe fallback for $name errors", async ({ response }) => {
    const fetchApi = vi.fn<typeof fetch>(async () => response);

    const error = await createApiClient({ fetch: fetchApi })
      .health.live()
      .catch((value: unknown) => value);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      code: "API_REQUEST_FAILED",
      details: {},
      message: "The API request could not be completed.",
      status: response.status,
    });
    expect(JSON.stringify(error)).not.toContain("internal stack");
    expect(JSON.stringify(error)).not.toContain("unsafe incomplete payload");
  });

  it("normalizes explicit configuration without ever inventing a generator localhost", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      jsonResponse({ data: { status: "ok" }, meta: { request_id: "configured" } }),
    );

    await createApiClient({
      basePath: "https://api.example.test/root/",
      credentials: "omit",
      fetch: fetchApi,
    }).health.live();

    expect(fetchApi).toHaveBeenCalledWith(
      "https://api.example.test/root/api/v1/health/live",
      expect.objectContaining({ credentials: "omit" }),
    );
    expect(() => createApiClient({ basePath: "//generator.example.test" })).toThrow(
      "protocol-relative",
    );
    expect(() => createApiClient({ basePath: "ftp://generator.example.test" })).toThrow(
      "safe HTTP(S)",
    );
  });
});
