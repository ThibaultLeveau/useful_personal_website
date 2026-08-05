"use client";

import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import {
  AnalyticsProvider,
  ThemePolicy,
  type SocialLinkInput,
  type WebsiteSettingsData,
  type WebsiteSettingsUpdateRequest,
} from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import { MediaPicker } from "@/features/media/media-picker";
import { ApiError } from "@/lib/api";

import { adminSiteApi, type AdminSiteApiBoundary } from "./admin-api";
import {
  FormStatus,
  optional,
  splitLines,
  toApiError,
  UnsavedChangesGuard,
  useDeferredInitialLoad,
} from "./configuration-form";
import styles from "./configuration.module.css";
import { revalidatePublicConfiguration } from "./revalidate-public";

interface SettingsDraft {
  accentColor: string;
  analyticsProvider: (typeof AnalyticsProvider)[keyof typeof AnalyticsProvider];
  analyticsPublicId: string;
  contactEmail: string;
  contactPhone: string;
  defaultDescription: string;
  defaultLocale: string;
  defaultTitle: string;
  faviconMediaId: string | null;
  logoMediaId: string | null;
  primaryColor: string;
  publicAvailability: string;
  seoDescription: string;
  seoTitleSuffix: string;
  socialImageMediaId: string | null;
  socialLinks: string;
  themePolicy: (typeof ThemePolicy)[keyof typeof ThemePolicy];
  timezone: string;
  websiteName: string;
}

function text(value?: string | null): string {
  return value ?? "";
}

function draftFrom(data: WebsiteSettingsData): SettingsDraft {
  return {
    accentColor: text(data.accentColor),
    analyticsProvider: data.analyticsProvider ?? AnalyticsProvider.None,
    analyticsPublicId: text(data.analyticsPublicId),
    contactEmail: text(data.contactEmail),
    contactPhone: text(data.contactPhone),
    defaultDescription: text(data.defaultDescription),
    defaultLocale: data.defaultLocale ?? "en",
    defaultTitle: text(data.defaultTitle),
    faviconMediaId: data.faviconMediaId ?? null,
    logoMediaId: data.logoMediaId ?? null,
    primaryColor: text(data.primaryColor),
    publicAvailability: text(data.publicAvailability),
    seoDescription: text(data.seoDescription),
    seoTitleSuffix: text(data.seoTitleSuffix),
    socialImageMediaId: data.socialImageMediaId ?? null,
    socialLinks: (data.socialLinks ?? []).map((link) => `${link.label} | ${link.url}`).join("\n"),
    themePolicy: data.themePolicy ?? ThemePolicy.System,
    timezone: data.timezone ?? "UTC",
    websiteName: text(data.websiteName),
  };
}

function links(value: string): SocialLinkInput[] {
  return splitLines(value).map((line) => {
    const separator = line.indexOf("|");
    return separator < 1
      ? { label: line, url: "" }
      : {
          label: line.slice(0, separator).trim(),
          url: line.slice(separator + 1).trim(),
        };
  });
}

function requestFrom(draft: SettingsDraft): WebsiteSettingsUpdateRequest {
  return {
    accentColor: optional(draft.accentColor),
    analyticsProvider: draft.analyticsProvider,
    analyticsPublicId: optional(draft.analyticsPublicId),
    contactEmail: optional(draft.contactEmail),
    contactPhone: optional(draft.contactPhone),
    defaultDescription: optional(draft.defaultDescription),
    defaultLocale: draft.defaultLocale.trim(),
    defaultTitle: optional(draft.defaultTitle),
    faviconMediaId: draft.faviconMediaId,
    logoMediaId: draft.logoMediaId,
    primaryColor: optional(draft.primaryColor),
    publicAvailability: optional(draft.publicAvailability),
    seoDescription: optional(draft.seoDescription),
    seoTitleSuffix: optional(draft.seoTitleSuffix),
    socialImageMediaId: draft.socialImageMediaId,
    socialLinks: links(draft.socialLinks),
    themePolicy: draft.themePolicy,
    timezone: draft.timezone.trim(),
    websiteName: optional(draft.websiteName),
  };
}

export function SettingsEditor({ api = adminSiteApi }: { api?: AdminSiteApiBoundary }) {
  const auth = useAuth();
  const [draft, setDraft] = useState<SettingsDraft | null>(null);
  const [etag, setEtag] = useState("");
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resource = await api.getSettings();
      setDraft(draftFrom(resource.data));
      setEtag(resource.etag);
      setDirty(false);
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setLoading(false);
    }
  }, [api, auth]);

  useDeferredInitialLoad(load);

  const update = useCallback(
    <Key extends keyof SettingsDraft>(key: Key, value: SettingsDraft[Key]) => {
      setDraft((current) => (current ? { ...current, [key]: value } : current));
      setDirty(true);
      setSaved(null);
    },
    [],
  );

  const request = useMemo(() => (draft ? requestFrom(draft) : null), [draft]);
  const save = useCallback(async (): Promise<boolean> => {
    if (!request || !etag) return false;
    setSaving(true);
    setError(null);
    setSaved(null);
    try {
      const resource = await api.updateSettings(request, etag);
      setDraft(draftFrom(resource.data));
      setEtag(resource.etag);
      setDirty(false);
      const refreshed = await revalidatePublicConfiguration("settings");
      setSaved(
        refreshed
          ? "Website settings saved. Public metadata and shell data are refreshing."
          : "Website settings saved. Public pages will refresh within one minute.",
      );
      return true;
    } catch (caught) {
      const next = toApiError(caught);
      setError(next);
      if (next.status === 401) auth.expireSession();
      return false;
    } finally {
      setSaving(false);
    }
  }, [api, auth, etag, request]);

  if (loading) return <LoadingPanel label="Loading website settings" />;
  if (!draft || !request) {
    return (
      <section className={styles.notice}>
        <p>The website settings could not be loaded.</p>
        <Button onClick={() => void load()} variant="secondary">
          Try again
        </Button>
      </section>
    );
  }

  return (
    <>
      <header className={styles.pageHeader}>
        <div>
          <p className="eyebrow">Configuration / Website</p>
          <h1>Website settings</h1>
          <p>Manage public identity, locale, theme policy, SEO defaults, and public identifiers.</p>
        </div>
      </header>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          void save();
        }}
      >
        <FormStatus error={error} saved={saved} />
        {error?.code === "RESOURCE_VERSION_CONFLICT" ? (
          <div className="button-row">
            <Button onClick={() => void load()} type="button" variant="secondary">
              Reload current version
            </Button>
            <Button
              onClick={() => void navigator.clipboard.writeText(JSON.stringify(request, null, 2))}
              type="button"
              variant="quiet"
            >
              Copy my changes
            </Button>
          </div>
        ) : null}
        <section className={styles.section}>
          <h2>Identity and defaults</h2>
          <div className={styles.fieldGrid}>
            <Field
              label="Website name"
              value={draft.websiteName}
              onChange={(value) => update("websiteName", value)}
            />
            <Field
              label="Default page title"
              value={draft.defaultTitle}
              onChange={(value) => update("defaultTitle", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              label="Default description"
              multiline
              value={draft.defaultDescription}
              onChange={(value) => update("defaultDescription", value)}
            />
            <Field
              label="Default locale"
              value={draft.defaultLocale}
              onChange={(value) => update("defaultLocale", value)}
            />
            <Field
              label="IANA timezone"
              value={draft.timezone}
              onChange={(value) => update("timezone", value)}
            />
            <label className={styles.field}>
              <span>Initial theme policy</span>
              <select
                value={draft.themePolicy}
                onChange={(event) =>
                  update("themePolicy", event.target.value as SettingsDraft["themePolicy"])
                }
              >
                <option value={ThemePolicy.System}>Follow system</option>
                <option value={ThemePolicy.Light}>Light</option>
                <option value={ThemePolicy.Dark}>Dark</option>
              </select>
            </label>
            <Field
              hint="Six-digit hex, for example #315C87"
              label="Primary color"
              value={draft.primaryColor}
              onChange={(value) => update("primaryColor", value)}
            />
            <Field
              hint="Six-digit hex, for example #C56A3A"
              label="Accent color"
              value={draft.accentColor}
              onChange={(value) => update("accentColor", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Public contact</h2>
          <div className={styles.fieldGrid}>
            <Field
              label="Contact email"
              type="email"
              value={draft.contactEmail}
              onChange={(value) => update("contactEmail", value)}
            />
            <Field
              label="Contact phone"
              type="tel"
              value={draft.contactPhone}
              onChange={(value) => update("contactPhone", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              hint="One per line: Label | https://example.test/profile"
              label="Social links"
              multiline
              value={draft.socialLinks}
              onChange={(value) => update("socialLinks", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              label="Public availability"
              value={draft.publicAvailability}
              onChange={(value) => update("publicAvailability", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Search defaults</h2>
          <div className={styles.fieldGrid}>
            <Field
              label="SEO title suffix"
              value={draft.seoTitleSuffix}
              onChange={(value) => update("seoTitleSuffix", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              label="SEO description"
              multiline
              value={draft.seoDescription}
              onChange={(value) => update("seoDescription", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Public analytics identifier</h2>
          <p className={styles.sectionDescription}>
            This stores an allow-listed public identifier only. It does not inject scripts or store
            credentials.
          </p>
          <div className={styles.fieldGrid}>
            <label className={styles.field}>
              <span>Provider</span>
              <select
                value={draft.analyticsProvider}
                onChange={(event) =>
                  update(
                    "analyticsProvider",
                    event.target.value as SettingsDraft["analyticsProvider"],
                  )
                }
              >
                <option value={AnalyticsProvider.None}>None</option>
                <option value={AnalyticsProvider.Plausible}>Plausible</option>
                <option value={AnalyticsProvider.GoogleAnalytics}>Google Analytics</option>
              </select>
            </label>
            <Field
              label="Public identifier"
              value={draft.analyticsPublicId}
              onChange={(value) => update("analyticsPublicId", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Brand media</h2>
          <div className={styles.fieldGrid}>
            <MediaPicker
              description="Used as the public site logo after this save commits."
              disabled={saving}
              label="Logo"
              onChange={(value) => update("logoMediaId", value)}
              value={draft.logoMediaId}
            />
            <MediaPicker
              description="A decorative browser and shortcut icon source."
              disabled={saving}
              label="Favicon"
              onChange={(value) => update("faviconMediaId", value)}
              value={draft.faviconMediaId}
            />
            <MediaPicker
              description="Default preview image for public link metadata."
              disabled={saving}
              label="Social preview"
              onChange={(value) => update("socialImageMediaId", value)}
              value={draft.socialImageMediaId}
            />
          </div>
        </section>
        <div className={styles.actionBar}>
          <Button disabled={saving} type="submit">
            {saving ? "Saving…" : "Save settings"}
          </Button>
          <Button
            disabled={!dirty || saving}
            onClick={() => void load()}
            type="button"
            variant="quiet"
          >
            Discard changes
          </Button>
          <UnsavedChangesGuard dirty={dirty} onSave={save} />
        </div>
      </form>
    </>
  );
}

function Field({
  className,
  hint,
  label,
  multiline = false,
  onChange,
  type = "text",
  value,
}: {
  className?: string;
  hint?: string;
  label: string;
  multiline?: boolean;
  onChange: (value: string) => void;
  type?: "email" | "tel" | "text";
  value: string;
}) {
  return (
    <label className={`${styles.field} ${className ?? ""}`}>
      <span>{label}</span>
      {multiline ? (
        <textarea onChange={(event) => onChange(event.target.value)} value={value} />
      ) : (
        <input onChange={(event) => onChange(event.target.value)} type={type} value={value} />
      )}
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}
