import { ApiError } from "@/lib/api";

export interface AuthErrorView {
  message: string;
  requestId?: string;
  title: string;
}

export function isExpiredAuthError(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.status === 401 || error.code === "CSRF_INVALID" || error.code === "CSRF_MISSING")
  );
}

export function loginErrorView(error: unknown): AuthErrorView {
  if (error instanceof ApiError) {
    if (error.code === "AUTHENTICATION_FAILED" || error.status === 401) {
      return {
        title: "Unable to sign in",
        message: "The email or password is incorrect.",
        ...(error.requestId ? { requestId: error.requestId } : {}),
      };
    }
    if (error.code === "RATE_LIMITED" || error.status === 429) {
      return {
        title: "Too many attempts",
        message: error.retryAfter
          ? `Wait ${error.retryAfter} seconds before trying again.`
          : "Wait a little before trying again.",
        ...(error.requestId ? { requestId: error.requestId } : {}),
      };
    }
    if (error.code === "API_UNAVAILABLE" || error.status === 0) {
      return {
        title: "Connection unavailable",
        message: "Check your connection, then try again. Your credentials were not queued.",
      };
    }
    return {
      title: "Sign-in unavailable",
      message: "Sign-in could not be completed. Try again safely.",
      ...(error.requestId ? { requestId: error.requestId } : {}),
    };
  }
  return { title: "Sign-in unavailable", message: "Sign-in could not be completed." };
}

export function passwordErrorView(error: unknown): AuthErrorView {
  if (error instanceof ApiError) {
    if (error.code === "PASSWORD_POLICY_INVALID") {
      return {
        title: "Choose a different password",
        message: error.message,
        ...(error.requestId ? { requestId: error.requestId } : {}),
      };
    }
    if (error.code === "AUTHENTICATION_FAILED") {
      return {
        title: "Password change not completed",
        message: "The current password is incorrect.",
        ...(error.requestId ? { requestId: error.requestId } : {}),
      };
    }
    if (error.code === "RATE_LIMITED" || error.status === 429) {
      return {
        title: "Too many attempts",
        message: error.retryAfter
          ? `Wait ${error.retryAfter} seconds before trying again.`
          : "Wait a little before trying again.",
        ...(error.requestId ? { requestId: error.requestId } : {}),
      };
    }
    if (error.code === "API_UNAVAILABLE" || error.status === 0) {
      return {
        title: "Connection unavailable",
        message: "Check your connection, then try again. Your passwords were not queued.",
      };
    }
    return {
      title: "Password change not completed",
      message: "The password could not be changed. Try again safely.",
      ...(error.requestId ? { requestId: error.requestId } : {}),
    };
  }
  return {
    title: "Password change not completed",
    message: "The password could not be changed.",
  };
}
