import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { AuthContext } from "@/features/auth/auth-context";

import { ExperienceManager } from "./experience-manager";
import { authenticatedContext, experienceBoundary } from "./experience-fixtures";

const meta = {
  component: ExperienceManager,
  decorators: [
    (Story) => (
      <AuthContext.Provider value={authenticatedContext()}>
        <main className="admin-main">
          <Story />
        </main>
      </AuthContext.Provider>
    ),
  ],
  parameters: { layout: "fullscreen" },
  title: "Features/Experiences/Admin manager",
} satisfies Meta<typeof ExperienceManager>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DraftRecord: Story = { args: { api: experienceBoundary() } };

export const Empty: Story = {
  args: {
    api: experienceBoundary({
      list: async () => ({
        items: [],
        pagination: {
          hasNext: false,
          hasPrevious: false,
          page: 1,
          pageSize: 20,
          totalItems: 0,
          totalPages: 0,
        },
      }),
    }),
  },
};
