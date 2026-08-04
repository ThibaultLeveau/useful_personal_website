import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicSkillData } from "@/generated/api/src/models";

import { groupSkills, PublicSkills } from "./public-skills";

function skill(overrides: Partial<PublicSkillData> = {}): PublicSkillData {
  return {
    categoryDescription: "Services and systems",
    categoryName: "Backend",
    categoryPosition: 1,
    categorySlug: "backend",
    description: "Typed service boundaries.",
    featured: false,
    iconKey: null,
    name: "Python",
    position: 0,
    proficiencyLabel: "Advanced",
    proficiencyScore: 88,
    relatedExperiences: [],
    relatedProjects: [],
    slug: "python",
    yearsExperience: "6.50",
    ...overrides,
  };
}

describe("public skills", () => {
  it("groups in category order and renders semantic, privacy-safe cards", () => {
    const data = [
      skill(),
      skill({
        categoryName: "Interface",
        categoryPosition: 0,
        categorySlug: "interface",
        featured: true,
        name: "Accessibility",
        proficiencyScore: null,
        slug: "accessibility",
      }),
    ];

    expect(groupSkills(data).map((group) => group.slug)).toEqual(["interface", "backend"]);
    render(<PublicSkills skills={data} />);

    expect(screen.getAllByRole("heading", { level: 2 }).map((item) => item.textContent)).toEqual([
      "Interface",
      "Backend",
    ]);
    expect(screen.getByText("Featured")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Python proficiency" })).toHaveValue(88);
    expect(document.body.textContent).not.toContain("0198");
  });

  it("announces an empty filtered result", () => {
    render(<PublicSkills skills={[]} />);
    expect(screen.getByRole("status")).toHaveTextContent("No published skills match");
  });
});
