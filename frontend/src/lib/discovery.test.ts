import { afterEach, describe, expect, it, vi } from "vitest";

import { absolutePublicUrl, publicMetadata, publicOrigin, safeJsonLd } from "./discovery";

describe("public discovery helpers", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("uses the documented local origin when deployment has not selected one", () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");
    expect(publicOrigin().toString()).toBe("http://localhost:3000/");
    expect(absolutePublicUrl("/sitemap.xml")).toBe("http://localhost:3000/sitemap.xml");
  });

  it("normalizes one configured public origin", () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://portfolio.example.test/");
    expect(absolutePublicUrl("/projects/example")).toBe(
      "https://portfolio.example.test/projects/example",
    );
  });

  it.each([
    "ftp://portfolio.example.test",
    "https://operator:secret@portfolio.example.test",
    "https://portfolio.example.test/path",
    "https://portfolio.example.test?preview=1",
  ])("rejects an unsafe or non-origin deployment URL: %s", (value) => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", value);
    expect(() => publicOrigin()).toThrow("NEXT_PUBLIC_SITE_URL");
  });

  it("builds indexable canonical metadata without private fields", () => {
    expect(
      publicMetadata({ canonicalPath: "/projects", description: "Selected work.", title: "Work" }),
    ).toMatchObject({
      alternates: { canonical: "/projects" },
      description: "Selected work.",
      robots: { follow: true, index: true },
      title: "Work",
    });
  });

  it("escapes markup delimiters in structured data", () => {
    const output = safeJsonLd({ name: "</script><script>alert(1)</script>" });
    expect(output).not.toContain("<");
    expect(JSON.parse(output)).toEqual({ name: "</script><script>alert(1)</script>" });
  });
});
