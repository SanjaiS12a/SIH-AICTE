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
async function createCase(bureau = "RB") {
  const response = await post(backend, "/api/cases", {
    submission_id: crypto.randomUUID(),
    institution: institution.id,
    bureau,
    source_system: "phase2-browser-test",
    source_reference: crypto.randomUUID(),
    category: "refunds",
    summary: "The fictional institution has not returned the tuition refund.",
    description:
      "Synthetic workflow acceptance fixture. No real complainant data.",
  });
  expect(response.status(), await response.text()).toBe(201);
  return response.json();
}
async function record(page: Page, reason: string) {
  await page.getByLabel("Reason / note").fill(reason);
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await expect(
    page.getByText("Action recorded in the case history.", { exact: true }),
  ).toBeVisible();
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
    name: `Phase 2 Workflow Institute ${stamp}`,
    permanent_id: `PHASE2-${stamp}`,
    region: "Southern",
    district: "Fictional",
    reason: "Synthetic Phase 2 browser fixtures",
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

test("classification, next action, closure history and institution reporting", async ({
  page,
}) => {
  const initial = await createCase();
  await login(page);
  await page.goto(`/cases/${initial.id}`);
  await expect(
    page.locator("dd").filter({ hasText: /^Unclassified$/ }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("classification");
  await page
    .getByLabel("New classification")
    .selectOption("regulatory_compliance");
  await record(page, "Inspection is a regulatory compliance matter");
  await expect(
    page.locator("dd").filter({ hasText: /^Regulatory \/ Compliance$/ }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("next_action");
  await page
    .getByLabel("Next action description")
    .fill("Request laboratory inspection photographs");
  await page.getByLabel("Expected action date (optional)").fill("2026-11-12");
  await record(page, "Schedule evidence collection");
  const updated = await (await backend.get(`/api/cases/${initial.id}`)).json();
  expect(updated.due_at).toBe(initial.due_at);
  expect(updated.next_action_date).toBe("2026-11-12");
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("status");
  await page.getByLabel("New status").selectOption("disposed");
  await page
    .getByLabel("Resolution note")
    .fill("Inspection evidence accepted and case resolved");
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await expect(
    page.locator("dd").filter({ hasText: /^No next action recorded$/ }),
  ).toBeVisible();
  const closed = await (await backend.get(`/api/cases/${initial.id}`)).json();
  expect(closed.next_action).toBe("");
  expect(closed.next_action_date).toBeNull();
  expect(
    closed.actions.find((a: any) => a.kind === "status").changes.next_action
      .before,
  ).toBe("Request laboratory inspection photographs");
  await page.goto(`/institutions/${institution.id}?from=2099-01-01`);
  const counts = page.getByRole("region", {
    name: "All-time case classifications",
  });
  await expect(counts.getByText("Regulatory / Compliance")).toBeVisible();
  await counts.getByRole("link", { name: "1", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Classification", exact: true }),
  ).toHaveValue("regulatory_compliance");
  await expect(
    page.getByRole("link", { name: initial.reference, exact: true }),
  ).toBeVisible();
  await page.goto(
    `/reports?institution=${institution.id}&classification=regulatory_compliance`,
  );
  await expect(
    page.getByRole("heading", { name: "Data report" }),
  ).toBeVisible();
  const filtered = await (
    await backend.get(
      `/api/dashboard?institution=${institution.id}&classification=regulatory_compliance`,
    )
  ).json();
  expect(filtered.total).toBe(1);
  expect(filtered.disposed).toBe(1);
  await page.goto(`/cases/${initial.id}`);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Original complaint" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(392);
  await page.screenshot({
    path: artifact("phase2-case-mobile.png"),
    fullPage: true,
  });
});

test("stale next-action draft receives 409 and is preserved until explicit reload", async ({
  page,
}) => {
  const initial = await createCase();
  await login(page);
  await page.goto(`/cases/${initial.id}`);
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("next_action");
  await page
    .getByLabel("Next action description")
    .fill("Retain my unsaved draft");
  const current = await (await backend.get(`/api/cases/${initial.id}`)).json();
  const changed = await post(backend, `/api/cases/${initial.id}/actions`, {
    kind: "note",
    expected_version: current.version,
    reason: "Concurrent official action",
  });
  expect(changed.status()).toBe(200);
  await page.getByLabel("Reason / note").fill("Stale browser action");
  const response = page.waitForResponse(
    (r) =>
      r.url().endsWith(`/api/cases/${initial.id}/actions`) &&
      r.status() === 409,
  );
  await page
    .getByRole("button", { name: "Record action", exact: true })
    .click();
  await response;
  await expect(page.getByLabel("Next action description")).toHaveValue(
    "Retain my unsaved draft",
  );
  await expect(
    page.getByRole("button", { name: "Record action", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Reload case and discard draft" })
    .click();
  await expect(page.getByLabel("Reason / note")).toHaveValue("");
  await expect(
    page.getByText("Concurrent official action", { exact: true }),
  ).toBeVisible();
});

for (const username of ["officer_rb", "auditor"]) {
  test(`${username} workflow controls and backend restrictions agree`, async ({
    page,
  }) => {
    const initial = await createCase();
    const hidden = await createCase("PGRC");
    await login(page, username);
    await page.goto(`/cases/${initial.id}`);
    if (username === "officer_rb") {
      await expect(
        page
          .getByRole("combobox", { name: "Action", exact: true })
          .locator('option[value="classification"]'),
      ).toHaveCount(0);
      await page
        .getByRole("combobox", { name: "Action", exact: true })
        .selectOption("next_action");
      await page
        .getByLabel("Next action description")
        .fill("Officer requests clarification");
      await record(page, "Bureau follow-up");
      const current = await (
        await page.request.get(`/api/cases/${initial.id}`)
      ).json();
      expect(
        (
          await post(page.request, `/api/cases/${initial.id}/actions`, {
            kind: "classification",
            classification: "grievance",
            expected_version: current.version,
            reason: "Unauthorized correction",
          })
        ).status(),
      ).toBe(403);
      expect((await page.request.get(`/api/cases/${hidden.id}`)).status()).toBe(
        404,
      );
    } else {
      await expect(
        page.getByRole("combobox", { name: "Action", exact: true }),
      ).toHaveCount(0);
      expect(
        (
          await post(page.request, `/api/cases/${initial.id}/actions`, {
            kind: "next_action",
            next_action: "Auditor cannot write",
            expected_version: initial.version,
            reason: "Unauthorized update",
          })
        ).status(),
      ).toBe(403);
    }
  });
}
