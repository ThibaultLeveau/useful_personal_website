import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { ProjectData } from "@/generated/api/src/models";

import type { AdminProjectsApiBoundary } from "./admin-api";
import { ProjectManager } from "./project-manager";

const project: ProjectData = {
  createdAt: new Date("2026-01-01T00:00:00Z"),
  deletedAt: null,
  draft: {
    architecture: "Architecture",
    basedOnRevisionId: null,
    createdAt: new Date("2026-01-01T00:00:00Z"),
    createdBy: "0198a12c-6000-7000-8000-000000000002",
    endDate: null,
    experienceIds: [],
    frozen: false,
    fullDescription: "Overview",
    id: "0198a12c-6000-7000-8000-000000000003",
    impact: "Impact",
    name: "API Platform",
    ownerRole: "Lead",
    problem: "Problem",
    relatedProjectIds: [],
    revisionNumber: 1,
    screenshotMediaIds: [],
    shortDescription: "Secure delivery platform",
    skillIds: [],
    solution: "Solution",
    startDate: new Date("2025-01-01T00:00:00Z"),
    status: "active",
    technologies: ["Python"],
    updatedAt: new Date("2026-01-01T00:00:00Z"),
  },
  featured: true,
  id: "0198a12c-6000-7000-8000-000000000001",
  lifecycle: "draft",
  position: 0,
  publishAt: null,
  published: null,
  slug: "api-platform",
  unpublishedAt: null,
  updatedAt: new Date("2026-01-01T00:00:00Z"),
  version: 1,
  visible: true,
};

function boundary(
  list = vi.fn<AdminProjectsApiBoundary["list"]>(async () => ({
    items: [project],
    pagination: {
      hasNext: false,
      hasPrevious: false,
      page: 1,
      pageSize: 50,
      totalItems: 1,
      totalPages: 1,
    },
  })),
): AdminProjectsApiBoundary {
  return {
    list,
    create: vi.fn(),
    delete: vi.fn(),
    get: vi.fn(),
    preview: vi.fn(),
    publish: vi.fn(),
    references: vi.fn(),
    reorder: vi.fn(),
    reschedule: vi.fn(),
    save: vi.fn(),
    setFeatured: vi.fn(),
    setVisibility: vi.fn(),
    unpublish: vi.fn(),
  };
}

describe("project manager", () => {
  it("shows lifecycle, route identity, display state, and workflow links", async () => {
    render(<ProjectManager api={boundary()} />);
    expect(await screen.findByRole("heading", { name: "Project case studies" })).toBeVisible();
    expect(screen.getAllByText("API Platform").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Visible").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "Edit" })[0]).toHaveAttribute(
      "href",
      `/admin/projects/${project.id}/edit`,
    );
    expect(screen.getByRole("link", { name: "New project" })).toHaveAttribute(
      "href",
      "/admin/projects/new",
    );
  });

  it("sends only generated allow-listed search and lifecycle filters", async () => {
    const user = userEvent.setup();
    const list = vi.fn<AdminProjectsApiBoundary["list"]>(async () => ({
      items: [project],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 50,
        totalItems: 1,
        totalPages: 1,
      },
    }));
    render(<ProjectManager api={boundary(list)} />);
    await screen.findByText("/api-platform");
    await user.type(screen.getByLabelText("Search"), "platform");
    await user.selectOptions(screen.getByLabelText("Lifecycle"), "draft");
    await user.click(screen.getByRole("button", { name: "Apply" }));
    expect(list).toHaveBeenLastCalledWith({ lifecycle: "draft", search: "platform" });
  });
});
