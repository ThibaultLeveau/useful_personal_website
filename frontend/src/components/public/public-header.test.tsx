import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LinkTarget, type PublicNavigationItemData } from "@/generated/api/src/models";

import { orderPublicNavigation, PublicHeader } from "./public-header";

vi.mock("next/navigation", () => ({ usePathname: () => "/about" }));

const navigation: PublicNavigationItemData[] = [
  { href: "/", key: "home", label: "Home", target: LinkTarget.SameWindow },
  { href: "/about", key: "about", label: "About", target: LinkTarget.SameWindow },
  {
    href: "https://example.test/work",
    key: "work",
    label: "Work",
    parentKey: "home",
    target: LinkTarget.NewWindow,
  },
];

describe("public navigation", () => {
  it("places child destinations directly after their parent without losing deterministic order", () => {
    expect(orderPublicNavigation(navigation).map((item) => item.key)).toEqual([
      "home",
      "work",
      "about",
    ]);
  });

  it("marks the current internal page and hardens new-window external destinations", () => {
    render(<PublicHeader brand="Example" navigation={navigation} />);

    for (const link of screen.getAllByRole("link", { name: "About" })) {
      expect(link).toHaveAttribute("aria-current", "page");
    }
    for (const link of screen.getAllByRole("link", { name: "Work" })) {
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
      expect(link).toHaveClass("public-nav__child");
    }
  });
});
