import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  MediaFormat,
  MediaOwnerType,
  MediaStatus,
  MediaUsageRole,
  VariantPurpose,
  type MediaAssetData,
  type SessionData,
} from "@/generated/api/src/models";
import { AuthContext, type AuthContextValue } from "@/features/auth/auth-context";

import type { AdminMediaApiBoundary } from "./admin-api";
import { MediaLibrary } from "./media-library";

const now = new Date("2026-08-04T10:00:00Z");
const asset: MediaAssetData = {
  byteSize: 42_000,
  createdAt: now,
  detectedFormat: MediaFormat.Jpeg,
  displayName: "Portrait",
  height: 800,
  id: "01989abc-def0-7000-8000-000000000901",
  status: MediaStatus.Ready,
  updatedAt: now,
  variants: [
    {
      adminUrl: "/api/v1/admin/media/01989abc-def0-7000-8000-000000000901/content?width=640",
      byteSize: 12_000,
      contentType: "image/webp",
      format: MediaFormat.Webp,
      height: 640,
      purpose: VariantPurpose.ResponsiveWebp,
      width: 640,
    },
  ],
  version: 1,
  width: 1200,
};

function boundary(overrides: Partial<AdminMediaApiBoundary> = {}): AdminMediaApiBoundary {
  return {
    delete: vi.fn(async () => undefined),
    list: vi.fn(async () => ({
      items: [asset],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: 1,
        totalPages: 1,
      },
    })),
    rename: vi.fn(async (item, displayName) => ({ ...item, displayName, version: 2 })),
    upload: vi.fn(async () => asset),
    usage: vi.fn(async () => []),
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

function renderLibrary(api: AdminMediaApiBoundary) {
  return render(
    <AuthContext.Provider value={auth()}>
      <MediaLibrary api={api} />
    </AuthContext.Provider>,
  );
}

describe("media library", () => {
  it("performs the deferred initial load once instead of remounting the workspace", async () => {
    const list = vi.fn<AdminMediaApiBoundary["list"]>(async () => ({
      items: [asset],
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: 1,
        totalPages: 1,
      },
    }));
    renderLibrary(boundary({ list }));

    expect(await screen.findByRole("heading", { name: "Media library" })).toBeInTheDocument();
    await new Promise((resolve) => window.setTimeout(resolve, 25));
    expect(list).toHaveBeenCalledTimes(1);
  });

  it("loads, inspects usage, and renames with the current version", async () => {
    const user = userEvent.setup();
    const rename = vi.fn<AdminMediaApiBoundary["rename"]>(async (item, displayName) => ({
      ...item,
      displayName,
      version: 2,
    }));
    const api = boundary({ rename });
    renderLibrary(api);

    expect(await screen.findByRole("heading", { name: "Media library" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Portrait/ }));
    expect(await screen.findByText("Not currently assigned.")).toBeInTheDocument();
    const name = screen.getByRole("textbox", { name: "Display name" });
    await user.clear(name);
    await user.type(name, "Editorial portrait");
    await user.click(screen.getByRole("button", { name: "Save name" }));
    await waitFor(() => expect(rename).toHaveBeenCalledWith(asset, "Editorial portrait"));
    expect(await screen.findByText("Display name saved.")).toBeInTheDocument();
  });

  it("keeps deletion disabled while an active usage exists", async () => {
    const api = boundary({
      usage: vi.fn(async () => [
        {
          active: true,
          ownerId: "01989abc-def0-7000-8000-000000000902",
          ownerType: MediaOwnerType.Profile,
          position: 0,
          _public: true,
          role: MediaUsageRole.ProfileImage,
        },
      ]),
    });
    const user = userEvent.setup();
    renderLibrary(api);
    await user.click(await screen.findByRole("button", { name: /Portrait/ }));
    expect(await screen.findByText("profile / profile image")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete media" })).toBeDisabled();
    expect(screen.getByText(/Remove all active usages/)).toBeInTheDocument();
  });

  it("does not report an asset as unassigned while usage is loading", async () => {
    let resolveUsage: ((value: []) => void) | undefined;
    const usage = vi.fn(
      () =>
        new Promise<[]>((resolve) => {
          resolveUsage = resolve;
        }),
    );
    const user = userEvent.setup();
    renderLibrary(boundary({ usage }));

    await user.click(await screen.findByRole("button", { name: /Portrait/ }));
    expect(screen.getByText("Loading usage…")).toBeInTheDocument();
    expect(screen.queryByText("Not currently assigned.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete media" })).toBeDisabled();

    resolveUsage?.([]);
    expect(await screen.findByText("Not currently assigned.")).toBeInTheDocument();
  });
});
