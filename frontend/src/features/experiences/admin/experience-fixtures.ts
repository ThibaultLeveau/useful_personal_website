import type {
  ExperienceData,
  ExperienceRevisionData,
  SessionData,
  SkillData,
} from "@/generated/api/src/models";
import type { AuthContextValue } from "@/features/auth/auth-context";

import type { AdminExperiencesApiBoundary } from "./admin-api";

export const fixtureNow = new Date("2026-08-03T08:00:00.000Z");

export const fixtureRevision: ExperienceRevisionData = {
  achievements: ["Reduced deployment time"],
  basedOnRevisionId: null,
  companyName: "Example Studio",
  companyUrl: "https://example.test",
  createdAt: fixtureNow,
  createdBy: "01989abc-def0-7000-8000-000000000001",
  currentPosition: true,
  detailedDescription: "Built a reliable delivery platform.",
  employmentType: "full_time",
  endDate: null,
  frozen: false,
  id: "01989abc-def0-7000-8000-000000000511",
  location: "Paris, France",
  remoteStatus: "hybrid",
  responsibilities: ["Led platform delivery"],
  revisionNumber: 1,
  roleTitle: "Staff Engineer",
  shortSummary: "Led the platform team.",
  skillIds: ["01989abc-def0-7000-8000-000000000401"],
  startDate: new Date("2024-01-01T00:00:00.000Z"),
  technologies: ["Python"],
  updatedAt: fixtureNow,
};

export const fixtureExperience: ExperienceData = {
  createdAt: fixtureNow,
  deletedAt: null,
  draft: fixtureRevision,
  id: "01989abc-def0-7000-8000-000000000501",
  lifecycle: "draft",
  position: 0,
  publishAt: null,
  published: null,
  unpublishedAt: null,
  updatedAt: fixtureNow,
  version: 1,
  visible: true,
};

export const fixtureSkill: SkillData = {
  categoryId: "01989abc-def0-7000-8000-000000000400",
  createdAt: fixtureNow,
  description: "Typed service boundaries.",
  featured: true,
  iconKey: null,
  id: "01989abc-def0-7000-8000-000000000401",
  name: "Python",
  position: 0,
  proficiencyLabel: "Advanced",
  proficiencyScore: 90,
  relationProvider: "unavailable",
  slug: "python",
  updatedAt: fixtureNow,
  version: 1,
  visible: true,
  yearsExperience: "7.50",
};

export function experienceBoundary(
  overrides: Partial<AdminExperiencesApiBoundary> = {},
): AdminExperiencesApiBoundary {
  return {
    create: async () => fixtureExperience,
    delete: async () => undefined,
    get: async () => ({
      experience: fixtureExperience,
      skills: [
        fixtureSkill,
        { ...fixtureSkill, id: "hidden-skill", name: "Internal", visible: false },
      ],
      timezone: "Europe/Paris",
    }),
    list: async () => ({
      items: [fixtureExperience],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: 1,
        totalPages: 1,
      },
    }),
    preview: async () => ({
      banner: "Draft preview - not public",
      experience: fixtureExperience,
      noindex: true,
    }),
    publish: async (item) => ({ ...item, lifecycle: "published", version: item.version + 1 }),
    reorder: async () => undefined,
    reschedule: async (item, publishAt) => ({
      ...item,
      lifecycle: "scheduled",
      publishAt,
      version: item.version + 1,
    }),
    save: async (item, input) => ({
      ...item,
      draft: { ...item.draft, ...input },
      version: item.version + 1,
    }),
    setVisibility: async (item, visible) => ({
      ...item,
      version: item.version + 1,
      visible,
    }),
    unpublish: async (item) => ({
      ...item,
      lifecycle: "unpublished",
      published: null,
      version: item.version + 1,
    }),
    ...overrides,
  };
}

export function authenticatedContext(): AuthContextValue {
  const session: SessionData = {
    absoluteExpiresAt: fixtureNow,
    administratorId: "01989abc-def0-7000-8000-000000000001",
    displayName: "Owner",
    idleExpiresAt: fixtureNow,
    mustChangePassword: false,
  };
  return {
    changePassword: async () => session,
    continueSession: async () => session,
    dismissExpiryWarning: () => undefined,
    expireSession: () => undefined,
    expiryWarning: false,
    login: async () => session,
    logout: async () => undefined,
    logoutUnconfirmed: false,
    session,
  };
}
