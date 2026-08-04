import type { Metadata } from "next";

import { EmptyState } from "@/components/ui/empty-state";
import { PageRenderer } from "@/features/pages/public/page-renderer";
import { getPublicHomePage } from "@/features/pages/public/public-api";
import { publicMetadata, safeJsonLd } from "@/lib/discovery";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  try {
    const site = await getPublicHomePage();
    return publicMetadata({
      canonicalPath: site.canonicalUrl ?? site.canonicalPath,
      title: site.seoTitle || site.title,
      description: site.seoDescription || site.description,
    });
  } catch {
    return { title: "Website unavailable" };
  }
}

async function loadPublicSite() {
  try {
    return await getPublicHomePage();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const site = await loadPublicSite();
  if (!site) {
    return (
      <EmptyState
        description="The published site configuration could not be loaded. Try again shortly."
        eyebrow="Public site"
        title="This page is temporarily unavailable."
      />
    );
  }
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: site.title,
    description: site.seoDescription || site.description,
    url: site.canonicalUrl ?? site.canonicalPath,
    datePublished: site.publishedAt.toISOString(),
  };
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(jsonLd) }} />
      <PageRenderer page={site} />
    </>
  );
}
