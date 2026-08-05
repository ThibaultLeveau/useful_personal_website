import type { ProjectData } from "@/generated/api/src/models";

import type { AdminProjectsApiBoundary } from "./admin-api";

export const fixtureProject: ProjectData = {
  createdAt: new Date("2026-08-04T08:00:00Z"),
  deletedAt: null,
  draft: {
    architecture: "FastAPI, PostgreSQL, and a generated client.",
    basedOnRevisionId: null,
    canonicalUrl: "https://portfolio.example.test/projects/api-platform",
    coverMediaId: null,
    createdAt: new Date("2026-08-04T08:00:00Z"),
    createdBy: "0198a12c-6000-7000-8000-000000000002",
    demoUrl: "https://example.test/demo",
    endDate: null,
    experienceIds: [],
    frozen: false,
    fullDescription: "## Overview\n\nA complete case study.",
    id: "0198a12c-6000-7000-8000-000000000003",
    impact: "Reduced lead time.",
    name: "API Platform",
    ownerRole: "Technical lead",
    problem: "Teams needed reliable delivery.",
    relatedProjectIds: [],
    repositoryUrl: "https://example.test/repository",
    revisionNumber: 1,
    screenshotMediaIds: [],
    seoDescription: "How a secure publishing platform was designed.",
    seoTitle: "API Platform case study",
    shortDescription: "A secure API-first publishing platform.",
    skillIds: [],
    solution: "Built bounded services and immutable revisions.",
    startDate: new Date("2025-01-01T00:00:00Z"),
    status: "active",
    technologies: ["Python", "PostgreSQL"],
    updatedAt: new Date("2026-08-04T08:00:00Z"),
  },
  featured: true,
  id: "0198a12c-6000-7000-8000-000000000001",
  lifecycle: "draft",
  position: 0,
  publishAt: null,
  published: null,
  slug: "api-platform",
  unpublishedAt: null,
  updatedAt: new Date("2026-08-04T08:00:00Z"),
  version: 1,
  visible: true,
};

export function projectBoundary(
  overrides: Partial<AdminProjectsApiBoundary> = {},
): AdminProjectsApiBoundary {
  const references = {
    experiences: [],
    projects: [fixtureProject],
    skills: [],
    timezone: "Europe/Paris",
  };
  return {
    create: async () => fixtureProject,
    delete: async () => undefined,
    get: async () => ({ ...references, project: fixtureProject }),
    list: async () => ({
      items: [fixtureProject],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 50,
        totalItems: 1,
        totalPages: 1,
      },
    }),
    preview: async () => ({
      banner: "Draft preview - not public",
      noindex: true,
      project: fixtureProject,
    }),
    publish: async (item) => ({ ...item, lifecycle: "published", version: item.version + 1 }),
    references: async () => references,
    reorder: async () => undefined,
    reschedule: async (item, publishAt) => ({
      ...item,
      lifecycle: "scheduled",
      publishAt,
      version: item.version + 1,
    }),
    save: async (item, input) => ({
      ...item,
      draft: { ...item.draft, ...input },
      version: item.version + 1,
    }),
    setFeatured: async (item, featured) => ({
      ...item,
      featured,
      version: item.version + 1,
    }),
    setVisibility: async (item, visible) => ({
      ...item,
      version: item.version + 1,
      visible,
    }),
    unpublish: async (item) => ({
      ...item,
      lifecycle: "unpublished",
      version: item.version + 1,
    }),
    ...overrides,
  };
}
