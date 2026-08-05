import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test.describe("skills catalog on a fresh unseeded database", () => {
  test.skip(
    process.env.M4_EXPECT_EMPTY_SKILLS !== "1",
    "Set M4_EXPECT_EMPTY_SKILLS=1 only for the isolated no-seed proof.",
  );

  test("renders an accessible empty state and keeps administration protected", async ({ page }) => {
    const response = await page.request.get("/api/v1/public/skills");
    expect(response.status()).toBe(200);
    expect((await response.json()).data).toEqual([]);

    await page.goto("/skills");
    await expect(
      page.getByRole("heading", { name: "Skills, grounded in practice." }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "No published skills match these filters." }),
    ).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    const width = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(width.scroll).toBeLessThanOrEqual(width.client);

    await page.goto("/admin/skills");
    await expect(page).toHaveURL(/\/admin\/login/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
