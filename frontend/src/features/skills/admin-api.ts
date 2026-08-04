"use client";

import { SkillsApi, type AdminSkillsListRequest } from "@/generated/api/src/apis/SkillsApi";
import type {
  PaginationData,
  SkillCategoryData,
  SkillCategoryInput,
  SkillData,
  SkillInput,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";

export interface SkillsSnapshot {
  categories: SkillCategoryData[];
  pagination: PaginationData;
  skills: SkillData[];
}

export interface AdminSkillsApiBoundary {
  createCategory(input: SkillCategoryInput): Promise<SkillCategoryData>;
  createSkill(input: SkillInput): Promise<SkillData>;
  deleteCategory(category: SkillCategoryData): Promise<void>;
  deleteSkill(skill: SkillData): Promise<void>;
  load(filters?: AdminSkillsListRequest): Promise<SkillsSnapshot>;
  reorderCategories(categories: SkillCategoryData[]): Promise<SkillCategoryData[]>;
  reorderSkills(categoryId: string, skills: SkillData[]): Promise<SkillData[]>;
  updateCategory(
    category: SkillCategoryData,
    input: SkillCategoryInput,
  ): Promise<SkillCategoryData>;
  updateSkill(skill: SkillData, input: SkillInput): Promise<SkillData>;
}

function browserOrigin(): string {
  if (typeof window === "undefined") {
    throw new ApiError({
      code: "AUTH_BROWSER_REQUIRED",
      message: "Open this editor in a browser.",
      status: 0,
    });
  }
  return window.location.origin;
}

function csrfToken(): string {
  if (typeof document !== "undefined") {
    for (const part of document.cookie.split(";")) {
      const [name, ...raw] = part.trim().split("=");
      if (name !== CSRF_COOKIE_NAME) continue;
      try {
        const value = decodeURIComponent(raw.join("="));
        if (value) return value;
      } catch {
        break;
      }
    }
  }
  throw new ApiError({
    code: "CSRF_MISSING",
    message: "The protected session could not be verified.",
    status: 401,
  });
}

function requestHeaders() {
  return { origin: browserOrigin(), xCSRFToken: csrfToken() };
}

function key(): string {
  if (typeof crypto === "undefined" || typeof crypto.randomUUID !== "function") {
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  }
  return crypto.randomUUID();
}

function etag(version: number): string {
  return `"v${version}"`;
}

class GeneratedAdminSkillsBoundary implements AdminSkillsApiBoundary {
  constructor(private readonly generated: SkillsApi) {}

  private async translated<Value>(operation: () => Promise<Value>): Promise<Value> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async load(filters: AdminSkillsListRequest = {}): Promise<SkillsSnapshot> {
    return this.translated(async () => {
      const [categories, skills] = await Promise.all([
        this.generated.adminSkillCategoriesList({ cache: "no-store" }),
        this.generated.adminSkillsList(
          { page: 1, pageSize: 20, sort: "position", ...filters },
          { cache: "no-store" },
        ),
      ]);
      return {
        categories: categories.data.items,
        pagination: skills.meta.pagination,
        skills: skills.data,
      };
    });
  }

  createCategory(input: SkillCategoryInput): Promise<SkillCategoryData> {
    return this.translated(
      async () =>
        (
          await this.generated.adminSkillCategoryCreate(
            {
              ...requestHeaders(),
              idempotencyKey: key(),
              skillCategoryInput: input,
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  updateCategory(
    category: SkillCategoryData,
    input: SkillCategoryInput,
  ): Promise<SkillCategoryData> {
    return this.translated(
      async () =>
        (
          await this.generated.adminSkillCategoryUpdate(
            {
              ...requestHeaders(),
              categoryId: category.id,
              ifMatch: etag(category.version),
              skillCategoryInput: input,
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  async deleteCategory(category: SkillCategoryData): Promise<void> {
    await this.translated(() =>
      this.generated.adminSkillCategoryDelete(
        {
          ...requestHeaders(),
          categoryId: category.id,
          ifMatch: etag(category.version),
        },
        { cache: "no-store" },
      ),
    );
  }

  reorderCategories(categories: SkillCategoryData[]): Promise<SkillCategoryData[]> {
    return this.translated(async () => {
      const result = await this.generated.adminSkillCategoriesReorder(
        {
          ...requestHeaders(),
          idempotencyKey: key(),
          ifMatch: etag(categories[0]?.version ?? 1),
          reorderRequest: { orderedIds: categories.map((item) => item.id) },
        },
        { cache: "no-store" },
      );
      return result.data.items;
    });
  }

  createSkill(input: SkillInput): Promise<SkillData> {
    return this.translated(
      async () =>
        (
          await this.generated.adminSkillCreate(
            { ...requestHeaders(), idempotencyKey: key(), skillInput: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  updateSkill(skill: SkillData, input: SkillInput): Promise<SkillData> {
    return this.translated(
      async () =>
        (
          await this.generated.adminSkillUpdate(
            {
              ...requestHeaders(),
              ifMatch: etag(skill.version),
              skillId: skill.id,
              skillInput: input,
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  async deleteSkill(skill: SkillData): Promise<void> {
    await this.translated(() =>
      this.generated.adminSkillDelete(
        { ...requestHeaders(), ifMatch: etag(skill.version), skillId: skill.id },
        { cache: "no-store" },
      ),
    );
  }

  reorderSkills(categoryId: string, skills: SkillData[]): Promise<SkillData[]> {
    return this.translated(async () => {
      const result = await this.generated.adminCategorySkillsReorder(
        {
          ...requestHeaders(),
          categoryId,
          idempotencyKey: key(),
          ifMatch: etag(skills[0]?.version ?? 1),
          reorderRequest: { orderedIds: skills.map((item) => item.id) },
        },
        { cache: "no-store" },
      );
      return result.data.items;
    });
  }
}

export function createAdminSkillsApi(fetchApi?: FetchAPI): AdminSkillsApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminSkillsBoundary(new SkillsApi(configuration));
}

export const adminSkillsApi = createAdminSkillsApi();
