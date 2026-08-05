import { afterEach, describe, expect, it, vi } from "vitest";

import type { ProjectCreateRequest } from "@/generated/api/src/models";

import { createAdminProjectsApi } from "./admin-api";
import { fixtureProject } from "./project-fixtures";

const rawRevision = {
  architecture: fixtureProject.draft.architecture,
  based_on_revision_id: null,
  canonical_url: fixtureProject.draft.canonicalUrl,
  cover_media_id: null,
  created_at: "2026-08-04T08:00:00Z",
  created_by: fixtureProject.draft.createdBy,
  demo_url: fixtureProject.draft.demoUrl,
  end_date: null,
  experience_ids: [],
  frozen: false,
  full_description: fixtureProject.draft.fullDescription,
  id: fixtureProject.draft.id,
  impact: fixtureProject.draft.impact,
  name: fixtureProject.draft.name,
  owner_role: fixtureProject.draft.ownerRole,
  problem: fixtureProject.draft.problem,
  related_project_ids: [],
  repository_url: fixtureProject.draft.repositoryUrl,
  revision_number: 1,
  screenshot_media_ids: [],
  seo_description: fixtureProject.draft.seoDescription,
  seo_title: fixtureProject.draft.seoTitle,
  short_description: fixtureProject.draft.shortDescription,
  skill_ids: [],
  solution: fixtureProject.draft.solution,
  start_date: "2025-01-01",
  status: "active",
  technologies: ["Python", "PostgreSQL"],
  updated_at: "2026-08-04T08:00:00Z",
};
const rawProject = {
  created_at: "2026-08-04T08:00:00Z",
  deleted_at: null,
  draft: rawRevision,
  featured: true,
  id: fixtureProject.id,
  lifecycle: "draft",
  position: 0,
  publish_at: null,
  published: null,
  slug: "api-platform",
  unpublished_at: null,
  updated_at: "2026-08-04T08:00:00Z",
  version: 1,
  visible: true,
};

function response(body: unknown) {
  return new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
}

function input(): ProjectCreateRequest {
  return {
    architecture: fixtureProject.draft.architecture,
    coverMediaId: "0198a12c-6000-7000-8000-000000000010",
    experienceIds: [],
    featured: false,
    fullDescription: fixtureProject.draft.fullDescription,
    impact: fixtureProject.draft.impact,
    name: fixtureProject.draft.name,
    ownerRole: fixtureProject.draft.ownerRole,
    problem: fixtureProject.draft.problem,
    relatedProjectIds: [],
    screenshotMediaIds: ["0198a12c-6000-7000-8000-000000000011"],
    shortDescription: fixtureProject.draft.shortDescription,
    skillIds: [],
    slug: fixtureProject.slug,
    solution: fixtureProject.draft.solution,
    startDate: fixtureProject.draft.startDate,
    status: "active",
    technologies: fixtureProject.draft.technologies,
    visible: true,
  };
}

afterEach(() => vi.restoreAllMocks());

describe("administrator projects API", () => {
  it("uses generated project filters and private no-store reads", async () => {
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({
        data: [rawProject],
        meta: {
          pagination: {
            has_next: false,
            has_previous: false,
            page: 1,
            page_size: 50,
            total_items: 1,
            total_pages: 1,
          },
          request_id: "list",
        },
      }),
    );
    const result = await createAdminProjectsApi(fetchApi).list({
      lifecycle: "draft",
      search: "platform",
    });
    expect(result.items[0]?.draft.name).toBe("API Platform");
    expect(String(fetchApi.mock.calls[0]?.[0])).toContain("lifecycle=draft");
    expect(String(fetchApi.mock.calls[0]?.[0])).toContain("search=platform");
    expect(fetchApi.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ cache: "no-store", method: "GET" }),
    );
  });

  it("sends only generated input with CSRF, Origin, and idempotency controls", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Etoken");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "01989abc-def0-7000-8000-000000000599",
    );
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({ data: rawProject, meta: { request_id: "create" } }),
    );

    await createAdminProjectsApi(fetchApi).create(input());

    const [, init] = fetchApi.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("x-csrf-token")).toBe("signed.token");
    expect(headers.get("origin")).toBe(window.location.origin);
    expect(headers.get("idempotency-key")).toHaveLength(36);
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    expect(body).toMatchObject({
      slug: "api-platform",
      start_date: "2025-01-01",
    });
    expect(body).toMatchObject({
      cover_media_id: "0198a12c-6000-7000-8000-000000000010",
      screenshot_media_ids: ["0198a12c-6000-7000-8000-000000000011"],
    });
    expect(String(init?.body)).not.toContain("version");
  });

  it("uses exact ETag preconditions and UTC publication JSON", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=token");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "01989abc-def0-7000-8000-000000000598",
    );
    const fetchApi = vi.fn<typeof fetch>(async () =>
      response({ data: rawProject, meta: { request_id: "publish" } }),
    );
    await createAdminProjectsApi(fetchApi).publish(
      fixtureProject,
      new Date("2026-08-04T10:00:00.000Z"),
    );
    const [, init] = fetchApi.mock.calls[0] ?? [];
    const headers = new Headers(init?.headers);
    expect(headers.get("if-match")).toBe('"v1"');
    expect(JSON.parse(String(init?.body))).toEqual({
      publish_at: "2026-08-04T10:00:00.000Z",
    });
  });
});
