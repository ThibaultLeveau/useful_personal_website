import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";

const administratorEmail = process.env.M1_TEST_ADMIN_EMAIL;
const administratorPassword = process.env.M1_TEST_ADMIN_PASSWORD;
const initialAdministratorPassword =
  process.env.M1_TEST_ADMIN_INITIAL_PASSWORD ?? process.env.M7_TEST_ADMIN_INITIAL_PASSWORD;
const evidenceDirectory = path.resolve(
  process.cwd(),
  "..",
  "docs",
  "evidence",
  "M7",
  "screenshots",
);

async function signIn(page: Page) {
  await page.goto("/admin/login");
  await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
  await page.getByLabel("Password", { exact: true }).fill(administratorPassword!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/admin(?:\/change-password)?$/u, { timeout: 3_000 }).catch(() => null);
  if (initialAdministratorPassword && /\/admin\/login/u.test(page.url())) {
    await page.getByRole("textbox", { name: "Administrator email" }).fill(administratorEmail!);
    await page.getByLabel("Password", { exact: true }).fill(initialAdministratorPassword);
    await page.getByRole("button", { name: "Sign in" }).click();
  }
  await expect(page).toHaveURL(/\/admin(?:\/change-password)?$/u);
  if (/\/admin\/change-password/u.test(page.url())) {
    await page
      .getByRole("textbox", { name: "Initial password", exact: true })
      .fill(initialAdministratorPassword!);
    await page
      .getByRole("textbox", { name: "New password", exact: true })
      .fill(administratorPassword!);
    await page
      .getByRole("textbox", { name: "Confirm new password", exact: true })
      .fill(administratorPassword!);
    await page.getByRole("button", { name: "Change password", exact: true }).click();
  }
  await expect(page).toHaveURL(/\/admin$/u);
}

async function expectNoOverflow(page: Page) {
  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    offenders: [...document.querySelectorAll<HTMLElement>("body *")]
      .filter(
        (element) =>
          element.getBoundingClientRect().right > document.documentElement.clientWidth + 1,
      )
      .slice(0, 8)
      .map(
        (element) =>
          `${element.tagName.toLowerCase()}.${element.className}:${Math.round(element.getBoundingClientRect().right)}`,
      ),
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll, `Horizontal overflow: ${width.offenders.join(", ")}`).toBeLessThanOrEqual(
    width.client,
  );
}

test.describe("blog lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("keeps drafts private and publishes only server-rendered safe content", async ({
    page,
    request,
  }, testInfo) => {
    test.setTimeout(90_000);
    const viewport = testInfo.project.name.replace("chromium-", "");
    const suffix = `${viewport}-${Date.now()}`;
    const slug = `blog-proof-${suffix}`;
    const title = `Blog proof ${suffix}`;
    const revisedTitle = `${title} revised`;

    await signIn(page);
    await page.goto("/admin/blog");
    await expect(page.getByRole("heading", { name: "Blog", exact: true })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    await page.getByRole("link", { name: "New article" }).click();
    await page.getByRole("textbox", { name: "Title", exact: true }).fill(title);
    await page.getByRole("textbox", { name: "Stable slug", exact: true }).fill(slug);
    await page.getByRole("textbox", { name: "Author", exact: true }).fill("M7 Browser Proof");
    await page
      .getByRole("textbox", { name: "Excerpt", exact: true })
      .fill("A real-stack proof of safe revisioned blog publishing.");
    await page
      .getByRole("textbox", { name: "Article source", exact: true })
      .fill(
        '# Typed at the boundary\n\nThe server renders **controlled content**.\n\n```python\nprint("escaped")\n```\n\n[About this portfolio](/about)',
      );
    await page.getByRole("textbox", { name: "SEO title", exact: true }).fill(title);
    await page
      .getByRole("textbox", { name: "SEO description", exact: true })
      .fill("A synthetic browser proof for controlled blog publishing.");
    await page.getByRole("button", { name: "Save draft" }).click();
    await expect(page).toHaveURL(/\/admin\/blog\/.+\/edit$/u);
    const postId = page.url().match(/\/admin\/blog\/([^/]+)\/edit/u)?.[1];
    expect(postId).toBeTruthy();
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    expect((await page.request.get(`/api/v1/public/blog/posts/${slug}`)).status()).toBe(404);
    expect((await request.get(`/api/v1/admin/blog/posts/${postId}/preview`)).status()).toBe(401);

    await page.getByRole("button", { name: "Preview", exact: true }).first().click();
    await expect(page.getByText("Draft preview - not public", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Typed at the boundary" })).toBeVisible();
    expect(await page.locator("script", { hasText: "escaped" }).count()).toBe(0);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);

    mkdirSync(evidenceDirectory, { recursive: true });
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `admin-blog-preview-${viewport}.png`),
    });

    await page.getByRole("tab", { name: "Write" }).click();
    await page.getByRole("button", { name: "Publish now" }).click();
    await expect(page.getByRole("status")).toContainText("Article published");

    await page.goto("/blog");
    await expect(page.getByRole("heading", { name: "Ideas worth making useful." })).toBeVisible();
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `public-blog-list-${viewport}.png`),
    });

    await page.getByRole("link", { name: title }).click();
    await expect(page).toHaveURL(new RegExp(`/blog/${slug}$`, "u"));
    await expect(page.getByRole("heading", { name: title, level: 1 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Typed at the boundary" })).toBeVisible();
    await expect(page.getByRole("link", { name: "About this portfolio" })).toHaveAttribute(
      "href",
      "/about",
    );
    expect(await page.locator("article script:not([type='application/ld+json'])").count()).toBe(0);
    const jsonLd = await page.locator('script[type="application/ld+json"]').textContent();
    expect(jsonLd).toContain(title);
    expect(jsonLd).not.toMatch(/created_by|revision|version|publish_at|source/u);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await expectNoOverflow(page);
    await page.screenshot({
      animations: "disabled",
      fullPage: true,
      path: path.join(evidenceDirectory, `public-blog-detail-${viewport}.png`),
    });
    if (viewport === "1440") {
      await page.setViewportSize({ width: 360, height: 900 });
      await expectNoOverflow(page);
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
      await page.screenshot({
        animations: "disabled",
        fullPage: true,
        path: path.join(evidenceDirectory, "public-blog-detail-400-percent-zoom.png"),
      });
      await page.setViewportSize({ width: 1440, height: 1000 });
    }

    await page.goto(`/admin/blog/${postId}/edit`);
    await page.getByRole("textbox", { name: "Title", exact: true }).fill(revisedTitle);
    await page.getByRole("button", { name: "Save draft" }).click();
    await expect(page.getByRole("status")).toContainText("Draft saved");
    const liveBefore = await page.request.get(`/api/v1/public/blog/posts/${slug}`);
    expect(await liveBefore.text()).toContain(title);
    expect(await liveBefore.text()).not.toContain(revisedTitle);
    await page.getByRole("button", { name: "Publish changes" }).click();
    await expect(page.getByRole("status")).toContainText("Pending changes published");
    expect(await (await page.request.get(`/api/v1/public/blog/posts/${slug}`)).text()).toContain(
      revisedTitle,
    );

    await page.getByRole("button", { name: "Hide" }).click();
    await expect(page.getByRole("status")).toContainText("Article hidden");
    expect((await page.request.get(`/api/v1/public/blog/posts/${slug}`)).status()).toBe(404);
    await page.getByRole("button", { name: "Show" }).click();
    await page.getByRole("button", { name: "Unpublish" }).click();
    await expect(page.getByRole("status")).toContainText("Article unpublished");
    expect((await page.request.get(`/api/v1/public/blog/posts/${slug}`)).status()).toBe(404);
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(page).toHaveURL(/\/admin\/blog$/u);
  });
});
