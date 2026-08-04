import { afterEach, describe, expect, it, vi } from "vitest";

import type { PageData } from "@/generated/api/src/models";
import { createAdminPagesApi } from "./admin-api";
import { newBlock } from "./block-catalog";

const rawPage = {
  created_at: "2026-08-04T10:00:00Z",
  deleted_at: null,
  draft: {
    based_on_revision_id: null,
    blocks: [],
    canonical_url: null,
    created_at: "2026-08-04T10:00:00Z",
    description: "A page.",
    frozen: false,
    id: "019fcc45-8817-7ea4-b15e-141719efcd07",
    revision_number: 1,
    seo_description: null,
    seo_title: null,
    title: "Home",
    updated_at: "2026-08-04T10:00:00Z",
  },
  id: "019fcc45-8817-7ea4-b15e-141719efcd06",
  lifecycle: "draft",
  navigation_visible: false,
  position: 0,
  publish_at: null,
  published: null,
  route_kind: "home",
  slug: null,
  unpublished_at: null,
  updated_at: "2026-08-04T10:00:00Z",
  version: 1,
  visible: true,
};

const page = {
  id: rawPage.id,
  version: 1,
} as PageData;

afterEach(() => vi.restoreAllMocks());

describe("administrator pages API", () => {
  it("serializes strict discriminated blocks without a camel-case wire duplicate", async () => {
    vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-admin_csrf=signed%2Etoken");
    vi.spyOn(globalThis.crypto, "randomUUID").mockReturnValue(
      "019fcc45-8817-7ea4-b15e-141719efcd08",
    );
    const fetchApi = vi.fn<typeof fetch>(
      async () =>
        new Response(JSON.stringify({ data: rawPage, meta: { request_id: "add-block" } }), {
          headers: { "content-type": "application/json" },
          status: 201,
        }),
    );

    await createAdminPagesApi(fetchApi).addBlock(page, newBlock("hero"));

    const [, init] = fetchApi.mock.calls[0] ?? [];
    const body = JSON.parse(String(init?.body)) as { block: Record<string, unknown> };
    expect(body.block.block_type).toBe("hero");
    expect(body.block).not.toHaveProperty("blockType");
    expect(body.block.config).toMatchObject({ heading: "A clear point of view" });
  });
});
