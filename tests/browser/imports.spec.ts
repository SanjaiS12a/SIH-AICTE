import { test, expect } from "@playwright/test";
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
async function login(page: any) {
  await page.goto("/");
  await page.getByRole("link", { name: /Sign in to workspace/ }).click();
  await page.getByLabel("Username:").fill("coordinator");
  await page
    .getByLabel("Password:")
    .fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Complaint Monitoring Dashboard" }),
  ).toBeVisible({ timeout: 30000 });
}
test("spreadsheet preview, rejected row, import, report and asynchronous export", async ({
  page,
}) => {
  test.setTimeout(180000);
  await login(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(
    page.getByRole("button", { name: /Open complaints/ }),
  ).toBeVisible({
    timeout: 30000,
  });
  await page.screenshot({
    path: "../tests/results/dashboard-upgraded.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Import data", exact: true }).click();
  const id = Date.now();
  const csv =
    "source_reference,institution_permanent_id,bureau,category,summary,description,received_at,status\n" +
    `BROWSER-${id},DEMO-0001,RB,refunds,The tuition refund was withheld.,Synthetic import browser test.,2026-08-01T10:00:00+05:30,registered\n` +
    `BROWSER-BAD-${id},UNKNOWN,RB,refunds,Fee complaint.,Invalid institution.,2026-08-01T10:00:00+05:30,registered`;
  await page.getByLabel("Spreadsheet", { exact: true }).setInputFiles({
    name: "browser-complaints.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(csv),
  });
  await page.getByRole("button", { name: "Upload and preview" }).click();
  await expect(
    page.getByRole("heading", { name: "Map and validate columns" }),
  ).toBeVisible();
  await expect(
    page.getByText(/Unknown institution permanent ID/),
  ).toBeVisible();
  await page.screenshot({
    path: "../tests/results/import-preview.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Confirm import", exact: true })
    .click();
  await expect(page.getByText(/1 \/ 2 rows processed/)).not.toBeVisible({
    timeout: 120000,
  });
  await page.getByRole("link", { name: "Open report", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Data report" }),
  ).toBeVisible();
  await expect(page.getByText(/1 imported/)).toBeVisible({ timeout: 120000 });
  await expect(
    page.getByRole("heading", { name: "Complaint categories" }),
  ).toBeVisible({ timeout: 30000 });
  await page.screenshot({
    path: "../tests/results/import-report.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Download CSV", exact: true }),
  ).toBeVisible({ timeout: 120000 });
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download CSV", exact: true }).click();
  expect((await download).suggestedFilename()).toBe("case-report.csv");
});
test("summary snapshots stay separate and use one date at a time", async ({
  page,
}) => {
  test.setTimeout(90000);
  await login(page);
  await page.goto("/imports");
  await page.getByLabel("Dataset type").selectOption("snapshot");
  const csv =
    "snapshot_date,institution_permanent_id,bureau,category,registered,under_review,awaiting_response,disposed,overdue\n2026-03-01,DEMO-0029,RB,documents,31,2,3,5,1\n2026-04-01,DEMO-0029,RB,documents,42,2,3,5,1";
  await page.getByLabel("Spreadsheet", { exact: true }).setInputFiles({
    name: "snapshots.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(csv),
  });
  await page.getByRole("button", { name: "Upload and preview" }).click();
  const confirm = page.getByRole("button", {
    name: "Confirm import",
    exact: true,
  });
  if (await confirm.isEnabled()) await confirm.click();
  await page.getByRole("link", { name: "Open report", exact: true }).click();
  await expect(
    page.getByText("Summary statistics — separate from individual cases", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("combobox", { name: "Snapshot date (one date at a time)" }),
  ).toHaveValue("2026-04-01", { timeout: 30000 });
  await page
    .getByRole("combobox", { name: "Snapshot date (one date at a time)" })
    .selectOption("2026-03-01");
  await expect(
    page.locator(".import-stats").getByText("31", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../tests/results/summary-report.png",
    fullPage: true,
  });
});
