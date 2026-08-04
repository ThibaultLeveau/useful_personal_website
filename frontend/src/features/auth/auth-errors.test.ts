import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api";

import { isExpiredAuthError, loginErrorView, passwordErrorView } from "./auth-errors";

function apiError(
  code: string,
  status: number,
  overrides: Partial<ConstructorParameters<typeof ApiError>[0]> = {},
) {
  return new ApiError({
    code,
    message: "unsafe backend wording",
    requestId: "request-safe",
    status,
    ...overrides,
  });
}

function apiErrorWithoutRequest(code: string, status: number) {
  return new ApiError({ code, message: "unsafe backend wording", status });
}

describe("authentication error projections", () => {
  it.each([
    [apiError("AUTHENTICATION_REQUIRED", 401), true],
    [apiError("CSRF_INVALID", 403), true],
    [apiError("CSRF_MISSING", 401), true],
    [apiError("API_UNAVAILABLE", 0), false],
    [new Error("ordinary"), false],
  ])("classifies expired-session errors without broadening the boundary", (error, expected) => {
    expect(isExpiredAuthError(error)).toBe(expected);
  });

  it.each([
    [apiError("AUTHENTICATION_FAILED", 401), "Unable to sign in", "incorrect"],
    [apiError("RATE_LIMITED", 429, { retryAfter: "17" }), "Too many attempts", "17 seconds"],
    [apiErrorWithoutRequest("RATE_LIMITED", 429), "Too many attempts", "little"],
    [apiError("API_UNAVAILABLE", 0), "Connection unavailable", "not queued"],
    [apiError("DEPENDENCY_UNAVAILABLE", 503), "Sign-in unavailable", "safely"],
    [new Error("unsafe exception"), "Sign-in unavailable", "could not be completed"],
  ])("maps login failures to safe visitor copy", (error, title, messageFragment) => {
    const view = loginErrorView(error);
    expect(view.title).toBe(title);
    expect(view.message).toContain(messageFragment);
    expect(JSON.stringify(view)).not.toContain("unsafe backend wording");
    expect(JSON.stringify(view)).not.toContain("unsafe exception");
  });

  it.each([
    [
      apiError("PASSWORD_POLICY_INVALID", 422, { message: "Use at least 12 characters." }),
      "Choose a different password",
      "12 characters",
    ],
    [apiError("AUTHENTICATION_FAILED", 401), "Password change not completed", "incorrect"],
    [apiError("RATE_LIMITED", 429, { retryAfter: "23" }), "Too many attempts", "23 seconds"],
    [apiErrorWithoutRequest("RATE_LIMITED", 429), "Too many attempts", "little"],
    [apiError("API_UNAVAILABLE", 0), "Connection unavailable", "not queued"],
    [apiError("DEPENDENCY_UNAVAILABLE", 503), "Password change not completed", "safely"],
    [new Error("unsafe exception"), "Password change not completed", "could not be changed"],
  ])("maps password failures without exposing unsafe details", (error, title, messageFragment) => {
    const view = passwordErrorView(error);
    expect(view.title).toBe(title);
    expect(view.message).toContain(messageFragment);
    expect(JSON.stringify(view)).not.toContain("unsafe backend wording");
    expect(JSON.stringify(view)).not.toContain("unsafe exception");
  });
});
