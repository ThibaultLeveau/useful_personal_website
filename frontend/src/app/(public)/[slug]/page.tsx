import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PageRenderer } from "@/features/pages/public/page-renderer";
import { getPublicCustomPage } from "@/features/pages/public/public-api";
import { publicMetadata, safeJsonLd } from "@/lib/discovery";

type Props = { params: Promise<{ slug: string }> };

async function load(slug: string) {
  try {
    return await getPublicCustomPage(slug);
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const page = await load((await params).slug);
  if (!page) return { title: "Page not found" };
  return publicMetadata({
    canonicalPath: page.canonicalUrl ?? page.canonicalPath,
    title: page.seoTitle || page.title,
    description: page.seoDescription || page.description,
  });
}

export default async function CustomPage({ params }: Props) {
  const page = await load((await params).slug);
  if (!page) notFound();
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: page.title,
    description: page.seoDescription || page.description,
    url: page.canonicalUrl ?? page.canonicalPath,
    datePublished: page.publishedAt.toISOString(),
  };
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd(jsonLd) }} />
      <PageRenderer page={page} />
    </>
  );
}
