import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  AnalyticsProvider,
  ContactPreference,
  FooterItemKind,
  LinkKind,
  LinkTarget,
  PublicProfileField,
  ThemePolicy,
  type FooterData,
  type NavigationData,
  type ProfileData,
  type SessionData,
  type WebsiteSettingsData,
} from "@/generated/api/src/models";
import { AuthContext, type AuthContextValue } from "@/features/auth/auth-context";
import { ApiError } from "@/lib/api";

import type { AdminSiteApiBoundary } from "./admin-api";
import { FooterEditor } from "./footer-editor";
import { NavigationEditor } from "./navigation-editor";
import { ProfileEditor } from "./profile-editor";
import { SettingsEditor } from "./settings-editor";

const action = vi.hoisted(() => ({ revalidate: vi.fn(async () => true) }));

vi.mock("./revalidate-public", () => ({
  revalidatePublicConfiguration: action.revalidate,
}));

const now = new Date("2026-08-03T08:00:00Z");

function profile(overrides: Partial<ProfileData> = {}): ProfileData {
  return {
    contactPreference: ContactPreference.None,
    createdAt: now,
    fullName: "Avery Example",
    id: "01989abc-def0-7000-8000-000000000301",
    publicFields: new Set([PublicProfileField.FullName]),
    updatedAt: now,
    version: 1,
    ...overrides,
  };
}

function settings(overrides: Partial<WebsiteSettingsData> = {}): WebsiteSettingsData {
  return {
    analyticsProvider: AnalyticsProvider.None,
    createdAt: now,
    defaultLocale: "en",
    id: "01989abc-def0-7000-8000-000000000302",
    themePolicy: ThemePolicy.System,
    timezone: "UTC",
    updatedAt: now,
    version: 1,
    websiteName: "Example Site",
    ...overrides,
  };
}

function navigation(
  linkKind: LinkKind = LinkKind.External,
  target: LinkTarget = LinkTarget.NewWindow,
): NavigationData {
  return {
    id: "01989abc-def0-7000-8000-000000000303",
    items: [
      {
        href: "https://example.test/work",
        id: "01989abc-def0-7000-8000-000000000311",
        label: "Work",
        linkKind,
        position: 0,
        target,
        version: 1,
        visible: true,
      },
    ],
    version: 1,
  };
}

function footer(
  linkKind: LinkKind = LinkKind.External,
  target: LinkTarget = LinkTarget.NewWindow,
): FooterData {
  return {
    columns: [
      {
        id: "01989abc-def0-7000-8000-000000000321",
        items: [
          {
            href: "https://example.test/privacy",
            id: "01989abc-def0-7000-8000-000000000322",
            itemKind: FooterItemKind.Legal,
            label: "Privacy",
            linkKind,
            position: 0,
            target,
            version: 1,
            visible: true,
          },
        ],
        position: 0,
        title: "Policies",
        version: 1,
        visible: true,
      },
    ],
    id: "01989abc-def0-7000-8000-000000000304",
    version: 1,
  };
}

function api(overrides: Partial<AdminSiteApiBoundary>): AdminSiteApiBoundary {
  return {
    getFooter: vi.fn(async () => ({ data: footer(), etag: '"v1"' })),
    getNavigation: vi.fn(async () => ({ data: navigation(), etag: '"v1"' })),
    getProfile: vi.fn(async () => ({ data: profile(), etag: '"v1"' })),
    getSettings: vi.fn(async () => ({ data: settings(), etag: '"v1"' })),
    replaceFooter: vi.fn(async () => ({ data: footer(), etag: '"v2"' })),
    replaceNavigation: vi.fn(async () => ({ data: navigation(), etag: '"v2"' })),
    updateProfile: vi.fn(async () => ({ data: profile(), etag: '"v2"' })),
    updateSettings: vi.fn(async () => ({ data: settings(), etag: '"v2"' })),
    ...overrides,
  };
}

function authContext(): AuthContextValue {
  const session: SessionData = {
    absoluteExpiresAt: new Date("2026-08-03T20:00:00Z"),
    administratorId: "01989abc-def0-7000-8000-000000000001",
    displayName: "Site Owner",
    idleExpiresAt: new Date("2026-08-03T09:00:00Z"),
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

function renderEditor(editor: ReactElement) {
  return render(<AuthContext.Provider value={authContext()}>{editor}</AuthContext.Provider>);
}

beforeEach(() => action.revalidate.mockClear());

describe("site configuration editors", () => {
  it("saves profile edits and the explicit publication allow-list using the loaded ETag", async () => {
    const user = userEvent.setup();
    const updateProfile = vi.fn<AdminSiteApiBoundary["updateProfile"]>(async (request) => ({
      data: profile({
        fullName: request.fullName ?? null,
        publicFields: request.publicFields ?? new Set(),
      }),
      etag: '"v2"',
    }));
    renderEditor(<ProfileEditor api={api({ updateProfile })} />);

    const name = await screen.findByRole("textbox", { name: "Full name" });
    await user.clear(name);
    await user.type(name, "Morgan Example");
    await user.click(screen.getByLabelText("Email address"));
    await user.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(updateProfile).toHaveBeenCalledOnce());
    const [request, etag] = updateProfile.mock.calls[0] ?? [];
    expect(etag).toBe('"v1"');
    expect(request?.fullName).toBe("Morgan Example");
    expect(request?.publicFields).toEqual(
      new Set([PublicProfileField.FullName, PublicProfileField.Email]),
    );
    await waitFor(() => expect(action.revalidate).toHaveBeenCalledWith("profile"));
  });

  it("retains profile edits and offers recovery after a concurrent update conflict", async () => {
    const user = userEvent.setup();
    const updateProfile = vi.fn<AdminSiteApiBoundary["updateProfile"]>(async () => {
      throw new ApiError({
        code: "RESOURCE_VERSION_CONFLICT",
        message: "The record changed.",
        status: 412,
      });
    });
    renderEditor(<ProfileEditor api={api({ updateProfile })} />);

    const name = await screen.findByRole("textbox", { name: "Full name" });
    await user.clear(name);
    await user.type(name, "Unsaved local edit");
    await user.click(screen.getByRole("button", { name: "Save profile" }));

    const conflict = await screen.findByRole("heading", {
      name: "This record changed elsewhere",
    });
    expect(conflict).toBeVisible();
    expect(conflict.parentElement).toHaveFocus();
    expect(name).toHaveValue("Unsaved local edit");
    expect(screen.getByRole("button", { name: "Reload current version" })).toBeVisible();
  });

  it("saves normalized website settings and refreshes the public site projection", async () => {
    const user = userEvent.setup();
    const updateSettings = vi.fn<AdminSiteApiBoundary["updateSettings"]>(async (request) => ({
      data: settings({ websiteName: request.websiteName ?? null }),
      etag: '"v2"',
    }));
    renderEditor(<SettingsEditor api={api({ updateSettings })} />);

    const websiteName = await screen.findByLabelText("Website name");
    await user.clear(websiteName);
    await user.type(websiteName, "Configured Site");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    await waitFor(() => expect(updateSettings).toHaveBeenCalledOnce());
    expect(updateSettings.mock.calls[0]?.[0].websiteName).toBe("Configured Site");
    expect(updateSettings.mock.calls[0]?.[1]).toBe('"v1"');
    await waitFor(() => expect(action.revalidate).toHaveBeenCalledWith("settings"));
  });

  it("forces same-window behavior when a navigation destination becomes internal", async () => {
    const user = userEvent.setup();
    const replaceNavigation = vi.fn<AdminSiteApiBoundary["replaceNavigation"]>(async (request) => ({
      data: navigation(
        request.items[0]?.linkKind ?? LinkKind.Internal,
        request.items[0]?.target ?? LinkTarget.SameWindow,
      ),
      etag: '"v2"',
    }));
    renderEditor(<NavigationEditor api={api({ replaceNavigation })} />);

    await screen.findByRole("heading", { name: "Primary navigation" });
    await user.selectOptions(screen.getByLabelText("Link type"), LinkKind.Internal);
    await user.clear(screen.getByLabelText("Destination"));
    await user.type(screen.getByLabelText("Destination"), "/about");
    await user.click(screen.getByRole("button", { name: "Save navigation" }));

    await waitFor(() => expect(replaceNavigation).toHaveBeenCalledOnce());
    const [request, etag, key] = replaceNavigation.mock.calls[0] ?? [];
    expect(request?.items[0]).toEqual(
      expect.objectContaining({
        href: "/about",
        linkKind: LinkKind.Internal,
        target: LinkTarget.SameWindow,
      }),
    );
    expect(etag).toBe('"v1"');
    expect(key).toEqual(expect.any(String));
  });

  it("forces same-window behavior when a footer destination becomes internal", async () => {
    const user = userEvent.setup();
    const replaceFooter = vi.fn<AdminSiteApiBoundary["replaceFooter"]>(async (request) => ({
      data: footer(
        request.columns[0]?.items[0]?.linkKind ?? LinkKind.Internal,
        request.columns[0]?.items[0]?.target ?? LinkTarget.SameWindow,
      ),
      etag: '"v2"',
    }));
    renderEditor(<FooterEditor api={api({ replaceFooter })} />);

    await screen.findByRole("heading", { name: "Footer", level: 1 });
    await user.selectOptions(screen.getByLabelText("Link type"), LinkKind.Internal);
    await user.clear(screen.getByLabelText("Destination"));
    await user.type(screen.getByLabelText("Destination"), "/privacy");
    await user.click(screen.getByRole("button", { name: "Save footer" }));

    await waitFor(() => expect(replaceFooter).toHaveBeenCalledOnce());
    expect(replaceFooter.mock.calls[0]?.[0].columns[0]?.items[0]).toEqual(
      expect.objectContaining({
        href: "/privacy",
        linkKind: LinkKind.Internal,
        target: LinkTarget.SameWindow,
      }),
    );
    expect(replaceFooter.mock.calls[0]?.[2]).toEqual(expect.any(String));
  });
});
