"use client";

import {
  BlogAdministrationApi,
  type AdminBlogPostsListRequest,
} from "@/generated/api/src/apis/BlogAdministrationApi";
import {
  TaxonomyKind,
  type PaginationData,
  type PostCreateRequest,
  type PostData,
  type PostInput,
  type PostPreviewData,
  type PostSourceExportData,
  type TaxonomyCreateRequest,
  type TaxonomyData,
  type TaxonomyUpdateRequest,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";
const etag = (value: { version: number }) => `"v${value.version}"`;

function browserOrigin(): string {
  if (typeof window === "undefined")
    throw new ApiError({
      code: "AUTH_BROWSER_REQUIRED",
      message: "Open this editor in a browser.",
      status: 0,
    });
  return window.location.origin;
}

function csrfToken(): string {
  if (typeof document !== "undefined")
    for (const part of document.cookie.split(";")) {
      const [name, ...raw] = part.trim().split("=");
      if (name === CSRF_COOKIE_NAME) {
        const value = decodeURIComponent(raw.join("="));
        if (value) return value;
      }
    }
  throw new ApiError({
    code: "CSRF_MISSING",
    message: "The protected session could not be verified.",
    status: 401,
  });
}

function idempotencyKey(): string {
  if (typeof crypto?.randomUUID !== "function")
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  return crypto.randomUUID();
}
const unsafe = () => ({ origin: browserOrigin(), xCSRFToken: csrfToken() });

export interface BlogListSnapshot {
  items: PostData[];
  pagination: PaginationData;
}
export interface BlogEditorSnapshot {
  post: PostData;
  posts: PostData[];
  tags: TaxonomyData[];
  categories: TaxonomyData[];
}
export interface BlogReferences {
  posts: PostData[];
  tags: TaxonomyData[];
  categories: TaxonomyData[];
}

export interface AdminBlogApiBoundary {
  list(filters?: AdminBlogPostsListRequest): Promise<BlogListSnapshot>;
  references(): Promise<BlogReferences>;
  get(id: string): Promise<BlogEditorSnapshot>;
  create(input: PostCreateRequest): Promise<PostData>;
  save(item: PostData, input: PostInput): Promise<PostData>;
  preview(id: string): Promise<PostPreviewData>;
  publish(item: PostData, publishAt?: Date): Promise<PostData>;
  reschedule(item: PostData, publishAt: Date): Promise<PostData>;
  unpublish(item: PostData): Promise<PostData>;
  setVisibility(item: PostData, visible: boolean): Promise<PostData>;
  delete(item: PostData): Promise<void>;
  exportSource(id: string): Promise<PostSourceExportData>;
  createTaxonomy(input: TaxonomyCreateRequest): Promise<TaxonomyData>;
  updateTaxonomy(item: TaxonomyData, input: TaxonomyUpdateRequest): Promise<TaxonomyData>;
  deleteTaxonomy(item: TaxonomyData): Promise<void>;
}

class GeneratedAdminBlogBoundary implements AdminBlogApiBoundary {
  constructor(private readonly blog: BlogAdministrationApi) {}
  private async translated<Value>(operation: () => Promise<Value>): Promise<Value> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }
  list(filters: AdminBlogPostsListRequest = {}): Promise<BlogListSnapshot> {
    return this.translated(async () => {
      const result = await this.blog.adminBlogPostsList(
        { page: 1, pageSize: 50, sort: "position", ...filters },
        { cache: "no-store" },
      );
      return { items: result.data, pagination: result.meta.pagination };
    });
  }
  private taxonomies(
    kind: typeof TaxonomyKind.Tag | typeof TaxonomyKind.Category,
  ): Promise<TaxonomyData[]> {
    return this.translated(
      async () =>
        (await this.blog.adminBlogTaxonomiesList({ kind }, { cache: "no-store" })).data.items,
    );
  }
  async references(): Promise<BlogReferences> {
    const [posts, tags, categories] = await Promise.all([
      this.list({ pageSize: 100 }),
      this.taxonomies(TaxonomyKind.Tag),
      this.taxonomies(TaxonomyKind.Category),
    ]);
    return { posts: posts.items, tags, categories };
  }
  async get(id: string): Promise<BlogEditorSnapshot> {
    return this.translated(async () => {
      const [post, references] = await Promise.all([
        this.blog.adminBlogPostGet({ postId: id }, { cache: "no-store" }),
        this.references(),
      ]);
      return { post: post.data, ...references };
    });
  }
  create(input: PostCreateRequest): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostCreate(
            { ...unsafe(), idempotencyKey: idempotencyKey(), postCreateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  save(item: PostData, input: PostInput): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostDraftUpdate(
            { ...unsafe(), postId: item.id, ifMatch: etag(item), postInput: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  preview(id: string): Promise<PostPreviewData> {
    return this.translated(
      async () =>
        (await this.blog.adminBlogPostPreview({ postId: id }, { cache: "no-store" })).data,
    );
  }
  publish(item: PostData, publishAt?: Date): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostPublish(
            {
              ...unsafe(),
              postId: item.id,
              ifMatch: etag(item),
              idempotencyKey: idempotencyKey(),
              publishPostRequest: publishAt ? { publishAt } : {},
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  reschedule(item: PostData, publishAt: Date): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostReschedule(
            {
              ...unsafe(),
              postId: item.id,
              ifMatch: etag(item),
              idempotencyKey: idempotencyKey(),
              reschedulePostRequest: { publishAt },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  unpublish(item: PostData): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostUnpublish(
            { ...unsafe(), postId: item.id, ifMatch: etag(item), idempotencyKey: idempotencyKey() },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  setVisibility(item: PostData, visible: boolean): Promise<PostData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostVisibilityUpdate(
            {
              ...unsafe(),
              postId: item.id,
              ifMatch: etag(item),
              blogVisibilityRequest: { visible },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  async delete(item: PostData): Promise<void> {
    await this.translated(() =>
      this.blog.adminBlogPostDelete(
        { ...unsafe(), postId: item.id, ifMatch: etag(item) },
        { cache: "no-store" },
      ),
    );
  }
  exportSource(id: string): Promise<PostSourceExportData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogPostSourceExport(
            { postId: id, accept: "application/json" },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  createTaxonomy(input: TaxonomyCreateRequest): Promise<TaxonomyData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogTaxonomyCreate(
            { ...unsafe(), idempotencyKey: idempotencyKey(), taxonomyCreateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  updateTaxonomy(item: TaxonomyData, input: TaxonomyUpdateRequest): Promise<TaxonomyData> {
    return this.translated(
      async () =>
        (
          await this.blog.adminBlogTaxonomyUpdate(
            { ...unsafe(), taxonomyId: item.id, ifMatch: etag(item), taxonomyUpdateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  async deleteTaxonomy(item: TaxonomyData): Promise<void> {
    await this.translated(() =>
      this.blog.adminBlogTaxonomyDelete(
        { ...unsafe(), taxonomyId: item.id, ifMatch: etag(item) },
        { cache: "no-store" },
      ),
    );
  }
}

export function createAdminBlogApi(fetchApi?: FetchAPI): AdminBlogApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminBlogBoundary(new BlogAdministrationApi(configuration));
}

export const adminBlogApi = createAdminBlogApi();
