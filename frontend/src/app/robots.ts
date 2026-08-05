import type { MetadataRoute } from "next";

import { absolutePublicUrl, publicOrigin } from "@/lib/discovery";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin", "/api", "/_next"],
    },
    sitemap: absolutePublicUrl("/sitemap.xml"),
    host: publicOrigin().origin,
  };
}
