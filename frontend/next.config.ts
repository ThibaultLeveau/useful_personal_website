import path from "node:path";

import type { NextConfig } from "next";

export const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
  },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
  },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
] as const;

const nextConfig: NextConfig = {
  // Keep dynamic route metadata in the initial document head for every crawler and
  // audit client. The public detail page already blocks on the same cached project
  // projection, so streaming these tags adds compatibility without a second fetch.
  htmlLimitedBots: /.*/,
  async headers() {
    return [{ headers: [...securityHeaders], source: "/:path*" }];
  },
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), ".."),
  poweredByHeader: false,
  reactStrictMode: true,
  typedRoutes: true,
};

export default nextConfig;
