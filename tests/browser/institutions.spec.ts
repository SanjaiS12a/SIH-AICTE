import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

let backend: APIRequestContext;
let institution: { id: string; name: string; permanent_id: string };
const stamp = Date.now();

async function csrf(context: APIRequestContext) {
  return (await context.storageState()).cookies.find(
    (c) => c.name === "csrftoken",
  )!.value;
}
async function post(url: string, data: unknown, method = "post") {
  const response = await backend.fetch(url, {
    method,
    data,
    headers: { "X-CSRFToken": await csrf(backend) },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json();
}
async function createInstitution(suffix: string) {
  return post("/api/institution-registry", {
    name: `ZZZ Browser Institution ${stamp}-${suffix}`,
    permanent_id: `UI-${stamp}-${suffix}`,
    region: "Southern",
    district: "Fictional browser district",
    reason: "Synthetic institution frontend acceptance fixture",
  });
}
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
function section(page: Page, name: string) {
  return page
    .getByRole("navigation", { name: "Institution sections" })
    .getByRole("link", { name, exact: true });
}

test.beforeAll(async ({ playwright }) => {
  test.setTimeout(120000);
  backend = await playwright.request.newContext({
    baseURL: "http://127.0.0.1:5173",
  });
  await backend.get("/accounts/login/");
  const signedIn = await backend.post("/accounts/login/", {
    form: {
      username: "coordinator",
      password: process.env.DEMO_PASSWORD || "Demo-only-26264!",
      csrfmiddlewaretoken: await csrf(backend),
    },
  });
  expect(signedIn.ok()).toBeTruthy();
  institution = await createInstitution("pages");
  for (let i = 0; i < 25; i++) {
    await post("/api/cases", {
      submission_id: crypto.randomUUID(),
      institution: institution.id,
      bureau: i < 15 ? "RB" : "PGRC",
      source_system: "institution-browser-test",
      source_reference: `UI-${stamp}-${i}`,
      category: "refunds",
      summary: `The tuition refund for fictional student ${i} has not been paid.`,
      description:
        "Synthetic case for institution pagination and access acceptance tests.",
    });
  }
});
test.afterAll(async () => backend?.dispose());
test.beforeEach(async ({ context, page }) => {
  await page.bringToFront();
  await context.route(/^https?:\/\//, (route) =>
    ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname)
      ? route.continue()
      : route.abort(),
  );
});

test("institution navigation, server pagination, ID/name search and empty directory", async ({
  page,
}) => {
  await login(page);
  await page.getByRole("link", { name: "Institutions", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Institutions", exact: true }),
  ).toBeVisible();
  const directory = page.getByRole("region", {
    name: "Institution directory table",
  });
  await expect(directory.locator("tbody tr")).toHaveCount(20);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.getByText(/records · Page 2/)).toBeVisible();
  await page.getByLabel("Search institutions").fill(institution.permanent_id);
  await expect(directory.locator("tbody tr")).toHaveCount(1);
  await expect(page).not.toHaveURL(/page=2/);
  await page.getByLabel("Search institutions").fill(institution.name);
  await expect(
    directory.getByRole("link", { name: institution.name, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Region", exact: true })
    .selectOption("Southern");
  await page
    .getByRole("combobox", { name: "Responsible bureau", exact: true })
    .selectOption("RB");
  await expect(directory.locator("tbody tr")).toHaveCount(1);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: "../tests/results/institution-directory.png",
    fullPage: true,
  });
  await directory
    .getByRole("link", { name: institution.name, exact: true })
    .click();
  await expect(page).toHaveURL(`/institutions/${institution.id}`);
  await expect(
    page.getByRole("heading", { name: institution.name, exact: true }),
  ).toBeVisible();
  await page.goto(`/institutions?q=NO-SUCH-INSTITUTION-${stamp}`);
  await expect(
    page.getByText("No institutions match these filters."),
  ).toBeVisible();
});

test("all-time overview, case pagination beyond twenty, filter reset and full action history", async ({
  page,
}) => {
  await login(page);
  await page.goto(`/institutions/${institution.id}?from=2099-01-01`);
  await expect(
    page.getByText("All-time institution profile.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "All cases 25", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open cases 25", exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: "../tests/results/institution-profile.png",
    fullPage: true,
  });
  await section(page, "Cases").click();
  const cases = page.getByRole("region", {
    name: "Complaint list",
    exact: true,
  });
  await expect(cases.locator("tbody tr")).toHaveCount(20);
  const casePage = page.waitForResponse(
    (r) =>
      r.url().includes(`/institutions/${institution.id}/cases?`) &&
      r.url().includes("page=2"),
  );
  await page.getByRole("button", { name: "Next", exact: true }).click();
  expect((await casePage).status()).toBe(200);
  await expect(cases.locator("tbody tr")).toHaveCount(5);
  await page
    .getByRole("combobox", { name: "Status", exact: true })
    .selectOption("disposed");
  await expect(page).not.toHaveURL(/page=2/);
  await expect(page.getByText("No cases match these filters.")).toBeVisible();
  await section(page, "History").click();
  const timeline = page.getByRole("region", {
    name: "Institution action history",
    exact: true,
  });
  await expect(timeline.locator(".timeline > li")).toHaveCount(20);
  const firstId = await timeline.locator(".case-ref").first().textContent();
  await timeline.getByRole("button", { name: "Next", exact: true }).click();
  await expect(timeline.locator(".timeline > li")).toHaveCount(5);
  expect(await timeline.locator(".case-ref").first().textContent()).not.toBe(
    firstId,
  );
  await expect(timeline.locator(".case-ref").first()).toHaveAttribute(
    "href",
    /\/cases\//,
  );
});

test("district search is server-side, includes empty institutions and resets pagination", async ({
  page,
}) => {
  const record = await post("/api/institution-registry", {
    name: `District-only browser institution ${stamp}`,
    permanent_id: `DIST-${stamp}`,
    region: "Southern",
    district: `Coastal ${stamp} North`,
    reason: "Synthetic district search acceptance fixture",
  });
  await login(page);
  await page.goto("/institutions?page=2");
  await expect(page.getByText(/records · Page 2/)).toBeVisible();
  const response = page.waitForResponse(
    (r) =>
      r.url().includes("/api/institution-registry?") &&
      r.url().includes("district="),
  );
  await page.getByLabel("District", { exact: true }).fill(`${stamp} nOrTh`);
  expect((await (await response).json()).count).toBe(1);
  await expect(page).not.toHaveURL(/page=2/);
  await expect(
    page.getByRole("link", { name: record.name, exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByLabel("District", { exact: true })).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(392);
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(page.getByLabel("District", { exact: true })).toHaveValue("");
  await expect(page).not.toHaveURL(/district=/);
});

test("coordinator registration and audited editing use real APIs", async ({
  page,
}) => {
  await login(page);
  await page.goto("/institutions/new");
  const name = `Browser registered institution ${stamp}`;
  await page.getByLabel("Institution name", { exact: true }).fill(name);
  await page.getByLabel("AICTE Permanent ID").fill(`UI-${stamp}-form`);
  await page.getByLabel("Region", { exact: true }).fill("Southern");
  await page.getByLabel("District", { exact: true }).fill("Fictional district");
  await page.getByLabel("Official email (optional)").fill("office@example.org");
  await page
    .getByLabel("Reason for registration")
    .fill("Synthetic UI registration acceptance check");
  await page
    .getByRole("button", { name: "Register institution", exact: true })
    .click();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  await expect(page.getByText(/Institution saved/)).toBeVisible();
  const id = page.url().split("/").pop();
  await expect(
    page.getByRole("link", { name: "All cases 0", exact: true }),
  ).toBeVisible();
  await section(page, "History").click();
  await expect(
    page.getByText("No recorded case actions are visible within your access."),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Edit institution", exact: true })
    .click();
  await expect(page.getByLabel("AICTE Permanent ID")).toHaveAttribute(
    "readonly",
    "",
  );
  await page.getByLabel("Official phone (optional)").fill("+91 12345 67890");
  await page
    .getByLabel("Reason for edit")
    .fill("Add official contact for synthetic fixture");
  const saved = page.waitForResponse(
    (r) =>
      r.request().method() === "PATCH" &&
      r.url().endsWith(`/institutions/${id}`),
  );
  await page.getByRole("button", { name: "Save institution" }).click();
  expect((await saved).status()).toBe(200);
  await expect(
    page.getByText("+91 12345 67890", { exact: true }),
  ).toBeVisible();
  const profile = await (
    await page.request.get(`/api/institutions/${id}`)
  ).json();
  expect(profile.version).toBe(2);
  expect(profile.permanent_id).toBe(`UI-${stamp}-form`);
});

test("stale edits return 409, preserve the draft and require explicit reload", async ({
  page,
}) => {
  const record = await createInstitution("conflict");
  await login(page);
  await page.goto(`/institutions/${record.id}/edit`);
  await page
    .getByLabel("Institution name", { exact: true })
    .fill("Unsaved browser draft");
  await page.getByLabel("Reason for edit").fill("Stale browser change");
  await post(
    `/api/institutions/${record.id}`,
    {
      name: "Concurrent saved name",
      reason: "Concurrent acceptance edit",
      expected_version: 1,
    },
    "patch",
  );
  const conflicted = page.waitForResponse(
    (r) =>
      r.request().method() === "PATCH" &&
      r.url().endsWith(`/institutions/${record.id}`),
  );
  await page.getByRole("button", { name: "Save institution" }).click();
  expect((await conflicted).status()).toBe(409);
  await expect(page.getByRole("alert")).toContainText(
    "Your entries are still here",
  );
  await expect(
    page.getByLabel("Institution name", { exact: true }),
  ).toHaveValue("Unsaved browser draft");
  await expect(
    page.getByRole("button", { name: "Save institution" }),
  ).toBeDisabled();
  await page
    .getByRole("button", {
      name: "Reload latest profile (discard unsaved entries)",
    })
    .click();
  await expect(
    page.getByLabel("Institution name", { exact: true }),
  ).toHaveValue("Concurrent saved name");
  await page
    .getByLabel("Reason for edit")
    .fill("Review latest profile before resaving");
  await page
    .getByLabel("Institution name", { exact: true })
    .fill("Reviewed final name");
  await page.getByRole("button", { name: "Save institution" }).click();
  await expect(
    page.getByRole("heading", { name: "Reviewed final name", exact: true }),
  ).toBeVisible();
  expect(
    (await (await backend.get(`/api/institutions/${record.id}`)).json())
      .version,
  ).toBe(3);
});

for (const [username, total] of [
  ["officer_rb", 15],
  ["auditor", 25],
] as const) {
  test(`${username} sees the correct scope and cannot edit institutions`, async ({
    page,
  }) => {
    await login(page, username);
    await page.goto(`/institutions/${institution.id}`);
    await page.bringToFront();
    await expect(
      page.getByRole("link", { name: `All cases ${total}`, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Edit institution", exact: true }),
    ).toHaveCount(0);
    const response = await page.request.patch(
      `/api/institutions/${institution.id}`,
      {
        data: {
          name: "Forbidden",
          expected_version: 1,
          reason: "Permission test",
        },
        headers: { "X-CSRFToken": await csrf(page.request) },
      },
    );
    expect(response.status()).toBe(403);
    await section(page, "Cases").click();
    const rows = await (
      await page.request.get(`/api/institutions/${institution.id}/cases`)
    ).json();
    expect(rows.count).toBe(total);
    if (username === "officer_rb")
      expect(
        rows.results.every((c: { bureau: string }) => c.bureau === "RB"),
      ).toBeTruthy();
    const restricted: string[] = [];
    page.on("request", (request) => {
      if (
        request.url().includes("/api/overlaps") ||
        request.url().includes("/api/dashboard?institution=")
      )
        restricted.push(request.url());
    });
    await section(page, "Coordination").click();
    if (username === "officer_rb") {
      await expect(
        page.getByText(
          "Cross-bureau coordination is available to coordinators and auditors.",
        ),
      ).toBeVisible();
      expect(restricted).toEqual([]);
      await expect(page.getByText(/Cosine similarity/)).toHaveCount(0);
    } else {
      await expect(
        page.getByRole("link", { name: "Inspect suggestions →" }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Record decision" }),
      ).toHaveCount(0);
    }
    await page.goto(`/institutions/${institution.id}/edit`);
    await expect(page.getByRole("alert")).toContainText("Only coordinators");
    await expect(
      page.getByRole("button", { name: "Save institution" }),
    ).toHaveCount(0);
    await page.goto("/institutions/new");
    await expect(page.getByRole("alert")).toContainText("Only coordinators");
  });
}

test("coordination and reports reuse institution-scoped backend facts", async ({
  page,
}) => {
  await login(page);
  await page.goto(`/institutions/${institution.id}?section=coordination`);
  await expect(
    page.getByRole("heading", { name: "Cross-bureau attention needed" }),
  ).toBeVisible();
  await expect(
    page.getByText("25 open cases are currently owned by 2 distinct bureaus."),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Review suggestions →" }),
  ).toHaveAttribute("href", `/coordination?institution=${institution.id}`);
  await section(page, "Reports").click();
  await expect(
    page.getByRole("heading", { name: "Data report" }),
  ).toBeVisible();
  const facts = await (
    await page.request.get(`/api/dashboard?institution=${institution.id}`)
  ).json();
  expect(facts.total).toBe(25);
  await expect(
    page.locator(".import-stats").getByText("25", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Print / Save PDF" }),
  ).toBeVisible();
  await page.emulateMedia({ media: "print" });
  await expect(
    page.getByRole("navigation", { name: "Institution sections" }),
  ).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Refresh profile" }),
  ).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Data report" }),
  ).toBeVisible();
});

test("loading, malformed responses and directory errors remain usable", async ({
  page,
}) => {
  await login(page);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(`**/api/institutions/${institution.id}`, async (route) => {
    await gate;
    await route.fulfill({ json: {} });
  });
  await page.goto(`/institutions/${institution.id}`);
  await expect(
    page.getByRole("status").filter({ hasText: "Loading workspace" }),
  ).toBeVisible();
  release();
  await expect(page.getByRole("alert")).toContainText(
    "incomplete or invalid data",
  );
  await page.route("**/api/institution-registry?*", (route) =>
    route.fulfill({
      status: 500,
      json: { error: "Registry temporarily unavailable" },
    }),
  );
  await page.goto("/institutions");
  await expect(page.getByRole("alert")).toContainText(
    "Registry temporarily unavailable",
  );
  await expect(page.getByLabel("Search institutions")).toBeVisible();
});

test("institution links, keyboard navigation and mobile pages stay contained", async ({
  page,
}) => {
  await login(page);
  await page.goto(`/cases?institution=${institution.id}`);
  const link = page
    .getByRole("link", { name: institution.name, exact: true })
    .first();
  await link.focus();
  await expect(link).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(`/institutions/${institution.id}`);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: institution.name, exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../tests/results/institution-profile-mobile.png",
    fullPage: true,
  });
  for (const tab of [
    "Overview",
    "Cases",
    "History",
    "Coordination",
    "Reports",
  ]) {
    await section(page, tab).click();
    await expect(
      page.getByRole("heading", { name: institution.name, exact: true }),
    ).toBeVisible();
    if (tab === "Cases")
      await expect(page.locator(".table-scroll tbody tr")).toHaveCount(20);
    if (tab === "History")
      await expect(page.locator(".institution-timeline > li")).toHaveCount(20);
    if (tab === "Coordination")
      await expect(
        page.getByText(
          "25 open cases are currently owned by 2 distinct bureaus.",
        ),
      ).toBeVisible();
    if (tab === "Reports")
      await expect(
        page.getByRole("heading", { name: "Active bureau workload" }),
      ).toBeVisible();
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBeLessThanOrEqual(392);
  }
  await page.goto("/institutions");
  await expect(
    page.getByRole("heading", { name: "Institutions", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(392);
});
