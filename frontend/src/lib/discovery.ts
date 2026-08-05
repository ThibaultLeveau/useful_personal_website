import type { Metadata } from "next";

const developmentOrigin = "http://localhost:3000";

export function publicOrigin(): URL {
  const configured = process.env.UPW_PUBLIC_SITE_ORIGIN?.trim();
  if (!configured) return new URL(developmentOrigin);

  const origin = new URL(configured);
  if (!["http:", "https:"].includes(origin.protocol) || origin.username || origin.password) {
    throw new Error("UPW_PUBLIC_SITE_ORIGIN must be an HTTP(S) origin without credentials");
  }
  if (origin.pathname !== "/" || origin.search || origin.hash) {
    throw new Error("UPW_PUBLIC_SITE_ORIGIN must not contain a path, query, or fragment");
  }
  return origin;
}

export function absolutePublicUrl(path: string): string {
  return new URL(path, publicOrigin()).toString();
}

export function publicMetadata({
  canonicalPath,
  description,
  title,
  type = "website",
}: {
  canonicalPath: string;
  description: string;
  title: string;
  type?: "article" | "website";
}): Metadata {
  return {
    title,
    description,
    alternates: { canonical: canonicalPath },
    openGraph: {
      type,
      title,
      description,
      url: canonicalPath,
      siteName: "Personal website",
      locale: "en_US",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
    robots: { index: true, follow: true },
  };
}

export function safeJsonLd(value: unknown): string {
  return JSON.stringify(value).replaceAll("<", "\\u003c");
}
