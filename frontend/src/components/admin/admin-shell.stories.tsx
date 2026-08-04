import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { EmptyState } from "@/components/ui/empty-state";

import { AdminShell } from "./admin-shell";

const meta = {
  title: "Shell/Administration",
  component: AdminShell,
  tags: ["autodocs"],
  args: {
    children: (
      <main className="admin-main" id="admin-main">
        <EmptyState
          description="No disconnected records or controls are rendered."
          eyebrow="Initial state"
          title="No administrative data is connected."
        />
      </main>
    ),
  },
} satisfies Meta<typeof AdminShell>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
