import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const fixture = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M1",
  "screenshots",
  "admin-login-320.png",
);

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/u);
}

test.describe("page, block, and media lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("uploads media and composes, exports, publishes, and removes a page", async ({ page }) => {
    test.setTimeout(180_000);
    const suffix = Date.now();
    const slug = `browser-page-${suffix}`;
    const title = `Browser page ${suffix}`;
    const heroHeading = `Composed in the browser ${suffix}`;
    const mediaName = `Browser media ${suffix}`;

    await signIn(page);
    await page.goto("/admin/media");
    await expect(page.getByRole("heading", { name: "Media library" })).toBeVisible();
    await page.getByLabel("Upload image").setInputFiles(fixture);
    await page.getByRole("button", { name: "Upload", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("uploaded and verified");
    await page.getByLabel("Display name", { exact: true }).fill(mediaName);
    await page.getByRole("button", { name: "Save name" }).click();
    await expect(page.getByRole("status")).toContainText("Display name saved");
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

    await page.goto("/admin/pages");
    await page.getByLabel("Page title").fill(title);
    await page.getByLabel("Route").selectOption("custom");
    await page.getByLabel("Slug").fill(slug);
    await page.getByRole("button", { name: "Create page" }).click();
    await expect(page).toHaveURL(/\/admin\/pages\/.+\/edit$/u);
    const pageId = page.url().match(/\/admin\/pages\/([^/]+)\/edit/u)?.[1];
    expect(pageId).toBeTruthy();

    await page.getByRole("button", { name: "hero narrative", exact: true }).click();
    await page.getByRole("button", { name: /^01 hero hero$/u }).click();
    const config = page.getByLabel("Typed configuration");
    await config.fill(
      JSON.stringify({ heading: heroHeading, body: "A typed end-to-end page proof.", actions: [] }),
    );
    await page.getByRole("button", { name: "Save block" }).click();
    await expect(config).toHaveValue(new RegExp(heroHeading, "u"));

    await page.getByRole("button", { name: "image media", exact: true }).click();
    const newImage = page.getByRole("group", { name: "New block image" });
    const imageSelect = newImage.getByLabel("Selected image");
    const imageValue = await imageSelect
      .locator("option")
      .filter({ hasText: mediaName })
      .getAttribute("value");
    expect(imageValue).toBeTruthy();
    await imageSelect.selectOption(imageValue!);
    await expect(page.getByRole("button", { name: "Move image up" })).toBeEnabled();
    await page.getByRole("button", { name: "Move image up" }).click();

    const heroBlock = page.getByRole("button", { name: /^02 hero hero$/u });
    await heroBlock.click();
    await heroBlock.locator("..").getByRole("button", { name: "Duplicate", exact: true }).click();
    const duplicateHero = page.getByRole("button", { name: /^03 hero hero$/u });
    await duplicateHero.locator("..").getByRole("button", { name: "Hide", exact: true }).click();
    await page.getByRole("button", { name: "Check preview" }).click();
    await expect(page.getByText("Preview passed publication checks.")).toBeVisible();

    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export" }).click();
    const exported = await download;
    expect(exported.suggestedFilename()).toBe(`${slug}-page.json`);

    await page.getByRole("button", { name: "Publish now" }).click();
    await expect(page.getByText("published", { exact: true })).toBeVisible();
    await page.goto(`/${slug}`);
    await expect(page.getByRole("heading", { name: heroHeading })).toHaveCount(1);
    await expect(page.getByRole("img", { name: "Describe the image" })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

    await page.goto(`/admin/pages/${pageId}/edit`);
    await page.getByRole("button", { name: "Unpublish" }).click();
    await expect(page.getByText("unpublished", { exact: true })).toBeVisible();
    expect((await page.request.get(`/api/v1/public/pages/${slug}`)).status()).toBe(404);
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("contentinfo")
      .getByRole("button", { name: "Delete", exact: true })
      .click();
    await expect(page).toHaveURL(/\/admin\/pages$/u);

    await page.goto("/admin/media");
    await page.getByRole("button", { name: new RegExp(mediaName, "u") }).click();
    await expect(page.getByRole("region", { name: "Usage" })).toContainText("Inactive");
    await expect(page.getByRole("button", { name: "Delete media" })).toBeEnabled();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete media" }).click();
    await expect(page.getByRole("status")).toContainText("Media deleted");
  });
});
