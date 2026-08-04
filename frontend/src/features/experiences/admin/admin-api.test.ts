import { afterEach, describe, expect, it, vi } from "vitest";

import type { ExperienceCreateRequest } from "@/generated/api/src/models";

import { createAdminExperiencesApi } from "./admin-api";

const id = "01989abc-def0-7000-8000-000000000501";
const revision = {
  achievements: ["Shipped safely"],
  based_on_revision_id: null,
  company_name: "Example Studio",
  company_url: "https://example.test",
  created_at: "2026-08-03T08:00:00Z",
  created_by: "01989abc-def0-7000-8000-000000000001",
  current_position: true,
  detailed_description: "Platform work.",
  employment_type: "full_time",
  end_date: null,
  frozen: false,
  id: "01989abc-def0-7000-8000-000000000511",
  location: "Paris",
  remote_status: "hybrid",
  responsibilities: ["Led delivery"],
  revision_number: 1,
  role_title: "Staff Engineer",
  short_summary: "Led the platform team.",
  skill_ids: [],
  start_date: "2024-01-01",
  technologies: ["Python"],
  updated_at: "2026-08-03T08:00:00Z",
};
const experience = {
  created_at: "2026-08-03T08:00:00Z",
  deleted_at: null,
  draft: revision,
  id,
  lifecycle: "draft",
  position: 0,
  publish_at: null,
  published: null,
  unpublished_at: null,
  updated_at: "2026-08-03T08:00:00Z",
  version: 1,
  visible: true,
};

function response(body: unknown) {
  return new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
}

function input(): ExperienceCreateRequest {
  return {
    companyName: "Example Studio",
    currentPosition: true,
    employmentType: "full_time",
    remoteStatus: "hybrid",
    roleTitle: "Staff Engineer",
    shortSummary: "Led the platform team.",
    startDate: new Date("2024-01-01T00:00:00.000Z"),
    visible: true,
  };
}

afterEach(() => vi.restoreAllMocks());

describe("administrator experiences API", () => {
  it("uses generated query parameters and private no-store reads", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({
        data: [experience],
        meta: {
          pagination: {
            has_next: false,
            has_previous: false,
            page: 1,
            page_size: 20,
            total_items: 1,
            total_pages: 1,
          },
          request_id: "list",
        },
      }),
    );
    const result = await createAdminExperiencesApi(fetchApi).list({ lifecycle: "draft" });
    expect(result.items[0]?.draft.companyName).toBe("Example Studio");
    expect(String(fetchApi.mock.calls[0]?.[0])).toContain("lifecycle=draft");
    expect(fetchApi.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ cache: "no-store", method: "GET" }),
    );
  });

  it("sends CSRF, Origin, idempotency, and generated calendar-date JSON", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Etoken");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "01989abc-def0-7000-8000-000000000599",
    );
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({ data: experience, meta: { request_id: "create" } }),
    );

    await createAdminExperiencesApi(fetchApi).create(input());

    const [, init] = fetchApi.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("x-csrf-token")).toBe("signed.token");
    expect(headers.get("origin")).toBe(window.location.origin);
    expect(headers.get("idempotency-key")).toHaveLength(36);
    expect(JSON.parse(String(init?.body))).toMatchObject({ start_date: "2024-01-01" });
  });

  it("sends exact version preconditions for publication", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=token");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "01989abc-def0-7000-8000-000000000598",
    );
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({ data: experience, meta: { request_id: "publish" } }),
    );
    const api = createAdminExperiencesApi(fetchApi);
    const item = await api.create(input());
    await api.publish(item, new Date("2026-08-04T10:00:00.000Z"));
    const [, init] = fetchApi.mock.calls[1] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("if-match")).toBe('"v1"');
    expect(JSON.parse(String(init?.body))).toEqual({ publish_at: "2026-08-04T10:00:00.000Z" });
  });
});
