import { describe, expect, it } from "vitest";

import nextConfig, { securityHeaders } from "../next.config";

describe("browser security headers", () => {
  it("applies the hardened policy to every frontend route without unsafe inline CSP", async () => {
    const rules = await nextConfig.headers?.();
    const headers = new Headers(
      securityHeaders.map(({ key, value }) => [key, value] as [string, string]),
    );

    expect(rules).toEqual([{ headers: [...securityHeaders], source: "/:path*" }]);
    expect(headers.get("content-security-policy")).toContain("frame-ancestors 'none'");
    expect(headers.get("content-security-policy")).not.toContain("unsafe-inline");
    expect(headers.get("permissions-policy")).toContain("camera=()");
    expect(headers.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    expect(headers.get("strict-transport-security")).toContain("max-age=31536000");
    expect(headers.get("x-content-type-options")).toBe("nosniff");
    expect(headers.get("x-frame-options")).toBe("DENY");
  });
});
