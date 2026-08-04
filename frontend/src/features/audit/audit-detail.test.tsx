import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AuditEntryData } from "@/generated/api/src/models";

import type { AuditApi } from "./api";
import { AuditDetail } from "./audit-detail";

const entry: AuditEntryData = {
  actorId: null,
  actorLabel: "retention-operator",
  actorType: "system",
  eventType: "audit.retention_executed",
  id: "0198abc0-0000-7000-8000-000000000061",
  metadata: { deleted_count: "18", retention_days: "400" },
  occurredAt: new Date("2026-08-04T12:00:00Z"),
  outcome: "success",
  requestId: "operation:0198abc0-0000-7000-8000-000000000060",
  resourceId: null,
  resourceType: "audit_entry",
  schemaVersion: 1,
};

it("explains absence-based redaction and renders only safe metadata", async () => {
  const api: AuditApi = {
    events: vi.fn(async () => []),
    get: vi.fn(async () => entry),
    list: vi.fn(),
  };
  render(<AuditDetail api={api} id={entry.id} />);
  expect(await screen.findByRole("heading", { name: "audit.retention_executed" })).toBeVisible();
  expect(screen.getByText(/Sensitive values are absent, not masked/i)).toBeVisible();
  expect(screen.getByText("18")).toBeVisible();
  expect(screen.queryByText(/password|authorization/i)).not.toBeInTheDocument();
});
