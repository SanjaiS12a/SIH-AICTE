import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, async (route) => {
    if (
      !["127.0.0.1", "localhost"].includes(
        new URL(route.request().url()).hostname,
      )
    )
      return route.abort();
    return route.continue();
  });
});
async function login(page: Page, username = "coordinator") {
  await page.goto("/");
  await page.getByRole("link", { name: /Sign in to workspace/ }).click();
  await page.getByLabel("Username:").fill(username);
  await page
    .getByLabel("Password:")
    .fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Complaint Monitoring Dashboard" }),
  ).toBeVisible();
}
const idA = "10000000-0000-4000-8000-000000000001",
  idB = "10000000-0000-4000-8000-000000000002";
function job(id: string, filename: string) {
  return {
    id,
    kind: "complaints",
    filename,
    state: "complete",
    error: "",
    total: 1,
    counts: { imported: 1 },
    matching: { complete: 1 },
    headers: [],
    fields: [],
    required: [],
    mapping: {},
    preview: [],
    created_at: "2026-10-30T00:00:00Z",
  };
}

test("general reports never fetch an import or format session data as a job", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page);
  const importRequests: string[] = [],
    sessionRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/imports/"))
      importRequests.push(request.url());
    if (request.url().endsWith("/api/session"))
      sessionRequests.push(request.url());
  });
  await page.getByRole("link", { name: "Reports", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Data report" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Complaint categories" }),
  ).toBeVisible();
  await expect(page.getByText(/Authorized complaint records/)).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  expect(importRequests).toEqual([]);
  expect(sessionRequests).toEqual([]);
  expect(errors).toEqual([]);
});

test("switching from an import to general reports aborts old metadata and clears it", async ({
  page,
}) => {
  await login(page);
  const facts = await (await page.request.get("/api/dashboard")).json();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const aborted: string[] = [];
  page.on("requestfailed", (request) => aborted.push(request.url()));
  await page.route(`**/api/imports/${idA}`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    await route
      .fulfill({ json: job(idA, "Obsolete source A.csv") })
      .catch(() => {});
  });
  await page.route(`**/api/imports/${idA}/report?*`, (route) =>
    route.fulfill({ json: facts }),
  );
  const requested = page.waitForRequest((r) =>
    r.url().endsWith(`/api/imports/${idA}`),
  );
  await page.goto(`/reports?import_id=${idA}`);
  await requested;
  await page.getByRole("link", { name: "Reports", exact: true }).click();
  await expect(page.getByText(/Authorized complaint records/)).toBeVisible();
  await expect
    .poll(() => aborted.some((url) => url.endsWith(`/api/imports/${idA}`)))
    .toBeTruthy();
  await expect(page.getByText(/Obsolete source A/)).toHaveCount(0);
  await page.route(`**/api/imports/${idB}`, (route) =>
    route.fulfill({ json: job(idB, "Current source B.csv") }),
  );
  await page.route(`**/api/imports/${idB}/report?*`, (route) =>
    route.fulfill({ json: facts }),
  );
  await page.goto(`/reports?import_id=${idB}`);
  await expect(page.getByText(/Current source B.csv/)).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Complaint categories" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("malformed report and import responses show errors without crashing", async ({
  page,
}) => {
  await login(page);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const facts = await (await page.request.get("/api/dashboard")).json();
  await page.route("**/api/dashboard?*", (route) =>
    route.fulfill({ json: { user: { name: "Not report data" } } }),
  );
  await page.goto("/reports?category=refunds");
  await expect(page.getByRole("alert")).toContainText(
    "incomplete or invalid data",
  );
  await expect(
    page.getByRole("heading", { name: "Complaint categories" }),
  ).toHaveCount(0);
  await page.route(`**/api/imports/${idA}`, (route) =>
    route.fulfill({ json: { id: idA, filename: "Incomplete.csv" } }),
  );
  await page.route(`**/api/imports/${idA}/report?*`, (route) =>
    route.fulfill({ json: facts }),
  );
  await page.goto(`/reports?import_id=${idA}`);
  await expect(page.getByRole("alert")).toContainText(
    "incomplete or invalid data",
  );
  expect(errors).toEqual([]);
});

test("home prioritizes active cases and keeps filter-aware drilldowns working", async ({
  page,
}) => {
  await login(page);
  await expect(page.locator(".home-stat")).toHaveCount(9);
  await expect(
    page.getByRole("heading", { name: "Cases needing attention" }),
  ).toBeVisible();
  const facts = await (await page.request.get("/api/dashboard")).json();
  const table = page.getByRole("region", {
    name: "Cases needing attention list",
    exact: true,
  });
  await expect(table.locator("tbody tr")).toHaveCount(
    Math.min(8, facts.attention.length),
  );
  expect(facts.attention.map((c: any) => new Date(c.due_at).getTime())).toEqual(
    [...facts.attention]
      .sort(
        (a: any, b: any) =>
          new Date(a.due_at).getTime() - new Date(b.due_at).getTime(),
      )
      .map((c: any) => new Date(c.due_at).getTime()),
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: "../tests/results/dashboard-simple.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Overdue complaints/ }).click();
  await expect(page).toHaveURL(/overdue=true/);
  const overdue = await (
    await page.request.get("/api/cases?overdue=true")
  ).json();
  expect(overdue.count).toBe(facts.overdue);
  await page.goto("/");
  await page.getByText("More filters", { exact: true }).click();
  await page
    .getByRole("combobox", { name: "Category", exact: true })
    .selectOption("refunds");
  await expect(page).toHaveURL(/category=refunds/);
  await expect(
    page.getByRole("heading", { name: "Complaints received and closed" }),
  ).toBeVisible();
  await page
    .getByText("View monthly values and complaints", { exact: true })
    .click();
  await page
    .getByRole("link", { name: /received complaints:/ })
    .first()
    .click();
  await expect(page).toHaveURL(/category=refunds/);
  await expect(page).toHaveURL(/from=/);
  await page.goto("/");
  await page
    .getByRole("link", { name: "Review overlaps →", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/institution=/);
  const institution = new URL(page.url()).searchParams.get("institution");
  await page
    .getByRole("button", { name: "Related issue", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`institution=${institution}`));
});

test("officer home hides cross-bureau information", async ({ page }) => {
  await login(page, "officer_rb");
  await expect(page.locator(".home-stat")).toHaveCount(2);
  await expect(
    page.getByRole("button", { name: /Possible overlaps/ }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Needs coordination" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Open complaints by category" }),
  ).toBeVisible();
  expect((await page.request.get("/api/overlaps")).status()).toBe(403);
});

test("mobile dashboard and general reports remain keyboard accessible and contained", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  const table = page.getByRole("region", {
    name: "Cases needing attention list",
    exact: true,
  });
  await expect(table).toBeVisible();
  await table.focus();
  await expect(table).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../tests/results/dashboard-simple-mobile.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Reports", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Complaint categories" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("auditor can inspect attention cases but cannot change them", async ({
  page,
}) => {
  await login(page, "auditor");
  await expect(page.locator(".home-stat")).toHaveCount(9);
  await expect(
    page.getByRole("heading", { name: "Needs coordination" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Register case", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Upload Excel", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("link", { name: /Open case C-/ })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Original complaint" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record action", exact: true }),
  ).toHaveCount(0);
});

test("monthly chart links intersect the current receipt dates", async ({
  page,
}) => {
  await login(page);
  const filters = "from=2026-08-15&to=2026-08-31";
  const facts = await (
    await page.request.get(`/api/dashboard?${filters}`)
  ).json();
  for (const closed of [false, true]) {
    await page.goto(`/?${filters}`);
    await page
      .getByText("View monthly values and complaints", { exact: true })
      .click();
    const entry = facts.trend.find(
      (t: any) => (closed ? t.disposed : t.received) > 0,
    );
    expect(entry).toBeTruthy();
    const month = new Date(`${entry.month}-01T00:00:00`).toLocaleDateString(
      "en-IN",
      { month: "short", year: "2-digit" },
    );
    const count = closed ? entry.disposed : entry.received;
    await page
      .getByRole("link", {
        name: `${month} ${closed ? "closed" : "received"} complaints: ${count}`,
        exact: true,
      })
      .click();
    const query = new URL(page.url()).searchParams;
    expect(query.get("from")).toBe("2026-08-15");
    expect(query.get("to")).toBe("2026-08-31");
    const list = await (await page.request.get(`/api/cases?${query}`)).json();
    expect(list.count).toBe(count);
  }
});
