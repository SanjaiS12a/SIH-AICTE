import { defineConfig } from "@playwright/test";
import { artifact } from "../tests/browser/support";
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174";
const endpoint = new URL(baseURL);
if (!["127.0.0.1", "localhost"].includes(endpoint.hostname) || ["5173", "8000"].includes(endpoint.port)) {
  throw new Error("Browser verification requires an isolated localhost test stack; working demo ports are forbidden.");
}
process.env.PLAYWRIGHT_BASE_URL = baseURL;
export default defineConfig({
  testDir: "../tests/browser",
  tsconfig: "../tests/tsconfig.json",
  outputDir: artifact("playwright"),
  fullyParallel: false,
  workers: 1,
  expect: { timeout: 15000 },
  use: {
    channel: "msedge",
    baseURL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: artifact("playwright-report") }],
  ],
});
