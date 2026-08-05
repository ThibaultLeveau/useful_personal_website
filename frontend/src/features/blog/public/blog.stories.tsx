import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import type { PublicPostData } from "@/generated/api/src/models";

import { PostCard } from "./post-card";
import { SafeRenderedContent } from "./safe-rendered-content";

const item: PublicPostData = {
  id: "0198a12c-6000-7000-8000-000000000010",
  slug: "designing-a-calm-api",
  title: "Designing a calm API",
  excerpt: "How explicit contracts make complex systems easier to trust.",
  authorDisplay: "Alex Morgan",
  readingMinutes: 4,
  publishedAt: new Date("2026-08-04T09:30:00Z"),
  seoTitle: "Designing a calm API",
  seoDescription: "A practical note on dependable API contracts.",
  canonicalUrl: null,
  coverMediaId: null,
  categories: [
    { id: "0198a12c-6000-7000-8000-000000000012", name: "Engineering", slug: "engineering" },
  ],
  tags: [
    { id: "0198a12c-6000-7000-8000-000000000011", name: "Architecture", slug: "architecture" },
  ],
  relatedPosts: [],
  content: {
    html: "<h2>Start with the contract</h2><p>Useful APIs make their boundaries visible.</p>",
    policyName: "upw-commonmark",
    policyVersion: "1.0.0",
    sourceChecksum: "sha256:fixture",
  },
};

const meta = {
  component: PostCard,
  args: { item },
  parameters: { layout: "padded" },
  title: "Features/Blog/Public article",
} satisfies Meta<typeof PostCard>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Card: Story = {};
export const RenderedArticle: Story = {
  render: () => <SafeRenderedContent content={item.content} />,
};
