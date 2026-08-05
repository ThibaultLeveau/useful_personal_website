import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/u);
}

test.describe("API token lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("reveals once, authorizes by scope, rotates, and revokes", async ({ page, request }) => {
    const tokenName = `Browser integration ${Date.now()}`;
    expect((await request.get("/api/v1/integrations/projects")).status()).toBe(401);

    await signIn(page);
    await page.goto("/admin/api-tokens");
    await expect(page.getByRole("heading", { name: "API tokens" })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

    await page.getByLabel("Name").fill(tokenName);
    await page.getByRole("checkbox", { name: "Read content" }).check();
    await page.getByRole("button", { name: "Create token" }).click();
    const reveal = page.getByRole("alert", { name: "Copy this token now" });
    await expect(reveal).toBeVisible();
    const original = (await reveal.locator("code").textContent())?.trim();
    expect(original).toMatch(/^pp_live_[^.]+\..+$/u);
    expect(
      (
        await request.get("/api/v1/integrations/projects", {
          headers: { Authorization: `Bearer ${original}` },
        })
      ).status(),
    ).toBe(200);

    await reveal.getByRole("button", { name: "I stored it securely" }).click();
    await expect(reveal).toHaveCount(0);
    const row = page.getByRole("row", { name: new RegExp(tokenName, "u") });
    page.once("dialog", (dialog) => dialog.accept());
    await row.getByRole("button", { name: "Rotate" }).click();
    const rotatedReveal = page.getByRole("alert", { name: "Copy this token now" });
    const rotated = (await rotatedReveal.locator("code").textContent())?.trim();
    expect(rotated).toMatch(/^pp_live_[^.]+\..+$/u);
    expect(rotated).not.toBe(original);
    expect(
      (
        await request.get("/api/v1/integrations/projects", {
          headers: { Authorization: `Bearer ${original}` },
        })
      ).status(),
    ).toBe(401);
    expect(
      (
        await request.get("/api/v1/integrations/projects", {
          headers: { Authorization: `Bearer ${rotated}` },
        })
      ).status(),
    ).toBe(200);

    await rotatedReveal.getByRole("button", { name: "I stored it securely" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await row.getByRole("button", { name: "Revoke" }).click();
    await expect(page.getByRole("status")).toContainText("Token revoked");
    expect(
      (
        await request.get("/api/v1/integrations/projects", {
          headers: { Authorization: `Bearer ${rotated}` },
        })
      ).status(),
    ).toBe(401);
    await expect(
      page.getByRole("row", { name: new RegExp(tokenName, "u") }).filter({ hasText: "revoked" }),
    ).toHaveCount(2);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
});
