import { test, expect } from "@playwright/test";
import { artifact } from "./support";

async function login(page: import("@playwright/test").Page, username = "coordinator") {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username:").fill(username);
  await page.getByLabel("Password:").fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complaint Monitoring Dashboard" })).toBeVisible();
}

test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, route =>
    ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname)
      ? route.continue() : route.abort());
});

test("institution-first search supports keyboard submission and real profile navigation", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await login(page);
  const institution = (await (await page.request.get("/api/institution-registry?q=DEMO-0001")).json()).results[0];
  expect(institution).toBeTruthy();
  const search = page.getByRole("search", { name: "Find an institution" });
  await search.getByRole("searchbox", { name: "Find an institution" }).fill(institution.permanent_id);
  await search.getByRole("searchbox").press("Enter");
  await expect(page).toHaveURL(new RegExp(`institutions\\?q=${institution.permanent_id}`));
  await page.getByRole("link", { name: `Open profile for ${institution.name}`, exact: true }).click();
  await expect(page.getByRole("heading", { name: institution.name, exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Cases", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "History", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test("management layout separates receipt scope from all-time coordination", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1050 });
  await login(page);
  await expect(page.locator(".home-summary .home-stat")).toHaveCount(4);
  await expect(page.locator(".home-scope-note")).toContainText("Under-process is included in Open");
  await expect(page.locator(".home-coordination .scope-tag")).toHaveText("All-time coordination");
  const search = await page.locator(".institution-finder").boundingBox();
  const filters = await page.locator(".home-filterbar").boundingBox();
  const totals = await page.locator(".home-summary").boundingBox();
  expect(search!.y + search!.height).toBeLessThanOrEqual(filters!.y + 1);
  expect(filters!.y + filters!.height).toBeLessThan(totals!.y);
  await page.screenshot({ path: artifact("portal-desktop.png"), fullPage: true });
  await page.screenshot({ path: artifact("portal-desktop-first-screen.png") });
});

test("phone navigation, filters, tables and sign-out remain accessible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  const nav = page.getByRole("navigation", { name: "Primary navigation" });
  for (const name of ["Home", "Institutions", "My Work", "Data Imports", "Reports"]) {
    await expect(nav.getByRole("link", { name, exact: true })).toBeVisible();
  }
  expect((await nav.boundingBox())!.width).toBeGreaterThan(350);
  await page.setViewportSize({ width: 820, height: 1180 });
  expect((await nav.boundingBox())!.width).toBeGreaterThan(780);
  await expect(page.getByRole("button", { name: "Sign out" }).filter({ visible: true })).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Sign out" }).filter({ visible: true })).toHaveCount(1);
  await page.getByText("More filters", { exact: true }).click();
  await page.getByRole("combobox", { name: "Category", exact: true }).selectOption("refunds");
  await expect(page).toHaveURL(/category=refunds/);
  await page.goto("/");
  await expect(page.locator(".home-summary strong").first()).toBeVisible();
  const table = page.getByRole("region", { name: "Cases needing attention list", exact: true });
  await table.focus();
  await expect(table).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: artifact("portal-mobile.png"), fullPage: true });
  for (const name of ["Institutions", "My Work", "Data Imports", "Reports"]) {
    await nav.getByRole("link", { name, exact: true }).click();
    await expect(page.locator("#main h1")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  await page.getByRole("button", { name: "Sign out" }).filter({ visible: true }).click();
  await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
});

test("auditor and officer retain their role-specific home actions", async ({ page }) => {
  await login(page, "auditor");
  await expect(page.getByRole("link", { name: "Register case", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Needs coordination", exact: true })).toBeVisible();
  await page.context().clearCookies();
  await login(page, "officer_rb");
  await expect(page.locator(".home-stat")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "Needs coordination", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Open complaints by category", exact: true })).toBeVisible();
  expect((await page.request.get("/api/overlaps")).status()).toBe(403);
});
