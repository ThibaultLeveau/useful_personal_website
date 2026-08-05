"use client";

import {
  ExperiencesApi,
  type AdminExperiencesListRequest,
} from "@/generated/api/src/apis/ExperiencesApi";
import { PublicSiteApi } from "@/generated/api/src/apis/PublicSiteApi";
import { SkillsApi } from "@/generated/api/src/apis/SkillsApi";
import type {
  ExperienceCreateRequest,
  ExperienceData,
  ExperienceInput,
  ExperiencePreviewData,
  PaginationData,
  SkillData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";

export interface ExperienceListSnapshot {
  items: ExperienceData[];
  pagination: PaginationData;
}

export interface ExperienceEditorSnapshot {
  experience: ExperienceData;
  skills: SkillData[];
  timezone: string;
}

export interface AdminExperiencesApiBoundary {
  create(input: ExperienceCreateRequest): Promise<ExperienceData>;
  delete(item: ExperienceData): Promise<void>;
  get(id: string): Promise<ExperienceEditorSnapshot>;
  list(filters?: AdminExperiencesListRequest): Promise<ExperienceListSnapshot>;
  preview(id: string): Promise<ExperiencePreviewData>;
  publish(item: ExperienceData, publishAt?: Date): Promise<ExperienceData>;
  reorder(items: ExperienceData[]): Promise<void>;
  reschedule(item: ExperienceData, publishAt: Date): Promise<ExperienceData>;
  save(item: ExperienceData, input: ExperienceInput): Promise<ExperienceData>;
  setVisibility(item: ExperienceData, visible: boolean): Promise<ExperienceData>;
  unpublish(item: ExperienceData): Promise<ExperienceData>;
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

function unsafeHeaders() {
  return { origin: browserOrigin(), xCSRFToken: csrfToken() };
}

function idempotencyKey(): string {
  if (typeof crypto === "undefined" || typeof crypto.randomUUID !== "function") {
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  }
  return crypto.randomUUID();
}

function etag(item: ExperienceData): string {
  return `"v${item.version}"`;
}

class GeneratedAdminExperiencesBoundary implements AdminExperiencesApiBoundary {
  constructor(
    private readonly experiences: ExperiencesApi,
    private readonly skills: SkillsApi,
    private readonly publicSite: PublicSiteApi,
  ) {}

  private async translated<Value>(operation: () => Promise<Value>): Promise<Value> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  list(filters: AdminExperiencesListRequest = {}): Promise<ExperienceListSnapshot> {
    return this.translated(async () => {
      const result = await this.experiences.adminExperiencesList(
        { page: 1, pageSize: 20, sort: "position", ...filters },
        { cache: "no-store" },
      );
      return { items: result.data, pagination: result.meta.pagination };
    });
  }

  create(input: ExperienceCreateRequest): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperienceCreate(
            {
              ...unsafeHeaders(),
              experienceCreateRequest: input,
              idempotencyKey: idempotencyKey(),
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  get(id: string): Promise<ExperienceEditorSnapshot> {
    return this.translated(async () => {
      const [experience, skills, site] = await Promise.all([
        this.experiences.adminExperienceGet({ experienceId: id }, { cache: "no-store" }),
        this.skills.adminSkillsList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.publicSite.publicSiteGet({ cache: "no-store" }),
      ]);
      return {
        experience: experience.data,
        skills: skills.data,
        timezone: site.data.timezone,
      };
    });
  }

  preview(id: string): Promise<ExperiencePreviewData> {
    return this.translated(async () => {
      const result = await this.experiences.adminExperiencePreview(
        { experienceId: id },
        { cache: "no-store" },
      );
      return result.data;
    });
  }

  save(item: ExperienceData, input: ExperienceInput): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperienceDraftUpdate(
            {
              ...unsafeHeaders(),
              experienceId: item.id,
              experienceInput: input,
              ifMatch: etag(item),
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  publish(item: ExperienceData, publishAt?: Date): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperiencePublish(
            {
              ...unsafeHeaders(),
              experienceId: item.id,
              idempotencyKey: idempotencyKey(),
              ifMatch: etag(item),
              publishExperienceRequest: publishAt ? { publishAt } : {},
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  reschedule(item: ExperienceData, publishAt: Date): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperienceReschedule(
            {
              ...unsafeHeaders(),
              experienceId: item.id,
              idempotencyKey: idempotencyKey(),
              ifMatch: etag(item),
              rescheduleExperienceRequest: { publishAt },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  unpublish(item: ExperienceData): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperienceUnpublish(
            {
              ...unsafeHeaders(),
              experienceId: item.id,
              idempotencyKey: idempotencyKey(),
              ifMatch: etag(item),
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  setVisibility(item: ExperienceData, visible: boolean): Promise<ExperienceData> {
    return this.translated(
      async () =>
        (
          await this.experiences.adminExperienceVisibilityUpdate(
            {
              ...unsafeHeaders(),
              experienceId: item.id,
              ifMatch: etag(item),
              visibilityRequest: { visible },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }

  async reorder(items: ExperienceData[]): Promise<void> {
    await this.translated(() =>
      this.experiences.adminExperiencesReorder(
        {
          ...unsafeHeaders(),
          idempotencyKey: idempotencyKey(),
          ifMatch: etag(items[0] ?? ({ version: 1 } as ExperienceData)),
          reorderExperiencesRequest: { orderedIds: items.map((item) => item.id) },
        },
        { cache: "no-store" },
      ),
    );
  }

  async delete(item: ExperienceData): Promise<void> {
    await this.translated(() =>
      this.experiences.adminExperienceDelete(
        { ...unsafeHeaders(), experienceId: item.id, ifMatch: etag(item) },
        { cache: "no-store" },
      ),
    );
  }
}

export function createAdminExperiencesApi(fetchApi?: FetchAPI): AdminExperiencesApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminExperiencesBoundary(
    new ExperiencesApi(configuration),
    new SkillsApi(configuration),
    new PublicSiteApi(configuration),
  );
}

export const adminExperiencesApi = createAdminExperiencesApi();
