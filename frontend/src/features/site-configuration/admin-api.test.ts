import { afterEach, describe, expect, it, vi } from "vitest";

import { ContactPreference, PublicProfileField } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { createAdminSiteApi } from "./admin-api";

function profileEnvelope(fullName = "Avery Example") {
  return {
    data: {
      contact_preference: "none",
      created_at: "2026-08-03T08:00:00Z",
      full_name: fullName,
      id: "01989abc-def0-7000-8000-000000000301",
      public_fields: ["full_name"],
      updated_at: "2026-08-03T08:00:00Z",
      version: 4,
    },
    meta: { request_id: "request-profile" },
  };
}

function jsonResponse(body: unknown, etag = '"v4"') {
  return new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json", etag },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("administrator site configuration API", () => {
  it("reads a versioned resource without caching or exposing browser credentials explicitly", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () => jsonResponse(profileEnvelope()));

    const result = await createAdminSiteApi(fetchApi).getProfile();

    expect(result.etag).toBe('"v4"');
    expect(result.data.fullName).toBe("Avery Example");
    expect(fetchApi).toHaveBeenCalledOnce();
    const [url, init] = fetchApi.mock.calls[0] ?? [];
    expect(url).toBe("/api/v1/admin/profile");
    expect(init).toEqual(expect.objectContaining({ cache: "no-store", method: "GET" }));
  });

  it("sends CSRF, Origin, and optimistic concurrency headers through the generated client", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Etoken");
    const fetchApi = vi.fn<typeof fetch>(async () => jsonResponse(profileEnvelope("Updated")));

    await createAdminSiteApi(fetchApi).updateProfile(
      {
        contactPreference: ContactPreference.None,
        fullName: "Updated",
        publicFields: new Set([PublicProfileField.FullName]),
      },
      '"v3"',
    );

    const [url, init] = fetchApi.mock.calls[0] ?? [];
    expect(url).toBe("/api/v1/admin/profile");
    expect(init).toEqual(expect.objectContaining({ cache: "no-store", method: "PUT" }));
    const headers = new Headers(init?.headers);
    expect(headers.get("if-match")).toBe('"v3"');
    expect(headers.get("origin")).toBe(window.location.origin);
    expect(headers.get("x-csrf-token")).toBe("signed.token");
    expect(JSON.parse(String(init?.body))).toEqual(
      expect.objectContaining({ full_name: "Updated", public_fields: ["full_name"] }),
    );
  });

  it("fails before an unsafe request when the signed CSRF cookie is absent", async () => {
    const fetchApi = vi.fn<typeof fetch>();

    const error = await createAdminSiteApi(fetchApi)
      .updateProfile({ fullName: "Never sent" }, '"v1"')
      .catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "CSRF_MISSING", status: 401 });
    expect(fetchApi).not.toHaveBeenCalled();
  });

  it("rejects a response that omits a valid ETag", async () => {
    const fetchApi = vi.fn<typeof fetch>(
      async () =>
        new Response(JSON.stringify(profileEnvelope()), {
          headers: { "content-type": "application/json" },
        }),
    );

    await expect(createAdminSiteApi(fetchApi).getProfile()).rejects.toMatchObject({
      code: "API_INVALID_RESPONSE",
    });
  });
});
