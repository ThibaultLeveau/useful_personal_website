import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = [
  {
    path: "/",
    heading:
      /Independent product engineering|Reliability, carefully engineered|Useful systems, clearly made/,
  },
  { path: "/admin/login", heading: "Sign in" },
] as const;

for (const route of routes) {
  test(`${route.path} shell is responsive and accessible`, async ({
    page,
    browserName,
  }, testInfo) => {
    await page.goto(route.path);

    await expect(page.getByRole("heading", { name: route.heading })).toBeVisible();
    await expect(page.locator("main")).toBeVisible();

    const documentWidth = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(documentWidth.scroll).toBeLessThanOrEqual(documentWidth.client);

    const skipLink = page.getByRole("link", { name: /skip to/i });
    if (browserName === "webkit") {
      // Playwright WebKit mirrors Safari's OS default that omits links from
      // sequential focus unless full keyboard access is enabled. Chromium and
      // Firefox exercise first-Tab order; WebKit still verifies focus styling.
      await skipLink.focus();
    } else {
      await page.keyboard.press("Tab");
    }
    await expect(skipLink).toBeFocused();

    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(accessibility.violations).toEqual([]);

    await page.screenshot({
      path: testInfo.outputPath(`${route.path === "/" ? "public" : "admin-login"}-shell.png`),
      fullPage: true,
    });
  });
}

test("theme control applies the dark token set", async ({ page }) => {
  await page.goto("/");

  const viewport = page.viewportSize();
  if (!viewport) throw new Error("A configured viewport is required for the shell smoke.");

  const theme =
    viewport.width < 1024
      ? page.getByRole("dialog", { name: "Navigation" }).getByRole("combobox", { name: "Theme" })
      : page.locator(".public-header__actions").getByRole("combobox", { name: "Theme" });

  if (viewport.width < 1024) {
    await page.getByRole("button", { name: "Menu" }).click();
  }

  await expect(theme).toBeEnabled();
  await theme.selectOption("dark");

  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "dark");
  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem("upw-theme")))
    .toBe("dark");
});
