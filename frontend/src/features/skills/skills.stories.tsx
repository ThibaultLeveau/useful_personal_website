import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { PublicSkills } from "./public-skills";

const meta = {
  component: PublicSkills,
  parameters: { layout: "padded" },
  title: "Features/Skills/Public catalog",
} satisfies Meta<typeof PublicSkills>;

export default meta;
type Story = StoryObj<typeof meta>;

export const GroupedCatalog: Story = {
  args: {
    skills: [
      {
        categoryDescription: "Services, APIs, and durable data boundaries.",
        categoryName: "Backend engineering",
        categoryPosition: 0,
        categorySlug: "backend-engineering",
        description: "Typed APIs with security and operability designed in.",
        featured: true,
        iconKey: "python",
        name: "Python",
        position: 0,
        proficiencyLabel: "Advanced",
        proficiencyScore: 91,
        relatedExperiences: [],
        relatedProjects: [],
        slug: "python",
        yearsExperience: "7.50",
      },
    ],
  },
};

export const Empty: Story = { args: { skills: [] } };
