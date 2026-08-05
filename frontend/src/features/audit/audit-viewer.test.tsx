import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AuditEntryData, ListEnvelopeAuditEntryData } from "@/generated/api/src/models";
import { ApiError } from "@/lib/api";

import type { AuditApi } from "./api";
import { AuditViewer } from "./audit-viewer";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/audit",
  useRouter: () => ({ replace }),
}));

const EVENT: AuditEntryData = {
  actorId: "0198abc0-0000-7000-8000-000000000052",
  actorType: "administrator",
  eventType: "project.published",
  id: "0198abc0-0000-7000-8000-000000000051",
  metadata: { fields: "published_revision", version: "2" },
  occurredAt: new Date("2026-08-04T12:00:00Z"),
  outcome: "success",
  requestId: "audit-request-1",
  resourceId: "0198abc0-0000-7000-8000-000000000050",
  resourceType: "project",
  schemaVersion: 1,
};

function result(data: AuditEntryData[] = [EVENT]): ListEnvelopeAuditEntryData {
  return {
    data,
    meta: {
      requestId: "response-request",
      pagination: {
        hasNext: false,
        hasPrevious: false,
        page: 1,
        pageSize: 20,
        totalItems: data.length,
        totalPages: data.length ? 1 : 0,
      },
    },
  };
}

function api(overrides: Partial<AuditApi> = {}): AuditApi {
  return {
    events: vi.fn(async () => ["project.published", "admin.login_failed"]),
    get: vi.fn(async () => EVENT),
    list: vi.fn(async () => result()),
    ...overrides,
  };
}

beforeEach(() => replace.mockReset());

describe("audit viewer", () => {
  it("renders equivalent table and card content with safe metadata omitted", async () => {
    render(<AuditViewer api={api()} />);
    expect(await screen.findByRole("heading", { name: "Audit activity" })).toBeVisible();
    expect(screen.getAllByText("project.published")).toHaveLength(3);
    expect(screen.getAllByText("success")).toHaveLength(2);
    expect(screen.queryByText(/password|token secret|postgresql/i)).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /view/i })).toHaveLength(2);
  });

  it("applies exact filters and exposes removable active chips", async () => {
    const boundary = api();
    const user = userEvent.setup();
    render(<AuditViewer api={boundary} />);
    await screen.findAllByText("project.published", { selector: "code" });
    await user.selectOptions(screen.getByLabelText("Outcome"), "success");
    await user.type(screen.getByLabelText("Resource type"), "project");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() =>
      expect(boundary.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ outcome: "success", resourceType: "project" }),
        expect.any(AbortSignal),
      ),
    );
    expect(screen.getByRole("button", { name: /outcome: success/i })).toBeVisible();
  });

  it("renders the no-match state and clears protected data on session expiry", async () => {
    const empty = api({ list: vi.fn(async () => result([])) });
    const { rerender } = render(<AuditViewer api={empty} />);
    expect(await screen.findByRole("heading", { name: "No matching events" })).toBeVisible();
    rerender(
      <AuditViewer
        api={api({
          list: vi.fn(async () => {
            throw new ApiError({
              code: "AUTHENTICATION_REQUIRED",
              message: "Expired",
              status: 401,
            });
          }),
        })}
      />,
    );
    expect(
      await screen.findByText("Protected audit details were cleared. Redirecting securely…"),
    ).toBeVisible();
    expect(screen.queryByText("project.published")).not.toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/admin/session-expired?return_to=%2Fadmin%2Faudit");
  });
});
