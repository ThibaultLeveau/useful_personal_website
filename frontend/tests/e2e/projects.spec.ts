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
  "M6",
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

test.describe("project lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("keeps draft revisions private and republishes case-study changes", async ({
    page,
    request,
  }, testInfo) => {
    test.setTimeout(240_000);
    const viewport = testInfo.project.name.replace("chromium-", "");
    const suffix = `${viewport}-${Date.now()}`;
    const slug = `project-proof-${suffix}`;
    const name = `Project proof ${suffix}`;
    const revisedName = `${name} evolved`;

    await signIn(page);
    await page.goto("/admin/projects");
    await expect(page.getByRole("heading", { name: "Project case studies" })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    await page.getByRole("link", { name: "New project" }).click();
    await expect(page.getByRole("heading", { name: "New case study" })).toBeVisible();
    await page.getByLabel("Slug").fill(slug);
    await page.getByLabel("Project name").fill(name);
    await page.getByLabel("Short description").fill("A synthetic, revision-safe browser proof.");
    await page.getByLabel("Owner role").fill("Technical lead");
    await page.getByLabel("SEO title").fill(`${name} case study`);
    await page
      .getByLabel("SEO description")
      .fill("A safe synthetic project used for M6 browser verification.");
    await page.getByLabel("Canonical URL").fill(`https://portfolio.example.test/projects/${slug}`);
    await page.getByRole("button", { name: "Save project" }).click();
    await expect(page).toHaveURL(/\/admin\/projects\/.+\/edit$/u);
    const projectId = page.url().match(/\/admin\/projects\/([^/]+)\/edit/u)?.[1];
    expect(projectId).toBeTruthy();
    await expect(page.getByRole("heading", { name })).toBeVisible();
    await expect(page.getByText("Gallery unavailable in this milestone")).toBeVisible();

    const draftPublic = await page.request.get(`/api/v1/public/projects/${slug}`);
    expect(draftPublic.status()).toBe(404);
    const guessedPreview = await request.get(`/api/v1/admin/projects/${projectId}/preview`);
    expect(guessedPreview.status()).toBe(401);

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-project-editor-${viewport}.png`),
    });
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    await page.getByRole("link", { name: "Preview" }).click();
    await expect(page.getByText("Draft preview - not public", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name })).toBeVisible();
    await expect(page.locator("meta[name=robots]")).toHaveAttribute("content", /noindex/u);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-project-preview-${viewport}.png`),
    });

    await page.getByRole("link", { name: "Return to editor" }).click();
    await page.getByRole("button", { name: "Publish now" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Project published" })).toBeVisible();

    await page.goto("/projects");
    await expect(
      page.getByRole("heading", { name: "Systems with a point of view." }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `public-project-list-${viewport}.png`),
    });

    await page.getByRole("link", { name }).click();
    await expect(page).toHaveURL(new RegExp(`/projects/${slug}$`, "u"));
    await expect(page.getByRole("heading", { name, level: 1 })).toBeVisible();
    await expect(
      page.getByRole("img", { name: "Project gallery not yet available" }),
    ).toBeVisible();
    const canonical = page.locator('link[rel="canonical"]');
    await expect(canonical).toHaveAttribute("href", /portfolio\.example\.test/u);
    const jsonLd = await page.locator('script[type="application/ld\+json"]').textContent();
    expect(jsonLd).toContain(name);
    expect(jsonLd).not.toMatch(/created_by|revision|version|publish_at/u);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `public-project-detail-${viewport}.png`),
    });

    if (viewport === "1440") {
      for (const width of [320, 360, 390, 768, 1024, 1280, 1440, 1920]) {
        await page.setViewportSize({ height: 1000, width });
        for (const theme of ["light", "dark"] as const) {
          await page.evaluate((preference) => {
            localStorage.setItem("upw-theme", preference);
            document.documentElement.dataset.theme = preference;
            document.documentElement.dataset.themePreference = preference;
            document.documentElement.style.colorScheme = preference;
            window.dispatchEvent(new Event("upw-theme-change"));
          }, theme);
          await expectNoOverflow(page);
          await page.screenshot({
            animations: "disabled",
            fullPage: true,
            path: path.join(evidenceDirectory, `public-project-detail-${width}-${theme}.png`),
          });
        }
      }
      // A 320 CSS-pixel layout is the WCAG reflow equivalent of a 1280px
      // viewport at 400% browser zoom, without using CSS zoom to distort layout.
      await page.setViewportSize({ height: 1000, width: 320 });
      await expectNoOverflow(page);
      await page.screenshot({
        animations: "disabled",
        fullPage: true,
        path: path.join(evidenceDirectory, "public-project-detail-390-zoom-400.png"),
      });
      await page.setViewportSize({ height: 1000, width: 1440 });
    }

    await page.goto(`/admin/projects/${projectId}/edit`);
    const nameField = page.getByLabel("Project name");
    await nameField.fill(revisedName);
    await page.getByRole("button", { name: "Save project" }).click();
    await expect(page.getByRole("heading", { name: revisedName })).toBeVisible();
    await expect(page.getByRole("heading", { name: "published changes pending" })).toBeVisible();
    const liveBeforeRepublish = await page.request.get(`/api/v1/public/projects/${slug}`);
    const liveBeforeRepublishText = await liveBeforeRepublish.text();
    expect(liveBeforeRepublishText).toContain(name);
    expect(liveBeforeRepublishText).not.toContain(revisedName);

    await page.getByRole("button", { name: "Publish changes" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Pending changes published" }),
    ).toBeVisible();
    const liveAfterRepublish = await page.request.get(`/api/v1/public/projects/${slug}`);
    expect(await liveAfterRepublish.text()).toContain(revisedName);

    await page.getByRole("button", { name: "Hide" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Project hidden" })).toBeVisible();
    expect((await page.request.get(`/api/v1/public/projects/${slug}`)).status()).toBe(404);
    await page.getByRole("button", { name: "Show" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Project visible" })).toBeVisible();
    await page.getByRole("button", { name: "Unpublish" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Project unpublished" })).toBeVisible();
    expect((await page.request.get(`/api/v1/public/projects/${slug}`)).status()).toBe(404);
    await page.getByRole("checkbox", { name: "Confirm deletion" }).check();
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(page).toHaveURL(/\/admin\/projects$/u);
  });
});
