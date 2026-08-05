"use client";

import {
  MediaApi,
  type ListMediaApiV1AdminMediaGetRequest,
} from "@/generated/api/src/apis/MediaApi";
import {
  SuccessEnvelopeMediaAssetDataFromJSON,
  type MediaAssetData,
  type MediaUsageData,
  type PaginationData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { ApiError } from "@/lib/api";
import { translateApiError } from "@/lib/api/errors";

const CSRF_COOKIE_NAME = "__Host-admin_csrf";
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const acceptedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);

export interface MediaListSnapshot {
  items: MediaAssetData[];
  pagination: PaginationData;
}

export interface MediaUploadOptions {
  idempotencyKey?: string;
  onProgress?: (percent: number) => void;
}

export interface AdminMediaApiBoundary {
  delete(asset: MediaAssetData): Promise<void>;
  list(filters?: ListMediaApiV1AdminMediaGetRequest): Promise<MediaListSnapshot>;
  rename(asset: MediaAssetData, displayName: string): Promise<MediaAssetData>;
  upload(file: File, options?: MediaUploadOptions): Promise<MediaAssetData>;
  usage(assetId: string): Promise<MediaUsageData[]>;
}

function csrfToken(): string {
  if (typeof document !== "undefined") {
    for (const part of document.cookie.split(";")) {
      const [name, ...raw] = part.trim().split("=");
      if (name !== CSRF_COOKIE_NAME) continue;
      try {
        const token = decodeURIComponent(raw.join("="));
        if (token) return token;
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

function requestKey(): string {
  if (typeof crypto === "undefined" || typeof crypto.randomUUID !== "function") {
    throw new ApiError({
      code: "IDEMPOTENCY_UNAVAILABLE",
      message: "A safe upload identifier could not be created.",
      status: 0,
    });
  }
  return crypto.randomUUID();
}

function validateFile(file: File): void {
  if (!acceptedTypes.has(file.type)) {
    throw new ApiError({
      code: "UNSUPPORTED_MEDIA_TYPE",
      message: "Choose a JPEG, PNG, or WebP image.",
      status: 415,
    });
  }
  if (file.size <= 0 || file.size > MAX_UPLOAD_BYTES) {
    throw new ApiError({
      code: "REQUEST_TOO_LARGE",
      message: "Choose an image no larger than 10 MiB.",
      status: 413,
    });
  }
}

function uploadError(xhr: XMLHttpRequest): ApiError {
  const value: unknown = xhr.response;
  if (typeof value === "object" && value !== null && "error" in value) {
    const error = (value as { error?: unknown }).error;
    if (typeof error === "object" && error !== null) {
      const record = error as Record<string, unknown>;
      if (typeof record.code === "string" && typeof record.message === "string") {
        const requestId = typeof record.request_id === "string" ? record.request_id : undefined;
        return new ApiError({
          code: record.code,
          details:
            typeof record.details === "object" && record.details !== null
              ? (record.details as Record<string, unknown>)
              : {},
          message: record.message,
          status: xhr.status,
          ...(requestId ? { requestId } : {}),
        });
      }
    }
  }
  return new ApiError({
    code: xhr.status === 0 ? "API_UNAVAILABLE" : "API_REQUEST_FAILED",
    message:
      xhr.status === 0 ? "The API could not be reached." : "The upload could not be completed.",
    status: xhr.status,
  });
}

export function uploadWithProgress(
  file: File,
  { idempotencyKey = requestKey(), onProgress }: MediaUploadOptions = {},
): Promise<MediaAssetData> {
  validateFile(file);
  const token = csrfToken();
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/admin/media");
    xhr.responseType = "json";
    xhr.withCredentials = true;
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("Idempotency-Key", idempotencyKey);
    xhr.setRequestHeader("X-CSRF-Token", token);
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
    });
    xhr.addEventListener("error", () => reject(uploadError(xhr)));
    xhr.addEventListener("load", () => {
      if (xhr.status < 200 || xhr.status >= 300) {
        reject(uploadError(xhr));
        return;
      }
      try {
        resolve(SuccessEnvelopeMediaAssetDataFromJSON(xhr.response).data);
      } catch {
        reject(
          new ApiError({
            code: "API_INVALID_RESPONSE",
            message: "The API returned an invalid upload response.",
            status: 0,
          }),
        );
      }
    });
    const form = new FormData();
    form.append("file", file, file.name);
    xhr.send(form);
  });
}

class GeneratedAdminMediaBoundary implements AdminMediaApiBoundary {
  constructor(private readonly media: MediaApi) {}

  private async translated<Value>(operation: () => Promise<Value>): Promise<Value> {
    try {
      return await operation();
    } catch (error) {
      throw await translateApiError(error);
    }
  }

  list(filters: ListMediaApiV1AdminMediaGetRequest = {}): Promise<MediaListSnapshot> {
    return this.translated(async () => {
      const result = await this.media.listMediaApiV1AdminMediaGet(
        { page: 1, pageSize: 20, ...filters },
        { cache: "no-store" },
      );
      return { items: result.data, pagination: result.meta.pagination };
    });
  }

  usage(assetId: string): Promise<MediaUsageData[]> {
    return this.translated(async () => {
      const result = await this.media.getMediaUsageApiV1AdminMediaAssetIdUsageGet(
        { assetId },
        { cache: "no-store" },
      );
      return result.data.items;
    });
  }

  rename(asset: MediaAssetData, displayName: string): Promise<MediaAssetData> {
    return this.translated(async () => {
      const result = await this.media.updateMediaApiV1AdminMediaAssetIdPatch(
        {
          assetId: asset.id,
          ifMatch: `"v${asset.version}"`,
          mediaMetadataRequest: { displayName },
          xCSRFToken: csrfToken(),
        },
        { cache: "no-store" },
      );
      return result.data;
    });
  }

  async delete(asset: MediaAssetData): Promise<void> {
    await this.translated(() =>
      this.media.deleteMediaApiV1AdminMediaAssetIdDelete(
        { assetId: asset.id, ifMatch: `"v${asset.version}"`, xCSRFToken: csrfToken() },
        { cache: "no-store" },
      ),
    );
  }

  upload(file: File, options?: MediaUploadOptions): Promise<MediaAssetData> {
    return uploadWithProgress(file, options);
  }
}

export function createAdminMediaApi(fetchApi?: FetchAPI): AdminMediaApiBoundary {
  const configuration = new Configuration({
    basePath: "",
    credentials: "same-origin",
    ...(fetchApi ? { fetchApi } : {}),
  });
  return new GeneratedAdminMediaBoundary(new MediaApi(configuration));
}

export const adminMediaApi = createAdminMediaApi();
