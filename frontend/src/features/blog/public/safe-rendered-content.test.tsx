import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SafeRenderedContent } from "./safe-rendered-content";

describe("SafeRenderedContent", () => {
  it("renders only the generated safe DTO and exposes policy provenance", () => {
    const { container } = render(
      <SafeRenderedContent
        content={{
          html: '<h2 id="safe">Safe heading</h2><p>&lt;script&gt;alert(1)&lt;/script&gt;</p>',
          policyName: "upw-commonmark",
          policyVersion: "1.0.0",
          sourceChecksum: "sha256:abc",
        }}
      />,
    );
    expect(screen.getByRole("heading", { name: "Safe heading" })).toBeVisible();
    expect(screen.getByText("<script>alert(1)</script>")).toBeVisible();
    expect(container.querySelector("script")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute(
      "data-content-policy",
      "upw-commonmark@1.0.0",
    );
  });
});
