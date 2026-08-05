import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AdminHealthData, SuccessEnvelopeAdminHealthData } from "@/generated/api/src/models";
import { ApiError, type AdminHealthApiBoundary } from "@/lib/api";

import { AuthContext, type AuthContextValue } from "../auth/auth-context";
import { HealthPanel } from "./health-panel";

const replace = vi.fn();
const router = { replace };

vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/health",
  useRouter: () => router,
}));

function healthData(overrides: Partial<AdminHealthData> = {}): AdminHealthData {
  return {
    applicationStatus: "operational",
    buildCommit: "abcdef1",
    buildVersion: "1.2.3",
    checkedAt: new Date("2026-08-03T08:00:00Z"),
    databaseStatus: "operational",
    migrationStatus: "current",
    status: "operational",
    ...overrides,
  };
}

function envelope(data = healthData()): SuccessEnvelopeAdminHealthData {
  return { data, meta: { requestId: "health-response" } };
}

function boundary(get: AdminHealthApiBoundary["get"]): AdminHealthApiBoundary {
  return { get };
}

beforeEach(() => replace.mockReset());

describe("administrator health panel", () => {
  it("renders a text-plus-color operational summary with build and checked time", async () => {
    render(<HealthPanel api={boundary(vi.fn(async () => envelope()))} />);

    expect(await screen.findByRole("heading", { name: "System status" })).toBeVisible();
    expect(screen.getAllByText("Operational").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText("1.2.3")).toBeVisible();
    expect(screen.getByText("abcdef1")).toBeVisible();
    expect(screen.getByRole("button", { name: "Refresh status" })).toBeEnabled();
  });

  it("explains degraded dependency state without infrastructure detail", async () => {
    const data = healthData({
      databaseStatus: "unavailable",
      migrationStatus: "unknown",
      status: "degraded",
    });
    render(<HealthPanel api={boundary(vi.fn(async () => envelope(data)))} />);

    expect(await screen.findByText("Degraded")).toBeVisible();
    expect(
      screen.getByText("a required dependency needs attention", { exact: false }),
    ).toBeVisible();
    expect(screen.getAllByText("Unavailable")).toHaveLength(1);
    expect(screen.getByText("Unknown", { exact: true })).toBeVisible();
    expect(screen.queryByText(/hostname|postgresql|sql/i)).not.toBeInTheDocument();
  });

  it("distinguishes unavailable and unknown failures with safe recovery guidance", async () => {
    const unavailable = boundary(
      vi.fn(async () => {
        throw new ApiError({
          code: "API_UNAVAILABLE",
          message: "The API could not be reached.",
          requestId: "health-request-1",
          status: 0,
        });
      }),
    );
    const { rerender } = render(<HealthPanel api={unavailable} />);

    expect(await screen.findByText("Unavailable")).toBeVisible();
    expect(screen.getByText("Request ID: health-request-1")).toBeVisible();
    expect(screen.getByRole("link", { name: "Open API documentation" })).toHaveAttribute(
      "href",
      "/api/v1/docs",
    );

    rerender(
      <HealthPanel
        api={boundary(
          vi.fn(async () => {
            throw new Error("sensitive transport detail");
          }),
        )}
      />,
    );
    expect(await screen.findByText("Unknown")).toBeVisible();
  });

  it("routes an initially expired session without rendering health details", async () => {
    render(
      <HealthPanel
        api={boundary(
          vi.fn(async () => {
            throw new ApiError({
              code: "AUTHENTICATION_REQUIRED",
              message: "Authentication is required.",
              status: 401,
            });
          }),
        )}
      />,
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Protected health details were cleared",
    );
    expect(replace).toHaveBeenCalledWith("/admin/session-expired?return_to=%2Fadmin%2Fhealth");
    expect(screen.queryByRole("heading", { name: "System status" })).not.toBeInTheDocument();
  });

  it("routes forced-password sessions before rendering health details", async () => {
    render(
      <HealthPanel
        api={boundary(
          vi.fn(async () => {
            throw new ApiError({
              code: "PASSWORD_CHANGE_REQUIRED",
              message: "The password must be changed.",
              status: 403,
            });
          }),
        )}
      />,
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Protected health details were cleared",
    );
    expect(replace).toHaveBeenCalledWith("/admin/change-password");
    expect(screen.queryByText("abcdef1")).not.toBeInTheDocument();
  });

  it("announces a successful refresh and replaces a degraded snapshot", async () => {
    const get = vi
      .fn<AdminHealthApiBoundary["get"]>()
      .mockResolvedValueOnce(envelope(healthData({ status: "degraded" })))
      .mockResolvedValueOnce(envelope());
    const user = userEvent.setup();
    render(<HealthPanel api={boundary(get)} />);
    await screen.findByText("Degraded");

    await user.click(screen.getByRole("button", { name: "Refresh status" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Health status refreshed. Operational.",
    );
    expect(screen.getAllByText("Operational").length).toBeGreaterThanOrEqual(3);
    expect(screen.queryByText("Stale result")).not.toBeInTheDocument();
  });

  it("retains a stale result while disabling only the refresh control", async () => {
    let rejectRefresh: ((reason: ApiError) => void) | undefined;
    const get = vi
      .fn<AdminHealthApiBoundary["get"]>()
      .mockResolvedValueOnce(envelope())
      .mockImplementationOnce(
        () =>
          new Promise((_, reject) => {
            rejectRefresh = reject;
          }),
      );
    const user = userEvent.setup();
    render(<HealthPanel api={boundary(get)} />);
    await screen.findByText("abcdef1");

    await user.click(screen.getByRole("button", { name: "Refresh status" }));
    expect(screen.getByRole("button", { name: "Refreshing…" })).toBeDisabled();
    expect(screen.getByRole("link", { name: "Review account" })).toHaveAttribute(
      "href",
      "/admin/account",
    );
    rejectRefresh?.(
      new ApiError({
        code: "DEPENDENCY_UNAVAILABLE",
        message: "A dependency is unavailable.",
        requestId: "refresh-request",
        status: 503,
      }),
    );

    expect(await screen.findByText("Stale result")).toBeVisible();
    expect(screen.getByText("abcdef1")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Health refresh failed. The previous result is marked stale.",
    );
  });

  it("clears privileged content before redirecting an expired session", async () => {
    const get = vi
      .fn<AdminHealthApiBoundary["get"]>()
      .mockResolvedValueOnce(envelope())
      .mockRejectedValueOnce(
        new ApiError({
          code: "AUTHENTICATION_REQUIRED",
          message: "Authentication is required.",
          status: 401,
        }),
      );
    const user = userEvent.setup();
    const expireSession = vi.fn();
    const session = {
      absoluteExpiresAt: new Date("2026-08-03T20:00:00Z"),
      administratorId: "01989abc-def0-7000-8000-000000000001",
      displayName: "Site Owner",
      idleExpiresAt: new Date("2026-08-03T09:00:00Z"),
      mustChangePassword: false,
    };
    const context: AuthContextValue = {
      changePassword: vi.fn(async () => session),
      continueSession: vi.fn(async () => session),
      dismissExpiryWarning: vi.fn(),
      expireSession,
      expiryWarning: false,
      login: vi.fn(async () => session),
      logout: vi.fn(async () => undefined),
      logoutUnconfirmed: false,
      session,
    };
    render(
      <AuthContext.Provider value={context}>
        <HealthPanel api={boundary(get)} />
      </AuthContext.Provider>,
    );
    await screen.findByText("abcdef1");

    await user.click(screen.getByRole("button", { name: "Refresh status" }));

    await waitFor(() => expect(expireSession).toHaveBeenCalledOnce());
    expect(replace).not.toHaveBeenCalled();
    expect(screen.queryByText("abcdef1")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Protected health details were cleared");
  });
});
