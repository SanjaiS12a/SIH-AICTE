import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
let backend: APIRequestContext;
let institution: any, first: any, second: any;
const stamp = Date.now();
async function token(context: APIRequestContext) {
  return (await context.storageState()).cookies.find(
    (c) => c.name === "csrftoken",
  )!.value;
}
async function post(url: string, data: unknown, context = backend) {
  return context.post(url, {
    data,
    headers: { "X-CSRFToken": await token(context) },
  });
}
async function login(page: Page, username = "coordinator") {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username:").fill(username);
  await page
    .getByLabel("Password:")
    .fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Complaint Monitoring Dashboard" }),
  ).toBeVisible();
}
async function makeInstitution(suffix: string) {
  const r = await post("/api/institution-registry", {
    name: `Completion Institute ${stamp}-${suffix}`,
    permanent_id: `FIN-${stamp}-${suffix}`,
    region: "Southern",
    district: "Final district",
    reason: "Synthetic completion acceptance fixture",
  });
  expect(r.status()).toBe(201);
  return r.json();
}
async function makeCase(inst: any, bureau: string, old = false) {
  const r = await post("/api/cases", {
    submission_id: crypto.randomUUID(),
    institution: inst.id,
    bureau,
    source_system: "completion-browser",
    source_reference: crypto.randomUUID(),
    category: bureau === "RB" ? "facilities" : "scholarships",
    summary:
      bureau === "RB"
        ? "Wheelchair access to the library ramp is obstructed by stored furniture."
        : "A scholarship payment was deposited into an incorrect student bank account.",
    description:
      "Fictional acceptance data; no real institution or complainant.",
    ...(old ? { received_at: "2025-01-15T10:00:00+05:30" } : {}),
  });
  expect(r.status()).toBe(201);
  return r.json();
}
test.beforeAll(async ({ playwright }) => {
  backend = await playwright.request.newContext({
    baseURL: "http://127.0.0.1:5173",
  });
  await backend.get("/accounts/login/");
  expect(
    (
      await backend.post("/accounts/login/", {
        form: {
          username: "coordinator",
          password: process.env.DEMO_PASSWORD || "Demo-only-26264!",
          csrfmiddlewaretoken: await token(backend),
        },
      })
    ).ok(),
  ).toBeTruthy();
  institution = await makeInstitution("cohort");
  first = await makeCase(institution, "RB");
  second = await makeCase(institution, "PGRC", true);
  expect(
    (
      await post("/api/relationships", {
        left: first.id,
        right: second.id,
        decision: "unrelated",
        reason: "Separate incidents; restricted coordination evidence",
      })
    ).ok(),
  ).toBeTruthy();
});
test.afterAll(async () => backend?.dispose());
test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, (route) =>
    ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname)
      ? route.continue()
      : route.abort(),
  );
});

test("manual comparison, retry-safe pair and stale review preserve both histories", async ({
  page,
}) => {
  const inst = await makeInstitution("manual");
  const a = await makeCase(inst, "RB"),
    b = await makeCase(inst, "PGRC");
  await login(page);
  await page.goto(`/institutions/${inst.id}?section=coordination`);
  await page
    .getByRole("link", { name: "Create manual relationship", exact: true })
    .click();
  await page
    .getByRole("checkbox", { name: `Select ${a.reference}`, exact: true })
    .check();
  await page
    .getByRole("checkbox", { name: `Select ${b.reference}`, exact: true })
    .check();
  await page
    .getByRole("combobox", { name: "Relationship decision" })
    .selectOption("related_issue");
  await page
    .getByLabel("Relationship explanation")
    .fill("Human review links two different access and administration issues");
  await page
    .getByRole("button", { name: "Record manual relationship", exact: true })
    .click();
  await expect(
    page.getByText("Not model-scored", { exact: true }).first(),
  ).toBeVisible();
  const pairs = await (
    await backend.get(`/api/overlaps?institution=${inst.id}&decision=all`)
  ).json();
  expect(pairs.count).toBe(1);
  const pair = pairs.results[0];
  expect(pair.origin).toBe("manual");
  expect(pair.score).toBeNull();
  await page
    .getByRole("textbox", { name: "Review reason", exact: true })
    .fill("Retain this conflicting draft");
  expect(
    (
      await post(`/api/overlaps/${pair.id}/review`, {
        expected_version: pair.version,
        decision: "unrelated",
        reason: "Another coordinator has verified separate incidents",
      })
    ).status(),
  ).toBe(200);
  await page
    .getByRole("button", { name: "Record decision", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reload relationship and discard draft" }),
  ).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Review reason", exact: true }),
  ).toHaveValue("Retain this conflicting draft");
  await page
    .getByRole("button", { name: "Reload relationship and discard draft" })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Review reason", exact: true }),
  ).toHaveValue("Another coordinator has verified separate incidents");
  const csv = await backend.get(
    `/api/relationships.csv?institution=${inst.id}&decision=all`,
  );
  expect(await csv.text()).toContain("manual,Not model-scored");
  for (const record of [a, b]) {
    const detail = await (await backend.get(`/api/cases/${record.id}`)).json();
    expect(
      detail.actions.filter((x: any) => x.kind === "overlap_review").length,
    ).toBe(2);
  }
  await page.screenshot({
    path: "../tests/results/manual-relationship.png",
    fullPage: true,
  });
});

test("management receipt cohort and all-time coordination have matching drill-downs", async ({
  page,
}) => {
  await login(page);
  const today = new Date().toLocaleDateString("en-CA");
  await page.goto(`/?institution=${institution.id}&from=${today}&to=${today}`);
  const facts = await (
    await backend.get(
      `/api/dashboard?institution=${institution.id}&from=${today}&to=${today}`,
    )
  ).json();
  expect(facts.total).toBe(1);
  expect(facts.coordination_institutions).toBe(1);
  await expect(
    page.getByRole("heading", { name: "Institution monitoring", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Case classifications — Unclassified included",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Institutions with cases/ }).click();
  await expect(
    page.getByRole("link", { name: institution.name, exact: true }),
  ).toBeVisible();
  await page.goto(
    `/coordination/activity?institution=${institution.id}&from=2099-01-01&category=facilities&bureau=RB`,
  );
  await expect(
    page.getByRole("heading", {
      name: "Cross-Bureau Activity — Coordination Review Required",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: first.reference, exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: second.reference, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "View all 2 active cases →", exact: true })
    .click();
  await expect(page).not.toHaveURL(/from=/);
  await expect(page.getByText(/2 records · Page 1/)).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/?institution=${institution.id}`);
  await expect(
    page.getByRole("heading", { name: "Institution monitoring", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(392);
  await page.screenshot({
    path: "../tests/results/management-mobile.png",
    fullPage: true,
  });
});

test("auditor reads manual evidence while officers cannot obtain it", async ({
  page,
}) => {
  await login(page, "auditor");
  await page.goto(`/coordination?institution=${institution.id}&decision=all`);
  await expect(
    page.getByText("Not model-scored", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record decision", exact: true }),
  ).toHaveCount(0);
  expect(
    (
      await post(
        "/api/relationships",
        {
          left: first.id,
          right: second.id,
          decision: "same_incident",
          reason: "Forbidden",
        },
        page.request,
      )
    ).status(),
  ).toBe(403);
  await login(page, "officer_rb");
  expect(
    (
      await page.request.get(`/api/overlaps?institution=${institution.id}`)
    ).status(),
  ).toBe(403);
  expect((await page.request.get("/api/coordination-notices")).status()).toBe(
    403,
  );
  const own = await (await page.request.get(`/api/cases/${first.id}`)).json();
  expect(JSON.stringify(own.actions)).not.toContain(
    "restricted coordination evidence",
  );
  expect(JSON.stringify(own.actions)).not.toContain("overlap_id");
  await page.goto(`/relationships/new?institution=${institution.id}`);
  await expect(
    page.getByText("Only coordinators can create relationships.", {
      exact: true,
    }),
  ).toBeVisible();
});

test("movement views use action timestamps and CSV agrees with the complete list", async ({
  page,
}) => {
  await login(page);
  const today = new Date().toLocaleDateString("en-CA");
  const query = `institution=${institution.id}&from=${today}&to=${today}&event=registered`;
  const facts = await (await backend.get(`/api/movements?${query}`)).json();
  expect(facts.count).toBe(2);
  await page.goto(`/movements?${query}`);
  await expect(page.getByText(/2 records · Page 1/)).toBeVisible();
  await expect(
    page.getByRole("link", { name: second.reference, exact: true }),
  ).toBeVisible();
  const csv = await (await backend.get(`/api/movements.csv?${query}`)).text();
  expect(csv).toContain(second.reference);
  expect(csv.trim().split("\n").length).toBe(3);
});
