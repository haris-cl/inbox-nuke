import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for InboxNuke comprehensive E2E tests.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./tests",

  /* Test execution settings */
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,

  /* Timeout settings */
  timeout: 30000,
  expect: {
    timeout: 10000,
  },

  /* Reporter configuration */
  reporter: [
    ["list"],
    ["html", { open: "never" }],
    ...(process.env.CI ? [["github" as const]] : []),
  ],

  /* Shared settings for all projects */
  use: {
    baseURL: "http://localhost:3000",

    /* Collect trace on first retry */
    trace: "on-first-retry",

    /* Screenshot on failure */
    screenshot: "only-on-failure",

    /* Video recording */
    video: "on-first-retry",

    /* Action timeout */
    actionTimeout: 10000,

    /* Navigation timeout */
    navigationTimeout: 15000,
  },

  /* Test projects - different browsers and viewports */
  projects: [
    /* Desktop browsers */
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },

    /* Mobile viewports */
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "mobile-safari",
      use: { ...devices["iPhone 12"] },
    },

    /* Tablet viewport */
    {
      name: "tablet",
      use: { ...devices["iPad (gen 7)"] },
    },
  ],

  /* Run local dev server before starting tests */
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  /* Output folder for test artifacts */
  outputDir: "test-results/",
});
