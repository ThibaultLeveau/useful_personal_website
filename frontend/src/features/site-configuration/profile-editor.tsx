"use client";

import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { LoadingPanel } from "@/components/ui/loading-panel";
import {
  ContactPreference,
  PublicProfileField,
  type ProfileData,
  type ProfileUpdateRequest,
  type SocialLinkInput,
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

const PUBLIC_FIELDS = [
  [PublicProfileField.FullName, "Full name"],
  [PublicProfileField.ProfessionalTitle, "Professional title"],
  [PublicProfileField.ShortBiography, "Short biography"],
  [PublicProfileField.FullBiography, "Full biography"],
  [PublicProfileField.Location, "Location"],
  [PublicProfileField.Availability, "Availability"],
  [PublicProfileField.Email, "Email address"],
  [PublicProfileField.SocialLinks, "Social links"],
  [PublicProfileField.GithubUrl, "GitHub link"],
  [PublicProfileField.LinkedinUrl, "LinkedIn link"],
  [PublicProfileField.PersonalValues, "Personal values"],
  [PublicProfileField.WorkPreferences, "Work preferences"],
  [PublicProfileField.ResumeUrl, "Résumé link"],
  [PublicProfileField.ContactPreference, "Contact preference"],
] as const;

interface ProfileDraft {
  availability: string;
  contactPreference: (typeof ContactPreference)[keyof typeof ContactPreference];
  email: string;
  fullBiography: string;
  fullName: string;
  githubUrl: string;
  linkedinUrl: string;
  location: string;
  personalValues: string;
  profileImageId: string | null;
  professionalTitle: string;
  publicFields: Set<(typeof PublicProfileField)[keyof typeof PublicProfileField]>;
  resumeUrl: string;
  shortBiography: string;
  socialLinks: string;
  workPreferences: string;
}

function text(value?: string | null): string {
  return value ?? "";
}

function draftFrom(data: ProfileData): ProfileDraft {
  return {
    availability: text(data.availability),
    contactPreference: data.contactPreference ?? ContactPreference.None,
    email: text(data.email),
    fullBiography: text(data.fullBiography),
    fullName: text(data.fullName),
    githubUrl: text(data.githubUrl),
    linkedinUrl: text(data.linkedinUrl),
    location: text(data.location),
    personalValues: (data.personalValues ?? []).join("\n"),
    profileImageId: data.profileImageId ?? null,
    professionalTitle: text(data.professionalTitle),
    publicFields: new Set(data.publicFields ?? []),
    resumeUrl: text(data.resumeUrl),
    shortBiography: text(data.shortBiography),
    socialLinks: (data.socialLinks ?? []).map((link) => `${link.label} | ${link.url}`).join("\n"),
    workPreferences: (data.workPreferences ?? []).join("\n"),
  };
}

function socialLinks(value: string): SocialLinkInput[] {
  return splitLines(value).map((line) => {
    const separator = line.indexOf("|");
    if (separator < 1) return { label: line, url: "" };
    return {
      label: line.slice(0, separator).trim(),
      url: line.slice(separator + 1).trim(),
    };
  });
}

function requestFrom(draft: ProfileDraft): ProfileUpdateRequest {
  return {
    availability: optional(draft.availability),
    contactPreference: draft.contactPreference,
    email: optional(draft.email),
    fullBiography: optional(draft.fullBiography),
    fullName: optional(draft.fullName),
    githubUrl: optional(draft.githubUrl),
    linkedinUrl: optional(draft.linkedinUrl),
    location: optional(draft.location),
    personalValues: splitLines(draft.personalValues),
    profileImageId: draft.profileImageId,
    professionalTitle: optional(draft.professionalTitle),
    publicFields: draft.publicFields,
    resumeUrl: optional(draft.resumeUrl),
    shortBiography: optional(draft.shortBiography),
    socialLinks: socialLinks(draft.socialLinks),
    workPreferences: splitLines(draft.workPreferences),
  };
}

export function ProfileEditor({ api = adminSiteApi }: { api?: AdminSiteApiBoundary }) {
  const auth = useAuth();
  const [draft, setDraft] = useState<ProfileDraft | null>(null);
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
      const resource = await api.getProfile();
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
    <Key extends keyof ProfileDraft>(key: Key, value: ProfileDraft[Key]) => {
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
      const resource = await api.updateProfile(request, etag);
      setDraft(draftFrom(resource.data));
      setEtag(resource.etag);
      setDirty(false);
      const refreshed = await revalidatePublicConfiguration("profile");
      setSaved(
        refreshed
          ? "Profile saved. Public pages now use only the fields approved below."
          : "Profile saved. Public pages will refresh within one minute.",
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

  if (loading) return <LoadingPanel label="Loading profile settings" />;
  if (!draft || !request) {
    return (
      <section className={styles.notice}>
        <p>The profile could not be loaded.</p>
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
          <p className="eyebrow">Content / Profile</p>
          <h1>Profile and privacy</h1>
          <p>Write once, then explicitly choose which fields the public API may publish.</p>
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
              onClick={() =>
                void navigator.clipboard.writeText(
                  JSON.stringify(
                    { ...request, publicFields: [...(request.publicFields ?? [])] },
                    null,
                    2,
                  ),
                )
              }
              type="button"
              variant="quiet"
            >
              Copy my changes
            </Button>
          </div>
        ) : null}
        <section className={styles.section}>
          <h2>Identity and biography</h2>
          <div className={styles.fieldGrid}>
            <Field
              label="Full name"
              value={draft.fullName}
              onChange={(value) => update("fullName", value)}
            />
            <Field
              label="Professional title"
              value={draft.professionalTitle}
              onChange={(value) => update("professionalTitle", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              label="Short biography"
              multiline
              value={draft.shortBiography}
              onChange={(value) => update("shortBiography", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              label="Full biography"
              multiline
              value={draft.fullBiography}
              onChange={(value) => update("fullBiography", value)}
            />
            <Field
              label="Location"
              value={draft.location}
              onChange={(value) => update("location", value)}
            />
            <Field
              label="Availability"
              value={draft.availability}
              onChange={(value) => update("availability", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Contact and links</h2>
          <div className={styles.fieldGrid}>
            <Field
              label="Email"
              type="email"
              value={draft.email}
              onChange={(value) => update("email", value)}
            />
            <label className={styles.field}>
              <span>Contact preference</span>
              <select
                value={draft.contactPreference}
                onChange={(event) =>
                  update(
                    "contactPreference",
                    event.target.value as ProfileDraft["contactPreference"],
                  )
                }
              >
                <option value={ContactPreference.None}>None</option>
                <option value={ContactPreference.Email}>Email</option>
                <option value={ContactPreference.Social}>Social</option>
                <option value={ContactPreference.EmailAndSocial}>Email and social</option>
              </select>
            </label>
            <Field
              label="GitHub HTTPS URL"
              type="url"
              value={draft.githubUrl}
              onChange={(value) => update("githubUrl", value)}
            />
            <Field
              label="LinkedIn HTTPS URL"
              type="url"
              value={draft.linkedinUrl}
              onChange={(value) => update("linkedinUrl", value)}
            />
            <Field
              label="Résumé HTTPS URL"
              type="url"
              value={draft.resumeUrl}
              onChange={(value) => update("resumeUrl", value)}
            />
            <Field
              className={styles.fieldWide ?? ""}
              hint="One per line: Label | https://example.test/profile"
              label="Social links"
              multiline
              value={draft.socialLinks}
              onChange={(value) => update("socialLinks", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Values and preferences</h2>
          <div className={styles.fieldGrid}>
            <Field
              hint="One value per line"
              label="Personal values"
              multiline
              value={draft.personalValues}
              onChange={(value) => update("personalValues", value)}
            />
            <Field
              hint="One preference per line"
              label="Work preferences"
              multiline
              value={draft.workPreferences}
              onChange={(value) => update("workPreferences", value)}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2>Public-field approval</h2>
          <p className={styles.sectionDescription}>
            Unchecked values remain absent from JSON, HTML, metadata, and public caches.
          </p>
          <fieldset className={styles.checkboxGrid}>
            <legend className="visually-hidden">Fields approved for public display</legend>
            {PUBLIC_FIELDS.map(([field, label]) => (
              <label className={styles.checkbox} key={field}>
                <input
                  checked={draft.publicFields.has(field)}
                  onChange={(event) => {
                    const fields = new Set(draft.publicFields);
                    if (event.target.checked) fields.add(field);
                    else fields.delete(field);
                    update("publicFields", fields);
                  }}
                  type="checkbox"
                />
                <span>{label}</span>
              </label>
            ))}
          </fieldset>
        </section>
        <section className={styles.section}>
          <h2>Profile image</h2>
          <MediaPicker
            description="A verified responsive image. Public delivery begins only after this profile save commits."
            disabled={saving}
            label="Portrait"
            onChange={(value) => update("profileImageId", value)}
            value={draft.profileImageId}
          />
        </section>
        <div className={styles.actionBar}>
          <Button disabled={saving} type="submit">
            {saving ? "Saving…" : "Save profile"}
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
  type?: "email" | "text" | "url";
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
