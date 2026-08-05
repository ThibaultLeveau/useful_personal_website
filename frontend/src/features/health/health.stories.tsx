import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import type { AdminHealthData } from "@/generated/api/src/models";
import { ApiError, type AdminHealthApiBoundary } from "@/lib/api";

import { HealthPanel } from "./health-panel";

function apiFor(data: AdminHealthData): AdminHealthApiBoundary {
  return {
    get: async () => ({ data, meta: { requestId: "storybook-health" } }),
  };
}

const operational: AdminHealthData = {
  applicationStatus: "operational",
  buildCommit: "abcdef1",
  buildVersion: "1.2.3",
  checkedAt: new Date("2026-08-03T08:00:00Z"),
  databaseStatus: "operational",
  migrationStatus: "current",
  status: "operational",
};

const meta = {
  title: "Administration/Health",
  component: HealthPanel,
  parameters: { layout: "padded", nextjs: { appDirectory: true } },
} satisfies Meta<typeof HealthPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Operational: Story = { args: { api: apiFor(operational) } };

export const Degraded: Story = {
  args: {
    api: apiFor({
      ...operational,
      databaseStatus: "unavailable",
      migrationStatus: "unknown",
      status: "degraded",
    }),
  },
};

export const Unavailable: Story = {
  args: {
    api: {
      get: async () => {
        throw new ApiError({
          code: "API_UNAVAILABLE",
          message: "The API could not be reached.",
          requestId: "storybook-unavailable",
          status: 0,
        });
      },
    },
  },
};

export const Unknown: Story = {
  args: {
    api: {
      get: async () => {
        throw new ApiError({
          code: "API_INVALID_RESPONSE",
          message: "The API returned an invalid response.",
          status: 0,
        });
      },
    },
  },
};
