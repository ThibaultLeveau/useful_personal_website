import { AuthenticationApi } from "@/generated/api/src/apis/AuthenticationApi";
import type { ChangePasswordRequest, LoginRequest, SessionData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";

export interface AuthRequestOptions {
  signal?: AbortSignal;
}

export interface AuthApiBoundary {
  changePassword(
    request: ChangePasswordRequest,
    options?: AuthRequestOptions,
  ): Promise<SessionData>;
  getSession(options?: AuthRequestOptions): Promise<SessionData>;
  login(request: LoginRequest, options?: AuthRequestOptions): Promise<SessionData>;
  logout(options?: AuthRequestOptions): Promise<void>;
  refreshSession(options?: AuthRequestOptions): Promise<SessionData>;
}

export interface CreateAuthApiOptions {
  fetch?: FetchAPI;
}

function browserOrigin(): string {
  if (typeof window === "undefined") {
    throw new ApiError({
      code: "AUTH_BROWSER_REQUIRED",
      message: "Authentication is available only in a browser session.",
      status: 0,
    });
  }
  return window.location.origin;
}

function readCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined;

  for (const part of document.cookie.split(";")) {
    const [rawName, ...rawValue] = part.trim().split("=");
    if (rawName !== name) continue;
    try {
      return decodeURIComponent(rawValue.join("="));
    } catch {
      return undefined;
    }
  }
  return undefined;
}

function csrfToken(): string {
  const token = readCookie(CSRF_COOKIE_NAME);
  if (!token) {
    throw new ApiError({
      code: "CSRF_MISSING",
      message: "The protected session could not be verified.",
      status: 401,
    });
  }
  return token;
}

function requestInit(options?: AuthRequestOptions): RequestInit {
  return {
    cache: "no-store",
    ...(options?.signal ? { signal: options.signal } : {}),
  };
}

function validateSession(value: SessionData): SessionData {
  if (
    !value.administratorId ||
    !value.displayName ||
    typeof value.mustChangePassword !== "boolean" ||
    !Number.isFinite(value.idleExpiresAt.getTime()) ||
    !Number.isFinite(value.absoluteExpiresAt.getTime())
  ) {
    throw new ApiError({
      code: "API_INVALID_RESPONSE",
      message: "The API returned an invalid response.",
      status: 0,
    });
  }
  return value;
}

class GeneratedAuthBoundary implements AuthApiBoundary {
  constructor(private readonly generated: AuthenticationApi) {}

  async login(request: LoginRequest, options?: AuthRequestOptions): Promise<SessionData> {
    try {
      const response = await this.generated.authLogin(
        { loginRequest: request, origin: browserOrigin() },
        requestInit(options),
      );
      return validateSession(response.data);
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async getSession(options?: AuthRequestOptions): Promise<SessionData> {
    try {
      const response = await this.generated.authSessionGet(requestInit(options));
      return validateSession(response.data);
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async changePassword(
    request: ChangePasswordRequest,
    options?: AuthRequestOptions,
  ): Promise<SessionData> {
    try {
      const response = await this.generated.authPasswordChange(
        {
          changePasswordRequest: request,
          origin: browserOrigin(),
          xCSRFToken: csrfToken(),
        },
        requestInit(options),
      );
      return validateSession(response.data);
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async refreshSession(options?: AuthRequestOptions): Promise<SessionData> {
    try {
      const response = await this.generated.authSessionRefresh(
        { origin: browserOrigin(), xCSRFToken: csrfToken() },
        requestInit(options),
      );
      return validateSession(response.data);
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async logout(options?: AuthRequestOptions): Promise<void> {
    try {
      await this.generated.authLogout(
        { origin: browserOrigin(), xCSRFToken: csrfToken() },
        requestInit(options),
      );
    } catch (error) {
      throw await translateApiError(error);
    }
  }
}

export function createAuthApi(options: CreateAuthApiOptions = {}): AuthApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(options.fetch ? { fetchApi: options.fetch } : {}),
  });
  return new GeneratedAuthBoundary(new AuthenticationApi(configuration));
}
