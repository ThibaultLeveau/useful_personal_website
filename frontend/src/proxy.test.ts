import {
  getRewrittenUrl,
  isRewrite,
  unstable_doesMiddlewareMatch,
} from "next/experimental/testing/server";
import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { config, proxy, resolveApiUpstreamOrigin } from "./proxy";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("same-origin API proxy", () => {
  it("matches only the versioned API boundary", () => {
    for (const url of ["/api/v1", "/api/v1/auth/login", "/api/v1/projects?page=2"]) {
      expect(unstable_doesMiddlewareMatch({ config, url })).toBe(true);
    }
    for (const url of ["/", "/admin", "/api", "/api/v2", "/apiary/v1"]) {
      expect(unstable_doesMiddlewareMatch({ config, url })).toBe(false);
    }
  });

  it("rewrites path and query to the validated internal origin", () => {
    vi.stubEnv("UPW_API_UPSTREAM_ORIGIN", "http://backend:8000");
    const response = proxy(
      new NextRequest("https://portfolio.example.test/api/v1/auth/session?refresh=false"),
    );

    expect(isRewrite(response)).toBe(true);
    expect(getRewrittenUrl(response)).toBe("http://backend:8000/api/v1/auth/session?refresh=false");
    expect(response.headers.get("location")).toBeNull();
  });

  it("uses localhost only outside production and refuses missing production configuration", () => {
    expect(resolveApiUpstreamOrigin({ NODE_ENV: "development" })).toBe("http://127.0.0.1:8000");
    expect(() => resolveApiUpstreamOrigin({ NODE_ENV: "production" })).toThrow(
      "required in production",
    );
  });

  it.each([
    "//evil.example.test",
    "ftp://backend:8000",
    "http://name:password@backend:8000",
    "http://backend:8000/private",
    "http://backend:8000?target=elsewhere",
    "http://backend:8000#fragment",
    "http://*.internal:8000",
    " http://backend:8000",
    "http://backend:8000\n",
    "not-an-origin",
  ])("refuses unsafe upstream value %s without echoing it", (value) => {
    let thrown: unknown;
    try {
      resolveApiUpstreamOrigin({ NODE_ENV: "production", UPW_API_UPSTREAM_ORIGIN: value });
    } catch (error) {
      thrown = error;
    }
    expect(thrown).toBeInstanceOf(Error);
    expect((thrown as Error).message).not.toContain(value);
  });
});
