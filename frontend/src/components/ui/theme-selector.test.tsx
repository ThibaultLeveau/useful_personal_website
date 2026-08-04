import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeSelector } from "./theme-selector";

describe("ThemeSelector", () => {
  it("persists and applies a named theme preference", async () => {
    const user = userEvent.setup();
    render(<ThemeSelector />);

    const selector = screen.getByRole("combobox", { name: "Theme" });
    await waitFor(() => expect(selector).toBeEnabled());
    await user.selectOptions(selector, "dark");

    await waitFor(() => expect(document.documentElement).toHaveAttribute("data-theme", "dark"));
    expect(document.documentElement).toHaveAttribute("data-theme-preference", "dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
    expect(window.localStorage.getItem("upw-theme")).toBe("dark");
  });

  it("hydrates from a stored preference before enabling interaction", async () => {
    window.localStorage.setItem("upw-theme", "dark");
    render(<ThemeSelector />);

    const selector = screen.getByRole("combobox", { name: "Theme" });
    await waitFor(() => expect(selector).toBeEnabled());
    expect(selector).toHaveValue("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  });
});
