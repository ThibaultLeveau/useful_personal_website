import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const useExternalServer = process.env.PLAYWRIGHT_EXTERNAL_SERVER === "1";

export default defineConfig({
  testDir: "./tests/e2e",
  // These real-stack tests intentionally mutate one administrator's shared
  // rate-limit and session state. Serial workers make that security lifecycle
  // deterministic instead of racing invalid-login and successful-login flows.
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    colorScheme: "light",
    trace: "retain-on-failure",
  },
  projects: [
    ...(
      [
        [320, 800],
        [360, 800],
        [390, 844],
        [768, 1024],
        [1024, 900],
        [1280, 900],
        [1440, 1000],
        [1920, 1080],
      ] as const
    ).map(([width, height]) => ({
      name: `chromium-${width}`,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width, height },
      },
    })),
    {
      name: "firefox-1440",
      use: { ...devices["Desktop Firefox"], viewport: { width: 1440, height: 1000 } },
    },
    {
      name: "webkit-1440",
      use: { ...devices["Desktop Safari"], viewport: { width: 1440, height: 1000 } },
    },
  ],
  ...(useExternalServer
    ? {}
    : {
        webServer: {
          command: process.env.CI
            ? "node node_modules/next/dist/bin/next build && node node_modules/next/dist/bin/next start"
            : "node node_modules/next/dist/bin/next dev",
          url: baseURL,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      }),
});
