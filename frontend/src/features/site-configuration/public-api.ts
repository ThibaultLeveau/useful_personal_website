import "server-only";

import { PublicSiteApi } from "@/generated/api/src/apis/PublicSiteApi";
import type {
  PublicNavigationData,
  PublicProfileData,
  PublicSiteSettingsData,
} from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

const PUBLIC_REVALIDATE_SECONDS = 60;

function publicFetch(tag: string): FetchAPI {
  return async (input, init) =>
    fetch(input, {
      ...init,
      credentials: "omit",
      next: { revalidate: PUBLIC_REVALIDATE_SECONDS, tags: [tag] },
    });
}

function api(tag: string): PublicSiteApi {
  return new PublicSiteApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: publicFetch(tag),
    }),
  );
}

export async function getPublicProfile(): Promise<PublicProfileData> {
  return (await api("public-profile").publicProfileGet()).data;
}

export async function getPublicSite(): Promise<PublicSiteSettingsData> {
  return (await api("public-site").publicSiteGet()).data;
}

export async function getPublicNavigation(): Promise<PublicNavigationData> {
  return (await api("public-navigation").publicNavigationGet()).data;
}
