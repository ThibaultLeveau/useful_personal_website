import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./empty-state";

describe("EmptyState", () => {
  it("provides a named region and passes the axe primitive smoke", async () => {
    const { container } = render(
      <EmptyState
        description="Published content is not available."
        eyebrow="Initial state"
        title="Nothing is configured yet."
      />,
    );

    expect(screen.getByRole("region", { name: "Nothing is configured yet." })).toBeVisible();
    const results = await axe.run(container, {
      rules: {
        "color-contrast": { enabled: false },
      },
    });
    expect(results.violations).toEqual([]);
  });
});
