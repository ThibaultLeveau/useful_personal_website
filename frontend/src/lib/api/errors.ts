import { FetchError, ResponseError } from "@/generated/api/src/runtime";

const fallbackDetails: Readonly<Record<string, unknown>> = Object.freeze({});

interface ApiErrorParameters {
  code: string;
  details?: Readonly<Record<string, unknown>>;
  message: string;
  requestId?: string;
  retryAfter?: string;
  status: number;
}

export class ApiError extends Error {
  override readonly name = "ApiError";
  readonly code: string;
  readonly details: Readonly<Record<string, unknown>>;
  readonly requestId: string | undefined;
  readonly retryAfter: string | undefined;
  readonly status: number;

  constructor({ code, details, message, requestId, retryAfter, status }: ApiErrorParameters) {
    super(message);
    this.code = code;
    this.details = details ?? fallbackDetails;
    this.requestId = requestId;
    this.retryAfter = retryAfter;
    this.status = status;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readDocumentedError(value: unknown) {
  if (!isRecord(value) || !isRecord(value.error)) return undefined;

  const { code, details, message, request_id: requestId } = value.error;
  if (
    typeof code !== "string" ||
    !isRecord(details) ||
    typeof message !== "string" ||
    typeof requestId !== "string"
  ) {
    return undefined;
  }

  return { code, details, message, requestId };
}

async function fromResponseError(error: ResponseError): Promise<ApiError> {
  const { response } = error;
  let documentedError: ReturnType<typeof readDocumentedError>;

  try {
    documentedError = readDocumentedError(await response.clone().json());
  } catch {
    documentedError = undefined;
  }

  if (documentedError) {
    const retryAfter = response.headers.get("retry-after");
    return new ApiError({
      ...documentedError,
      status: response.status,
      ...(retryAfter ? { retryAfter } : {}),
    });
  }

  const requestId = response.headers.get("x-request-id");
  const retryAfter = response.headers.get("retry-after");
  return new ApiError({
    code: "API_REQUEST_FAILED",
    message: "The API request could not be completed.",
    status: response.status,
    ...(requestId ? { requestId } : {}),
    ...(retryAfter ? { retryAfter } : {}),
  });
}

export async function translateApiError(error: unknown): Promise<ApiError> {
  if (error instanceof ApiError) return error;
  if (error instanceof ResponseError) return fromResponseError(error);
  if (error instanceof FetchError) {
    return new ApiError({
      code: "API_UNAVAILABLE",
      message: "The API could not be reached.",
      status: 0,
    });
  }
  if (error instanceof SyntaxError) {
    return new ApiError({
      code: "API_INVALID_RESPONSE",
      message: "The API returned an invalid response.",
      status: 0,
    });
  }
  return new ApiError({
    code: "API_CLIENT_ERROR",
    message: "The API request failed safely.",
    status: 0,
  });
}
