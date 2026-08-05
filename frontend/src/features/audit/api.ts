"use client";

import { AuditAdministrationApi } from "@/generated/api/src/apis/AuditAdministrationApi";
import type {
  ActorType,
  AuditEntryData,
  AuditOutcome,
  ListEnvelopeAuditEntryData,
} from "@/generated/api/src/models";
import { Configuration } from "@/generated/api/src/runtime";

const generated = new AuditAdministrationApi(
  new Configuration({ basePath: "", credentials: "same-origin" }),
);

function requestInit(signal?: AbortSignal): RequestInit {
  return { cache: "no-store", ...(signal ? { signal } : {}) };
}

export interface AuditFilters {
  eventType?: string;
  actorType?: ActorType;
  actorId?: string;
  resourceType?: string;
  resourceId?: string;
  outcome?: AuditOutcome;
  occurredFrom?: Date;
  occurredTo?: Date;
  requestId?: string;
  page: number;
}

export interface AuditApi {
  events(signal?: AbortSignal): Promise<string[]>;
  list(filters: AuditFilters, signal?: AbortSignal): Promise<ListEnvelopeAuditEntryData>;
  get(id: string, signal?: AbortSignal): Promise<AuditEntryData>;
}

export const auditApi: AuditApi = {
  async events(signal) {
    return (await generated.adminAuditEventCatalog(requestInit(signal))).data.events;
  },
  async list(filters, signal) {
    return generated.adminAuditList({ ...filters, pageSize: 20 }, requestInit(signal));
  },
  async get(id, signal) {
    return (await generated.adminAuditGet({ entryId: id }, requestInit(signal))).data;
  },
};
