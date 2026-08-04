import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { PublicFooter } from "./public-footer";

const meta = {
  title: "Shell/Public footer",
  component: PublicFooter,
  tags: ["autodocs"],
  args: {
    brand: "Fictional Studio",
    footer: {
      copyrightText: "Fictional demonstration content.",
      columns: [
        {
          title: "Explore",
          items: [
            {
              href: "/about",
              itemKind: "link",
              label: "About",
              target: "same_window",
            },
          ],
        },
      ],
    },
  },
} satisfies Meta<typeof PublicFooter>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
