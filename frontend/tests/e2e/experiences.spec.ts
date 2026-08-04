import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const evidenceDirectory = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M5",
  "screenshots",
);

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/u);
}

async function expectNoOverflow(page: Page) {
  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll).toBeLessThanOrEqual(width.client);
}

test.describe("experience lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("keeps drafts private and publishes immutable revisions", async ({ page }, testInfo) => {
    test.setTimeout(180_000);
    const viewport = testInfo.project.name.replace("chromium-", "");
    const role = `Experience proof ${viewport} ${Date.now()}`;
    const revisedRole = `${role} refined`;

    await signIn(page);
    await page.goto("/admin/experiences");
    await expect(page.getByRole("heading", { name: "Experience ledger" })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    const create = page.locator("form").filter({
      has: page.getByRole("button", { name: "Create draft" }),
    });
    await create.getByLabel("Company").fill("Evidence Studio");
    await create.getByLabel("Role title").fill(role);
    await create.getByLabel("Start date").fill("2024-01-01");
    await create.getByLabel("Short summary").fill("A synthetic browser lifecycle proof.");
    await create.getByRole("button", { name: "Create draft" }).click();
    await expect(page).toHaveURL(/\/admin\/experiences\/.+\/edit$/u);

    await page.getByLabel("Company HTTPS URL").fill("https://example.test/careers");
    await page.getByLabel("Location").fill("Paris, France");
    await page.getByLabel("Detailed description").fill("Private draft content for M5 evidence.");
    await page.getByRole("button", { name: "Add responsibilities item" }).click();
    await page
      .getByRole("textbox", { exact: true, name: "Responsibilities item 1" })
      .fill("Designed revision-safe services");
    await page.getByRole("button", { name: "Add achievements item" }).click();
    await page
      .getByRole("textbox", { exact: true, name: "Achievements item 1" })
      .fill("Proved live content isolation");
    await page.getByRole("button", { name: "Add technologies item" }).click();
    await page
      .getByRole("textbox", { exact: true, name: "Technologies item 1" })
      .fill("PostgreSQL");
    await page.getByRole("tab", { name: "Relations" }).click();
    await page.getByRole("checkbox", { name: /Python/u }).check();
    await page.getByRole("button", { name: "Save draft" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Draft saved" })).toBeVisible();

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-experience-editor-${viewport}.png`),
    });

    await page.getByRole("link", { name: "Preview draft" }).click();
    await expect(page.getByText("Draft preview - not public", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: role })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-experience-preview-${viewport}.png`),
    });

    await page.getByRole("link", { name: "Return to editor" }).click();
    await page.getByRole("tab", { name: "Publication" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Publish now" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Experience published" }),
    ).toBeVisible();

    await page.goto("/experience");
    await expect(page.getByRole("heading", { name: role })).toBeVisible();
    const publicEntry = page.getByRole("article", { name: role });
    await expect(publicEntry.getByRole("link", { name: "Python" })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `public-experience-${viewport}.png`),
    });
    if (viewport === "1440") {
      for (const width of [320, 390, 768, 1024, 1440, 1920]) {
        await page.setViewportSize({ height: 900, width });
        for (const theme of ["light", "dark"] as const) {
          await page.evaluate((preference) => {
            localStorage.setItem("upw-theme", preference);
            document.documentElement.dataset.theme = preference;
            document.documentElement.dataset.themePreference = preference;
            document.documentElement.style.colorScheme = preference;
            window.dispatchEvent(new Event("upw-theme-change"));
          }, theme);
          await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
          await expectNoOverflow(page);
          await page.screenshot({
            animations: "disabled",
            fullPage: true,
            path: path.join(evidenceDirectory, `public-experience-${width}-${theme}.png`),
          });
        }
      }
      await page.setViewportSize({ height: 900, width: 1440 });
    }

    await page.goto("/admin/experiences");
    const record = page.locator("li").filter({ hasText: role });
    await record.getByRole("link", { name: "Edit" }).click();
    await expect(page).toHaveURL(/\/admin\/experiences\/.+\/edit$/u);
    await expect(page.getByRole("heading", { name: role })).toBeVisible();
    await page.getByLabel("Role title").fill(revisedRole);
    await expect(page.getByRole("heading", { name: revisedRole })).toBeVisible();
    await page.getByRole("button", { name: "Save draft" }).click();
    await expect(page.getByText(/published changes pending/u)).toBeVisible();

    const liveBeforeRepublish = await page.request.get("/api/v1/public/experiences");
    const liveBeforeRepublishText = await liveBeforeRepublish.text();
    expect(liveBeforeRepublishText).toContain(role);
    expect(liveBeforeRepublishText).not.toContain(revisedRole);
    await page.getByRole("tab", { name: "Publication" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Publish now" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Experience published" }),
    ).toBeVisible();

    await page.goto("/experience");
    await expect(page.getByRole("heading", { name: revisedRole })).toBeVisible();
    await page.goto("/admin/experiences");
    const revisedRecord = page.locator("li").filter({ hasText: revisedRole });
    await revisedRecord.getByRole("button", { name: "Hide" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Experience hidden" })).toBeVisible();
    const hiddenPublic = await page.request.get("/api/v1/public/experiences");
    expect(await hiddenPublic.text()).not.toContain(revisedRole);
    await revisedRecord.getByRole("button", { name: "Show" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Experience visible" })).toBeVisible();
    page.once("dialog", (dialog) => dialog.accept());
    await revisedRecord.getByRole("button", { name: "Unpublish" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Experience unpublished" }),
    ).toBeVisible();
    page.once("dialog", (dialog) => dialog.accept());
    await revisedRecord.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Experience deleted" })).toBeVisible();
  });
});
