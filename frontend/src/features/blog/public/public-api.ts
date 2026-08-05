import "server-only";

import { cache } from "react";

import {
  PublicBlogApi,
  type PublicBlogPostsListRequest,
} from "@/generated/api/src/apis/PublicBlogApi";
import type { ListEnvelopePublicPostData, PublicPostData } from "@/generated/api/src/models";
import { Configuration, type FetchAPI } from "@/generated/api/src/runtime";
import { resolveApiUpstreamOrigin } from "@/lib/api/upstream";

function publicFetch(): FetchAPI {
  return async (input, init) => fetch(input, { ...init, cache: "no-store", credentials: "omit" });
}

function api(): PublicBlogApi {
  return new PublicBlogApi(
    new Configuration({
      basePath: resolveApiUpstreamOrigin(),
      credentials: "omit",
      fetchApi: publicFetch(),
    }),
  );
}

export async function getPublicPosts(
  filters: PublicBlogPostsListRequest = {},
): Promise<ListEnvelopePublicPostData> {
  return api().publicBlogPostsList({ page: 1, pageSize: 12, ...filters });
}

export const getPublicPost = cache(async (slug: string): Promise<PublicPostData> => {
  const result = await api().publicBlogPostDetail({ slug });
  return result.data;
});
