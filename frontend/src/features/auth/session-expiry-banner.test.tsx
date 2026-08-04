import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { SessionData } from "@/generated/api/src/models";

import { AuthContext, type AuthContextValue } from "./auth-context";
import { SessionExpiryBanner } from "./session-expiry-banner";

const session: SessionData = {
  absoluteExpiresAt: new Date("2026-08-03T08:00:00Z"),
  administratorId: "01989abc-def0-7000-8000-000000000001",
  displayName: "Site Owner",
  idleExpiresAt: new Date("2026-08-02T20:30:00Z"),
  mustChangePassword: false,
};

function context(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    changePassword: vi.fn(async () => session),
    continueSession: vi.fn(async () => session),
    dismissExpiryWarning: vi.fn(),
    expireSession: vi.fn(),
    expiryWarning: true,
    login: vi.fn(async () => session),
    logout: vi.fn(async () => undefined),
    logoutUnconfirmed: false,
    session,
    ...overrides,
  };
}

function renderBanner(value: AuthContextValue) {
  return render(
    <AuthContext.Provider value={value}>
      <SessionExpiryBanner />
    </AuthContext.Provider>,
  );
}

describe("session expiry banner", () => {
  it("is absent until the boundary enters its warning window", () => {
    renderBanner(context({ expiryWarning: false }));
    expect(screen.queryByText("Your session will expire soon")).not.toBeInTheDocument();
  });

  it("continues the session and supports dismissing the warning", async () => {
    const user = userEvent.setup();
    const continueSession = vi.fn(async () => session);
    const dismissExpiryWarning = vi.fn();
    renderBanner(context({ continueSession, dismissExpiryWarning }));

    await user.click(screen.getByRole("button", { name: "Continue session" }));
    expect(continueSession).toHaveBeenCalledOnce();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(dismissExpiryWarning).toHaveBeenCalledOnce();
  });

  it("announces a refresh failure and permits a safe retry", async () => {
    const user = userEvent.setup();
    const continueSession = vi
      .fn<AuthContextValue["continueSession"]>()
      .mockRejectedValueOnce(new Error("offline detail"))
      .mockResolvedValueOnce(session);
    renderBanner(context({ continueSession }));

    await user.click(screen.getByRole("button", { name: "Continue session" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The session could not be continued. Try again.",
    );
    expect(screen.queryByText("offline detail")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Continue session" }));
    await waitFor(() => expect(continueSession).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
