import type { Route } from "next";
import Link from "next/link";

import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import type { PublicPostData } from "@/generated/api/src/models";

import styles from "./blog.module.css";

const date = new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" });

export function PostCard({ item }: { item: PublicPostData }) {
  return (
    <article className={styles.card}>
      {item.coverMediaId ? (
        <ResponsiveMediaImage
          alt={`${item.title} article cover`}
          assetId={item.coverMediaId}
          className={styles.cardCover ?? ""}
          sizes="(max-width: 800px) 100vw, 50vw"
        />
      ) : null}
      <p className={styles.meta}>
        <time dateTime={item.publishedAt.toISOString()}>{date.format(item.publishedAt)}</time>
        <span aria-hidden="true">·</span>
        <span>{item.readingMinutes} min read</span>
      </p>
      <h2>
        <Link href={`/blog/${item.slug}` as Route}>{item.title}</Link>
      </h2>
      <p>{item.excerpt}</p>
      {item.categories.length ? (
        <ul className={styles.taxonomy} aria-label="Categories">
          {item.categories.map((value) => (
            <li key={value.id}>{value.name}</li>
          ))}
        </ul>
      ) : null}
      <Link className={styles.readLink} href={`/blog/${item.slug}` as Route}>
        Read article <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}
