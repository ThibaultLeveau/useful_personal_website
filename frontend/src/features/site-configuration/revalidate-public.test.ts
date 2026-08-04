import { beforeEach, describe, expect, it, vi } from "vitest";

const next = vi.hoisted(() => ({
  cookie: vi.fn(),
  revalidatePath: vi.fn(),
  updateTag: vi.fn(),
}));

vi.mock("next/headers", () => ({
  cookies: async () => ({ get: next.cookie }),
}));

vi.mock("next/cache", () => ({
  revalidatePath: next.revalidatePath,
  updateTag: next.updateTag,
}));

import { revalidatePublicConfiguration } from "./revalidate-public";

beforeEach(() => {
  next.cookie.mockReset();
  next.revalidatePath.mockReset();
  next.updateTag.mockReset();
  vi.restoreAllMocks();
});

describe("public configuration cache invalidation", () => {
  it("does nothing when the server cannot authenticate an administrator session", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");

    await expect(revalidatePublicConfiguration("profile")).resolves.toBe(false);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(next.revalidatePath).not.toHaveBeenCalled();
    expect(next.updateTag).not.toHaveBeenCalled();
  });

  it.each([
    ["profile", "public-profile"],
    ["settings", "public-site"],
    ["footer", "public-site"],
    ["navigation", "public-navigation"],
  ] as const)("authenticates before invalidating the %s projection", async (scope, tag) => {
    next.cookie.mockReturnValue({ value: "opaque-session" });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}", { status: 200 }));

    await expect(revalidatePublicConfiguration(scope)).resolves.toBe(true);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/session",
      expect.objectContaining({ cache: "no-store", credentials: "omit", redirect: "manual" }),
    );
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("cookie")).toBe("__Host-admin_session=opaque-session");
    expect(next.updateTag).toHaveBeenCalledWith(tag);
    expect(next.revalidatePath).toHaveBeenCalledWith(scope === "profile" ? "/about" : "/");
    if (scope !== "profile") {
      expect(next.revalidatePath).toHaveBeenCalledWith("/about");
    }
  });

  it("does not invalidate content when the upstream rejects the session", async () => {
    next.cookie.mockReturnValue({ value: "expired-session" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 401 }));

    await expect(revalidatePublicConfiguration("settings")).resolves.toBe(false);

    expect(next.revalidatePath).not.toHaveBeenCalled();
    expect(next.updateTag).not.toHaveBeenCalled();
  });
});
