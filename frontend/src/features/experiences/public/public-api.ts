import "server-only";

import {
  PublicExperiencesApi,
  type PublicExperiencesListRequest,
} from "@/generated/api/src/apis/PublicExperiencesApi";
import type { ListEnvelopePublicExperienceData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

function scheduledContentFetch(): FetchAPI {
  return async (input, init) =>
    fetch(input, {
      ...init,
      cache: "no-store",
      credentials: "omit",
    });
}

export async function getPublicExperiences(
  filters: PublicExperiencesListRequest = {},
): Promise<ListEnvelopePublicExperienceData> {
  const api = new PublicExperiencesApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: scheduledContentFetch(),
    }),
  );
  return api.publicExperiencesList({ page: 1, pageSize: 100, ...filters });
}
