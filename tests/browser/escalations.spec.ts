import { artifact } from "./support";
import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

let backend: APIRequestContext;
let institution: { id: string; name: string };
const stamp = Date.now();
async function csrf(context: APIRequestContext) {
  return (await context.storageState()).cookies.find(
    (c) => c.name === "csrftoken",
  )!.value;
}
async function post(context: APIRequestContext, url: string, data: unknown) {
  return context.post(url, {
    data,
    headers: { "X-CSRFToken": await csrf(context) },
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
async function createCase() {
  const response = await post(backend, "/api/cases", {
    submission_id: crypto.randomUUID(),
    institution: institution.id,
    bureau: "RB",
    classification: "grievance",
    source_system: "escalation-browser-test",
    source_reference: crypto.randomUUID(),
    category: "refunds",
    summary: "The fictional institution has not issued a tuition refund.",
    description: "Synthetic manual escalation acceptance fixture.",
  });
  expect(response.status(), await response.text()).toBe(201);
  const created = await response.json();
  const next = await post(backend, `/api/cases/${created.id}/actions`, {
    kind: "next_action",
    expected_version: created.version,
    reason: "Independent action tracking fixture",
    next_action: "Await written reply",
    next_action_date: "2026-11-15",
  });
  expect(next.status()).toBe(200);
  return next.json();
}
async function escalate(
  record: any,
  reason = "Supervisory intervention requested",
) {
  const response = await post(backend, `/api/cases/${record.id}/escalations`, {
    submission_id: crypto.randomUUID(),
    expected_version: record.version,
    reason,
  });
  expect(response.status(), await response.text()).toBe(201);
  return response.json();
}

test.beforeAll(async ({ playwright }) => {
  backend = await playwright.request.newContext({
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173",
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
  const response = await post(backend, "/api/institution-registry", {
    name: `Escalation Workflow Institute ${stamp}`,
    permanent_id: `ESC-${stamp}`,
    region: "Southern",
    district: "Fictional",
    reason: "Synthetic escalation browser fixtures",
  });
  expect(response.status()).toBe(201);
  institution = await response.json();
});
test.afterAll(async () => backend?.dispose());
test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, (route) =>
    ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname)
      ? route.continue()
      : route.abort(),
  );
});

test("officer escalation notifies coordinator and is resolved independently", async ({
  page,
}) => {
  const initial = await createCase();
  await login(page, "officer_rb");
  await page.goto(`/cases/${initial.id}`);
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("escalate");
  await page
    .getByLabel("Escalation reason", { exact: true })
    .fill("Bureau requests supervisory guidance for the refund dispute");
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await expect(
    page.getByText("Unresolved escalation", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Escalations", exact: true })
      .getByText("Pending review", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("combobox", { name: "Action", exact: true })
      .locator('option[value="escalate"]'),
  ).toHaveCount(0);
  const escalated = await (
    await backend.get(`/api/cases/${initial.id}`)
  ).json();
  for (const field of [
    "bureau",
    "status",
    "due_at",
    "next_action",
    "next_action_date",
    "classification",
  ])
    expect(escalated[field]).toBe(initial[field]);
  await expect
    .poll(async () =>
      (await (await backend.get("/api/notifications")).json()).results.some(
        (n: any) => n.kind === "escalation" && n.case_id === initial.id,
      ),
    )
    .toBe(true);
  await login(page);
  await page
    .getByRole("button", { name: "Notifications", exact: true })
    .click();
  await page
    .locator(".alerts")
    .getByRole("link", { name: new RegExp(initial.reference) })
    .click();
  await expect(page).toHaveURL(new RegExp(`${initial.id}#escalations`));
  await page.getByRole("link", { name: "Escalations", exact: true }).click();
  await page.getByLabel("Search case or institution").fill(initial.reference);
  await expect(
    page.getByRole("link", { name: initial.reference, exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: artifact("escalation-queue.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Resolve escalation", exact: true })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Resolution reason", exact: true }),
  ).toHaveAttribute("required", "");
  await page
    .getByRole("textbox", { name: "Resolution reason", exact: true })
    .fill(
      "Supervisory guidance supplied; the Bureau continues its investigation",
    );
  await page
    .getByRole("button", { name: "Confirm resolution", exact: true })
    .click();
  await expect(
    page.getByText("Escalation resolved and recorded in case history.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("No escalations match this view.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Escalation state" })
    .selectOption("resolved");
  await expect(
    page.getByText(
      "Supervisory guidance supplied; the Bureau continues its investigation",
      { exact: true },
    ),
  ).toBeVisible();
  const resolved = await (await backend.get(`/api/cases/${initial.id}`)).json();
  expect(resolved.has_unresolved_escalation).toBe(false);
  for (const field of [
    "bureau",
    "status",
    "due_at",
    "next_action",
    "next_action_date",
    "classification",
  ])
    expect(resolved[field]).toBe(initial[field]);
  expect(
    resolved.actions.filter((a: any) => a.kind.startsWith("escalation_"))
      .length,
  ).toBe(2);
});

test("transfer and closure preserve escalation, institution indicator and auditor history", async ({
  page,
}) => {
  const initial = await createCase();
  const escalation = await escalate(initial);
  await login(page);
  await page.goto(`/cases/${initial.id}`);
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("transfer");
  await page.getByLabel("Receiving bureau").selectOption("PGRC");
  await page.getByLabel("Reason / note").fill("Independent ownership transfer");
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await expect(
    page.getByText("Unresolved escalation", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("status");
  await page
    .getByRole("combobox", { name: "New status" })
    .selectOption("disposed");
  await page
    .getByLabel("Resolution note")
    .fill("Case closed independently; supervisory request still needs review");
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await expect(
    page.getByText("Unresolved escalation", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Escalations", exact: true })
      .getByText("Pending review", { exact: true }),
  ).toBeVisible();
  await page.goto(`/institutions/${institution.id}`);
  const indicator = page.getByRole("link", { name: /Unresolved escalations/ });
  await expect(indicator).toBeVisible();
  await indicator.click();
  await expect(page).toHaveURL(/escalated=true/);
  await expect(
    page.getByRole("link", { name: initial.reference, exact: true }),
  ).toBeVisible();
  await login(page, "auditor");
  await page.goto(`/cases/${initial.id}`);
  await expect(
    page.getByRole("button", { name: "Resolve escalation", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("combobox", { name: "Action", exact: true }),
  ).toHaveCount(0);
  expect(
    (
      await post(page.request, `/api/escalations/${escalation.id}/resolve`, {
        expected_version: 1,
        reason: "Forbidden auditor mutation",
      })
    ).status(),
  ).toBe(403);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(392);
  await page.screenshot({
    path: artifact("escalation-case-mobile.png"),
    fullPage: true,
  });
});

test("concurrent resolution returns 409 and preserves coordinator draft", async ({
  page,
}) => {
  const initial = await createCase();
  const escalation = await escalate(initial);
  await login(page);
  await page.goto(`/escalations?state=all&q=${initial.reference}`);
  await page
    .getByRole("button", { name: "Resolve escalation", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Resolution reason", exact: true })
    .fill("Retain my unsaved supervisory draft");
  const response = await post(
    backend,
    `/api/escalations/${escalation.id}/resolve`,
    { expected_version: 1, reason: "Another coordinator decision" },
  );
  expect(response.status()).toBe(200);
  await page
    .getByRole("button", { name: "Confirm resolution", exact: true })
    .click();
  await expect(
    page.getByText(/This escalation changed\. Your draft is retained/),
  ).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Resolution reason", exact: true }),
  ).toHaveValue("Retain my unsaved supervisory draft");
  await expect(
    page.getByRole("button", { name: "Confirm resolution", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", {
      name: "Reload escalation and discard draft",
      exact: true,
    })
    .click();
  await expect(
    page.getByText("Another coordinator decision", { exact: true }),
  ).toBeVisible();
});

test("officer queue access and foreign case escalation are denied", async ({
  page,
}) => {
  const initial = await createCase();
  await escalate(initial);
  const moved = await (await backend.get(`/api/cases/${initial.id}`)).json();
  expect(
    (
      await post(backend, `/api/cases/${initial.id}/actions`, {
        kind: "transfer",
        expected_version: moved.version,
        bureau: "PGRC",
        reason: "Foreign bureau access fixture",
      })
    ).status(),
  ).toBe(200);
  await login(page, "officer_rb");
  await expect(
    page.getByRole("link", { name: "Escalations", exact: true }),
  ).toHaveCount(0);
  await page.goto("/escalations");
  await expect(
    page.getByText("The escalation queue requires coordination access.", {
      exact: true,
    }),
  ).toBeVisible();
  expect(
    (await page.request.get(`/api/cases/${initial.id}/escalations`)).status(),
  ).toBe(404);
  expect((await page.request.get("/api/escalations")).status()).toBe(403);
});

test("invalid escalation queue responses show an error without crashing", async ({
  page,
}) => {
  await login(page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/escalations?*", (route) =>
    route.fulfill({ json: { count: 1, results: [{ id: "incomplete" }] } }),
  );
  await page.goto("/escalations");
  await expect(
    page.getByText(/server returned incomplete or invalid data/),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
