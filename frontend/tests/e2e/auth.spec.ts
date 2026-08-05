import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const initialAdministratorPassword = process.env.M1_TEST_ADMIN_INITIAL_PASSWORD;
const evidenceDirectory = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M1",
  "screenshots",
);

test.describe("administrator authentication against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack authentication proof.",
  );

  test("login, protected navigation, accessibility, logout, and history safety", async ({
    page,
  }, testInfo) => {
    const viewportName = testInfo.project.name.replace("chromium-", "");

    await page.goto("/admin/login");
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await page.screenshot({
      animations: "disabled",
      path: path.join(evidenceDirectory, `admin-login-${viewportName}.png`),
      fullPage: true,
    });

    const loginAccessibility = await new AxeBuilder({ page }).analyze();
    expect(loginAccessibility.violations).toEqual([]);

    await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
    await page.getByLabel("Password", { exact: true }).fill("deliberately-wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert", { name: "Unable to sign in" })).toContainText(
      "The email or password is incorrect.",
    );

    await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.waitForURL(/\/admin(?:\/change-password)?$/u, { timeout: 3_000 }).catch(() => null);
    if (initialAdministratorPassword && /\/admin\/login/u.test(page.url())) {
      await page.getByLabel("Password", { exact: true }).fill(initialAdministratorPassword);
      await page.getByRole("button", { name: "Sign in" }).click();
    }
    await page.waitForURL(/\/admin(?:\/change-password)?$/u);
    if (page.url().endsWith("/admin/change-password")) {
      expect(initialAdministratorPassword).toBeTruthy();
      await page
        .getByRole("textbox", { name: "Initial password", exact: true })
        .fill(initialAdministratorPassword!);
      await page
        .getByRole("textbox", { name: "New password", exact: true })
        .fill(administratorPassword!);
      await page
        .getByRole("textbox", { name: "Confirm new password", exact: true })
        .fill(administratorPassword!);
      await page.getByRole("button", { name: "Change password" }).click();
    }

    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole("heading", { name: "Site configuration" })).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { name: "Site configuration" })).toBeVisible();
    await page.locator("main").focus();
    await expect(page.locator("main")).toBeFocused();

    for (const csrfHeader of [undefined, "forged-csrf-value"]) {
      const denial = await page.evaluate(async (header) => {
        const response = await fetch("/api/v1/auth/session/refresh", {
          method: "POST",
          ...(header ? { headers: { "X-CSRF-Token": header } } : {}),
        });
        return {
          allowOrigin: response.headers.get("access-control-allow-origin"),
          body: (await response.json()) as { error?: { code?: string; request_id?: string } },
          cacheControl: response.headers.get("cache-control"),
          status: response.status,
        };
      }, csrfHeader);
      expect(denial.status).toBe(403);
      expect(denial.body.error?.code).toBe("CSRF_INVALID");
      expect(denial.body.error?.request_id).toMatch(/^[a-f0-9]{32}$/);
      expect(denial.cacheControl).toBe("private, no-store");
      expect(denial.allowOrigin).not.toBe("*");
    }

    const width = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(width.scroll).toBeLessThanOrEqual(width.client);

    const overviewAccessibility = await new AxeBuilder({ page }).analyze();
    expect(overviewAccessibility.violations).toEqual([]);
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
    await page.screenshot({
      animations: "disabled",
      path: path.join(evidenceDirectory, `admin-overview-${viewportName}.png`),
      fullPage: true,
    });

    await page.getByRole("link", { name: "Account" }).click();
    await expect(page.getByRole("heading", { name: "Account security" })).toBeVisible();
    const continueSession = page.getByRole("button", { name: "Continue session" });
    await expect(continueSession).toBeEnabled();
    await continueSession.click();
    await expect(continueSession).toBeEnabled();

    const sessionRegion = page.getByRole("region", { name: "Administrator session" });
    await sessionRegion.getByRole("button", { name: "Sign out" }).click();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Account security" })).toHaveCount(0);

    await page.goBack();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Site configuration" })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
