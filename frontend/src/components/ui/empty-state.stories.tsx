import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Button } from "./button";
import { EmptyState } from "./empty-state";

const meta = {
  title: "Foundation/Empty state",
  component: EmptyState,
  tags: ["autodocs"],
  args: {
    eyebrow: "Initial state",
    title: "Nothing is configured yet.",
    description:
      "Connect an official data source before presenting records or actions in this region.",
  },
  decorators: [
    (Story) => (
      <div style={{ maxWidth: "60rem", padding: "2rem" }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithAction: Story = {
  args: {
    action: <Button variant="secondary">Learn more</Button>,
  },
};

export const LongContent: Story = {
  args: {
    title: "The requested collection has no records that can be presented in this workspace.",
    description:
      "Long labels and translated content must wrap without obscuring focus, actions, or the reading order at narrow widths and high zoom.",
  },
};
