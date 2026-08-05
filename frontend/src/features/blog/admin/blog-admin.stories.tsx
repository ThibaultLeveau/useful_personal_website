import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { blogBoundary } from "./blog-fixtures";
import { BlogManager } from "./blog-manager";

const meta = {
  component: BlogManager,
  args: { api: blogBoundary() },
  parameters: { layout: "fullscreen" },
  title: "Features/Blog/Admin publishing desk",
} satisfies Meta<typeof BlogManager>;
export default meta;
type Story = StoryObj<typeof meta>;
export const WithDraft: Story = {};
export const Empty: Story = {
  args: {
    api: blogBoundary({
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
      references: async () => ({ posts: [], tags: [], categories: [] }),
    }),
  },
};
