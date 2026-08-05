import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PublicSiteSettingsData } from "@/generated/api/src/models";
import { getPublicSite } from "@/features/site-configuration/public-api";

import LegalPage from "./page";

vi.mock("@/features/site-configuration/public-api", () => ({ getPublicSite: vi.fn() }));

describe("legal page", () => {
  afterEach(() => vi.clearAllMocks());

  it("publishes the configured owner and hosting identity", async () => {
    vi.mocked(getPublicSite).mockResolvedValue({
      contactEmail: "owner@example.test",
      websiteName: "Owner Name",
    } as PublicSiteSettingsData);

    render(await LegalPage());

    expect(screen.getByText(/personal website is published by Owner Name/)).toBeVisible();
    expect(screen.getByRole("link", { name: "owner@example.test" })).toHaveAttribute(
      "href",
      "mailto:owner@example.test",
    );
    expect(screen.getByText(/Hostinger International Ltd/)).toBeVisible();
  });

  it("fails visibly when the publisher identity is unavailable", async () => {
    vi.mocked(getPublicSite).mockRejectedValue(new Error("unavailable"));

    render(await LegalPage());

    expect(screen.getByText(/Publisher identity is incomplete/)).toBeVisible();
  });
});
