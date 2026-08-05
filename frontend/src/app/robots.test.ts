import { afterEach, describe, expect, it, vi } from "vitest";

import robots from "./robots";

describe("robots route", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("indexes public pages while excluding private application surfaces", () => {
    vi.stubEnv("UPW_PUBLIC_SITE_ORIGIN", "https://portfolio.example.test");
    expect(robots()).toEqual({
      host: "https://portfolio.example.test",
      rules: {
        allow: "/",
        disallow: ["/admin", "/api", "/_next"],
        userAgent: "*",
      },
      sitemap: "https://portfolio.example.test/sitemap.xml",
    });
  });
});
