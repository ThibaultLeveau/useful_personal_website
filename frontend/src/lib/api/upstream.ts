const DEVELOPMENT_API_ORIGIN = "http://127.0.0.1:8000";
const API_ORIGIN_VARIABLE = "UPW_API_UPSTREAM_ORIGIN";
const ASCII_CONTROL = /[\u0000-\u001f\u007f]/u;

export function resolveApiUpstreamOrigin(
  environment: Readonly<NodeJS.ProcessEnv> = process.env,
): string {
  const configured = environment[API_ORIGIN_VARIABLE];
  if (!configured) {
    if (environment.NODE_ENV === "production") {
      throw new Error("The server-only API upstream origin is required in production.");
    }
    return DEVELOPMENT_API_ORIGIN;
  }

  if (configured !== configured.trim() || ASCII_CONTROL.test(configured)) {
    throw new Error("The server-only API upstream origin is invalid.");
  }

  let parsed: URL;
  try {
    parsed = new URL(configured);
  } catch {
    throw new Error("The server-only API upstream origin is invalid.");
  }

  if (
    (parsed.protocol !== "http:" && parsed.protocol !== "https:") ||
    !parsed.hostname ||
    parsed.hostname.includes("*") ||
    parsed.username ||
    parsed.password ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("The server-only API upstream origin is invalid.");
  }

  return parsed.origin;
}
