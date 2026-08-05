import type { MetadataRoute } from "next";

import { getPublicPosts } from "@/features/blog/public/public-api";
import { getPublicPageRoutes } from "@/features/pages/public/public-api";
import { getPublicProjects } from "@/features/projects/public/public-api";
import { publicOrigin } from "@/lib/discovery";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = publicOrigin().origin;
  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/about",
    "/skills",
    "/experience",
    "/projects",
    "/blog",
    "/contact",
    "/privacy",
  ].map((path) => ({ url: `${base}${path}`, changeFrequency: path === "" ? "weekly" : "monthly" }));
  const [projects, posts, pages] = await Promise.all([
    getPublicProjects({ page: 1, pageSize: 100 }).catch(() => null),
    getPublicPosts({ page: 1, pageSize: 100 }).catch(() => null),
    getPublicPageRoutes().catch(() => null),
  ]);
  const staticPaths = new Set(staticRoutes.map((item) => new URL(item.url).pathname));
  return [
    ...staticRoutes,
    ...(pages?.data
      .filter((item) => !staticPaths.has(item.canonicalPath))
      .map((item) => ({
        url: `${base}${item.canonicalPath}`,
        lastModified: item.updatedAt,
        changeFrequency: "monthly" as const,
      })) ?? []),
    ...(projects?.data.map((item) => ({
      url: `${base}/projects/${item.slug}`,
      lastModified: item.startDate,
      changeFrequency: "monthly" as const,
    })) ?? []),
    ...(posts?.data.map((item) => ({
      url: `${base}/blog/${item.slug}`,
      lastModified: item.publishedAt,
      changeFrequency: "monthly" as const,
    })) ?? []),
  ];
}
