import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const evidenceDirectory = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M2",
  "screenshots",
);

test.describe("administrator health against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack health proof.",
  );

  test("denies anonymous access and renders an accessible operational summary", async ({
    page,
  }, testInfo) => {
    const anonymous = await page.request.get("/api/v1/admin/health");
    expect(anonymous.status()).toBe(401);
    expect(anonymous.headers()["cache-control"]).toBe("private, no-store");
    expect((await anonymous.json()).error.code).toBe("AUTHENTICATION_REQUIRED");

    await page.goto("/admin/health");
    await expect(page).toHaveURL(/\/admin\/login\?return_to=%2Fadmin%2Fhealth$/);
    await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
    await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/admin\/health$/);
    await expect(page.getByRole("heading", { name: "Application health" })).toBeVisible();
    await expect(page.getByText("Operational").first()).toBeVisible();
    await expect(page.getByText("Current", { exact: true })).toBeVisible();
    await expect(page.getByText("Stale result")).toHaveCount(0);

    const healthResponse = await page.evaluate(async () => {
      const response = await fetch("/api/v1/admin/health", { credentials: "same-origin" });
      return {
        body: await response.json(),
        cacheControl: response.headers.get("cache-control"),
        status: response.status,
      };
    });
    expect(healthResponse.status).toBe(200);
    expect(healthResponse.cacheControl).toBe("private, no-store");
    const serialized = JSON.stringify(healthResponse.body).toLowerCase();
    for (const forbidden of ["postgresql", "database_url", "select ", "password", "traceback"]) {
      expect(serialized).not.toContain(forbidden);
    }

    const refresh = page.getByRole("button", { name: "Refresh status" });
    await refresh.click();
    await expect(page.getByRole("link", { name: "Review account" })).toBeEnabled();
    await expect(page.getByRole("status")).toContainText("Health status refreshed. Operational.");
    await expect(refresh).toHaveText("Refresh status");

    const dimensions = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.client);

    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(accessibility.violations).toEqual([]);
    await page.locator("main").focus();
    await expect(page.locator("main")).toBeFocused();
    await expect
      .poll(
        async () =>
          (await page.getByRole("link", { name: /skip to administration/i }).boundingBox())?.y ?? 0,
      )
      .toBeLessThan(0);
    await page.evaluate(() => window.scrollTo(0, 0));
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      path: path.join(
        evidenceDirectory,
        `admin-health-${testInfo.project.name.replace("chromium-", "")}.png`,
      ),
      fullPage: true,
    });
  });
});
