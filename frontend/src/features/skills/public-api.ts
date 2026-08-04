import "server-only";

import { PublicSkillsApi } from "@/generated/api/src/apis/PublicSkillsApi";
import type { ListEnvelopePublicSkillData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

export interface PublicSkillFilters {
  category?: string;
  featured?: boolean;
  search?: string;
  sort?: string;
}

function publicFetch(): FetchAPI {
  return async (input, init) =>
    fetch(input, {
      ...init,
      credentials: "omit",
      next: { revalidate: 60, tags: ["public-skills"] },
    });
}

export async function getPublicSkills(
  filters: PublicSkillFilters = {},
): Promise<ListEnvelopePublicSkillData> {
  const api = new PublicSkillsApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: publicFetch(),
    }),
  );
  return api.publicSkillsList({ page: 1, pageSize: 100, ...filters });
}
