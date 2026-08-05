"use client";

import { SiteConfigurationApi } from "@/generated/api/src/apis/SiteConfigurationApi";
import type {
  FooterData,
  FooterReplaceRequest,
  NavigationData,
  NavigationReplaceRequest,
  ProfileData,
  ProfileUpdateRequest,
  WebsiteSettingsData,
  WebsiteSettingsUpdateRequest,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";
const ETAG_PATTERN = /^"v[1-9][0-9]*"$/u;

export interface Versioned<Data> {
  data: Data;
  etag: string;
}

export interface AdminSiteApiBoundary {
  getFooter(signal?: AbortSignal): Promise<Versioned<FooterData>>;
  getNavigation(signal?: AbortSignal): Promise<Versioned<NavigationData>>;
  getProfile(signal?: AbortSignal): Promise<Versioned<ProfileData>>;
  getSettings(signal?: AbortSignal): Promise<Versioned<WebsiteSettingsData>>;
  replaceFooter(
    request: FooterReplaceRequest,
    etag: string,
    idempotencyKey?: string,
  ): Promise<Versioned<FooterData>>;
  replaceNavigation(
    request: NavigationReplaceRequest,
    etag: string,
    idempotencyKey?: string,
  ): Promise<Versioned<NavigationData>>;
  updateProfile(request: ProfileUpdateRequest, etag: string): Promise<Versioned<ProfileData>>;
  updateSettings(
    request: WebsiteSettingsUpdateRequest,
    etag: string,
  ): Promise<Versioned<WebsiteSettingsData>>;
}

function browserOrigin(): string {
  if (typeof window === "undefined") {
    throw new ApiError({
      code: "AUTH_BROWSER_REQUIRED",
      message: "Administration is available only in a browser session.",
      status: 0,
    });
  }
  return window.location.origin;
}

function csrfToken(): string {
  if (typeof document !== "undefined") {
    for (const part of document.cookie.split(";")) {
      const [rawName, ...rawValue] = part.trim().split("=");
      if (rawName !== CSRF_COOKIE_NAME) continue;
      try {
        const value = decodeURIComponent(rawValue.join("="));
        if (value) return value;
      } catch {
        break;
      }
    }
  }
  throw new ApiError({
    code: "CSRF_MISSING",
    message: "The protected session could not be verified.",
    status: 401,
  });
}

function noStore(signal?: AbortSignal): RequestInit {
  return { cache: "no-store", ...(signal ? { signal } : {}) };
}

function readEtag(response: Response): string {
  const etag = response.headers.get("etag");
  if (!etag || !ETAG_PATTERN.test(etag)) {
    throw new SyntaxError("The API response omitted its resource version.");
  }
  return etag;
}

function idempotencyKey(value?: string): string {
  if (value) return value;
  if (typeof crypto === "undefined" || typeof crypto.randomUUID !== "function") {
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe request identifier could not be created.",
      status: 0,
    });
  }
  return crypto.randomUUID();
}

class GeneratedAdminSiteBoundary implements AdminSiteApiBoundary {
  constructor(private readonly generated: SiteConfigurationApi) {}

  private async result<Data>(response: {
    raw: Response;
    value(): Promise<{ data: Data }>;
  }): Promise<Versioned<Data>> {
    return { data: (await response.value()).data, etag: readEtag(response.raw) };
  }

  private async translated<Data>(
    operation: () => Promise<Versioned<Data>>,
  ): Promise<Versioned<Data>> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  getProfile(signal?: AbortSignal) {
    return this.translated(async () =>
      this.result(await this.generated.adminProfileGetRaw(noStore(signal))),
    );
  }

  getSettings(signal?: AbortSignal) {
    return this.translated(async () =>
      this.result(await this.generated.adminWebsiteSettingsGetRaw(noStore(signal))),
    );
  }

  getNavigation(signal?: AbortSignal) {
    return this.translated(async () =>
      this.result(await this.generated.adminNavigationGetRaw(noStore(signal))),
    );
  }

  getFooter(signal?: AbortSignal) {
    return this.translated(async () =>
      this.result(await this.generated.adminFooterGetRaw(noStore(signal))),
    );
  }

  updateProfile(request: ProfileUpdateRequest, etag: string) {
    return this.translated(async () =>
      this.result(
        await this.generated.adminProfileUpdateRaw(
          {
            xCSRFToken: csrfToken(),
            origin: browserOrigin(),
            profileUpdateRequest: request,
            ifMatch: etag,
          },
          noStore(),
        ),
      ),
    );
  }

  updateSettings(request: WebsiteSettingsUpdateRequest, etag: string) {
    return this.translated(async () =>
      this.result(
        await this.generated.adminWebsiteSettingsUpdateRaw(
          {
            xCSRFToken: csrfToken(),
            origin: browserOrigin(),
            websiteSettingsUpdateRequest: request,
            ifMatch: etag,
          },
          noStore(),
        ),
      ),
    );
  }

  replaceNavigation(request: NavigationReplaceRequest, etag: string, key?: string) {
    return this.translated(async () =>
      this.result(
        await this.generated.adminNavigationReplaceRaw(
          {
            xCSRFToken: csrfToken(),
            idempotencyKey: idempotencyKey(key),
            origin: browserOrigin(),
            navigationReplaceRequest: request,
            ifMatch: etag,
          },
          noStore(),
        ),
      ),
    );
  }

  replaceFooter(request: FooterReplaceRequest, etag: string, key?: string) {
    return this.translated(async () =>
      this.result(
        await this.generated.adminFooterReplaceRaw(
          {
            xCSRFToken: csrfToken(),
            idempotencyKey: idempotencyKey(key),
            origin: browserOrigin(),
            footerReplaceRequest: request,
            ifMatch: etag,
          },
          noStore(),
        ),
      ),
    );
  }
}

export function createAdminSiteApi(fetchApi?: FetchAPI): AdminSiteApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminSiteBoundary(new SiteConfigurationApi(configuration));
}

export const adminSiteApi = createAdminSiteApi();
