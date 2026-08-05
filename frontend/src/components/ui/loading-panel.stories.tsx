import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { LoadingPanel } from "./loading-panel";

const meta = {
  title: "Foundation/Loading panel",
  component: LoadingPanel,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <div style={{ padding: "2rem" }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof LoadingPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
