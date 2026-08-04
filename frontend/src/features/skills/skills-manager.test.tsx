import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { SessionData, SkillCategoryData, SkillData } from "@/generated/api/src/models";
import { AuthContext, type AuthContextValue } from "@/features/auth/auth-context";

import type { AdminSkillsApiBoundary } from "./admin-api";
import { SkillsManager, slugify } from "./skills-manager";

const now = new Date("2026-08-03T08:00:00Z");
const category: SkillCategoryData = {
  createdAt: now,
  id: "01989abc-def0-7000-8000-000000000401",
  name: "Backend",
  position: 0,
  slug: "backend",
  updatedAt: now,
  version: 1,
};
const skill: SkillData = {
  categoryId: category.id,
  createdAt: now,
  description: null,
  featured: true,
  iconKey: null,
  id: "01989abc-def0-7000-8000-000000000402",
  name: "Python",
  position: 0,
  proficiencyLabel: "Advanced",
  proficiencyScore: 90,
  relationProvider: "unavailable",
  slug: "python",
  updatedAt: now,
  version: 1,
  visible: true,
  yearsExperience: "6.50",
};

function boundary(overrides: Partial<AdminSkillsApiBoundary> = {}): AdminSkillsApiBoundary {
  return {
    createCategory: vi.fn(async (input) => ({ ...category, ...input })),
    createSkill: vi.fn(async () => skill),
    deleteCategory: vi.fn(async () => undefined),
    deleteSkill: vi.fn(async () => undefined),
    load: vi.fn(async () => ({
      categories: [category],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: 1,
        totalPages: 1,
      },
      skills: [skill],
    })),
    reorderCategories: vi.fn(async (items) => items),
    reorderSkills: vi.fn(async (_categoryId, items) => items),
    updateCategory: vi.fn(async (item, input) => ({ ...item, ...input, version: 2 })),
    updateSkill: vi.fn(async (item) => ({ ...item, version: 2 })),
    ...overrides,
  };
}

function auth(): AuthContextValue {
  const session: SessionData = {
    absoluteExpiresAt: now,
    administratorId: "01989abc-def0-7000-8000-000000000001",
    displayName: "Owner",
    idleExpiresAt: now,
    mustChangePassword: false,
  };
  return {
    changePassword: vi.fn(async () => session),
    continueSession: vi.fn(async () => session),
    dismissExpiryWarning: vi.fn(),
    expireSession: vi.fn(),
    expiryWarning: false,
    login: vi.fn(async () => session),
    logout: vi.fn(async () => undefined),
    logoutUnconfirmed: false,
    session,
  };
}

describe("skills manager", () => {
  it("loads complete admin data and exposes relation providers as unavailable", async () => {
    render(
      <AuthContext.Provider value={auth()}>
        <SkillsManager api={boundary()} />
      </AuthContext.Provider>,
    );
    expect(await screen.findByRole("heading", { name: "Capability catalog" })).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText(/Unavailable until the Projects/)).toBeInTheDocument();
    expect(screen.getByLabelText("Associated projects")).toBeDisabled();
  });

  it("previews normalized slugs and submits a new category", async () => {
    const user = userEvent.setup();
    const createCategory = vi.fn<AdminSkillsApiBoundary["createCategory"]>(async (input) => ({
      ...category,
      ...input,
    }));
    render(
      <AuthContext.Provider value={auth()}>
        <SkillsManager api={boundary({ createCategory })} />
      </AuthContext.Provider>,
    );

    const name = (await screen.findAllByRole("textbox", { name: "Name" }))[0];
    expect(name).toBeDefined();
    if (!name) throw new Error("new-category name input is missing");
    await user.type(name, "Data & AI");
    expect(screen.getAllByRole("textbox", { name: "Slug" })[0]).toHaveValue("data-ai");
    await user.click(screen.getByRole("button", { name: "Add category" }));

    await waitFor(() =>
      expect(createCategory).toHaveBeenCalledWith(expect.objectContaining({ slug: "data-ai" })),
    );
    expect(slugify("Crème brûlée")).toBe("creme-brulee");
  });
});
