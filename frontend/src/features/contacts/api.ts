"use client";
import { ContactAdministrationApi } from "@/generated/api/src/apis/ContactAdministrationApi";
import { ContactApi } from "@/generated/api/src/apis/ContactApi";
import type {
  ContactDetailData,
  ContactFormContextData,
  ContactState,
  ContactSubmitRequest,
  ContactSummaryData,
} from "@/generated/api/src/models";
import { Configuration } from "@/generated/api/src/runtime";

const configuration = new Configuration({ basePath: "", credentials: "same-origin" });
const publicClient = new ContactApi(configuration);
const adminClient = new ContactAdministrationApi(configuration);
function csrf() {
  const found = document.cookie
    .split(";")
    .map((x) => x.trim())
    .find((x) => x.startsWith("__Host-admin_csrf="));
  return found ? decodeURIComponent(found.split("=").slice(1).join("=")) : "";
}
export const contactApi = {
  async context(): Promise<ContactFormContextData> {
    return (await publicClient.formContextApiV1PublicContactsFormContextGet({ cache: "no-store" }))
      .data;
  },
  async submit(input: ContactSubmitRequest): Promise<void> {
    await publicClient.submitContactApiV1PublicContactsPost(
      { idempotencyKey: crypto.randomUUID(), contactSubmitRequest: input },
      { cache: "no-store" },
    );
  },
  async list(state: ContactState): Promise<ContactSummaryData[]> {
    return (
      await adminClient.listContactsApiV1AdminContactsGet(
        { state, pageSize: 50 },
        { cache: "no-store" },
      )
    ).data;
  },
  async get(id: string): Promise<ContactDetailData> {
    return (
      await adminClient.getContactApiV1AdminContactsContactIdGet(
        { contactId: id },
        { cache: "no-store" },
      )
    ).data;
  },
  async transition(
    item: ContactDetailData,
    state: "read" | "archived",
  ): Promise<ContactDetailData> {
    return (
      await adminClient.transitionContactApiV1AdminContactsContactIdStatePatch(
        {
          contactId: item.id,
          xCSRFToken: csrf(),
          ifMatch: `"v${item.version}"`,
          contactTransitionRequest: { state },
        },
        { cache: "no-store" },
      )
    ).data;
  },
  async delete(item: ContactDetailData): Promise<void> {
    await adminClient.deleteContactApiV1AdminContactsContactIdDelete(
      { contactId: item.id, xCSRFToken: csrf(), ifMatch: `"v${item.version}"` },
      { cache: "no-store" },
    );
  },
};
