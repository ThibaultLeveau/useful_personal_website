"use client";

import { PageAdministrationApi } from "@/generated/api/src/apis/PageAdministrationApi";
import type {
  Block,
  PageCreateRequest,
  PageData,
  PageExportData,
  PagePreviewData,
  PageUpdateRequest,
  RegistryData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";
const etag = (value: PageData) => `"v${value.version}"`;

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
function key(): string {
  if (typeof crypto?.randomUUID !== "function")
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  return crypto.randomUUID();
}
const unsafe = () => ({ origin: browserOrigin(), xCSRFToken: csrfToken() });

export interface AdminPagesApiBoundary {
  list(): Promise<PageData[]>;
  registry(): Promise<RegistryData>;
  get(id: string): Promise<PageData>;
  create(input: PageCreateRequest): Promise<PageData>;
  save(page: PageData, input: PageUpdateRequest): Promise<PageData>;
  duplicate(page: PageData, slug: string): Promise<PageData>;
  remove(page: PageData): Promise<void>;
  addBlock(page: PageData, block: Block): Promise<PageData>;
  updateBlock(page: PageData, blockId: string, block: Block): Promise<PageData>;
  duplicateBlock(page: PageData, blockId: string): Promise<PageData>;
  setBlockVisibility(page: PageData, blockId: string, visible: boolean): Promise<PageData>;
  deleteBlock(page: PageData, blockId: string): Promise<PageData>;
  reorder(page: PageData, orderedIds: string[]): Promise<PageData>;
  preview(id: string): Promise<PagePreviewData>;
  publish(page: PageData, publishAt?: Date): Promise<PageData>;
  reschedule(page: PageData, publishAt: Date): Promise<PageData>;
  unpublish(page: PageData): Promise<PageData>;
  exportPage(id: string): Promise<PageExportData>;
}

class Boundary implements AdminPagesApiBoundary {
  constructor(private readonly pages: PageAdministrationApi) {}
  private async translated<T>(operation: () => Promise<T>): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }
  list() {
    return this.translated(
      async () =>
        (await this.pages.adminPagesList({ page: 1, pageSize: 100 }, { cache: "no-store" })).data,
    );
  }
  registry() {
    return this.translated(
      async () => (await this.pages.adminPagesRegistryGet({ cache: "no-store" })).data,
    );
  }
  get(id: string) {
    return this.translated(
      async () => (await this.pages.adminPageGet({ pageId: id }, { cache: "no-store" })).data,
    );
  }
  create(input: PageCreateRequest) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageCreate(
            { ...unsafe(), idempotencyKey: key(), pageCreateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  save(page: PageData, input: PageUpdateRequest) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageUpdate(
            { ...unsafe(), pageId: page.id, ifMatch: etag(page), pageUpdateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  duplicate(page: PageData, slug: string) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageDuplicate(
            {
              ...unsafe(),
              pageId: page.id,
              ifMatch: etag(page),
              idempotencyKey: key(),
              pageDuplicateRequest: { slug },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  async remove(page: PageData) {
    await this.translated(() =>
      this.pages.adminPageDelete(
        { ...unsafe(), pageId: page.id, ifMatch: etag(page) },
        { cache: "no-store" },
      ),
    );
  }
  addBlock(page: PageData, block: Block) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlockAdd(
            {
              ...unsafe(),
              pageId: page.id,
              ifMatch: etag(page),
              idempotencyKey: key(),
              addBlockRequest: { block },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  updateBlock(page: PageData, blockId: string, block: Block) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlockUpdate(
            {
              ...unsafe(),
              pageId: page.id,
              blockId,
              ifMatch: etag(page),
              updateBlockRequest: { block },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  duplicateBlock(page: PageData, blockId: string) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlockDuplicate(
            { ...unsafe(), pageId: page.id, blockId, ifMatch: etag(page), idempotencyKey: key() },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  setBlockVisibility(page: PageData, blockId: string, visible: boolean) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlockVisibilitySet(
            {
              ...unsafe(),
              pageId: page.id,
              blockId,
              ifMatch: etag(page),
              blockVisibilityRequest: { visible },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  deleteBlock(page: PageData, blockId: string) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlockDelete(
            { ...unsafe(), pageId: page.id, blockId, ifMatch: etag(page) },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  reorder(page: PageData, orderedIds: string[]) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageBlocksReorder(
            {
              ...unsafe(),
              pageId: page.id,
              ifMatch: etag(page),
              idempotencyKey: key(),
              blockReorderRequest: { orderedIds },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  preview(id: string) {
    return this.translated(
      async () => (await this.pages.adminPagePreview({ pageId: id }, { cache: "no-store" })).data,
    );
  }
  publish(page: PageData, publishAt?: Date) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPagePublish(
            {
              ...unsafe(),
              pageId: page.id,
              ifMatch: etag(page),
              idempotencyKey: key(),
              publishPageRequest: publishAt ? { publishAt } : {},
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  reschedule(page: PageData, publishAt: Date) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageReschedule(
            {
              ...unsafe(),
              pageId: page.id,
              ifMatch: etag(page),
              idempotencyKey: key(),
              reschedulePageRequest: { publishAt },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  unpublish(page: PageData) {
    return this.translated(
      async () =>
        (
          await this.pages.adminPageUnpublish(
            { ...unsafe(), pageId: page.id, ifMatch: etag(page), idempotencyKey: key() },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  exportPage(id: string) {
    return this.translated(
      async () => (await this.pages.adminPageExport({ pageId: id }, { cache: "no-store" })).data,
    );
  }
}

export function createAdminPagesApi(fetchApi?: FetchAPI): AdminPagesApiBoundary {
  return new Boundary(
    new PageAdministrationApi(
      new Configuration({
        basePath: "",
        credentials: "same-origin",
        ...(fetchApi ? { fetchApi } : {}),
      }),
    ),
  );
}
export const adminPagesApi = createAdminPagesApi();
