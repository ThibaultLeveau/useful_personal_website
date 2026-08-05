import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ExperienceTimeline } from "./experience-timeline";

const meta = {
  component: ExperienceTimeline,
  parameters: { layout: "padded" },
  title: "Features/Experiences/Public timeline",
} satisfies Meta<typeof ExperienceTimeline>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Chronology: Story = {
  args: {
    experiences: [
      {
        achievements: [
          "Cut lead time while raising deployment confidence.",
          "Made service ownership legible across teams.",
        ],
        companyName: "Northstar Systems",
        companyUrl: "https://example.com",
        currentPosition: true,
        detailedDescription:
          "Led the platform group through a multi-year reliability and developer-experience program.",
        employmentType: "full_time",
        endDate: null,
        id: "01989abc-def0-7000-8000-000000000501",
        location: "Paris, France",
        remoteStatus: "hybrid",
        responsibilities: ["Technical direction", "Architecture reviews", "Mentoring"],
        roleTitle: "Staff Platform Engineer",
        shortSummary: "Built systems and practices that let product teams ship with confidence.",
        skills: [
          { name: "Python", slug: "python" },
          { name: "Accessibility", slug: "accessibility" },
        ],
        startDate: new Date("2024-01-01T00:00:00.000Z"),
        technologies: ["PostgreSQL", "Kubernetes", "OpenTelemetry"],
      },
    ],
  },
};

export const Empty: Story = { args: { experiences: [] } };
