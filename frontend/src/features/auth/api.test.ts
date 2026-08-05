import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

import { createAuthApi } from "./api";

function sessionEnvelope(overrides: Record<string, unknown> = {}) {
  return {
    data: {
      absolute_expires_at: "2026-08-03T08:00:00Z",
      administrator_id: "01989abc-def0-7000-8000-000000000001",
      display_name: "Site Owner",
      idle_expires_at: "2026-08-02T20:30:00Z",
      must_change_password: false,
      ...overrides,
    },
    meta: { request_id: "request-auth" },
  };
}

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json", ...init.headers },
    ...init,
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("auth API boundary", () => {
  it("uses the generated login operation with same-origin cookies and no-store", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () => jsonResponse(sessionEnvelope()));
    const api = createAuthApi({ fetch: fetchApi });

    await expect(api.login({ email: "owner@example.test", password: "private" })).resolves.toEqual(
      expect.objectContaining({ displayName: "Site Owner", mustChangePassword: false }),
    );

    expect(fetchApi).toHaveBeenCalledOnce();
    const [url, init] = fetchApi.mock.calls[0] ?? [];
    expect(url).toBe("/api/v1/auth/login");
    expect(init).toEqual(
      expect.objectContaining({ cache: "no-store", credentials: "same-origin", method: "POST" }),
    );
    const headers = new Headers(init?.headers);
    expect(headers.get("origin")).toBe(window.location.origin);
    expect(headers.get("x-csrf-token")).toBeNull();
    expect(String(init?.body)).toContain('"email":"owner@example.test"');
  });

  it("reads the signed double-submit value only from the CSRF cookie", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Evalue");
    const fetchApi = vi.fn<typeof fetch>(async (input) =>
      String(input).endsWith("/logout")
        ? jsonResponse({ data: { status: "logged_out" }, meta: { request_id: "logout" } })
        : jsonResponse(sessionEnvelope()),
    );
    const api = createAuthApi({ fetch: fetchApi });

    await api.changePassword({ currentPassword: "current", newPassword: "replacement" });
    await api.refreshSession();
    await api.logout();

    for (const call of fetchApi.mock.calls) {
      const headers = new Headers(call[1]?.headers);
      expect(headers.get("x-csrf-token")).toBe("signed.value");
      expect(headers.get("origin")).toBe(window.location.origin);
      expect(call[1]?.credentials).toBe("same-origin");
    }
  });

  it("fails safely before an unsafe request when the CSRF cookie is absent", async () => {
    const fetchApi = vi.fn<typeof fetch>();
    const error = await createAuthApi({ fetch: fetchApi })
      .logout()
      .catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "CSRF_MISSING", status: 401 });
    expect(fetchApi).not.toHaveBeenCalled();
  });

  it("rejects invalid generated session data instead of exposing it", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      jsonResponse(sessionEnvelope({ idle_expires_at: "not-a-date" })),
    );
    const error = await createAuthApi({ fetch: fetchApi })
      .getSession()
      .catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "API_INVALID_RESPONSE" });
    expect(JSON.stringify(error)).not.toContain("administrator_id");
  });
});
