import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicPageData } from "@/generated/api/src/models";
import { PAGE_BLOCK_TYPES, PageRenderer } from "./page-renderer";

const definitions: Record<string, object> = {
  hero: {
    config: {
      heading: "Systems with a point of view",
      body: "Secure, useful software.",
      actions: [],
    },
  },
  profile_summary: { config: {} },
  call_to_action: {
    config: { heading: "Work together", body: "Start with the problem.", actions: [] },
  },
  statistics: {
    config: { items: [{ label: "Projects", value: "12", context: "Shipped outcomes" }] },
  },
  skills_grid: { config: {} },
  featured_skills: { config: {} },
  experience_summary: { config: {} },
  experience_list: { config: {} },
  project_grid: { config: {} },
  featured_projects: { config: {} },
  latest_posts: { config: {} },
  rich_text: {
    config: {
      content: {
        html: "<h3>Safe narrative</h3><h4>Supporting detail</h4>",
        policyName: "public-commonmark",
        policyVersion: 1,
        sourceChecksum: "sha256:test",
      },
    },
  },
  image: { config: { mediaId: "asset-image", alt: "Architecture sketch" } },
  image_with_text: {
    config: {
      mediaId: "asset-split",
      alt: "Diagram",
      heading: "Visual evidence",
      body: "A staged asset.",
    },
  },
  links_collection: { config: { links: [{ label: "About", destination: "/about" }] } },
  contact_callout: { config: { heading: "Contact", body: "Say hello.", actions: [] } },
  testimonial: { config: { quote: "Reliable and thoughtful.", attribution: "A client" } },
  divider: { config: { style: "line" } },
  spacer: { config: { size: "small" } },
};

const page = {
  blocks: PAGE_BLOCK_TYPES.map((blockType, position) => ({
    id: `block-${position}`,
    position,
    references: [],
    definition: { blockType, schemaVersion: 1, visible: true, ...definitions[blockType] },
    ...(blockType === "profile_summary"
      ? {
          profile: {
            fullName: "Ada",
            professionalTitle: "Engineer",
            shortBiography: "Builds dependable systems.",
          },
        }
      : {}),
  })),
  canonicalPath: "/",
  canonicalUrl: null,
  description: "Portfolio",
  id: "page-home",
  publishedAt: new Date("2026-08-04T00:00:00Z"),
  routeKind: "home",
  seoDescription: "Portfolio",
  seoTitle: "Home",
  slug: null,
  title: "Home",
} as unknown as PublicPageData;

describe("page renderer", () => {
  it("keeps renderer parity with the frozen 19-kind registry", () => {
    expect(PAGE_BLOCK_TYPES).toHaveLength(19);
    expect(new Set(PAGE_BLOCK_TYPES).size).toBe(19);
    render(<PageRenderer page={page} />);
    expect(document.querySelectorAll("[id^='block-block-']")).toHaveLength(19);
    expect(screen.getByRole("heading", { name: "Systems with a point of view" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Safe narrative" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Safe narrative" })).toHaveProperty("tagName", "H2");
    expect(screen.getByRole("heading", { name: "Supporting detail" })).toHaveProperty(
      "tagName",
      "H3",
    );
    const statisticContext = screen.getByText("Shipped outcomes");
    expect(statisticContext).toHaveProperty("tagName", "SPAN");
    expect(statisticContext.closest("dd")).toBeTruthy();
    expect(statisticContext.closest("dl > div > p")).toBeNull();
  });

  it("renders only the server-safe rich-text DTO", () => {
    render(<PageRenderer page={page} />);
    expect(document.querySelector("[data-content-policy='public-commonmark@1']")).toBeTruthy();
    expect(document.body.textContent).not.toContain("source");
  });

  it("renders responsive public media without the former staging placeholder", () => {
    render(<PageRenderer page={page} />);
    expect(screen.getByAltText("Architecture sketch")).toHaveAttribute(
      "src",
      "/api/v1/media/asset-image/960?representation=fallback",
    );
    expect(screen.getByAltText("Diagram")).toHaveAttribute(
      "src",
      "/api/v1/media/asset-split/960?representation=fallback",
    );
    expect(document.body.textContent).not.toContain("Media publishing arrives in M9");
  });
});
