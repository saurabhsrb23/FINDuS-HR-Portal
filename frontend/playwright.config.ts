import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for FindUs end-to-end tests.
 *
 * Run:  npm run test:e2e
 * Debug: PWDEBUG=1 npm run test:e2e
 *
 * Requires the full stack (frontend + backend + DB) to be running.
 * The BASE_URL defaults to the Docker-compose frontend port.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 8_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1, // sequential — avoids DB race conditions
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
