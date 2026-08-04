import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicProjectData } from "@/generated/api/src/models";

import { ControlledMarkdown } from "./controlled-markdown";
import { ProjectCard } from "./project-card";

const project: PublicProjectData = {
  architecture: "Bounded services.",
  canonicalUrl: null,
  demoUrl: null,
  endDate: null,
  experiences: [],
  featured: true,
  fullDescription: "Overview",
  coverMediaId: null,
  id: "0198a12c-6000-7000-8000-000000000001",
  impact: "Faster delivery.",
  name: "API Platform",
  ownerRole: "Technical lead",
  problem: "Delivery risk.",
  relatedProjects: [],
  repositoryUrl: null,
  seoDescription: "A secure platform.",
  seoTitle: "API Platform",
  shortDescription: "A secure API-first platform.",
  screenshotMediaIds: [],
  skills: [{ name: "Python", slug: "python" }],
  slug: "api-platform",
  solution: "Typed contracts.",
  startDate: new Date("2025-01-01T00:00:00Z"),
  status: "active",
  technologies: ["Python", "PostgreSQL"],
};

describe("public projects", () => {
  it("renders a semantic case-study link without internal lifecycle data", () => {
    render(<ProjectCard index={0} item={project} />);
    expect(screen.getByRole("heading", { name: "API Platform" })).toBeVisible();
    expect(
      screen.getAllByRole("link", { name: /API Platform|Read case study/u })[0],
    ).toHaveAttribute("href", "/projects/api-platform");
    expect(screen.getByText("Featured case study")).toBeVisible();
    expect(document.body.textContent).not.toContain("revision");
  });

  it("renders an optimized public cover when the project has one", () => {
    render(
      <ProjectCard
        index={0}
        item={{ ...project, coverMediaId: "0198a12c-6000-7000-8000-000000000009" }}
      />,
    );
    const image = screen.getByRole("img", { name: "API Platform project cover" });
    expect(image).toHaveAttribute("loading", "lazy");
    expect(image).toHaveAttribute("srcset", expect.stringContaining("1920w"));
  });

  it("renders controlled markdown as React nodes and never executes raw markup", () => {
    render(
      <ControlledMarkdown
        value={"## Design\n\n- Safe links\n- No HTML\n\n[Read](/about) <script>alert(1)</script>"}
      />,
    );
    expect(screen.getByRole("heading", { name: "Design" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Read" })).toHaveAttribute("href", "/about");
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getByText(/<script>alert\(1\)<\/script>/u)).toBeVisible();
  });
});
