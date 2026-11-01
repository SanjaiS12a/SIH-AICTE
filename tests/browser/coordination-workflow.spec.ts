import { artifact } from "./support";
import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
let backend: APIRequestContext;
let institution: any, cases: any[], options: any;
const stamp = Date.now();
const rbTask = `Check regulatory records ${stamp}`;
const pgTask = `Confirm refund payment ${stamp}`;
async function token(context: APIRequestContext) {
  return (await context.storageState()).cookies.find(
    (c) => c.name === "csrftoken",
  )!.value;
}
async function post(url: string, data: unknown) {
  return backend.post(url, {
    data,
    headers: { "X-CSRFToken": await token(backend) },
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
function payload() {
  const rb = options.officers.find((o: any) => o.bureau === "RB"),
    pg = options.officers.find((o: any) => o.bureau === "PGRC");
  return {
    submission_id: crypto.randomUUID(),
    institution: institution.id,
    cases: cases.map((c) => c.id),
    reason: `Private cross-Bureau evidence ${stamp}`,
    lead_bureau: "RB",
    lead_officer: rb.id,
    participants: [
      { bureau: "RB", officer: rb.id, instruction: rbTask },
      { bureau: "PGRC", officer: pg.id, instruction: pgTask },
    ],
  };
}
test.beforeAll(async ({ playwright }) => {
  backend = await playwright.request.newContext({
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174",
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
  options = await (await backend.get("/api/options")).json();
  const inst = await post("/api/institution-registry", {
    name: `Accountable Institute ${stamp}`,
    permanent_id: `CW-${stamp}`,
    region: "Southern",
    district: "Coordination demonstration",
    reason: "Fictional workflow acceptance fixture",
  });
  expect(inst.status()).toBe(201);
  institution = await inst.json();
  cases = [];
  for (let n = 0; n < 21; n++) {
    const response = await post("/api/cases", {
      submission_id: crypto.randomUUID(),
      institution: institution.id,
      bureau: n === 1 ? "PGRC" : "RB",
      source_system: "coordination-workflow-browser",
      source_reference: crypto.randomUUID(),
      category: "refunds",
      summary: `Fictional fee refund records require verification for incident ${stamp}-${n}.`,
      description:
        "Synthetic acceptance data, no actual institution or complainant.",
    });
    expect(response.status()).toBe(201);
    cases.push(await response.json());
  }
});
test.afterAll(async () => backend?.dispose());
test("institution to agreed actions, acknowledgment, completion and outcome", async ({
  page,
  browser,
}) => {
  await login(page);
  await page.goto(`/institutions/${institution.id}?section=coordination`);
  await page
    .getByRole("link", { name: "Agreed responsibilities and follow-up" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Coordination workspace", exact: true }),
  ).toBeVisible();
  // The oldest case is beyond the first server page; selection survives navigation.
  await page
    .getByRole("checkbox", { name: new RegExp(cases[1].reference) })
    .check();
  await page.getByRole("button", { name: "Next cases", exact: true }).click();
  await page
    .getByRole("checkbox", { name: new RegExp(cases[0].reference) })
    .check();
  await page
    .getByLabel("Private coordination reason")
    .fill(`Private agreed review ${stamp}`);
  for (const [code, task] of [
    ["RB", rbTask],
    ["PGRC", pgTask],
  ]) {
    const bureau = options.bureaus.find((b: any) => b.code === code);
    await page
      .getByRole("checkbox", { name: bureau.name, exact: true })
      .check();
    await page
      .getByLabel(`Responsible officer — ${bureau.name}`, { exact: true })
      .selectOption(
        String(options.officers.find((o: any) => o.bureau === code).id),
      );
    await page
      .getByLabel(`Shared instruction — ${bureau.name}`, { exact: true })
      .fill(task);
  }
  await page.getByLabel("Lead Bureau", { exact: true }).selectOption("RB");
  await page
    .getByRole("button", { name: "Record agreed coordination", exact: true })
    .click();
  await expect(page).toHaveURL(/\/coordination\/workspace\/[0-9a-f-]+$/);
  const url = page.url();
  for (const [username, task] of [
    ["officer_rb", rbTask],
    ["officer_pgrc", pgTask],
  ]) {
    const officer = await browser.newPage({ baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174" });
    await login(officer, username);
    await officer.goto("/coordination/requests");
    const card = officer.locator("section.panel").filter({ hasText: task });
    await expect(card).toHaveCount(1);
    await expect(
      officer.getByText(`Private agreed review ${stamp}`),
    ).toHaveCount(0);
    await expect(
      officer.getByText(username === "officer_rb" ? pgTask : rbTask),
    ).toHaveCount(0);
    await card
      .getByRole("button", { name: "Acknowledge agreed action" })
      .click();
    await card
      .getByLabel("Completion note")
      .fill(`${username} verified the agreed records.`);
    await card.getByRole("button", { name: "Complete agreed action" }).click();
    await expect(
      card.getByText(`Completed: ${username} verified the agreed records.`),
    ).toBeVisible();
    await officer.close();
  }
  await page.goto(url);
  await page
    .getByLabel("Coordination outcome")
    .fill(
      "Regulatory evidence and refund payment checked; responsibilities completed independently.",
    );
  await page
    .getByRole("button", { name: "Close coordination", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Coordination closed", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: artifact("accountable-coordination.png"),
    fullPage: true,
  });
});
test("complete history pagination, auditor read-only and mobile placement", async ({
  page,
}) => {
  const r = await post("/api/coordination-records", payload());
  expect(r.status()).toBe(201);
  const record = await r.json();
  await login(page, "auditor");
  await page.goto(`/coordination/workspace/${record.id}`);
  await expect(
    page.getByRole("heading", { name: "Authoritative case action history" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(
    page.getByRole("heading", { name: "coordination opened" }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: "Close coordination", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Revise this Bureau’s agreed action"),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: artifact("accountable-coordination-mobile.png"),
    fullPage: true,
  });
});
test("stale action retains the outcome draft and officer direct navigation is denied", async ({
  page,
}) => {
  const r = await post("/api/coordination-records", payload());
  const record = await r.json();
  await login(page);
  await page.goto(`/coordination/workspace/${record.id}`);
  await page
    .getByLabel("Coordination outcome")
    .fill("Retain this outcome draft on conflict");
  await page.route(
    `**/api/coordination-records/${record.id}/actions`,
    (route) =>
      route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({
          error: "This record changed. Refresh before saving.",
        }),
      }),
  );
  await page
    .getByRole("button", { name: "Close coordination", exact: true })
    .click();
  await expect(page.getByLabel("Coordination outcome")).toHaveValue(
    "Retain this outcome draft on conflict",
  );
  await expect(
    page.getByRole("button", { name: "Close coordination", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Reload record and discard draft" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reload record and discard draft" })
    .click();
  await expect(page.getByLabel("Coordination outcome")).toHaveValue("");
  await login(page, "officer_rb");
  await page.goto(`/coordination/workspace/${record.id}`);
  await expect(page.getByRole("alert")).toHaveText(
    "Coordination management access is required.",
  );
  await expect(
    page.getByText(`Private cross-Bureau evidence ${stamp}`),
  ).toHaveCount(0);
});

test("malformed coordination responses show errors and empty workspaces remain usable", async ({
  page,
}) => {
  const r = await post("/api/coordination-records", payload());
  expect(r.status()).toBe(201);
  const record = await r.json();
  await login(page);
  await page.route(`**/api/coordination-records/${record.id}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ state: "in_coordination" }),
    }),
  );
  await page.goto(`/coordination/workspace/${record.id}`);
  await expect(page.getByRole("alert")).toContainText(
    "incomplete or invalid data",
  );
  await page.route("**/api/coordination-records?*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        count: 0,
        results: [],
        next: null,
        previous: null,
      }),
    }),
  );
  await page.goto("/coordination/workspace");
  await expect(page.getByText("No coordination records yet.")).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: "Choose an institution to open coordination",
    }),
  ).toBeVisible();
});
