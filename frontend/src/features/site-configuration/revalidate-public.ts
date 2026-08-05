"use server";

import { revalidatePath, updateTag } from "next/cache";
import { cookies } from "next/headers";

import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

const SESSION_COOKIE = "__Host-admin_session";

export async function revalidatePublicConfiguration(
  scope: "footer" | "navigation" | "profile" | "settings",
): Promise<boolean> {
  try {
    const session = (await cookies()).get(SESSION_COOKIE)?.value;
    if (!session) return false;

    const response = await fetch(`${resolveApiUpstreamOrigin()}/api/v1/auth/session`, {
      cache: "no-store",
      credentials: "omit",
      headers: {
        accept: "application/json",
        cookie: `${SESSION_COOKIE}=${session}`,
      },
      redirect: "manual",
    });
    if (!response.ok) return false;

    if (scope === "profile") {
      updateTag("public-profile");
      revalidatePath("/about");
    }
    if (scope === "navigation") updateTag("public-navigation");
    if (scope === "settings" || scope === "footer") updateTag("public-site");
    if (scope !== "profile") {
      // A build-time fallback has no data-tag dependency, so invalidate the
      // currently available public routes as well as their registered tags.
      revalidatePath("/");
      revalidatePath("/about");
    }
    return true;
  } catch {
    return false;
  }
}
