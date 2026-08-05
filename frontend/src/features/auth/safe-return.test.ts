import { describe, expect, it } from "vitest";

import { normalizeAdminReturnPath } from "./safe-return";

describe("admin return-path validation", () => {
  it.each([
    [null, "/admin"],
    ["", "/admin"],
    ["/admin", "/admin"],
    ["/admin/projects?page=2", "/admin/projects?page=2"],
    ["/admin?panel=security", "/admin?panel=security"],
  ])("normalizes %s to %s", (value, expected) => {
    expect(normalizeAdminReturnPath(value)).toBe(expected);
  });

  it.each([
    "//evil.example/admin",
    "https://evil.example/admin",
    "/administrator",
    "/admin-evil",
    "/admin\\evil",
    "/admin%2Fevil",
    "/admin/%2e%2e/evil",
    "/admin/login",
    "/admin/login?return_to=/admin/account",
    "/admin/session-expired",
    "/admin\u0000/account",
  ])("rejects adversarial or looping return path %s", (value) => {
    expect(normalizeAdminReturnPath(value)).toBe("/admin");
  });
});
