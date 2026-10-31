import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const fixtures = resolve(process.cwd(), "../tests/fixtures/bureau-intake");
const manifest = JSON.parse(
  readFileSync(resolve(fixtures, "manifest.json"), "utf8"),
);
const stamp = Date.now();
let backend: APIRequestContext, institution: any, firstJob: any;
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
function csv(name: string) {
  return readFileSync(resolve(fixtures, name), "utf8").replaceAll(
    manifest.institution.permanent_id,
    institution.permanent_id,
  );
}
function source(key: string) {
  return `${manifest.sources[key].source_system}-${stamp}`;
}
async function upload(key: string, filename?: string, content?: string) {
  const spec = manifest.sources[key];
  const response = await backend.post("/api/imports", {
    multipart: {
      kind: "complaints",
      source_system: source(key),
      source_bureau: spec.source_bureau,
      status_mapping: JSON.stringify(spec.status_mapping),
      file: {
        name: filename || spec.filename,
        mimeType: "text/csv",
        buffer: Buffer.from(content || csv(filename || spec.filename)),
      },
    },
    headers: { "X-CSRFToken": await token(backend) },
  });
  expect(response.status()).toBe(201);
  const job = await response.json();
  const preview = await post(`/api/imports/${job.id}`, {
    action: "preview",
    mapping: spec.mapping,
  });
  expect(preview.status()).toBe(200);
  return preview.json();
}
async function finish(job: any) {
  expect(
    (await post(`/api/imports/${job.id}`, { action: "confirm" })).ok(),
  ).toBeTruthy();
  await expect
    .poll(
      async () =>
        (await (await backend.get(`/api/imports/${job.id}`)).json())
          .registered_at,
      { timeout: 30000 },
    )
    .toBeTruthy();
}
async function ensureRB() {
  const existing = await (
    await backend.get(`/api/institutions/${institution.id}/cases`)
  ).json();
  if (!existing.results.some((c: any) => c.source_reference === "RB-2026-001"))
    await finish(await upload("rb"));
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
  const response = await post("/api/institution-registry", {
    ...manifest.institution,
    permanent_id: `SRC-${stamp}`,
    name: `Bureau Intake Institute ${stamp}`,
    reason: "Synthetic multi-source acceptance fixture",
  });
  expect(response.status()).toBe(201);
  institution = await response.json();
});
test.afterAll(async () => backend?.dispose());

test("independent Bureau files consolidate, replay safely and expose accepted source information", async ({
  page,
}) => {
  test.setTimeout(90000);
  await login(page);
  await page.goto("/imports");
  await page
    .getByRole("checkbox", { name: "This is a Bureau source upload" })
    .check();
  await page.getByLabel("Source ID", { exact: true }).fill(source("rb"));
  await page.getByLabel("Source Bureau", { exact: true }).selectOption("RB");
  await page.getByLabel("Source status 1", { exact: true }).fill("Received");
  await page.getByRole("button", { name: "Add status mapping" }).click();
  await page.getByLabel("Source status 2", { exact: true }).fill("Scrutiny");
  await page
    .getByLabel("Portal status 2", { exact: true })
    .selectOption("under_review");
  await page.getByLabel("Spreadsheet", { exact: true }).setInputFiles({
    name: "rb.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(csv("rb.csv")),
  });
  await page.screenshot({
    path: "../tests/results/source-upload-setup.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Upload and preview", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Map and validate columns" }),
  ).toBeVisible();
  const jobId = new URL(page.url()).pathname.split("/").pop();
  for (const [key, value] of Object.entries(manifest.sources.rb.mapping)) {
    await page
      .getByRole("combobox", {
        name: new RegExp(`^${key.replaceAll("_", " ")}`),
      })
      .selectOption(value as string);
  }
  await page
    .getByRole("button", { name: "Validate mapping", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Confirm import", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Confirm import", exact: true })
    .click();
  firstJob = { id: jobId };
  await finish(firstJob);
  for (const key of ["pgrc", "other"]) await finish(await upload(key));
  await page.goto(`/institutions/${institution.id}?section=cases`);
  for (const reference of [
    "RB-2026-001",
    "RB-2026-002",
    "PGRC-2026-001",
    "CELL-2026-001",
  ])
    await expect(page.getByText(new RegExp(reference))).toBeVisible();
  const cases = await (
    await backend.get(`/api/institutions/${institution.id}/cases`)
  ).json();
  expect(cases.count).toBe(4);
  expect(new Set(cases.results.map((c: any) => c.source_system)).size).toBe(3);
  const repeat = await upload("rb");
  expect(repeat.counts.duplicate).toBe(2);
  await finish(repeat);
  expect(
    (
      await (
        await backend.get(`/api/institutions/${institution.id}/cases`)
      ).json()
    ).count,
  ).toBe(4);
  await page.goto(
    `/cases/${cases.results.find((c: any) => c.source_reference === "RB-2026-001").id}`,
  );
  await expect(
    page.getByText(/Original source status: Received/),
  ).toBeVisible();
  const exported = await backend.get(
    `/api/reports.csv?institution=${institution.id}`,
  );
  expect(await exported.text()).toContain("Original source status");
  await page.goto(`/imports/sources?q=${stamp}`);
  for (const key of ["rb", "pgrc", "other"])
    await expect(
      page.getByRole("row").filter({ hasText: source(key) }),
    ).toHaveCount(1);
  await page.screenshot({
    path: "../tests/results/bureau-source-monitor.png",
    fullPage: true,
  });
  const notices = await (
    await backend.get(`/api/coordination-notices?institution=${institution.id}`)
  ).json();
  expect(notices.results[0].bureaus).toBe(3);
  await page.goto(`/institutions/${institution.id}?section=coordination`);
  await page
    .getByRole("link", { name: "Agreed responsibilities and follow-up" })
    .click();
  await expect(
    page
      .getByRole("group", { name: "Linked cases — select one or more" })
      .getByRole("checkbox"),
  ).toHaveCount(4);
});

test("changed source rows require review, reject stale case versions and never overwrite allegations", async ({
  page,
}) => {
  await ensureRB();
  const job = await upload("rb", "rb-changed.csv");
  expect(job.counts.conflict).toBe(1);
  await finish(job);
  await login(page);
  await page.goto(`/imports/${job.id}/rows?state=conflict`);
  await expect(
    page.getByRole("heading", { name: "Row 2 — conflict", exact: true }),
  ).toBeVisible();
  const row = (
    await (
      await backend.get(`/api/imports/${job.id}/rows?state=conflict`)
    ).json()
  ).results[0];
  expect(
    (await (await backend.get(`/api/imports/${job.id}/report`)).json()).total,
  ).toBe(0);
  const reason =
    "Retain verified portal evidence and request a corrected Bureau file.";
  await page.getByLabel("Reason for keeping portal record").fill(reason);
  expect(
    (
      await post(`/api/cases/${row.current_case.id}/actions`, {
        expected_version: row.current_case.version,
        kind: "note",
        reason: "New evidence arrived while source review was open.",
      })
    ).ok(),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "Keep portal record and record review" })
    .click();
  await expect(page.getByLabel("Reason for keeping portal record")).toHaveValue(
    reason,
  );
  await expect(
    page.getByRole("button", { name: "Keep portal record and record review" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Reload row and discard draft" })
    .click();
  await expect(page.getByLabel("Reason for keeping portal record")).toHaveValue(
    "",
  );
  await page.getByLabel("Reason for keeping portal record").fill(reason);
  await page
    .getByRole("button", { name: "Keep portal record and record review" })
    .click();
  await expect(page.getByText("No rows match this state.")).toBeVisible();
  await page.getByLabel("Row state", { exact: true }).selectOption("resolved");
  await expect(page.getByText(new RegExp(reason))).toBeVisible();
  const current = await (
    await backend.get(`/api/cases/${row.current_case.id}`)
  ).json();
  expect(current.summary).toBe(row.current_case.summary);
  expect(current.status).toBe(row.current_case.status);
  expect(
    current.actions.filter((a: any) => a.kind === "source_conflict"),
  ).toHaveLength(1);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../tests/results/source-conflict-mobile.png",
    fullPage: true,
  });
});

test("source rows paginate past twenty and role scopes apply to lists and reviews", async ({
  page,
}) => {
  await ensureRB();
  const header = csv("rb.csv").split(/\r?\n/)[0],
    sample = csv("rb.csv").split(/\r?\n/)[1];
  const content =
    header +
    "\n" +
    Array.from({ length: 21 }, (_, n) =>
      sample.replace("RB-2026-001", `ROW-${n}`),
    ).join("\n");
  const preview = await upload("rb", "pagination.csv", content);
  await login(page);
  await page.goto(`/imports/${preview.id}/rows`);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Row 22 — ready", exact: true }),
  ).toBeVisible();
  const changed = await upload("rb", "rb-changed.csv");
  await finish(changed);
  await login(page, "auditor");
  await page.goto(`/imports/${changed.id}/rows?state=conflict`);
  await expect(
    page.getByRole("heading", { name: "Row 2 — conflict", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Keep portal record and record review" }),
  ).toHaveCount(0);
  const denied = await page.request.post(
    `/api/imports/${changed.id}/rows/2/resolve`,
    { data: {}, headers: { "X-CSRFToken": await token(page.request) } },
  );
  expect(denied.status()).toBe(403);
  await login(page, "officer_pgrc");
  await page.goto(`/imports/${changed.id}/rows`);
  await expect(page.getByRole("alert")).toContainText(
    "unavailable in your current permission scope",
  );
  expect(
    (await page.request.get(`/api/imports/${changed.id}/rows`)).status(),
  ).toBe(404);
  await page.goto(`/imports/sources?q=${stamp}`);
  await expect(
    page.getByText(
      "No declared Bureau-source uploads in your current permission scope.",
    ),
  ).toBeVisible();
});

test("malformed source responses show a usable error", async ({ page }) => {
  await login(page);
  await page.route("**/api/source-intake?*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        count: 1,
        next: null,
        previous: null,
        results: [{ source_system: "incomplete" }],
      }),
    }),
  );
  await page.goto("/imports/sources");
  await expect(page.getByRole("alert")).toContainText(
    "incomplete or invalid data",
  );
  await expect(
    page.getByRole("heading", { name: "Bureau-source uploads", exact: true }),
  ).toBeVisible();
});
