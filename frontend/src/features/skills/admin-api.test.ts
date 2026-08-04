import { afterEach, describe, expect, it, vi } from "vitest";

import { createAdminSkillsApi } from "./admin-api";

const category = {
  created_at: "2026-08-03T08:00:00Z",
  id: "01989abc-def0-7000-8000-000000000401",
  name: "Backend",
  position: 0,
  slug: "backend",
  updated_at: "2026-08-03T08:00:00Z",
  version: 1,
};
const skill = {
  category_id: category.id,
  created_at: "2026-08-03T08:00:00Z",
  description: null,
  featured: true,
  icon_key: null,
  id: "01989abc-def0-7000-8000-000000000402",
  name: "Python",
  position: 0,
  proficiency_label: "Advanced",
  proficiency_score: 90,
  relation_provider: "unavailable",
  slug: "python",
  updated_at: "2026-08-03T08:00:00Z",
  version: 1,
  visible: true,
  years_experience: "6.50",
};

function response(body: unknown) {
  return new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
}

afterEach(() => vi.restoreAllMocks());

describe("administrator skills API", () => {
  it("loads categories and skills through generated query parameters without caching", async () => {
    const fetchApi = vi.fn<typeof fetch>(async (input) =>
      String(input).includes("skill-categories")
        ? response({ data: { items: [category] }, meta: { request_id: "categories" } })
        : response({
            data: [skill],
            meta: {
              pagination: {
                has_next: false,
                has_previous: false,
                page: 1,
                page_size: 100,
                total_items: 1,
                total_pages: 1,
              },
              request_id: "skills",
            },
          }),
    );

    const result = await createAdminSkillsApi(fetchApi).load({ featured: true });

    expect(result.categories[0]?.name).toBe("Backend");
    expect(result.skills[0]?.yearsExperience).toBe("6.50");
    expect(fetchApi).toHaveBeenCalledTimes(2);
    const skillCall = fetchApi.mock.calls.find(([url]) => String(url).includes("/admin/skills?"));
    expect(String(skillCall?.[0])).toContain("featured=true");
    expect(skillCall?.[1]).toEqual(expect.objectContaining({ cache: "no-store", method: "GET" }));
  });

  it("sends CSRF, Origin, idempotency, and exact decimal JSON on create", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Etoken");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "01989abc-def0-7000-8000-000000000499",
    );
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({ data: skill, meta: { request_id: "create-skill" } }),
    );

    await createAdminSkillsApi(fetchApi).createSkill({
      categoryId: category.id,
      name: "Python",
      slug: "python",
      yearsExperience: "6.50",
    });

    const [, init] = fetchApi.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("x-csrf-token")).toBe("signed.token");
    expect(headers.get("origin")).toBe(window.location.origin);
    expect(headers.get("idempotency-key")).toHaveLength(36);
    expect(JSON.parse(String(init?.body))).toMatchObject({ years_experience: "6.50" });
  });
});
