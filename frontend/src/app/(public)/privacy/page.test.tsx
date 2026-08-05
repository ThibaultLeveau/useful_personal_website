import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PublicSiteSettingsData } from "@/generated/api/src/models";
import { getPublicSite } from "@/features/site-configuration/public-api";

import PrivacyPage from "./page";

vi.mock("@/features/site-configuration/public-api", () => ({ getPublicSite: vi.fn() }));

describe("privacy page", () => {
  afterEach(() => vi.clearAllMocks());

  it("publishes the configured controller and bounded contact policy", async () => {
    vi.mocked(getPublicSite).mockResolvedValue({
      contactEmail: "owner@example.test",
      websiteName: "Owner Name",
    } as PublicSiteSettingsData);

    render(await PrivacyPage());

    expect(screen.getByText(/data controller is Owner Name/)).toBeVisible();
    expect(screen.getByRole("link", { name: "owner@example.test" })).toHaveAttribute(
      "href",
      "mailto:owner@example.test",
    );
    expect(screen.getByText(/retained for no more than 365 days/)).toBeVisible();
    expect(screen.getByText(/No automated decision-making/)).toBeVisible();
  });

  it("fails visibly when the controller identity is unavailable", async () => {
    vi.mocked(getPublicSite).mockRejectedValue(new Error("unavailable"));

    render(await PrivacyPage());

    expect(screen.getByText(/not ready for public contact collection/)).toBeVisible();
  });
});
