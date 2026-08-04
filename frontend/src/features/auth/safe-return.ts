const DEFAULT_ADMIN_PATH = "/admin";
const SIGNED_OUT_ROUTES = new Set(["/admin/login", "/admin/session-expired"]);

export function isSignedOutAuthRoute(pathname: string): boolean {
  return SIGNED_OUT_ROUTES.has(pathname);
}

export function normalizeAdminReturnPath(value: string | null | undefined): string {
  if (
    !value ||
    value.startsWith("//") ||
    value.includes("\\") ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    return DEFAULT_ADMIN_PATH;
  }

  try {
    const parsed = new URL(value, "https://admin.invalid");
    if (
      parsed.origin !== "https://admin.invalid" ||
      (parsed.pathname !== "/admin" && !parsed.pathname.startsWith("/admin/")) ||
      SIGNED_OUT_ROUTES.has(parsed.pathname)
    ) {
      return DEFAULT_ADMIN_PATH;
    }
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    return DEFAULT_ADMIN_PATH;
  }
}

export function currentSafeAdminPath(pathname: string): string {
  const search = typeof window === "undefined" ? "" : window.location.search;
  return normalizeAdminReturnPath(`${pathname}${search}`);
}

export function returnPathFromCurrentLocation(): string {
  if (typeof window === "undefined") return DEFAULT_ADMIN_PATH;
  return normalizeAdminReturnPath(new URLSearchParams(window.location.search).get("return_to"));
}

export function loginPathFor(pathname: string): string {
  const returnPath = currentSafeAdminPath(pathname);
  return `/admin/login?return_to=${encodeURIComponent(returnPath)}`;
}

export function expiredPathFor(pathname: string): string {
  const returnPath = currentSafeAdminPath(pathname);
  return `/admin/session-expired?return_to=${encodeURIComponent(returnPath)}`;
}
