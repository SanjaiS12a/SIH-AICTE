import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username:").fill("coordinator");
  await page.getByLabel("Password:").fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complaint Monitoring Dashboard", exact: true })).toBeVisible();
}

test("dashboard rejects nested omissions and null counts while genuine zero remains valid", async ({ page }) => {
  await login(page);
  const good = await (await page.request.get("/api/dashboard")).json();
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  for (const bad of [{ ...good, management: {} }, { ...good, ageing: undefined }, { ...good, pending: null }]) {
    await page.route("**/api/dashboard?*", route => route.fulfill({ json: bad }));
    await page.goto("/?category=refunds");
    await expect(page.getByRole("alert")).toContainText("incomplete or invalid data");
    await expect(page.locator("main")).toBeVisible();
    await page.unroute("**/api/dashboard?*");
  }
  await page.goto("/?from=2000-01-01&to=2000-01-31");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Open complaints/ })).toContainText("0");
  expect(errors).toEqual([]);
});

test("a page render failure preserves navigation and resets on route change", async ({ page }) => {
  await login(page);
  await page.route("**/api/institutions", route => route.fulfill({ json: { unexpected: true } }));
  await page.goto("/cases/new");
  await expect(page.getByRole("heading", { name: "This page could not be displayed" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry page" })).toBeVisible();
  await page.getByRole("link", { name: "Institutions", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Institutions", exact: true })).toBeVisible();
});
