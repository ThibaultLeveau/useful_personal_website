import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const evidenceDirectory = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M4",
  "screenshots",
);

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
}

async function expectNoOverflow(page: Page) {
  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll).toBeLessThanOrEqual(width.client);
}

function editor(page: Page, name: string): Locator {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  return page
    .locator("strong")
    .filter({ hasText: new RegExp(`^${escaped}$`, "u") })
    .locator("xpath=ancestor::form[1]");
}

test.describe("skills catalog against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack skills proof.",
  );

  test("publishes only visible grouped skills with URL-backed filters", async ({
    page,
  }, testInfo) => {
    await page.goto("/skills");
    await expect(
      page.getByRole("heading", { name: "Skills, grounded in practice." }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Engineering" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Product craft" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Python" })).toBeVisible();
    await expect(page.getByText("Internal tooling")).toHaveCount(0);
    await expect(page.getByText("Featured", { exact: true })).toHaveCount(2);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    await page.getByRole("searchbox", { name: "Search skills" }).fill("Python");
    await page.getByLabel("Category").selectOption("engineering");
    await page.getByLabel("Focus").selectOption("true");
    await page.getByRole("button", { name: "Apply" }).click();
    await expect(page).toHaveURL(/category=engineering/);
    await expect(page).toHaveURL(/featured=true/);
    await expect(page.getByRole("heading", { name: "Python" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "API design" })).toHaveCount(0);

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.goto("/skills");
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(
        evidenceDirectory,
        `public-skills-${testInfo.project.name.replace("chromium-", "")}.png`,
      ),
    });
  });

  test("creates, edits, reassigns, orders, filters, and removes skills", async ({
    page,
  }, testInfo) => {
    const viewport = testInfo.project.name.replace("chromium-", "");
    const categoryName = `Proof category ${viewport}`;
    const skillName = `Contract review ${viewport}`;
    const refinedName = `${skillName} refined`;

    await signIn(page);
    await page.goto("/admin/skills");
    await expect(page.getByRole("heading", { name: "Capability catalog" })).toBeVisible();
    await expect(page.getByText("Internal tooling", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Associated projects").first()).toBeDisabled();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-skills-${viewport}.png`),
    });

    const categoryCreate = page.locator("form").filter({
      has: page.getByRole("heading", { name: "New category" }),
    });
    await categoryCreate.getByRole("textbox", { name: "Name" }).fill(categoryName);
    await expect(categoryCreate.getByRole("textbox", { name: "Slug" })).toHaveValue(
      `proof-category-${viewport}`,
    );
    await categoryCreate.getByRole("textbox", { name: "Description" }).fill("Temporary E2E data.");
    await categoryCreate.getByRole("button", { name: "Add category" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Category created" })).toBeVisible();

    const skillCreate = page.locator("form").filter({
      has: page.getByRole("heading", { name: "New skill" }),
    });
    await skillCreate.getByRole("textbox", { name: "Name" }).fill(skillName);
    await skillCreate.getByLabel("Category").selectOption({ label: categoryName });
    await skillCreate.getByLabel("Years experience").fill("1.25");
    await skillCreate.getByLabel("Score").fill("73");
    await skillCreate.getByLabel("Published").uncheck();
    await skillCreate.getByRole("button", { name: "Add skill" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Skill created" })).toBeVisible();
    await expect(page.getByText(skillName, { exact: true })).toBeVisible();

    const hiddenResponse = await page.request.get(
      `/api/v1/public/skills?search=${encodeURIComponent(skillName)}`,
    );
    expect(hiddenResponse.status()).toBe(200);
    expect((await hiddenResponse.json()).data).toEqual([]);

    const skillEditor = editor(page, skillName);
    await skillEditor.getByRole("textbox", { name: "Name" }).fill(refinedName);
    await skillEditor.getByLabel("Category").selectOption({ label: "Engineering" });
    await skillEditor.getByLabel("Published").check();
    await skillEditor.getByRole("button", { name: "Save" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Skill saved" })).toBeVisible();
    await expect(page.getByText(refinedName, { exact: true })).toBeVisible();

    const publicResponse = await page.request.get(
      `/api/v1/public/skills?search=${encodeURIComponent(refinedName)}`,
    );
    expect(publicResponse.status()).toBe(200);
    expect((await publicResponse.json()).data).toEqual([
      expect.objectContaining({
        category_slug: "engineering",
        name: refinedName,
        years_experience: "1.25",
      }),
    ]);

    const refinedEditor = editor(page, refinedName);
    await refinedEditor.getByRole("button", { name: `Move ${refinedName} up` }).click();
    await expect(page.getByRole("status").filter({ hasText: "Skill order saved" })).toBeVisible();

    await page.locator('select[name="featured"]').selectOption("false");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page.getByText("Internal tooling", { exact: true })).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Move Internal tooling/ }).first(),
    ).toBeDisabled();
    await expect(
      editor(page, "Internal tooling").getByRole("button", { name: "Save" }),
    ).toBeEnabled();
    await page.getByRole("button", { name: "Clear" }).click();
    await expect(page.getByText(refinedName, { exact: true })).toBeVisible();

    page.once("dialog", (dialog) => dialog.accept());
    await editor(page, refinedName).getByRole("button", { name: "Delete" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Skill deleted" })).toBeVisible();
    await expect(page.getByText(refinedName, { exact: true })).toHaveCount(0);

    page.once("dialog", (dialog) => dialog.accept());
    await editor(page, categoryName).getByRole("button", { name: "Delete" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Category deleted" })).toBeVisible();
    await expect(page.getByText(categoryName, { exact: true })).toHaveCount(0);
  });
});
