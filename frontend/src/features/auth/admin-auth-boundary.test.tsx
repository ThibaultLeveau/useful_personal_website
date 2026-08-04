import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SessionData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import { AdminAuthBoundary } from "./admin-auth-boundary";
import type { AuthApiBoundary } from "./api";
import { AccountScreen, ChangePasswordScreen, LoginScreen } from "./screens";

let pathname = "/admin";
const replace = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ replace }),
}));

function session(overrides: Partial<SessionData> = {}): SessionData {
  return {
    absoluteExpiresAt: new Date("2026-08-03T08:00:00Z"),
    administratorId: "01989abc-def0-7000-8000-000000000001",
    displayName: "Site Owner",
    idleExpiresAt: new Date("2026-08-02T20:30:00Z"),
    mustChangePassword: false,
    ...overrides,
  };
}

function authApi(overrides: Partial<AuthApiBoundary> = {}): AuthApiBoundary {
  return {
    changePassword: vi.fn(async () => session()),
    getSession: vi.fn(async () => session()),
    login: vi.fn(async () => session()),
    logout: vi.fn(async () => undefined),
    refreshSession: vi.fn(async () => session()),
    ...overrides,
  };
}

function boundary(api: AuthApiBoundary, children: ReactNode = <p>Protected record</p>) {
  return (
    <AdminAuthBoundary api={api} now={() => new Date("2026-08-02T20:00:00Z").getTime()}>
      {children}
    </AdminAuthBoundary>
  );
}

beforeEach(() => {
  pathname = "/admin";
  replace.mockReset();
});

describe("administrator auth boundary", () => {
  it("keeps protected DOM hidden and redirects a signed-out request to a safe local login", async () => {
    const api = authApi({
      getSession: vi.fn(async () => {
        throw new ApiError({
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          status: 401,
        });
      }),
    });

    render(boundary(api));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/admin/login?return_to=%2Fadmin"));
    expect(screen.queryByText("Protected record")).not.toBeInTheDocument();
    expect(screen.getByText("Redirecting to secure sign in…")).toBeVisible();
  });

  it("blocks the ordinary shell until the initial password is changed", async () => {
    const api = authApi({ getSession: vi.fn(async () => session({ mustChangePassword: true })) });

    render(boundary(api));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/admin/change-password"));
    expect(screen.queryByText("Protected record")).not.toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Administration" })).not.toBeInTheDocument();
  });

  it("renders authenticated content with discoverable account and sign-out actions", async () => {
    render(boundary(authApi()));

    expect(await screen.findByText("Protected record")).toBeVisible();
    expect(screen.getByRole("link", { name: "Account" })).toHaveAttribute("href", "/admin/account");
    expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
  });

  it("removes protected DOM and routes to the expired screen when the idle timer elapses", async () => {
    vi.useFakeTimers();
    try {
      await act(async () => {
        render(boundary(authApi()));
      });
      expect(screen.getByText("Protected record")).toBeVisible();

      act(() => vi.advanceTimersByTime(30 * 60 * 1000));

      expect(screen.queryByText("Protected record")).not.toBeInTheDocument();
      expect(replace).toHaveBeenCalledWith("/admin/session-expired?return_to=%2Fadmin");
      expect(replace).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it("clears protected state when session refresh reports an authentication failure", async () => {
    pathname = "/admin/account";
    const user = userEvent.setup();
    const api = authApi({
      refreshSession: vi.fn(async () => {
        throw new ApiError({
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          status: 401,
        });
      }),
    });

    render(boundary(api, <AccountScreen />));
    await user.click(await screen.findByRole("button", { name: "Continue session" }));

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/admin/session-expired?return_to=%2Fadmin%2Faccount"),
    );
    expect(replace).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("heading", { name: "Account security" })).not.toBeInTheDocument();
  });

  it("keeps content hidden on a non-auth session-check failure and recovers through retry", async () => {
    const user = userEvent.setup();
    const getSession = vi
      .fn<AuthApiBoundary["getSession"]>()
      .mockRejectedValueOnce(
        new ApiError({ code: "API_UNAVAILABLE", message: "offline", status: 0 }),
      )
      .mockResolvedValueOnce(session());

    render(boundary(authApi({ getSession })));

    expect(
      await screen.findByRole("heading", { name: "The session could not be checked" }),
    ).toBeVisible();
    expect(screen.queryByText("Protected record")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Protected record")).toBeVisible();
    expect(getSession).toHaveBeenCalledTimes(2);
  });

  it("enters the ordinary shell after a successful forced password change", async () => {
    pathname = "/admin/change-password";
    const user = userEvent.setup();
    const api = authApi({
      changePassword: vi.fn(async () => session({ mustChangePassword: false })),
      getSession: vi.fn(async () => session({ mustChangePassword: true })),
    });
    const view = render(boundary(api, <ChangePasswordScreen />));

    await user.type(await screen.findByLabelText("Initial password"), "initial-password");
    await user.type(screen.getByLabelText("New password"), "replacement-password");
    await user.type(screen.getByLabelText("Confirm new password"), "replacement-password");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/admin"));

    pathname = "/admin";
    view.rerender(boundary(api));
    expect(await screen.findByText("Protected record")).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Administration" })).toBeVisible();
  });

  it("clears protected DOM immediately and exposes a safe logout retry after network failure", async () => {
    const user = userEvent.setup();
    const logout = vi
      .fn<AuthApiBoundary["logout"]>()
      .mockRejectedValueOnce(
        new ApiError({ code: "API_UNAVAILABLE", message: "offline", status: 0 }),
      )
      .mockResolvedValueOnce(undefined);
    const api = authApi({ logout });
    const view = render(boundary(api));

    expect(await screen.findByText("Protected record")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Sign out" }));
    expect(screen.queryByText("Protected record")).not.toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/admin/login");

    pathname = "/admin/login";
    view.rerender(boundary(api, <LoginScreen />));
    expect(await screen.findByText("Server sign-out was not confirmed")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry server sign out" }));
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.queryByText("Server sign-out was not confirmed")).not.toBeInTheDocument(),
    );
  });
});
