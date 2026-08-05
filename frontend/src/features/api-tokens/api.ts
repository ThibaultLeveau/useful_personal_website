"use client";
import { APITokenAdministrationApi } from "@/generated/api/src/apis/APITokenAdministrationApi";
import type {
  ApiTokenCreateRequest,
  ApiTokenData,
  ApiTokenRotateRequest,
  ApiTokenScope,
  ApiTokenSecretData,
} from "@/generated/api/src/models";
import { Configuration } from "@/generated/api/src/runtime";
const generated = new APITokenAdministrationApi(
  new Configuration({ basePath: "", credentials: "same-origin" }),
);
function csrf(): string {
  const found = document.cookie
    .split(";")
    .map((x) => x.trim())
    .find((x) => x.startsWith("__Host-admin_csrf="));
  if (!found) throw new Error("Protected session unavailable");
  return decodeURIComponent(found.split("=").slice(1).join("="));
}
export const apiTokenApi = {
  async scopes(): Promise<ApiTokenScope[]> {
    return (await generated.scopeCatalogApiV1AdminApiTokensScopesGet({ cache: "no-store" })).data
      .scopes;
  },
  async list(): Promise<ApiTokenData[]> {
    return (
      await generated.listTokensApiV1AdminApiTokensGet({ pageSize: 100 }, { cache: "no-store" })
    ).data;
  },
  async create(input: ApiTokenCreateRequest): Promise<ApiTokenSecretData> {
    return (
      await generated.createTokenApiV1AdminApiTokensPost(
        { xCSRFToken: csrf(), apiTokenCreateRequest: input },
        { cache: "no-store" },
      )
    ).data;
  },
  async rotate(item: ApiTokenData, input: ApiTokenRotateRequest): Promise<ApiTokenSecretData> {
    return (
      await generated.rotateTokenApiV1AdminApiTokensTokenIdRotatePost(
        {
          tokenId: item.id,
          xCSRFToken: csrf(),
          ifMatch: `"v${item.version}"`,
          apiTokenRotateRequest: input,
        },
        { cache: "no-store" },
      )
    ).data;
  },
  async revoke(item: ApiTokenData): Promise<ApiTokenData> {
    return (
      await generated.revokeTokenApiV1AdminApiTokensTokenIdRevokePost(
        { tokenId: item.id, xCSRFToken: csrf(), ifMatch: `"v${item.version}"` },
        { cache: "no-store" },
      )
    ).data;
  },
};
