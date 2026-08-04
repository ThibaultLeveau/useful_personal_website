import type { PostData, TaxonomyData } from "@/generated/api/src/models";

import type { AdminBlogApiBoundary } from "./admin-api";

const now = new Date("2026-08-04T09:30:00Z");
export const tag: TaxonomyData = {
  id: "0198a12c-6000-7000-8000-000000000011",
  kind: "tag",
  name: "Architecture",
  slug: "architecture",
  visible: true,
  position: 0,
  version: 1,
  createdAt: now,
  updatedAt: now,
  deletedAt: null,
};
export const category: TaxonomyData = {
  id: "0198a12c-6000-7000-8000-000000000012",
  kind: "category",
  name: "Engineering",
  slug: "engineering",
  visible: true,
  position: 0,
  version: 1,
  createdAt: now,
  updatedAt: now,
  deletedAt: null,
};
export const post: PostData = {
  id: "0198a12c-6000-7000-8000-000000000010",
  slug: "designing-a-calm-api",
  visible: true,
  position: 0,
  version: 2,
  lifecycle: "draft",
  publishAt: null,
  published: null,
  unpublishedAt: null,
  deletedAt: null,
  createdAt: now,
  updatedAt: now,
  draft: {
    id: "0198a12c-6000-7000-8000-000000000013",
    basedOnRevisionId: null,
    revisionNumber: 2,
    frozen: false,
    title: "Designing a calm API",
    excerpt: "How explicit contracts make complex systems easier to trust.",
    authorDisplay: "Alex Morgan",
    source: "## Start with the contract\n\nUseful APIs make their boundaries visible.",
    seoTitle: "Designing a calm API",
    seoDescription: "A practical note on explicit, dependable API contracts.",
    canonicalUrl: null,
    coverMediaId: null,
    tagIds: [tag.id],
    categoryIds: [category.id],
    relatedPostIds: [],
    contentChecksum: "sha256:fixture",
    contentPolicyName: "upw-commonmark",
    contentPolicyVersion: "1.0.0",
    readingMinutes: 2,
    createdBy: "0198a12c-6000-7000-8000-000000000014",
    createdAt: now,
    updatedAt: now,
  },
};

const pagination = {
  hasNext: false,
  hasPrevious: false,
  page: 1,
  pageSize: 50,
  totalItems: 1,
  totalPages: 1,
};
export function blogBoundary(overrides: Partial<AdminBlogApiBoundary> = {}): AdminBlogApiBoundary {
  const fallback = async (): Promise<never> => {
    throw new Error("Fixture operation not configured");
  };
  return {
    list: async () => ({ items: [post], pagination }),
    references: async () => ({ posts: [post], tags: [tag], categories: [category] }),
    get: async () => ({ post, posts: [post], tags: [tag], categories: [category] }),
    create: fallback,
    save: async () => post,
    preview: async () => ({
      postId: post.id,
      title: post.draft.title,
      excerpt: post.draft.excerpt,
      authorDisplay: post.draft.authorDisplay,
      coverMediaId: post.draft.coverMediaId ?? null,
      readingMinutes: 2,
      banner: "Draft preview - not public",
      noindex: true,
      content: {
        html: '<h2 id="start-with-the-contract">Start with the contract</h2><p>Useful APIs make their boundaries visible.</p>',
        policyName: "upw-commonmark",
        policyVersion: "1.0.0",
        sourceChecksum: "sha256:fixture",
      },
    }),
    publish: async () => ({ ...post, lifecycle: "published" }),
    reschedule: async () => ({ ...post, lifecycle: "scheduled" }),
    unpublish: async () => ({ ...post, lifecycle: "unpublished" }),
    setVisibility: async (_item, visible) => ({ ...post, visible }),
    delete: async () => undefined,
    exportSource: async () => ({
      postId: post.id,
      source: post.draft.source,
      checksum: post.draft.contentChecksum,
      contentType: "text/markdown; charset=utf-8",
      filename: `${post.slug}.md`,
      policyName: "upw-commonmark",
      policyVersion: "1.0.0",
      readingMinutes: 2,
    }),
    createTaxonomy: fallback,
    updateTaxonomy: fallback,
    deleteTaxonomy: async () => undefined,
    ...overrides,
  };
}
