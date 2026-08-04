import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "@/features/auth/auth-context";

import type { AdminExperiencesApiBoundary } from "./admin-api";
import { authenticatedContext, experienceBoundary, fixtureExperience } from "./experience-fixtures";
import { ExperienceManager } from "./experience-manager";

describe("experience manager", () => {
  it("renders lifecycle and visibility with text and exposes the complete workflow", async () => {
    render(
      <AuthContext.Provider value={authenticatedContext()}>
        <ExperienceManager api={experienceBoundary()} />
      </AuthContext.Provider>,
    );
    expect(await screen.findByRole("heading", { name: "Experience ledger" })).toBeVisible();
    expect(document.querySelector('[data-state="draft"]')).toHaveTextContent("Draft");
    expect(screen.getByText("◆ Visible")).toBeVisible();
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      `/admin/experiences/${fixtureExperience.id}/edit`,
    );
    expect(screen.getByRole("link", { name: "Preview draft" })).toBeVisible();
  });

  it("submits allow-listed search and lifecycle filters", async () => {
    const user = userEvent.setup();
    const list = vi.fn<AdminExperiencesApiBoundary["list"]>(async () => ({
      items: [fixtureExperience],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: 1,
        totalPages: 1,
      },
    }));
    render(
      <AuthContext.Provider value={authenticatedContext()}>
        <ExperienceManager api={experienceBoundary({ list })} />
      </AuthContext.Provider>,
    );
    await screen.findByRole("heading", { name: "Experience ledger" });
    await user.type(screen.getByRole("searchbox", { name: "Search" }), "platform");
    await user.selectOptions(screen.getByRole("combobox", { name: "Lifecycle" }), "draft");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() =>
      expect(list).toHaveBeenLastCalledWith({ lifecycle: "draft", search: "platform" }),
    );
  });
});
