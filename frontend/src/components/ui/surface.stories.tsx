import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Surface } from "./surface";

const meta = {
  title: "Foundation/Surface",
  component: Surface,
  tags: ["autodocs"],
  args: {
    children: "A semantic-token surface.",
  },
  decorators: [
    (Story) => (
      <div style={{ maxWidth: "32rem", padding: "2rem" }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Surface>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Subtle: Story = {
  args: { tone: "subtle" },
};

export const Inverse: Story = {
  args: { tone: "inverse" },
};
