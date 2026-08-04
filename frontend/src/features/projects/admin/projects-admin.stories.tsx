import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ProjectManager } from "./project-manager";
import { projectBoundary } from "./project-fixtures";

const meta = {
  component: ProjectManager,
  parameters: { layout: "fullscreen" },
  title: "Features/Projects/Admin manager",
} satisfies Meta<typeof ProjectManager>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DraftCaseStudy: Story = { args: { api: projectBoundary() } };

export const Empty: Story = {
  args: {
    api: projectBoundary({
      list: async () => ({
        items: [],
        pagination: {
          hasNext: false,
          hasPrevious: false,
          page: 1,
          pageSize: 50,
          totalItems: 0,
          totalPages: 0,
        },
      }),
    }),
  },
};
