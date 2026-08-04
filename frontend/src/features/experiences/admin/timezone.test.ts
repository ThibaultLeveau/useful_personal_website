import { describe, expect, it } from "vitest";

import { formatInTimezone, zonedLocalToUtc } from "./timezone";

describe("configured-timezone scheduling", () => {
  it("converts a valid Paris wall-clock instant to UTC", () => {
    const result = zonedLocalToUtc("2026-08-03T14:30", "Europe/Paris");
    expect(result.toISOString()).toBe("2026-08-03T12:30:00.000Z");
    expect(formatInTimezone(result, "Europe/Paris")).toContain("2:30");
  });

  it("rejects nonexistent and ambiguous daylight-saving times", () => {
    expect(() => zonedLocalToUtc("2026-03-29T02:30", "Europe/Paris")).toThrow("does not exist");
    expect(() => zonedLocalToUtc("2026-10-25T02:30", "Europe/Paris")).toThrow("ambiguous");
  });
});
