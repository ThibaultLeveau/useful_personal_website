"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState } from "react";

import type { ProjectPreviewData } from "@/generated/api/src/models";
import { ControlledMarkdown } from "@/features/projects/public/controlled-markdown";

import { adminProjectsApi } from "./admin-api";
import styles from "./projects-admin.module.css";

export function ProjectPreview({ projectId }: { projectId: string }) {
  const [preview, setPreview] = useState<ProjectPreviewData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    void adminProjectsApi
      .preview(projectId)
      .then((value) => {
        if (active) setPreview(value);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [projectId]);
  if (error)
    return (
      <section className={styles.state} role="alert">
        The private preview could not be loaded.
      </section>
    );
  if (!preview)
    return (
      <section className={styles.state} role="status">
        Loading private preview…
      </section>
    );
  const item = preview.project.draft;
  const screenshots = item.screenshotMediaIds ?? [];
  return (
    <div className={styles.preview}>
      <aside aria-label="Preview status">
        <strong role="status">{preview.banner}</strong>
        <span>Search indexing disabled · session-only response</span>
        <Link href={`/admin/projects/${preview.project.id}/edit` as Route}>Return to editor</Link>
      </aside>
      <article>
        <p className="eyebrow">{item.status} · preview</p>
        <h1>{item.name}</h1>
        <p className={styles.previewLede}>{item.shortDescription}</p>
        {item.coverMediaId ? (
          // Authenticated draft media cannot use the public delivery route.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt={`${item.name} project cover`}
            className={styles.previewMedia}
            src={`/api/v1/admin/media/${encodeURIComponent(item.coverMediaId)}/content?width=1440&representation=webp`}
          />
        ) : null}
        {screenshots.length ? (
          <div className={styles.previewGallery}>
            {screenshots.map((assetId, index) => (
              // Authenticated draft media cannot use the public delivery route.
              // eslint-disable-next-line @next/next/no-img-element
              <img
                alt={`${item.name} project screenshot ${index + 1}`}
                key={assetId}
                src={`/api/v1/admin/media/${encodeURIComponent(assetId)}/content?width=960&representation=webp`}
              />
            ))}
          </div>
        ) : null}
        {[
          ["Overview", item.fullDescription],
          ["Problem", item.problem],
          ["Solution", item.solution],
          ["Architecture", item.architecture],
          ["Impact", item.impact],
        ].map(([label, value]) => (
          <section key={label}>
            <h2>{label}</h2>
            <ControlledMarkdown value={value as string} />
          </section>
        ))}
      </article>
    </div>
  );
}
