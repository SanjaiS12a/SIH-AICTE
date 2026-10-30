import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "../tests/browser",
  tsconfig: "../tests/tsconfig.json",
  outputDir: "../tests/results/playwright",
  fullyParallel: false,
  workers: 1,
  expect: { timeout: 15000 },
  use: {
    channel: "msedge",
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [["list"], ["html", { open: "never", outputFolder: "../tests/results/playwright-report" }]],
});
