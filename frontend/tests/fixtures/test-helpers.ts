/**
 * Test helpers for Playwright tests
 * Provides common utilities for mocking API responses and test setup
 */

import { Page, Route } from "@playwright/test";
import * as mockData from "./mock-data";

const API_BASE = "http://localhost:8000/api";

type MockResponse = Record<string, unknown> | unknown[];

/**
 * Setup all API mocks with default responses
 */
export async function setupAllMocks(page: Page) {
  // Auth
  await mockApiRoute(page, "/auth/status", mockData.mockAuthConnected);

  // Stats
  await mockApiRoute(page, "/stats/current", mockData.mockStats);

  // V2 Cleanup
  await mockApiRoute(page, "/cleanup/inbox-health", mockData.mockInboxHealthHealthy);
  await mockApiRoute(page, "/cleanup/auto-protected", mockData.mockAutoProtected);

  // Senders
  await mockApiRoute(page, "/senders", mockData.mockSenders);
  await mockApiRoute(page, "/senders/", mockData.mockSenders);

  // Runs
  await mockApiRoute(page, "/runs", mockData.mockRuns);
  await mockApiRoute(page, "/runs/", mockData.mockRuns);

  // Whitelist
  await mockApiRoute(page, "/whitelist", mockData.mockWhitelist);
  await mockApiRoute(page, "/whitelist/", mockData.mockWhitelist);

  // Attachments
  await mockApiRoute(page, "/attachments/large", mockData.mockLargeAttachments);

  // Subscriptions
  await mockApiRoute(page, "/subscriptions", mockData.mockSubscriptions);
  await mockApiRoute(page, "/subscriptions/", mockData.mockSubscriptions);

  // Retention Rules
  await mockApiRoute(page, "/retention/rules", mockData.mockRetentionRules);

  // Scoring
  await mockApiRoute(page, "/scoring/progress", mockData.mockScoringProgress);
  await mockApiRoute(page, "/scoring/stats", mockData.mockScoringStats);
  await mockApiRoute(page, "/scoring/emails", mockData.mockScoredEmails);

  // Classifications
  await mockApiRoute(page, "/classification/summary", mockData.mockClassificationSummary);
  await mockApiRoute(page, "/classification/emails", mockData.mockClassifications);
}

/**
 * Mock a single API route
 */
export async function mockApiRoute(
  page: Page,
  endpoint: string,
  response: MockResponse,
  options: { status?: number; delay?: number; method?: string } = {}
) {
  const { status = 200, delay = 0, method } = options;
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;

  await page.route(url + "*", async (route: Route) => {
    // Check method if specified
    if (method && route.request().method() !== method) {
      return route.continue();
    }

    if (delay > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API to return an error
 */
export async function mockApiError(
  page: Page,
  endpoint: string,
  errorMessage: string,
  status = 500
) {
  await mockApiRoute(page, endpoint, { detail: errorMessage }, { status });
}

/**
 * Setup mocks for authenticated user
 */
export async function setupAuthenticatedMocks(page: Page) {
  await setupAllMocks(page);
}

/**
 * Setup mocks for unauthenticated user
 */
export async function setupUnauthenticatedMocks(page: Page) {
  await mockApiRoute(page, "/auth/status", mockData.mockAuthDisconnected);
  await mockApiRoute(page, "/stats/current", { error: "Not authenticated" }, { status: 401 });
}

/**
 * Setup mocks for V2 cleanup wizard flow
 */
export async function setupCleanupWizardMocks(page: Page) {
  await setupAllMocks(page);

  // Start cleanup
  await page.route(`${API_BASE}/cleanup/start`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockData.mockCleanupSession),
      });
    } else {
      await route.continue();
    }
  });

  // Progress endpoint - returns scanning then complete
  let progressCallCount = 0;
  await page.route(`${API_BASE}/cleanup/progress/*`, async (route) => {
    progressCallCount++;
    const response =
      progressCallCount < 3
        ? mockData.mockCleanupProgressScanning
        : mockData.mockCleanupProgressComplete;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });

  // Recommendations
  await page.route(`${API_BASE}/cleanup/recommendations/*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockRecommendationSummary),
    });
  });

  // Mode selection
  await page.route(`${API_BASE}/cleanup/mode/*`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok" }),
      });
    } else {
      await route.continue();
    }
  });

  // Review queue
  await page.route(`${API_BASE}/cleanup/review-queue/*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockReviewQueue),
    });
  });

  // Review decision
  await page.route(`${API_BASE}/cleanup/review-decision/*`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message_id: "msg-1",
          decision: "delete",
          remaining_in_queue: 49,
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Skip all
  await page.route(`${API_BASE}/cleanup/skip-all/*`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok" }),
      });
    } else {
      await route.continue();
    }
  });

  // Confirmation
  await page.route(`${API_BASE}/cleanup/confirmation/*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockConfirmationSummary),
    });
  });

  // Execute cleanup
  await page.route(`${API_BASE}/cleanup/execute/*`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session_id: "session-abc-123",
          status: "executing",
          job_id: "session-abc-123",
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Results
  await page.route(`${API_BASE}/cleanup/results/*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockCleanupResults),
    });
  });
}

/**
 * Setup mocks for run history page
 */
export async function setupHistoryMocks(page: Page) {
  await setupAllMocks(page);

  // Run detail
  await page.route(`${API_BASE}/runs/run-*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockRunDetail),
    });
  });

  // Run actions
  await page.route(`${API_BASE}/runs/*/actions*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockData.mockRunActions),
    });
  });
}

/**
 * Setup mocks for space manager page
 */
export async function setupSpaceManagerMocks(page: Page) {
  await setupAllMocks(page);

  // Cleanup attachments POST
  await page.route(`${API_BASE}/attachments/cleanup`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          deleted_count: 2,
          bytes_freed: 24117248,
        }),
      });
    } else {
      await route.continue();
    }
  });
}

/**
 * Wait for navigation to complete
 */
export async function waitForNavigation(page: Page, url: string) {
  await page.waitForURL(url, { timeout: 10000 });
}

/**
 * Click and wait for navigation
 */
export async function clickAndNavigate(page: Page, selector: string, expectedUrl: string) {
  await Promise.all([page.waitForURL(expectedUrl), page.click(selector)]);
}

/**
 * Check if element is visible
 */
export async function isVisible(page: Page, selector: string): Promise<boolean> {
  const element = page.locator(selector);
  return await element.isVisible();
}

/**
 * Wait for element and get its text
 */
export async function getElementText(page: Page, selector: string): Promise<string> {
  const element = page.locator(selector);
  await element.waitFor({ state: "visible" });
  return (await element.textContent()) || "";
}

/**
 * Fill form field
 */
export async function fillField(page: Page, selector: string, value: string) {
  const element = page.locator(selector);
  await element.waitFor({ state: "visible" });
  await element.fill(value);
}

/**
 * Select dropdown option
 */
export async function selectOption(page: Page, selector: string, value: string) {
  const element = page.locator(selector);
  await element.waitFor({ state: "visible" });
  await element.selectOption(value);
}

/**
 * Check checkbox
 */
export async function checkCheckbox(page: Page, selector: string, checked = true) {
  const element = page.locator(selector);
  await element.waitFor({ state: "visible" });
  if (checked) {
    await element.check();
  } else {
    await element.uncheck();
  }
}

/**
 * Count elements matching selector
 */
export async function countElements(page: Page, selector: string): Promise<number> {
  return await page.locator(selector).count();
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  await page.screenshot({ path: `tests/screenshots/${name}-${timestamp}.png` });
}

/**
 * Wait for loading to complete (no spinners visible)
 */
export async function waitForLoadingComplete(page: Page) {
  // Wait for any loading spinners to disappear
  await page.waitForSelector(".animate-spin", { state: "hidden", timeout: 10000 }).catch(() => {});
  // Wait for skeleton loaders to disappear
  await page.waitForSelector(".animate-pulse", { state: "hidden", timeout: 10000 }).catch(() => {});
}

/**
 * Get all navigation links
 */
export async function getNavLinks(page: Page): Promise<string[]> {
  const links = page.locator('nav a, aside a, [role="navigation"] a');
  const count = await links.count();
  const hrefs: string[] = [];
  for (let i = 0; i < count; i++) {
    const href = await links.nth(i).getAttribute("href");
    if (href) hrefs.push(href);
  }
  return hrefs;
}

/**
 * Verify page has no console errors
 */
export function setupConsoleErrorCapture(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });
  return errors;
}

/**
 * Mock POST request and return response
 */
export async function mockPostRequest(
  page: Page,
  endpoint: string,
  response: MockResponse,
  options: { status?: number; delay?: number } = {}
) {
  await mockApiRoute(page, endpoint, response, { ...options, method: "POST" });
}

/**
 * Mock DELETE request
 */
export async function mockDeleteRequest(
  page: Page,
  endpoint: string,
  response: MockResponse = { status: "ok" },
  options: { status?: number } = {}
) {
  await mockApiRoute(page, endpoint, response, { ...options, method: "DELETE" });
}
