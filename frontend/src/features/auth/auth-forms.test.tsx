import axe from "axe-core";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

import { ChangePasswordForm } from "./change-password-form";
import { LoginForm } from "./login-form";

describe("login form", () => {
  it("focuses a linked error summary and moves focus to invalid fields", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn();
    render(<LoginForm onLogin={onLogin} />);

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    const alert = screen.getByRole("alert");
    expect(alert).toHaveFocus();
    const emailLink = screen.getByRole("link", { name: "Enter your administrator email." });
    expect(emailLink).toHaveAttribute("href", "#admin-email");
    await user.click(emailLink);
    expect(screen.getByLabelText("Administrator email")).toHaveFocus();
    const passwordLink = screen.getByRole("link", { name: "Enter your password." });
    await user.click(passwordLink);
    expect(screen.getByLabelText("Password")).toHaveFocus();
    expect(onLogin).not.toHaveBeenCalled();
  });

  it("permits paste/reveal and presents non-enumerating authentication failure", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn(async () => {
      throw new ApiError({
        code: "AUTHENTICATION_FAILED",
        details: { unsafe_email_exists: true },
        message: "backend detail",
        requestId: "request-safe",
        status: 401,
      });
    });
    render(<LoginForm onLogin={onLogin} />);

    await user.type(screen.getByLabelText("Administrator email"), "owner@example.test");
    const password = screen.getByLabelText("Password");
    fireEvent.paste(password, { clipboardData: { getData: () => "pasted-private-password" } });
    fireEvent.change(password, { target: { value: "pasted-private-password" } });
    await user.click(screen.getByRole("button", { name: "Show password" }));
    expect(password).toHaveAttribute("type", "text");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("The email or password is incorrect.")).toBeVisible();
    expect(screen.queryByText("backend detail")).not.toBeInTheDocument();
    expect(screen.queryByText(/unsafe_email_exists/u)).not.toBeInTheDocument();
    expect(window.localStorage).toHaveLength(0);
  });

  it("has no automated accessibility violations in its initial state", async () => {
    const { container } = render(<LoginForm onLogin={vi.fn()} />);
    // jsdom has no layout/canvas implementation, so contrast is exercised by
    // the built-app Playwright + axe matrix instead of being silently guessed here.
    expect(
      (
        await axe.run(container, {
          rules: { "color-contrast": { enabled: false } },
        })
      ).violations,
    ).toEqual([]);
  });
});

describe("change-password form", () => {
  it("links every summary error to its field and supports focus navigation", async () => {
    const user = userEvent.setup();
    render(<ChangePasswordForm forced onChangePassword={vi.fn()} onLogout={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(screen.getByRole("alert")).toHaveFocus();

    for (const [message, label] of [
      ["Enter your current password.", "Initial password"],
      ["Enter a new password.", "New password"],
      ["Confirm the new password.", "Confirm new password"],
    ] as const) {
      const link = screen.getByRole("link", { name: message });
      await user.click(link);
      expect(screen.getByLabelText(label)).toHaveFocus();
    }
  });

  it("preserves values after mismatch, permits reveal, and submits matching values", async () => {
    const user = userEvent.setup();
    const onChangePassword = vi.fn(async () => undefined);
    render(<ChangePasswordForm onChangePassword={onChangePassword} onLogout={vi.fn()} />);

    await user.type(screen.getByLabelText("Current password"), "initial-password");
    await user.type(screen.getByLabelText("New password"), "replacement-password");
    await user.type(screen.getByLabelText("Confirm new password"), "different-password");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(screen.getByLabelText("New password")).toHaveValue("replacement-password");
    expect(screen.getAllByText("The new passwords do not match.")).toHaveLength(2);

    await user.clear(screen.getByLabelText("Confirm new password"));
    await user.type(screen.getByLabelText("Confirm new password"), "replacement-password");
    await user.click(screen.getByRole("button", { name: "Show new password" }));
    expect(screen.getByLabelText("New password")).toHaveAttribute("type", "text");
    await user.click(screen.getByRole("button", { name: "Change password" }));

    await waitFor(() =>
      expect(onChangePassword).toHaveBeenCalledWith({
        currentPassword: "initial-password",
        newPassword: "replacement-password",
      }),
    );
    expect(screen.getByLabelText("Current password")).toHaveValue("");
    expect(window.localStorage).toHaveLength(0);
  });
});
