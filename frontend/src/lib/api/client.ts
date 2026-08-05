import { AdministratorHealthApi } from "@/generated/api/src/apis/AdministratorHealthApi";
import { HealthApi } from "@/generated/api/src/apis/HealthApi";
import type {
  AdminHealthData,
  SuccessEnvelopeAdminHealthData,
  SuccessEnvelopeLiveData,
  SuccessEnvelopeReadyData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";

import { translateApiError } from "./errors";

export interface ApiClientOptions {
  basePath?: string;
  credentials?: "omit" | "same-origin";
  fetch?: FetchAPI;
}

export interface ApiRequestOptions {
  requestId?: string;
  signal?: AbortSignal;
}

export interface HealthApiBoundary {
  live(options?: ApiRequestOptions): Promise<SuccessEnvelopeLiveData>;
  ready(options?: ApiRequestOptions): Promise<SuccessEnvelopeReadyData>;
}

export interface AdminHealthApiBoundary {
  get(options?: ApiRequestOptions): Promise<SuccessEnvelopeAdminHealthData>;
}

export interface OfficialApiClient {
  readonly adminHealth: AdminHealthApiBoundary;
  readonly health: HealthApiBoundary;
}

function normalizeBasePath(value: string | undefined): string {
  const basePath = value?.trim() ?? "";
  if (!basePath) return "";

  if (basePath.startsWith("/")) {
    if (basePath.startsWith("//")) {
      throw new TypeError("The API base path must not be a protocol-relative URL.");
    }
    return basePath.replace(/\/+$/, "");
  }

  let parsed: URL;
  try {
    parsed = new URL(basePath);
  } catch {
    throw new TypeError("The API base path must be relative or use HTTP(S).");
  }

  if (
    (parsed.protocol !== "http:" && parsed.protocol !== "https:") ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash
  ) {
    throw new TypeError("The API base path must be a safe HTTP(S) URL without credentials.");
  }

  return parsed.toString().replace(/\/+$/, "");
}

function createRequestInit(options: ApiRequestOptions | undefined): RequestInit {
  const headers = new Headers({ Accept: "application/json" });
  const requestId = options?.requestId?.trim();
  if (requestId) headers.set("X-Request-ID", requestId);

  return {
    headers,
    ...(options?.signal ? { signal: options.signal } : {}),
  };
}

class HealthBoundary implements HealthApiBoundary {
  constructor(private readonly generated: HealthApi) {}

  async live(options?: ApiRequestOptions): Promise<SuccessEnvelopeLiveData> {
    try {
      return await this.generated.healthLive(createRequestInit(options));
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  async ready(options?: ApiRequestOptions): Promise<SuccessEnvelopeReadyData> {
    try {
      return await this.generated.healthReady(createRequestInit(options));
    } catch (error) {
      throw await translateApiError(error);
    }
  }
}

function validateAdminHealth(data: AdminHealthData): AdminHealthData {
  const validStatus = data.status === "operational" || data.status === "degraded";
  const validDatabase =
    data.databaseStatus === "operational" || data.databaseStatus === "unavailable";
  const validMigration =
    data.migrationStatus === "current" ||
    data.migrationStatus === "unavailable" ||
    data.migrationStatus === "unknown";
  if (
    !validStatus ||
    !validDatabase ||
    !validMigration ||
    data.applicationStatus !== "operational" ||
    !data.buildVersion ||
    !data.buildCommit ||
    !Number.isFinite(data.checkedAt.getTime())
  ) {
    throw new SyntaxError("The admin health response is invalid.");
  }
  return data;
}

class AdminHealthBoundary implements AdminHealthApiBoundary {
  constructor(private readonly generated: AdministratorHealthApi) {}

  async get(options?: ApiRequestOptions): Promise<SuccessEnvelopeAdminHealthData> {
    try {
      const envelope = await this.generated.adminHealthGet({
        ...createRequestInit(options),
        cache: "no-store",
      });
      validateAdminHealth(envelope.data);
      return envelope;
    } catch (error) {
      throw await translateApiError(error);
    }
  }
}

export function createApiClient(options: ApiClientOptions = {}): OfficialApiClient {
  const configuration = new Configuration({
    basePath: normalizeBasePath(options.basePath),
    credentials: options.credentials ?? "same-origin",
    ...(options.fetch ? { fetchApi: options.fetch } : {}),
  });

  return Object.freeze({
    adminHealth: new AdminHealthBoundary(new AdministratorHealthApi(configuration)),
    health: new HealthBoundary(new HealthApi(configuration)),
  });
}
