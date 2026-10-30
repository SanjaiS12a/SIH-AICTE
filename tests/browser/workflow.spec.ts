import { test, expect } from "@playwright/test";

test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\//, async (route) => {
    const hostname = new URL(route.request().url()).hostname;
    if (!["127.0.0.1", "localhost"].includes(hostname)) {
      await route.abort();
      throw new Error(
        `The local demo attempted an external request: ${hostname}`,
      );
    }
    await route.continue();
  });
});

async function login(page: any, username = "coordinator") {
  await page.goto("/");
  await page.getByRole("link", { name: /Sign in to workspace/ }).click();
  await page.getByLabel("Username:").fill(username);
  await page
    .getByLabel("Password:")
    .fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Complaint Monitoring Dashboard",
    }),
  ).toBeVisible();
}
test("register, annotate, transfer and verify the audit history", async ({
  page,
}) => {
  await login(page);
  await page.getByRole("link", { name: "Register case", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Institution", exact: true })
    .selectOption({ label: "Aster Institute of Technology · DEMO-0001" });
  await page.getByLabel("Receiving bureau").selectOption("RB");
  await page
    .getByRole("combobox", { name: "Category", exact: true })
    .selectOption("refunds");
  await page.getByLabel("Source reference").fill(`E2E-${Date.now()}`);
  await page
    .getByLabel("Short allegation summary")
    .fill(
      "The institution has not refunded tuition after admission cancellation in 2026.",
    );
  await page
    .getByLabel("Full complaint")
    .fill(
      "Synthetic browser test complaint. Please review the fee refund request.",
    );
  await page
    .getByRole("button", { name: "Register case", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Original complaint" }),
  ).toBeVisible();
  await expect(page.getByText("Scan complete", { exact: true })).toBeVisible({
    timeout: 20000,
  });
  await page
    .getByLabel("Reason / note")
    .fill("Supporting receipts requested from the institution.");
  await page.getByRole("button", { name: "Record action" }).click();
  await expect(
    page.getByText("Supporting receipts requested from the institution.", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Action", exact: true })
    .selectOption("transfer");
  await page.getByLabel("Receiving bureau").selectOption("PGRC");
  await page
    .getByLabel("Reason / note")
    .fill("Transferred for grievance coordination.");
  await page.getByRole("button", { name: "Record action" }).click();
  await expect(page.getByText("RB → PGRC", { exact: false })).toBeVisible();
  await page.screenshot({ path: "../tests/results/case-detail.png", fullPage: true });
});
test("dashboard, drill-down and coordination review", async ({ page }) => {
  await login(page);
  await expect(
    page.getByRole("button", { name: /Open complaints/ }),
  ).toBeVisible();
  await page.screenshot({ path: "../tests/results/dashboard.png", fullPage: true });
  await page.getByRole("button", { name: /Overdue complaints/ }).click();
  await expect(page).toHaveURL(/overdue=true/);
  await expect(
    page.getByRole("checkbox", { name: "Overdue only" }),
  ).toBeChecked();
  await page
    .getByRole("link", { name: "Coordination queue", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review potential relationship" }),
  ).toBeVisible();
  await page.getByLabel("Related issue", { exact: true }).check();
  await page
    .getByLabel("Review reason")
    .fill(
      "Related institution concerns; separate remedies. Synthetic evaluation decision.",
    );
  await page.getByRole("button", { name: "Record decision" }).click();
  await expect(
    page.getByRole("heading", { name: "Review potential relationship" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../tests/results/coordination.png",
    fullPage: true,
  });
});
test("bureau officers do not see coordination navigation", async ({ page }) => {
  await login(page, "officer_rb");
  await expect(
    page.getByRole("link", { name: "Coordination queue", exact: true }),
  ).toHaveCount(0);
  const result = await page.request.get("/api/overlaps");
  expect(result.status()).toBe(403);
});

test("mobile registry keeps table scrolling inside the viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("link", { name: "Case registry", exact: true }).click();
  const table = page.getByRole("region", {
    name: "Complaint list",
    exact: true,
  });
  await expect(table).toBeVisible();
  const sizes = await page.evaluate(() => ({
    viewport: innerWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(sizes.document).toBeLessThanOrEqual(sizes.viewport);
  await expect(
    page.getByRole("button", { name: "Sign out", exact: true }),
  ).toBeVisible();
  await table.focus();
  await expect(table).toBeFocused();
  await page.screenshot({ path: "../tests/results/mobile.png", fullPage: true });
});
