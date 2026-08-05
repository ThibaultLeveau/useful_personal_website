import "server-only";

import { cache } from "react";

import { PublicPagesApi } from "@/generated/api/src/apis/PublicPagesApi";
import type { ListEnvelopePublicPageRouteData, PublicPageData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

function publicFetch(): FetchAPI {
  return async (input, init) => fetch(input, { ...init, cache: "no-store", credentials: "omit" });
}

function api(): PublicPagesApi {
  return new PublicPagesApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: publicFetch(),
    }),
  );
}

export const getPublicHomePage = cache(async (): Promise<PublicPageData> => {
  return (await api().publicPageHomeGet({ cache: "no-store" })).data;
});

export const getPublicCustomPage = cache(async (slug: string): Promise<PublicPageData> => {
  return (await api().publicPageCustomGet({ slug }, { cache: "no-store" })).data;
});

export async function getPublicPageRoutes(): Promise<ListEnvelopePublicPageRouteData> {
  return api().publicPagesList({ page: 1, pageSize: 100 }, { cache: "no-store" });
}
