import { defineConfig } from "@playwright/test";
import { artifact } from "../tests/browser/support";
export default defineConfig({
  testDir: "../tests/browser",
  tsconfig: "../tests/tsconfig.json",
  outputDir: artifact("playwright"),
  fullyParallel: false,
  workers: 1,
  expect: { timeout: 15000 },
  use: {
    channel: "msedge",
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: artifact("playwright-report") }],
  ],
});
