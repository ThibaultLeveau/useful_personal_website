import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiTokenApi } from "./api";
import { ApiTokenManager } from "./api-token-manager";
vi.mock("./api", () => ({
  apiTokenApi: {
    list: vi.fn(),
    scopes: vi.fn(),
    create: vi.fn(),
    rotate: vi.fn(),
    revoke: vi.fn(),
  },
}));
const token = {
  id: "00000000-0000-7000-8000-000000000001",
  publicId: "abcdefghijklmnopqrstuv",
  name: "CI publisher",
  displaySuffix: "abc123",
  scopes: ["content:read" as const],
  status: "active" as const,
  createdAt: new Date("2026-08-04T12:00:00Z"),
  expiresAt: new Date("2026-11-02T12:00:00Z"),
  lastUsedAt: null,
  revokedAt: null,
  revocationReason: null,
  rotatedFromId: null,
  version: 1,
};
describe("ApiTokenManager", () => {
  beforeEach(() => {
    vi.mocked(apiTokenApi.list).mockResolvedValue([]);
    vi.mocked(apiTokenApi.scopes).mockResolvedValue(["content:read"]);
    vi.mocked(apiTokenApi.create).mockResolvedValue({
      token,
      plaintextToken: `pp_live_${"a".repeat(22)}.${"b".repeat(43)}`,
    });
  });
  it("requires an explicit scope and reveals a created secret once in page state", async () => {
    const user = userEvent.setup();
    render(<ApiTokenManager />);
    await screen.findByLabelText("Read content");
    await user.type(screen.getByLabelText("Name"), "CI publisher");
    await user.click(screen.getByLabelText("Read content"));
    await user.click(screen.getByRole("button", { name: "Create token" }));
    expect(await screen.findByText("Copy this token now")).toBeInTheDocument();
    expect(screen.getByText(/pp_live_/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "I stored it securely" }));
    await waitFor(() => expect(screen.queryByText(/pp_live_/)).not.toBeInTheDocument());
  });
});
