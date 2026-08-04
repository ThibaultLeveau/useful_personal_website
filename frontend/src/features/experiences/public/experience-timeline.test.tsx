import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicExperienceData } from "@/generated/api/src/models";

import { ExperienceTimeline, experienceDateRange } from "./experience-timeline";

function experience(overrides: Partial<PublicExperienceData> = {}): PublicExperienceData {
  return {
    achievements: ["Cut deployment time by 40%."],
    companyName: "Example Studio",
    companyUrl: "https://example.test",
    currentPosition: true,
    detailedDescription: "Built durable service boundaries.",
    employmentType: "full_time",
    endDate: null,
    id: "01989abc-def0-7000-8000-000000000501",
    location: "Paris, France",
    remoteStatus: "hybrid",
    responsibilities: ["Led platform delivery."],
    roleTitle: "Staff Engineer",
    shortSummary: "Led the platform team.",
    skills: [{ name: "Python", slug: "python" }],
    startDate: new Date("2024-01-01T00:00:00.000Z"),
    technologies: ["PostgreSQL"],
    ...overrides,
  };
}

describe("public experience timeline", () => {
  it("preserves API chronology and renders semantic, privacy-safe evidence", () => {
    render(
      <ExperienceTimeline
        experiences={[
          experience(),
          experience({
            companyName: "Earlier Studio",
            currentPosition: false,
            endDate: new Date("2023-12-31T00:00:00.000Z"),
            id: "01989abc-def0-7000-8000-000000000502",
            roleTitle: "Senior Engineer",
            startDate: new Date("2021-01-01T00:00:00.000Z"),
          }),
        ]}
      />,
    );

    expect(screen.getAllByRole("heading", { level: 2 }).map((node) => node.textContent)).toEqual([
      "Staff Engineer",
      "Senior Engineer",
    ]);
    expect(screen.getByRole("list", { name: "Professional experience chronology" })).toBeVisible();
    expect(screen.getAllByRole("link", { name: "Python" })[0]).toHaveAttribute(
      "href",
      "/skills#python",
    );
    expect(screen.getByText("Jan 2024 – Present")).toBeVisible();
    expect(document.body.textContent).not.toContain("revision");
    expect(document.body.textContent).not.toContain("createdBy");
  });

  it("uses an intentional unknown-end fallback and announces empty results", () => {
    expect(experienceDateRange(experience({ currentPosition: false, endDate: null }))).toContain(
      "End date open",
    );
    render(<ExperienceTimeline experiences={[]} />);
    expect(screen.getByRole("status")).toHaveTextContent("No published experience");
  });
});
