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
  "M3",
  "screenshots",
);

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Site configuration" })).toBeVisible();
}

test.describe("site configuration against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("edits all M3 aggregates and renders only approved public data", async ({
    page,
  }, testInfo) => {
    await signIn(page);

    await page.goto("/admin/profile");
    const fullName = page.getByRole("textbox", { name: "Full name" });
    await expect(fullName).toBeVisible();
    await fullName.fill("Avery Vale — Published Demo");
    await page
      .getByRole("textbox", { name: "Professional title" })
      .fill("Product systems engineer");
    await page
      .getByRole("textbox", { name: "Short biography" })
      .fill("A fictional profile used to verify explicit publication controls.");
    await page.getByRole("textbox", { name: "Email" }).fill("private@example.test");
    for (const field of ["Full name", "Professional title", "Short biography"]) {
      const approval = page.getByRole("checkbox", { name: field });
      if (!(await approval.isChecked())) await approval.check();
    }
    const emailApproval = page.getByRole("checkbox", { name: "Email address" });
    if (await emailApproval.isChecked()) await emailApproval.uncheck();
    await page.getByRole("button", { name: "Save profile" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Profile saved" })).toBeVisible();

    await page.goto("/admin/settings");
    await page.getByRole("textbox", { name: "Website name" }).fill("Vale Studio — M3 Proof");
    await page
      .getByRole("textbox", { name: "Default page title" })
      .fill("Reliability, carefully engineered");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Website settings saved" }),
    ).toBeVisible();

    await page.goto("/admin/navigation");
    await expect(page.getByRole("heading", { name: "Primary navigation" })).toBeVisible();
    const destinationInputs = page.getByRole("textbox", { name: "Destination" });
    while ((await destinationInputs.count()) < 2) {
      const before = await destinationInputs.count();
      await page.getByRole("button", { name: "Add destination" }).click();
      await expect(destinationInputs).toHaveCount(before + 1);
    }
    const destinations = page.locator("article");
    for (let index = 0; index < (await destinations.count()); index += 1) {
      const destination = destinations.nth(index);
      if (index === 0) {
        await destination.getByRole("textbox", { name: "Label" }).fill("Home");
        await destination.getByRole("textbox", { name: "Destination" }).fill("/");
      }
      if (index === 1) {
        await destination.getByRole("textbox", { name: "Label" }).fill("Profile");
        await destination.getByRole("textbox", { name: "Destination" }).fill("/about");
      }
    }
    await page.getByRole("button", { name: "Save navigation" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Navigation saved" })).toBeVisible();

    await page.goto("/admin/footer");
    await expect(page.getByRole("heading", { name: "Footer", level: 1 })).toBeVisible();
    if ((await page.getByRole("textbox", { name: "Column title" }).count()) === 0) {
      await page.getByRole("button", { name: "Add column" }).click();
    }
    const columnTitle = page.getByRole("textbox", { name: "Column title" });
    await columnTitle.fill("Explore");
    if ((await page.getByRole("textbox", { name: "Destination" }).count()) === 0) {
      await page.getByRole("button", { name: "Add link to Explore" }).click();
    }
    await page.getByRole("textbox", { name: "Label" }).first().fill("About");
    await page.getByRole("textbox", { name: "Destination" }).first().fill("/about");
    await page
      .getByRole("textbox", { name: "Copyright or footer note" })
      .fill("Fictional M3 configuration proof.");
    await page.getByRole("button", { name: "Save footer" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Footer saved" })).toBeVisible();

    const profileResponse = await page.request.get("/api/v1/public/profile");
    expect(profileResponse.status()).toBe(200);
    expect(profileResponse.headers()["cache-control"]).toContain("public");
    const profileBody = await profileResponse.json();
    expect(profileBody.data.full_name).toBe("Avery Vale — Published Demo");
    expect(profileBody.data.email).toBeUndefined();
    expect(JSON.stringify(profileBody)).not.toContain('"version"');
    expect(JSON.stringify(profileBody)).not.toContain('"id"');

    const navigationResponse = await page.request.get("/api/v1/public/navigation");
    expect(navigationResponse.status()).toBe(200);
    expect((await navigationResponse.json()).data.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ href: "/about", label: "Profile" })]),
    );

    await page.goto("/about");
    await expect(page.getByRole("heading", { name: "Avery Vale — Published Demo" })).toBeVisible();
    await expect(page.getByText("private@example.test")).toHaveCount(0);
    await expect(page.getByText("Fictional M3 configuration proof.")).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

    const dimensions = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.client);

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(
        evidenceDirectory,
        `configured-about-${testInfo.project.name.replace("chromium-", "")}.png`,
      ),
    });
  });
});
