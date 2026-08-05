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

test.describe("contact lifecycle against the real API", () => {
  test.skip(
    !administratorEmail || !administratorPassword,
    "Set M1_TEST_ADMIN_EMAIL and M1_TEST_ADMIN_PASSWORD to run the real-stack proof.",
  );

  test("submits publicly and manages the private inbox", async ({ page, request }) => {
    const suffix = Date.now();
    const subject = `Browser contact proof ${suffix}`;
    const message = `Synthetic private message ${suffix}.`;

    await page.goto("/contact");
    await expect(page.getByRole("heading", { name: "Let’s start a conversation." })).toBeVisible();
    await page.getByLabel("Name").fill("Browser Contact");
    await page.getByLabel("Email").fill(`browser-${suffix}@example.test`);
    await page.getByLabel("Subject").fill(subject);
    await page.getByRole("textbox", { name: "Message", exact: true }).fill(message);
    await page.getByRole("checkbox", { name: /I consent/u }).check();
    await page.waitForTimeout(2_100);
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByRole("status")).toContainText("Thank you");
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    expect((await request.get("/api/v1/admin/contacts")).status()).toBe(401);

    await signIn(page);
    await page.goto("/admin/contacts");
    await expect(page.getByRole("heading", { name: "Contacts" })).toBeVisible();
    await page.getByRole("link", { name: new RegExp(subject, "u") }).click();
    await expect(page.getByRole("heading", { name: subject })).toBeVisible();
    await expect(page.getByText(message)).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);

    await page.getByRole("button", { name: "Mark read" }).click();
    await expect(page.getByText("read", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Archive" }).click();
    await expect(page.getByText("archived", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Restore to read" }).click();
    await expect(page.getByText("read", { exact: true })).toBeVisible();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete permanently" }).click();
    await expect(page).toHaveURL(/\/admin\/contacts$/u);
    await expect(page.getByRole("link", { name: new RegExp(subject, "u") })).toHaveCount(0);
  });
});
