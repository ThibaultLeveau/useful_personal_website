import "server-only";

import { cache } from "react";

import {
  PublicProjectsApi,
  type PublicProjectsListRequest,
} from "@/generated/api/src/apis/PublicProjectsApi";
import type { ListEnvelopePublicProjectData, PublicProjectData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

function scheduledContentFetch(): FetchAPI {
  return async (input, init) => fetch(input, { ...init, cache: "no-store", credentials: "omit" });
}

function api(): PublicProjectsApi {
  return new PublicProjectsApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: scheduledContentFetch(),
    }),
  );
}

export async function getPublicProjects(
  filters: PublicProjectsListRequest = {},
): Promise<ListEnvelopePublicProjectData> {
  return api().publicProjectsList({ page: 1, pageSize: 24, ...filters });
}

export const getPublicProject = cache(async (slug: string): Promise<PublicProjectData> => {
  const result = await api().publicProjectsDetail({ slug });
  return result.data;
});
