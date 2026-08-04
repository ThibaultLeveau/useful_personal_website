"use client";

import { ExperiencesApi } from "@/generated/api/src/apis/ExperiencesApi";
import { ProjectsApi, type AdminProjectsListRequest } from "@/generated/api/src/apis/ProjectsApi";
import { PublicSiteApi } from "@/generated/api/src/apis/PublicSiteApi";
import { SkillsApi } from "@/generated/api/src/apis/SkillsApi";
import type {
  ExperienceData,
  PaginationData,
  ProjectCreateRequest,
  ProjectData,
  ProjectInput,
  ProjectPreviewData,
  SkillData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";

export interface ProjectListSnapshot {
  items: ProjectData[];
  pagination: PaginationData;
}
export interface ProjectEditorSnapshot {
  project: ProjectData;
  projects: ProjectData[];
  skills: SkillData[];
  experiences: ExperienceData[];
  timezone: string;
}
export interface ProjectReferenceSnapshot {
  projects: ProjectData[];
  skills: SkillData[];
  experiences: ExperienceData[];
  timezone: string;
}
export interface AdminProjectsApiBoundary {
  create(input: ProjectCreateRequest): Promise<ProjectData>;
  delete(item: ProjectData): Promise<void>;
  get(id: string): Promise<ProjectEditorSnapshot>;
  list(filters?: AdminProjectsListRequest): Promise<ProjectListSnapshot>;
  preview(id: string): Promise<ProjectPreviewData>;
  references(): Promise<ProjectReferenceSnapshot>;
  publish(item: ProjectData, publishAt?: Date): Promise<ProjectData>;
  reorder(items: ProjectData[]): Promise<void>;
  reschedule(item: ProjectData, publishAt: Date): Promise<ProjectData>;
  save(item: ProjectData, input: ProjectInput): Promise<ProjectData>;
  setFeatured(item: ProjectData, featured: boolean): Promise<ProjectData>;
  setVisibility(item: ProjectData, visible: boolean): Promise<ProjectData>;
  unpublish(item: ProjectData): Promise<ProjectData>;
}

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
      if (name !== CSRF_COOKIE_NAME) continue;
      try {
        const value = decodeURIComponent(raw.join("="));
        if (value) return value;
      } catch {
        break;
      }
    }
  throw new ApiError({
    code: "CSRF_MISSING",
    message: "The protected session could not be verified.",
    status: 401,
  });
}

const unsafeHeaders = () => ({ origin: browserOrigin(), xCSRFToken: csrfToken() });
function idempotencyKey(): string {
  if (typeof crypto === "undefined" || typeof crypto.randomUUID !== "function")
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  return crypto.randomUUID();
}
const etag = (item: ProjectData) => `"v${item.version}"`;

class GeneratedAdminProjectsBoundary implements AdminProjectsApiBoundary {
  constructor(
    private readonly projects: ProjectsApi,
    private readonly skills: SkillsApi,
    private readonly experiences: ExperiencesApi,
    private readonly site: PublicSiteApi,
  ) {}
  private async translated<Value>(operation: () => Promise<Value>): Promise<Value> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }
  list(filters: AdminProjectsListRequest = {}): Promise<ProjectListSnapshot> {
    return this.translated(async () => {
      const result = await this.projects.adminProjectsList(
        { page: 1, pageSize: 50, sort: "position", ...filters },
        { cache: "no-store" },
      );
      return { items: result.data, pagination: result.meta.pagination };
    });
  }
  create(input: ProjectCreateRequest): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectCreate(
            { ...unsafeHeaders(), idempotencyKey: idempotencyKey(), projectCreateRequest: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  async get(id: string): Promise<ProjectEditorSnapshot> {
    return this.translated(async () => {
      const [project, projects, skills, experiences, site] = await Promise.all([
        this.projects.adminProjectGet({ projectId: id }, { cache: "no-store" }),
        this.projects.adminProjectsList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.skills.adminSkillsList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.experiences.adminExperiencesList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.site.publicSiteGet({ cache: "no-store" }),
      ]);
      return {
        project: project.data,
        projects: projects.data,
        skills: skills.data,
        experiences: experiences.data,
        timezone: site.data.timezone,
      };
    });
  }
  async references(): Promise<ProjectReferenceSnapshot> {
    return this.translated(async () => {
      const [projects, skills, experiences, site] = await Promise.all([
        this.projects.adminProjectsList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.skills.adminSkillsList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.experiences.adminExperiencesList(
          { page: 1, pageSize: 100, sort: "position" },
          { cache: "no-store" },
        ),
        this.site.publicSiteGet({ cache: "no-store" }),
      ]);
      return {
        projects: projects.data,
        skills: skills.data,
        experiences: experiences.data,
        timezone: site.data.timezone,
      };
    });
  }
  preview(id: string): Promise<ProjectPreviewData> {
    return this.translated(
      async () =>
        (await this.projects.adminProjectPreview({ projectId: id }, { cache: "no-store" })).data,
    );
  }
  save(item: ProjectData, input: ProjectInput): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectDraftUpdate(
            { ...unsafeHeaders(), projectId: item.id, ifMatch: etag(item), projectInput: input },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  publish(item: ProjectData, publishAt?: Date): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectPublish(
            {
              ...unsafeHeaders(),
              projectId: item.id,
              ifMatch: etag(item),
              idempotencyKey: idempotencyKey(),
              publishProjectRequest: publishAt ? { publishAt } : {},
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  reschedule(item: ProjectData, publishAt: Date): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectReschedule(
            {
              ...unsafeHeaders(),
              projectId: item.id,
              ifMatch: etag(item),
              idempotencyKey: idempotencyKey(),
              rescheduleProjectRequest: { publishAt },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  unpublish(item: ProjectData): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectUnpublish(
            {
              ...unsafeHeaders(),
              projectId: item.id,
              ifMatch: etag(item),
              idempotencyKey: idempotencyKey(),
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  setVisibility(item: ProjectData, visible: boolean): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectVisibilityUpdate(
            {
              ...unsafeHeaders(),
              projectId: item.id,
              ifMatch: etag(item),
              visibilityRequest: { visible },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  setFeatured(item: ProjectData, featured: boolean): Promise<ProjectData> {
    return this.translated(
      async () =>
        (
          await this.projects.adminProjectFeaturedUpdate(
            {
              ...unsafeHeaders(),
              projectId: item.id,
              ifMatch: etag(item),
              featuredRequest: { featured },
            },
            { cache: "no-store" },
          )
        ).data,
    );
  }
  async reorder(items: ProjectData[]): Promise<void> {
    await this.translated(() =>
      this.projects.adminProjectsReorder(
        {
          ...unsafeHeaders(),
          ifMatch: etag(items[0] ?? ({ version: 1 } as ProjectData)),
          idempotencyKey: idempotencyKey(),
          reorderProjectsRequest: { orderedIds: items.map((item) => item.id) },
        },
        { cache: "no-store" },
      ),
    );
  }
  async delete(item: ProjectData): Promise<void> {
    await this.translated(() =>
      this.projects.adminProjectDelete(
        { ...unsafeHeaders(), projectId: item.id, ifMatch: etag(item) },
        { cache: "no-store" },
      ),
    );
  }
}

export function createAdminProjectsApi(fetchApi?: FetchAPI): AdminProjectsApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminProjectsBoundary(
    new ProjectsApi(configuration),
    new SkillsApi(configuration),
    new ExperiencesApi(configuration),
    new PublicSiteApi(configuration),
  );
}

export const adminProjectsApi = createAdminProjectsApi();
