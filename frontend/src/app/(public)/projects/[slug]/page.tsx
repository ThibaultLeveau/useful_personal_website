import type { Metadata, Route } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ResponsiveMediaImage } from "@/components/public/responsive-media-image";
import { ResponseError } from "@/generated/api/src/runtime";
import { ControlledMarkdown } from "@/features/projects/public/controlled-markdown";
import { getPublicProject } from "@/features/projects/public/public-api";
import styles from "@/features/projects/public/projects.module.css";
import { safeJsonLd } from "@/lib/discovery";

export const dynamic = "force-dynamic";
type Params = Promise<{ slug: string }>;

async function projectOrNotFound(slug: string) {
  try {
    return await getPublicProject(slug);
  } catch (error) {
    if (error instanceof ResponseError && error.response.status === 404) notFound();
    throw error;
  }
}
export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const item = await projectOrNotFound((await params).slug);
  return {
    title: item.seoTitle,
    description: item.seoDescription,
    alternates: { canonical: item.canonicalUrl ?? `/projects/${item.slug}` },
    openGraph: item.coverMediaId
      ? {
          images: [
            `/api/v1/media/${encodeURIComponent(item.coverMediaId)}/1440?representation=fallback`,
          ],
        }
      : undefined,
    robots: { index: true, follow: true },
  };
}

export default async function ProjectDetailPage({ params }: { params: Params }) {
  const item = await projectOrNotFound((await params).slug);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    name: item.name,
    description: item.seoDescription,
    url: item.canonicalUrl ?? `/projects/${item.slug}`,
    dateCreated: item.startDate.toISOString().slice(0, 10),
    image: item.coverMediaId
      ? `/api/v1/media/${encodeURIComponent(item.coverMediaId)}/1440?representation=fallback`
      : undefined,
    keywords: item.technologies.join(", "),
  };
  return (
    <article>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(jsonLd) }} />
      <header className={styles.detailHero}>
        <div>
          <p className="eyebrow">Case study · {item.status}</p>
          <h1>{item.name}</h1>
          <p className={styles.lede}>{item.shortDescription}</p>
          <div className={styles.actions}>
            {item.demoUrl ? (
              <a className="button button--primary" href={item.demoUrl} rel="noopener noreferrer">
                View demo
              </a>
            ) : null}
            {item.repositoryUrl ? (
              <a
                className="button button--quiet"
                href={item.repositoryUrl}
                rel="noopener noreferrer"
              >
                Repository
              </a>
            ) : null}
          </div>
        </div>
        <dl className={styles.facts}>
          <div>
            <dt>Role</dt>
            <dd>{item.ownerRole}</dd>
          </div>
          <div>
            <dt>Started</dt>
            <dd>{item.startDate.getUTCFullYear()}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{item.status}</dd>
          </div>
        </dl>
      </header>
      {item.coverMediaId || item.screenshotMediaIds.length ? (
        <section className={styles.projectGallery} aria-labelledby="project-gallery-heading">
          <div>
            <p className="eyebrow">Visual record</p>
            <h2 id="project-gallery-heading">Project gallery</h2>
          </div>
          {item.coverMediaId ? (
            <ResponsiveMediaImage
              alt={`${item.name} project cover`}
              assetId={item.coverMediaId}
              className={styles.galleryCover ?? ""}
              eager
              sizes="100vw"
            />
          ) : null}
          {item.screenshotMediaIds.length ? (
            <div className={styles.galleryGrid}>
              {item.screenshotMediaIds.map((assetId, index) => (
                <ResponsiveMediaImage
                  alt={`${item.name} project screenshot ${index + 1}`}
                  assetId={assetId}
                  key={assetId}
                  sizes="(max-width: 760px) 100vw, 50vw"
                />
              ))}
            </div>
          ) : null}
        </section>
      ) : null}
      <section className={styles.story}>
        <h2>Overview</h2>
        <div className={styles.storyBody}>
          <ControlledMarkdown value={item.fullDescription} />
        </div>
      </section>
      <section className={styles.story}>
        <h2>The problem</h2>
        <div className={styles.storyBody}>
          <ControlledMarkdown value={item.problem} />
        </div>
      </section>
      <section className={styles.story}>
        <h2>The solution</h2>
        <div className={styles.storyBody}>
          <ControlledMarkdown value={item.solution} />
        </div>
      </section>
      <section className={styles.story}>
        <h2>Architecture</h2>
        <div className={styles.storyBody}>
          <ControlledMarkdown value={item.architecture} />
        </div>
      </section>
      <section className={styles.story}>
        <h2>Impact</h2>
        <div className={styles.storyBody}>
          <ControlledMarkdown value={item.impact} />
        </div>
      </section>
      <div className={styles.evidence}>
        <section>
          <h2>Technology</h2>
          <ul>
            {item.technologies.map((value) => (
              <li key={value}>{value}</li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Capabilities</h2>
          <ul>
            {item.skills.map((value) => (
              <li key={value.slug}>
                <Link href={`/skills#${value.slug}` as Route}>{value.name}</Link>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Related work</h2>
          <ul>
            {item.relatedProjects.map((value) => (
              <li key={value.id}>
                <Link href={`/projects/${value.slug}` as Route}>{value.name}</Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </article>
  );
}
