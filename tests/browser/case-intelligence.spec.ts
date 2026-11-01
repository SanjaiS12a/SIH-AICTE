import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
import type { Overlap } from "../../frontend/src/api";
import { artifact } from "./support";

let backend: APIRequestContext;
let pair: Overlap;
const stamp = Date.now();

async function post(context: APIRequestContext, url: string, data: unknown) {
  const token = (await context.storageState()).cookies.find(c => c.name === "csrftoken")!.value;
  return context.post(url, { data, headers: { "X-CSRFToken": token } });
}
async function login(page: Page, username = "coordinator") {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username:").fill(username);
  await page.getByLabel("Password:").fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complaint Monitoring Dashboard", exact: true })).toBeVisible();
}
async function showPair(page: Page, value: Overlap) {
  await page.route("**/api/overlaps?*", route => route.fulfill({ json: { count: 1, next: null, previous: null, results: [value] } }));
  await page.goto(`/coordination?decision=all&pair=${value.id}`);
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toBeVisible();
}

test.beforeAll(async ({ playwright }) => {
  backend = await playwright.request.newContext({ baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174" });
  await backend.get("/accounts/login/");
  const token = (await backend.storageState()).cookies.find(c => c.name === "csrftoken")!.value;
  expect((await backend.post("/accounts/login/", { form: { username: "coordinator", password: process.env.DEMO_PASSWORD || "Demo-only-26264!", csrfmiddlewaretoken: token } })).ok()).toBeTruthy();
  const institutionResponse = await post(backend, "/api/institution-registry", {
    name: `Case Intelligence Test Institute ${stamp}`, permanent_id: `CI-A-${stamp}`,
    region: "Southern", district: "Fictional", reason: "Synthetic Milestone A browser fixtures",
  });
  expect(institutionResponse.status()).toBe(201);
  const institution = await institutionResponse.json();
  const cases = [];
  for (const bureau of ["RB", "PGRC"]) {
    const response = await post(backend, "/api/cases", {
      submission_id: crypto.randomUUID(), institution: institution.id, bureau,
      source_system: "milestone-a-browser", source_reference: crypto.randomUUID(),
      category: "refunds", classification: "grievance",
      summary: "A tuition refund after admission cancellation remains unpaid.",
      description: "Fictional fixture for human relationship review. No real personal data.",
    });
    expect(response.status(), await response.text()).toBe(201);
    cases.push(await response.json());
  }
  const relationship = await post(backend, "/api/relationships", {
    left: cases[0].id, right: cases[1].id, decision: "related_issue", reason: "Existing independently recorded relationship",
  });
  expect([200, 201]).toContain(relationship.status());
  pair = await relationship.json();
});
test.afterAll(async () => backend?.dispose());
test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, route => ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
});

for (const username of ["coordinator", "auditor", "officer_rb"]) {
  test(`${username}: five destinations, truthful work scope and role-safe navigation`, async ({ page }) => {
    await login(page, username);
    const nav = page.getByRole("navigation", { name: "Primary navigation", exact: true });
    await expect(nav.getByRole("link")).toHaveText(["Home", "Institutions", "My Work", "Data Imports", "Reports"]);
    await nav.getByRole("link", { name: "My Work", exact: true }).click();
    await expect(page.getByRole("heading", { name: "My Work", exact: true })).toBeVisible();
    await expect(nav.getByRole("link", { name: "My Work", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByText("My Assigned Cases", { exact: true })).toHaveCount(0);
    if (username === "officer_rb") {
      await expect(page.getByRole("heading", { name: "Cases in my Bureau", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Coordination actions", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Coordination queue", exact: true })).toHaveCount(0);
      await expect(page.getByRole("link", { name: /Create manual relationship/ })).toHaveCount(0);
      expect((await page.request.get("/api/overlaps")).status()).toBe(403);
    } else {
      await expect(page.getByRole("heading", { name: "Coordination queue", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Awaiting acknowledgment", exact: true })).toBeVisible();
    }
    await expect(page.getByRole("link", { name: "Register case", exact: true })).toHaveCount(username === "auditor" ? 0 : 1);
    for (const [label, url] of [["Institutions", "/institutions"], ["Data Imports", "/imports"], ["Reports", "/reports"], ["Home", "/"]]) {
      await nav.getByRole("link", { name: label, exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`${url}$`));
      await expect(page.locator("main h1")).toBeVisible();
      await expect(nav.getByRole("link", { name: label, exact: true })).toHaveAttribute("aria-current", "page");
    }
  });
}

test("contextual navigation preserves case, coordination, import, report and manual routes", async ({ page }) => {
  await login(page);
  await page.goto("/work");
  await page.getByRole("link", { name: "Case registry", exact: true }).click();
  await expect(page).toHaveURL(/\/cases$/);
  const work = page.getByRole("navigation", { name: "Work navigation", exact: true });
  for (const [label, url] of [["Coordination workspace", "/coordination/workspace"], ["Coordination queue", "/coordination"], ["Escalations", "/escalations"]]) {
    await work.getByRole("link", { name: label, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`${url}$`));
    await expect(page.locator(".breadcrumb")).toContainText(label);
    await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "My Work", exact: true })).toHaveAttribute("aria-current", "page");
  }
  await page.getByRole("link", { name: "Work overview", exact: true }).click();
  await page.getByRole("link", { name: "Create manual relationship", exact: true }).click();
  await expect(page).toHaveURL(/\/relationships\/new$/);
  await expect(page.getByRole("link", { name: "Choose an institution from the registry first" })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/work$/);
  await page.getByRole("link", { name: "Register case", exact: true }).click();
  await expect(page).toHaveURL(/\/cases\/new$/);
  await page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Data Imports", exact: true }).click();
  const imports = page.getByRole("navigation", { name: "Import navigation", exact: true });
  await imports.getByRole("link", { name: "Source-upload history", exact: true }).click();
  await expect(page).toHaveURL(/\/imports\/source-jobs$/);
  await imports.getByRole("link", { name: "Source intake", exact: true }).click();
  await expect(page).toHaveURL(/\/imports\/sources$/);
  await page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Reports", exact: true }).click();
  const reports = page.getByRole("navigation", { name: "Report navigation", exact: true });
  await reports.getByRole("link", { name: "Case movements", exact: true }).click();
  await expect(page).toHaveURL(/\/movements$/);
  await reports.getByRole("link", { name: "Cross-bureau activity", exact: true }).click();
  await expect(page).toHaveURL(/\/coordination\/activity$/);
  await expect(page.locator(".breadcrumb")).toContainText("Reports");
  await page.goto(`/institutions/${pair.left.institution.id}?section=history`);
  await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Institutions", exact: true })).toHaveAttribute("aria-current", "page");
});

test("pending review requires an explicit decision and a nonblank reason; saved review stays selected", async ({ page }) => {
  await login(page);
  const pending = { ...pair, decision: "pending", reason: "", reviewer: null, reviewed_at: null };
  let submissions: Record<string, unknown>[] = [];
  await page.route(`**/api/overlaps/${pair.id}/review`, async route => {
    submissions.push(route.request().postDataJSON());
    await route.fulfill({ json: { id: pair.id, decision: "same_incident", version: pair.version + 1 } });
  });
  await showPair(page, pending);
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  await page.getByLabel("Review reason").fill("Independent review, no automatic merging");
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  expect(submissions).toHaveLength(0);
  await page.getByLabel("Same incident", { exact: true }).focus();
  await page.keyboard.press("Space");
  await expect(page.getByLabel("Same incident", { exact: true })).toBeChecked();
  await page.getByLabel("Review reason").fill("");
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  expect(submissions).toHaveLength(0);
  await page.getByLabel("Review reason").fill("   ");
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("enter a review reason");
  expect(submissions).toHaveLength(0);
  await page.getByLabel("Review reason").fill("Deliberate relationship decision");
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  await expect.poll(() => submissions.length).toBe(1);
  expect(submissions[0]).toEqual({ decision: "same_incident", reason: "Deliberate relationship decision", expected_version: pair.version });
  await showPair(page, pair);
  await expect(page.getByLabel("Related issue", { exact: true })).toBeChecked();
  await expect(page.getByLabel("Review reason")).toHaveValue(pair.reason);
});

test("comparison shows original evidence, missing fields and long text on desktop and 390px mobile", async ({ page }) => {
  await login(page);
  const longText = "Original allegation line.\n" + "UnbrokenEvidenceReference".repeat(90);
  const example: Overlap = { ...pair, score: 0.8123, origin: "semantic", model_revision: "browser-presentation-fixture", decision: "pending", reason: "", reviewer: null,
    left: { ...pair.left, description: longText, source_reference: "", incident_date: null },
    right: { ...pair.right, incident_date: "2025-09-01", category: "documents" } };
  await page.setViewportSize({ width: 1440, height: 1000 });
  await showPair(page, example);
  const a = page.getByRole("article", { name: "Complaint A", exact: true });
  const b = page.getByRole("article", { name: "Complaint B", exact: true });
  await expect(a).toContainText(pair.left.institution.permanent_id);
  await expect(a).toContainText(pair.left.source_system);
  await expect(a).toContainText("Grievance");
  await expect(a.getByText("Not recorded", { exact: true })).toHaveCount(2);
  await expect(a).toContainText(longText);
  await expect(page.getByText("Cosine similarity: 0.812", { exact: true })).toBeVisible();
  const metadata = page.getByRole("region", { name: "Metadata comparison", exact: true });
  await expect(metadata.getByRole("row", { name: "Category Different recorded values" })).toBeVisible();
  await expect(metadata.getByRole("row", { name: "Incident date Not recorded on one or both cases" })).toBeVisible();
  await expect(page.getByText(/This does not confirm that they concern the same incident/)).toBeVisible();
  const aBox = (await a.boundingBox())!, bBox = (await b.boundingBox())!;
  expect(Math.abs(aBox.y - bBox.y)).toBeLessThan(2);
  expect(bBox.x).toBeGreaterThan(aBox.x);
  await page.screenshot({ path: artifact("after-review-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  expect((await b.boundingBox())!.y).toBeGreaterThan((await a.boundingBox())!.y);
  await page.screenshot({ path: artifact("after-review-mobile.png"), fullPage: true });
  await a.getByRole("link", { name: "Attachments", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/cases/${pair.left.id}#case-attachments$`));
  await expect(page.getByRole("heading", { name: "Supporting documents", exact: true })).toBeFocused();
  await page.goBack();
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toBeVisible();
  await page.getByRole("article", { name: "Complaint A", exact: true }).getByRole("link", { name: "Case actions and history", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Case history", exact: true })).toBeVisible();
  await expect(page.locator("#case-history")).toBeFocused();
});

test("actual stale relationship returns 409 and keeps the deliberate draft until reload", async ({ page }) => {
  await login(page);
  await page.goto(`/coordination?decision=all&pair=${pair.id}`);
  await expect(page.getByLabel("Review reason")).toHaveValue(pair.reason);
  await page.getByLabel("Same incident", { exact: true }).check();
  await page.getByLabel("Review reason").fill("Keep this unsaved independent review draft");
  const changed = await post(backend, `/api/overlaps/${pair.id}/review`, { decision: "unrelated", reason: "Concurrent reviewed evidence", expected_version: pair.version });
  expect(changed.status()).toBe(200);
  const stale = page.waitForResponse(r => r.url().endsWith(`/api/overlaps/${pair.id}/review`) && r.status() === 409);
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  await stale;
  await expect(page.getByLabel("Same incident", { exact: true })).toBeChecked();
  await expect(page.getByLabel("Review reason")).toHaveValue("Keep this unsaved independent review draft");
  await expect(page.getByRole("button", { name: "Record decision", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Reload relationship and discard draft" }).click();
  await expect(page.getByLabel("Review reason")).toHaveValue("Concurrent reviewed evidence");
  await expect(page.getByLabel("Unrelated", { exact: true })).toBeChecked();
});

test("review queue retains loading, error and empty states without inventing a pair", async ({ page }) => {
  await login(page);
  let release!: () => void;
  const waiting = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/overlaps?*", async route => {
    await waiting;
    await route.fulfill({ json: { count: 0, results: [], next: null, previous: null } });
  });
  await page.goto("/coordination?decision=pending");
  await expect(page.getByRole("status")).toContainText("Loading workspace");
  release();
  await expect(page.getByText(/No pairs in this review category/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toHaveCount(0);
  await page.unroute("**/api/overlaps?*");
  await page.route("**/api/overlaps?*", route => route.fulfill({ status: 503, json: { detail: "Test review service unavailable" } }));
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("Test review service unavailable");
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toHaveCount(0);
});

test("auditor comparison is read-only; officer direct access exposes no relationship data", async ({ page }) => {
  await login(page, "auditor");
  await page.goto(`/coordination?decision=all&pair=${pair.id}`);
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toBeVisible();
  await expect(page.getByText(/Read-only audit access/)).toBeVisible();
  await expect(page.getByRole("radio")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Record decision", exact: true })).toHaveCount(0);
  const current = await (await backend.get(`/api/overlaps?decision=all&pair=${pair.id}`)).json();
  expect((await post(page.request, `/api/overlaps/${pair.id}/review`, { decision: "same_incident", reason: "Unauthorized auditor attempt", expected_version: current.results[0].version })).status()).toBe(403);
  await page.context().clearCookies();
  await login(page, "officer_rb");
  const calls: string[] = [];
  page.on("request", r => { if (new URL(r.url()).pathname.startsWith("/api/overlaps")) calls.push(r.url()); });
  await page.goto(`/coordination?pair=${pair.id}`);
  await expect(page.getByRole("alert")).toContainText("Coordination access is required");
  await expect(page.getByRole("region", { name: "Case comparison", exact: true })).toHaveCount(0);
  await expect(page.getByText(pair.right.description, { exact: true })).toHaveCount(0);
  expect(calls).toHaveLength(0);
  expect((await page.request.get(`/api/cases/${[pair.left, pair.right].find(c => c.bureau === "PGRC")!.id}`)).status()).toBe(404);
});

test("mobile workspace and keyboard links preserve focus and browser Back", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.screenshot({ path: artifact("after-home-mobile.png"), fullPage: true });
  const work = page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "My Work", exact: true });
  await work.focus();
  expect(await work.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(10);
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/work$/);
  const deadlines = page.getByRole("link", { name: /Approaching deadlines/ });
  await deadlines.focus();
  await expect(deadlines).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/approaching=true/);
  await expect(page.getByRole("checkbox", { name: "Due in next seven days", exact: true })).toBeChecked();
  const contextLink = page.getByRole("navigation", { name: "Work navigation" }).getByRole("link", { name: "Case registry", exact: true });
  expect(await contextLink.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
  await page.goBack();
  await expect(page).toHaveURL(/\/work$/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: artifact("after-work-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: artifact("after-work-desktop.png"), fullPage: true });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Complaint Monitoring Dashboard", exact: true })).toBeVisible();
  await page.screenshot({ path: artifact("after-home-desktop.png"), fullPage: true });
});
