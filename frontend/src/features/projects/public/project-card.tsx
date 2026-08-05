import type { Route } from "next";
import Link from "next/link";

import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import type { PublicProjectData } from "@/generated/api/src/models";

import styles from "./projects.module.css";

const statusLabels: Record<PublicProjectData["status"], string> = {
  active: "Active",
  archived: "Archived",
  completed: "Completed",
  maintenance: "Maintained",
  paused: "Paused",
  planned: "Planned",
};

export function ProjectCard({ item, index }: { item: PublicProjectData; index: number }) {
  return (
    <article className={styles.card}>
      {item.coverMediaId ? (
        <ResponsiveMediaImage
          alt={`${item.name} project cover`}
          assetId={item.coverMediaId}
          className={styles.cardMedia ?? ""}
          sizes="(max-width: 760px) 100vw, 50vw"
        />
      ) : null}
      <div className={styles.cardTopline}>
        <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
        <span className={styles.status}>{statusLabels[item.status]}</span>
      </div>
      <div>
        {item.featured ? <p className="eyebrow">Featured case study</p> : null}
        <h2>
          <Link href={`/projects/${item.slug}` as Route}>{item.name}</Link>
        </h2>
        <p>{item.shortDescription}</p>
      </div>
      <ul className={styles.tags} aria-label="Technologies">
        {item.technologies.slice(0, 5).map((technology) => (
          <li key={technology}>{technology}</li>
        ))}
      </ul>
      <Link className={styles.caseLink} href={`/projects/${item.slug}` as Route}>
        Read case study <span aria-hidden="true">↗</span>
      </Link>
    </article>
  );
}
