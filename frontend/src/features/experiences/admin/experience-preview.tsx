"use client";

import type { Route } from "next";
import Link from "next/link";
import { useCallback, useState } from "react";

import { LoadingPanel } from "@/components/ui/loading-panel";
import type { ExperiencePreviewData } from "@/generated/api/src/models";
import { useAuth } from "@/features/auth/auth-context";
import {
  toApiError,
  useDeferredInitialLoad,
} from "@/features/site-configuration/configuration-form";
import { ApiError } from "@/lib/api";

import { adminExperiencesApi, type AdminExperiencesApiBoundary } from "./admin-api";
import styles from "./experiences-admin.module.css";

const month = new Intl.DateTimeFormat("en", {
  month: "short",
  timeZone: "UTC",
  year: "numeric",
});

export function ExperiencePreview({
  api = adminExperiencesApi,
  experienceId,
}: {
  api?: AdminExperiencesApiBoundary;
  experienceId: string;
}) {
  const auth = useAuth();
  const [preview, setPreview] = useState<ExperiencePreviewData | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setPreview(await api.preview(experienceId));
      setError(null);
    } catch (caught) {
      const next = toApiError(caught);
      setPreview(null);
      setError(next);
      if (next.status === 401) auth.expireSession();
    } finally {
      setLoading(false);
    }
  }, [api, auth, experienceId]);

  useDeferredInitialLoad(load);

  if (loading) return <LoadingPanel label="Loading private draft preview" />;
  if (!preview) {
    return (
      <div className={styles.empty} role="alert">
        <h1>Preview unavailable</h1>
        <p>{error?.message ?? "The draft could not be loaded."}</p>
      </div>
    );
  }

  const item = preview.experience;
  const draft = item.draft;
  const achievements = draft.achievements ?? [];
  const responsibilities = draft.responsibilities ?? [];
  const technologies = draft.technologies ?? [];
  const range = `${month.format(draft.startDate)} – ${draft.currentPosition ? "Present" : draft.endDate ? month.format(draft.endDate) : "End date open"}`;
  return (
    <div className={styles.preview}>
      <header className={styles.previewBanner}>
        <span>{preview.banner}</span>
        <Link
          className="button button--secondary"
          href={`/admin/experiences/${item.id}/edit` as Route}
        >
          Return to editor
        </Link>
      </header>
      <article>
        <p className="eyebrow">{range}</p>
        <h1>{draft.roleTitle}</h1>
        <p>
          <strong>{draft.companyName}</strong>
          {draft.location ? ` · ${draft.location}` : ""}
        </p>
        <p>{draft.shortSummary}</p>
        {draft.detailedDescription ? <p>{draft.detailedDescription}</p> : null}
        {achievements.length ? (
          <section>
            <h2>Selected outcomes</h2>
            <ul>
              {achievements.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </section>
        ) : null}
        {responsibilities.length ? (
          <section>
            <h2>Responsibilities</h2>
            <ul>
              {responsibilities.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </section>
        ) : null}
        {technologies.length ? (
          <p>
            <strong>Technologies:</strong> {technologies.join(" · ")}
          </p>
        ) : null}
      </article>
    </div>
  );
}
