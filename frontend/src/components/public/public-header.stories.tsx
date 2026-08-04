import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { PublicHeader } from "./public-header";

const meta = {
  title: "Shell/Public header",
  component: PublicHeader,
  tags: ["autodocs"],
  args: {
    brand: "Fictional Studio",
    navigation: [
      {
        href: "/",
        key: "00000000-0000-7000-8000-000000000001",
        label: "Home",
        target: "same_window",
      },
    ],
  },
} satisfies Meta<typeof PublicHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
