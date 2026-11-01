import { test, expect } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
import type { Overlap } from "../../frontend/src/api";
import { artifact } from "./support";

let backend: APIRequestContext;
let semantic: Overlap, manual: Overlap;
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
async function current(pair: Overlap) {
  return (await (await backend.get(`/api/overlaps?decision=all&pair=${pair.id}`)).json()).results[0] as Overlap;
}

test.beforeAll(async ({ playwright }) => {
  backend = await playwright.request.newContext({ baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174" });
  await backend.get("/accounts/login/");
  const token = (await backend.storageState()).cookies.find(c => c.name === "csrftoken")!.value;
  expect((await backend.post("/accounts/login/", { form: { username: "coordinator", password: process.env.DEMO_PASSWORD || "Demo-only-26264!", csrfmiddlewaretoken: token } })).ok()).toBeTruthy();
  const institution = await post(backend, "/api/institution-registry", { permanent_id: `B1-${stamp}`, name: `Evidence Test Institute ${stamp}`, region: "Southern", district: "Fictional", reason: "Synthetic B1 browser fixtures" });
  expect(institution.status()).toBe(201);
  const inst = await institution.json();
  async function create(bureau: string, summary: string) {
    const result = await post(backend, "/api/cases", { submission_id: crypto.randomUUID(), institution: inst.id, bureau,
      source_system: `B1-${bureau}`, source_reference: crypto.randomUUID(), category: "refunds", classification: "grievance",
      summary, description: "Fictional B1 evidence review fixture. No real personal data." });
    expect(result.status(), await result.text()).toBe(201);
    return result.json();
  }
  const summary = "The tuition refund remains unpaid after admission cancellation.";
  const a = await create("RB", summary), b = await create("PGRC", summary);
  await expect.poll(async () => {
    const result = await (await backend.get(`/api/overlaps?institution=${inst.id}&decision=pending`)).json();
    semantic = result.results.find((p: Overlap) => [p.left.id, p.right.id].includes(a.id) && [p.left.id, p.right.id].includes(b.id));
    return Boolean(semantic?.evidence.schema_version === 1);
  }, { timeout: 60000 }).toBe(true);
  const c = await create("RB", "The laboratory roof has severe structural cracks and requires a safety inspection."),
    d = await create("PGRC", "A student scholarship application was rejected because its bank details were incorrect.");
  const recorded = await post(backend, "/api/relationships", { left: c.id, right: d.id, decision: "unrelated", reason: "Separate incidents after manual review" });
  expect([200, 201]).toContain(recorded.status());
  manual = await recorded.json();
  expect(manual.origin).toBe("manual");
});
test.afterAll(async () => backend?.dispose());
test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, route => ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
});

test("real semantic evidence displays genuine cosine, revisions, unknown states and immutable two-case review history", async ({ page }) => {
  await login(page);
  await page.goto(`/coordination?decision=all&pair=${semantic.id}`);
  await expect(page.getByText("Evidence schema 1 · Discovery: Same-institution MiniLM top five", { exact: true })).toBeVisible();
  await expect(page.getByText(`Cosine similarity: ${semantic.score!.toFixed(3)}`, { exact: true })).toBeVisible();
  await expect(page.getByText(`Matching-policy revision: institution-exact-top5-v1`, { exact: true })).toBeVisible();
  await expect(page.getByText(`Encoder revision: ${semantic.model_revision}`, { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Metadata comparison", exact: true }).getByRole("row", { name: "Incident date Not recorded Not recorded Unknown", exact: true })).toBeVisible();
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  await page.getByLabel("Related issue", { exact: true }).check();
  await page.getByLabel("Review reason").fill("Independently reviewed captured evidence and distinct remedies");
  await page.getByRole("button", { name: "Record decision", exact: true }).click();
  await expect(page.getByLabel("Review reason")).toHaveValue("Independently reviewed captured evidence and distinct remedies");
  const snapshot = page.getByText("Review-time evidence snapshot", { exact: true });
  await snapshot.click();
  await expect(page.getByText("Review-time matching policy: institution-exact-top5-v1", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: artifact("b1-evidence-desktop.png"), fullPage: true });
  const saved = await current(semantic);
  expect(saved.review_snapshot?.evidence).toEqual(semantic.evidence);
  for (const c of [saved.left, saved.right]) {
    const detail = await (await backend.get(`/api/cases/${c.id}`)).json();
    expect(detail.actions.find((action: any) => action.changes.overlap_id === saved.id).changes.review_snapshot).toEqual(saved.review_snapshot);
  }
  await page.goto(`/cases/${saved.left.id}#case-history`);
  await page.getByText("Review-time evidence snapshot", { exact: true }).click();
  await expect(page.getByRole("region", { name: "Review-time metadata", exact: true })).toBeVisible();
  await expect(page.getByText("review snapshot: None → None", { exact: true })).toHaveCount(0);
});

test("manual evidence remains unscored and auditors inspect snapshots without write controls", async ({ page }) => {
  await login(page, "auditor");
  await page.goto(`/coordination?decision=all&pair=${manual.id}`);
  await expect(page.getByText("Evidence schema 1 · Discovery: Manual selection", { exact: true })).toBeVisible();
  await expect(page.getByText("Not model-scored", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("radio")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Record decision", exact: true })).toHaveCount(0);
  await page.getByText("Review-time evidence snapshot", { exact: true }).click();
  await expect(page.getByText("Review-time cosine: Not model-scored", { exact: true })).toBeVisible();
  expect((await post(page.request, `/api/overlaps/${manual.id}/review`, { decision: "related_issue", reason: "Auditor cannot write", expected_version: manual.version })).status()).toBe(403);
});

test("legacy evidence is labeled without invented provenance or empty-reference proof", async ({ page }) => {
  await login(page);
  const legacy = { ...manual, review_snapshot: null, evidence: { shared_reference: true, scope: "Old unversioned evidence" },
    left: { ...manual.left, source_reference: "", source_system: "" }, right: { ...manual.right, source_reference: "", source_system: "" } };
  await page.route("**/api/overlaps?*", route => route.fulfill({ json: { count: 1, next: null, previous: null, results: [legacy] } }));
  await page.goto(`/coordination?decision=all&pair=${manual.id}`);
  await expect(page.getByText(/Legacy evidence \(unversioned\)/)).toBeVisible();
  await expect(page.getByText("Legacy review: no decision-time evidence snapshot recorded.", { exact: true })).toBeVisible();
  await expect(page.getByText("Shared explicit source reference", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Metadata comparison", exact: true }).getByRole("row", { name: "Source reference Not recorded on one or both cases", exact: true })).toBeVisible();
  await expect(page.getByLabel("Unrelated", { exact: true })).toBeChecked();
});

test("409 retains the versioned-evidence draft and recorded snapshot until explicit reload", async ({ page }) => {
  const original = await current(manual);
  await login(page);
  await page.goto(`/coordination?decision=all&pair=${manual.id}`);
  await page.getByLabel("Related issue", { exact: true }).check();
  await page.getByLabel("Review reason").fill("Unsaved B1 evidence draft");
  expect((await post(backend, `/api/overlaps/${manual.id}/review`, { decision: "same_incident", reason: "Concurrent human evidence review", expected_version: original.version })).status()).toBe(200);
  const conflict = page.waitForResponse(r => r.url().endsWith(`/api/overlaps/${manual.id}/review`) && r.status() === 409);
  await page.getByRole("button", { name: "Record decision", exact: true }).click(); await conflict;
  await expect(page.getByLabel("Review reason")).toHaveValue("Unsaved B1 evidence draft");
  await expect(page.getByLabel("Related issue", { exact: true })).toBeChecked();
  await expect(page.getByRole("button", { name: "Record decision", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Reload relationship and discard draft" }).click();
  await expect(page.getByLabel("Review reason")).toHaveValue("Concurrent human evidence review");
});

test("390px evidence table and keyboard snapshot stay contained; officers cannot retrieve snapshots", async ({ page }) => {
  await login(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/coordination?decision=all&pair=${manual.id}`);
  const metadata = page.getByRole("region", { name: "Metadata comparison", exact: true });
  await metadata.focus(); await expect(metadata).toBeFocused();
  const snapshot = page.getByText("Review-time evidence snapshot", { exact: true });
  await snapshot.focus(); await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: "Review-time metadata", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: artifact("b1-evidence-mobile.png"), fullPage: true });
  await page.context().clearCookies();
  await login(page, "officer_rb");
  await page.goto(`/coordination?pair=${manual.id}`);
  await expect(page.getByRole("alert")).toContainText("Coordination access is required");
  await expect(page.getByText("Review-time evidence snapshot", { exact: true })).toHaveCount(0);
  expect((await page.request.get(`/api/overlaps?pair=${manual.id}`)).status()).toBe(403);
  const own = [manual.left, manual.right].find(c => c.bureau === "RB")!;
  expect(JSON.stringify(await (await page.request.get(`/api/cases/${own.id}`)).json())).not.toContain("review_snapshot");
});
