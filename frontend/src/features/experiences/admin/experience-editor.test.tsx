import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "@/features/auth/auth-context";

import type { AdminExperiencesApiBoundary } from "./admin-api";
import { ExperienceEditor } from "./experience-editor";
import { authenticatedContext, experienceBoundary, fixtureExperience } from "./experience-fixtures";

describe("experience editor", () => {
  it("retains cross-tab state, controls dates, relations, and ordered content", async () => {
    const user = userEvent.setup();
    const save = vi.fn<AdminExperiencesApiBoundary["save"]>(async (item, input) => ({
      ...item,
      draft: { ...item.draft, ...input },
      version: 2,
    }));
    render(
      <AuthContext.Provider value={authenticatedContext()}>
        <ExperienceEditor api={experienceBoundary({ save })} experienceId={fixtureExperience.id} />
      </AuthContext.Provider>,
    );
    expect(await screen.findByRole("heading", { name: "Staff Engineer", level: 1 })).toBeVisible();
    expect(screen.getByLabelText("End date")).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: "Current position" }));
    expect(screen.getByLabelText("End date")).toBeEnabled();
    await user.click(screen.getByRole("tab", { name: "Relations" }));
    await user.click(screen.getByRole("checkbox", { name: /Internal/ }));
    expect(screen.getByText(/1 selected skill is hidden/)).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Content" }));
    expect(screen.getByRole("checkbox", { name: "Current position" })).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    await waitFor(() => expect(save).toHaveBeenCalled());
    expect(save.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({
        currentPosition: false,
        skillIds: expect.arrayContaining(["hidden-skill"]),
      }),
    );
  });

  it("focuses linked local validation without discarding input", async () => {
    const user = userEvent.setup();
    render(
      <AuthContext.Provider value={authenticatedContext()}>
        <ExperienceEditor api={experienceBoundary()} experienceId={fixtureExperience.id} />
      </AuthContext.Provider>,
    );
    const company = await screen.findByRole("textbox", { name: "Company" });
    await user.clear(company);
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a company name");
    expect(company).toHaveValue("");
  });
});
