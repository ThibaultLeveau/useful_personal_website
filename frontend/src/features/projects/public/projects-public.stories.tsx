import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import type { PublicProjectData } from "@/generated/api/src/models";

import { ProjectCard } from "./project-card";

const project: PublicProjectData = {
  architecture: "Bounded services with immutable revisions.",
  canonicalUrl: "https://portfolio.example.test/projects/api-platform",
  demoUrl: "https://example.test/demo",
  endDate: null,
  experiences: [],
  featured: true,
  fullDescription: "## Overview\n\nA complete case study.",
  coverMediaId: null,
  id: "0198a12c-6000-7000-8000-000000000001",
  impact: "Reduced lead time.",
  name: "API Platform",
  ownerRole: "Technical lead",
  problem: "Teams needed reliable delivery.",
  relatedProjects: [],
  repositoryUrl: "https://example.test/repository",
  seoDescription: "How a secure publishing platform was designed.",
  seoTitle: "API Platform case study",
  shortDescription: "A secure API-first publishing platform.",
  screenshotMediaIds: [],
  skills: [{ name: "Python", slug: "python" }],
  slug: "api-platform",
  solution: "Built bounded services and immutable revisions.",
  startDate: new Date("2025-01-01T00:00:00Z"),
  status: "active",
  technologies: ["Python", "PostgreSQL"],
};

const meta = {
  args: { index: 0, item: project },
  component: ProjectCard,
  parameters: { layout: "padded" },
  title: "Features/Projects/Public card",
} satisfies Meta<typeof ProjectCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Featured: Story = {};

export const Standard: Story = {
  args: { item: { ...project, featured: false } },
};
