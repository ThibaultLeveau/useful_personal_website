import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import type { ReactNode } from "react";

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

import type { AdminSiteApiBoundary } from "./admin-api";
import { FooterEditor } from "./footer-editor";
import { NavigationEditor } from "./navigation-editor";
import { ProfileEditor } from "./profile-editor";
import { SettingsEditor } from "./settings-editor";

const now = new Date("2026-08-03T08:00:00Z");

const profile: ProfileData = {
  availability: "Available for carefully scoped collaborations",
  contactPreference: ContactPreference.Email,
  createdAt: now,
  email: "avery@example.test",
  fullName: "Avery Example",
  id: "01989abc-def0-7000-8000-000000000301",
  professionalTitle: "Software and AI engineer",
  publicFields: new Set([PublicProfileField.FullName, PublicProfileField.ProfessionalTitle]),
  shortBiography: "Builds dependable tools for people doing complex work.",
  updatedAt: now,
  version: 1,
};

const settings: WebsiteSettingsData = {
  accentColor: "#C56A3A",
  analyticsProvider: AnalyticsProvider.None,
  createdAt: now,
  defaultDescription: "A fictional, privacy-aware engineering portfolio.",
  defaultLocale: "en",
  id: "01989abc-def0-7000-8000-000000000302",
  primaryColor: "#315C87",
  themePolicy: ThemePolicy.System,
  timezone: "Europe/Paris",
  updatedAt: now,
  version: 1,
  websiteName: "Avery Example",
};

const navigation: NavigationData = {
  id: "01989abc-def0-7000-8000-000000000303",
  items: [
    {
      href: "/",
      id: "01989abc-def0-7000-8000-000000000311",
      label: "Home",
      linkKind: LinkKind.Internal,
      position: 0,
      target: LinkTarget.SameWindow,
      version: 1,
      visible: true,
    },
    {
      href: "/about",
      id: "01989abc-def0-7000-8000-000000000312",
      label: "About",
      linkKind: LinkKind.Internal,
      position: 1,
      target: LinkTarget.SameWindow,
      version: 1,
      visible: true,
    },
  ],
  version: 1,
};

const footer: FooterData = {
  columns: [
    {
      id: "01989abc-def0-7000-8000-000000000321",
      items: [
        {
          href: "/about",
          id: "01989abc-def0-7000-8000-000000000322",
          itemKind: FooterItemKind.Link,
          label: "About",
          linkKind: LinkKind.Internal,
          position: 0,
          target: LinkTarget.SameWindow,
          version: 1,
          visible: true,
        },
      ],
      position: 0,
      title: "Explore",
      version: 1,
      visible: true,
    },
  ],
  copyrightText: "Fictional demonstration content.",
  id: "01989abc-def0-7000-8000-000000000304",
  version: 1,
};

function api(): AdminSiteApiBoundary {
  return {
    getFooter: async () => ({ data: footer, etag: '"v1"' }),
    getNavigation: async () => ({ data: navigation, etag: '"v1"' }),
    getProfile: async () => ({ data: profile, etag: '"v1"' }),
    getSettings: async () => ({ data: settings, etag: '"v1"' }),
    replaceFooter: async () => ({ data: footer, etag: '"v2"' }),
    replaceNavigation: async () => ({ data: navigation, etag: '"v2"' }),
    updateProfile: async () => ({ data: profile, etag: '"v2"' }),
    updateSettings: async () => ({ data: settings, etag: '"v2"' }),
  };
}

function Authenticated({ children }: { children: ReactNode }) {
  const session: SessionData = {
    absoluteExpiresAt: new Date("2026-08-03T20:00:00Z"),
    administratorId: "01989abc-def0-7000-8000-000000000001",
    displayName: "Site Owner",
    idleExpiresAt: new Date("2026-08-03T09:00:00Z"),
    mustChangePassword: false,
  };
  const value: AuthContextValue = {
    changePassword: async () => session,
    continueSession: async () => session,
    dismissExpiryWarning: () => undefined,
    expireSession: () => undefined,
    expiryWarning: false,
    login: async () => session,
    logout: async () => undefined,
    logoutUnconfirmed: false,
    session,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

const meta = {
  title: "Administration/Site configuration",
  parameters: { layout: "fullscreen" },
  decorators: [
    (Story) => (
      <Authenticated>
        <main className="admin-main">
          <Story />
        </main>
      </Authenticated>
    ),
  ],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Profile: Story = { render: () => <ProfileEditor api={api()} /> };
export const WebsiteSettings: Story = { render: () => <SettingsEditor api={api()} /> };
export const Navigation: Story = { render: () => <NavigationEditor api={api()} /> };
export const Footer: Story = { render: () => <FooterEditor api={api()} /> };
