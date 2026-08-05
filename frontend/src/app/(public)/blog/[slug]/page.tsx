import type { Metadata, Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import { ResponseError } from "@/generated/api/src/runtime";
import styles from "@/features/blog/public/blog.module.css";
import { getPublicPost } from "@/features/blog/public/public-api";
import { SafeRenderedContent } from "@/features/blog/public/safe-rendered-content";
import { safeJsonLd } from "@/lib/discovery";

export const dynamic = "force-dynamic";
type Params = Promise<{ slug: string }>;
const date = new Intl.DateTimeFormat("en", { dateStyle: "long", timeZone: "UTC" });
async function postOrNotFound(slug: string) {
  try {
    return await getPublicPost(slug);
  } catch (error) {
    if (error instanceof ResponseError && error.response.status === 404) notFound();
    throw error;
  }
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const item = await postOrNotFound((await params).slug);
  return {
    title: item.seoTitle,
    description: item.seoDescription,
    alternates: { canonical: item.canonicalUrl ?? `/blog/${item.slug}` },
    robots: { index: true, follow: true },
    openGraph: {
      type: "article",
      title: item.seoTitle,
      description: item.seoDescription,
      publishedTime: item.publishedAt.toISOString(),
      authors: [item.authorDisplay],
      images: item.coverMediaId
        ? [`/api/v1/media/${encodeURIComponent(item.coverMediaId)}/1440?representation=fallback`]
        : undefined,
      tags: item.tags.map((value) => value.name),
    },
  };
}

export default async function BlogDetailPage({ params }: { params: Params }) {
  const item = await postOrNotFound((await params).slug);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: item.title,
    description: item.seoDescription,
    datePublished: item.publishedAt.toISOString(),
    author: { "@type": "Person", name: item.authorDisplay },
    keywords: item.tags.map((value) => value.name),
    image: item.coverMediaId
      ? `/api/v1/media/${encodeURIComponent(item.coverMediaId)}/1440?representation=fallback`
      : undefined,
    url: item.canonicalUrl ?? `/blog/${item.slug}`,
  };
  return (
    <article>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(jsonLd) }} />
      <header className={styles.articleHeader}>
        <p className="eyebrow">
          {item.categories.map((value) => value.name).join(" · ") || "Article"}
        </p>
        <h1>{item.title}</h1>
        <p className={styles.lede}>{item.excerpt}</p>
        <p className={styles.byline}>
          <span>By {item.authorDisplay}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={item.publishedAt.toISOString()}>{date.format(item.publishedAt)}</time>
          <span aria-hidden="true">·</span>
          <span>{item.readingMinutes} min read</span>
        </p>
      </header>
      {item.coverMediaId ? (
        <ResponsiveMediaImage
          alt={`${item.title} article cover`}
          assetId={item.coverMediaId}
          className={styles.articleCover ?? ""}
          eager
          sizes="100vw"
        />
      ) : null}
      <div className={styles.articleLayout}>
        <SafeRenderedContent content={item.content} />
        <aside className={styles.aside}>
          {item.tags.length ? (
            <section>
              <h2>Tagged</h2>
              <ul>
                {item.tags.map((value) => (
                  <li key={value.id}>
                    <Link href={`/blog?tag=${value.slug}` as Route}>{value.name}</Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          {item.relatedPosts.length ? (
            <section>
              <h2>Continue reading</h2>
              <ul>
                {item.relatedPosts.map((value) => (
                  <li key={value.id}>
                    <Link href={`/blog/${value.slug}` as Route}>{value.title}</Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </aside>
      </div>
      <Link className={styles.back} href={"/blog" as Route}>
        ← Back to all writing
      </Link>
    </article>
  );
}
