import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import type { PublicPageData } from "@/generated/api/src/models";
import { PageRenderer } from "./page-renderer";

const page = {
  blocks: [
    {
      id: "hero",
      position: 0,
      references: [],
      definition: {
        blockType: "hero",
        schemaVersion: 1,
        visible: true,
        layout: "wide",
        theme: "default",
        config: {
          eyebrow: "Independent engineer",
          heading: "Useful systems, clearly made.",
          body: "I design secure products where strong contracts and humane interfaces reinforce each other.",
          actions: [{ label: "See the work", destination: "/projects" }],
        },
      },
    },
    {
      id: "stats",
      position: 1,
      references: [],
      definition: {
        blockType: "statistics",
        schemaVersion: 1,
        visible: true,
        config: {
          items: [
            { label: "Years", value: "8+", context: "Building production systems" },
            { label: "Projects", value: "24", context: "Across product and platform work" },
          ],
        },
      },
    },
    {
      id: "quote",
      position: 2,
      references: [],
      definition: {
        blockType: "testimonial",
        schemaVersion: 1,
        visible: true,
        config: {
          quote: "Turns ambiguity into a system people can trust.",
          attribution: "Product partner",
          context: "Platform program",
        },
      },
    },
    {
      id: "contact",
      position: 3,
      references: [],
      definition: {
        blockType: "contact_callout",
        schemaVersion: 1,
        visible: true,
        theme: "muted",
        config: {
          heading: "Have a consequential problem?",
          body: "Bring the constraints. We can find the shape of the solution.",
          actions: [{ label: "Get in touch", destination: "/contact" }],
        },
      },
    },
  ],
  canonicalPath: "/",
  canonicalUrl: null,
  description: "A personal portfolio.",
  id: "home",
  publishedAt: new Date("2026-08-04T00:00:00Z"),
  routeKind: "home",
  seoDescription: "Useful systems, clearly made.",
  seoTitle: "Home",
  slug: null,
  title: "Home",
} as unknown as PublicPageData;

const meta = {
  component: PageRenderer,
  args: { page },
  parameters: { layout: "fullscreen" },
  title: "Features/Pages/Public renderer",
} satisfies Meta<typeof PageRenderer>;
export default meta;
type Story = StoryObj<typeof meta>;
export const PortfolioHome: Story = {};
