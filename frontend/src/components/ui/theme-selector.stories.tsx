import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ThemeSelector } from "./theme-selector";

const meta = {
  title: "Foundation/Theme selector",
  component: ThemeSelector,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <div style={{ padding: "2rem" }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof ThemeSelector>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Compact: Story = {
  args: { compact: true },
};
