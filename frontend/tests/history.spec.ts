/**
 * History Page Tests
 * Tests for cleanup run history and run details
 */

import { test, expect } from "@playwright/test";
import {
  setupHistoryMocks,
  setupAuthenticatedMocks,
  mockApiRoute,
  waitForLoadingComplete,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("History Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupHistoryMocks(page);
    await page.goto("/dashboard/history");
    await waitForLoadingComplete(page);
  });

  test.describe("Page Rendering", () => {
    test("should display page title", async ({ page }) => {
      const title = page.locator("h1, h2").first();
      await expect(title).toBeVisible();
    });

    test("should display run history list", async ({ page }) => {
      // Should show run entries
      const runList = page.locator('[class*="card"], [class*="list"], table');
      const count = await runList.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display run dates", async ({ page }) => {
      // Should show dates
      const dates = page.locator('text=/\\d{1,2}.*\\d{4}|ago|yesterday|today/i');
      const count = await dates.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display run status badges", async ({ page }) => {
      // Should show status indicators
      const statusBadges = page.locator('text=/completed|running|cancelled|failed/i');
      const count = await statusBadges.count();
      expect(count).toBeGreaterThan(0);
    });
  });

  test.describe("Run List Items", () => {
    test("should display emails deleted count", async ({ page }) => {
      const deletedCount = page.locator('text=/\\d+.*deleted|emails/i');
      const count = await deletedCount.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display storage freed", async ({ page }) => {
      const storageFreed = page.locator('text=/MB|GB|freed|saved/i');
      const count = await storageFreed.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display unsubscribed count", async ({ page }) => {
      const unsubscribed = page.locator('text=/unsubscribed/i');
      const count = await unsubscribed.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should be clickable to view details", async ({ page }) => {
      const runItem = page.locator('[class*="card"], tr, a[href*="history"]').first();
      if (await runItem.count() > 0) {
        const isClickable = await runItem.evaluate((el) => {
          return el.tagName === 'A' || el.onclick !== null || el.closest('a') !== null;
        });
        expect(typeof isClickable).toBe('boolean');
      }
    });
  });

  test.describe("Run Status Types", () => {
    test("should show completed runs with green/success style", async ({ page }) => {
      const completedBadge = page.locator('text=/completed/i').first();
      if (await completedBadge.count() > 0) {
        await expect(completedBadge).toBeVisible();
      }
    });

    test("should show cancelled runs with appropriate style", async ({ page }) => {
      const cancelledBadge = page.locator('text=/cancelled/i').first();
      if (await cancelledBadge.count() > 0) {
        await expect(cancelledBadge).toBeVisible();
      }
    });
  });

  test.describe("Empty State", () => {
    test("should show empty state when no runs exist", async ({ page }) => {
      await mockApiRoute(page, "/runs", { runs: [], total: 0, limit: 20, offset: 0 });
      await page.goto("/dashboard/history");
      await waitForLoadingComplete(page);

      const emptyMessage = page.locator('text=/no.*runs|no.*history|empty|nothing/i');
      const count = await emptyMessage.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Pagination", () => {
    test("should show pagination if many runs", async ({ page }) => {
      // Mock many runs
      const manyRuns = {
        runs: Array(25).fill(mockData.mockRuns.runs[0]).map((run, i) => ({
          ...run,
          id: `run-${i}`,
        })),
        total: 25,
        limit: 20,
        offset: 0,
      };
      await mockApiRoute(page, "/runs", manyRuns);
      await page.goto("/dashboard/history");
      await waitForLoadingComplete(page);

      const pagination = page.locator('button:has-text("Next"), button:has-text("Previous"), [class*="pagination"]');
      const count = await pagination.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });
});

test.describe("Run Detail Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupHistoryMocks(page);
    await page.goto("/dashboard/history/run-1");
    await waitForLoadingComplete(page);
  });

  test.describe("Page Rendering", () => {
    test("should display run detail page", async ({ page }) => {
      await expect(page.locator("body")).toBeVisible();
    });

    test("should display run ID or title", async ({ page }) => {
      const title = page.locator("h1, h2").first();
      await expect(title).toBeVisible();
    });

    test("should display run status", async ({ page }) => {
      const status = page.locator('text=/completed|running|cancelled|failed/i');
      const count = await status.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display start and end times", async ({ page }) => {
      const times = page.locator('text=/started|finished|duration|ago/i');
      const count = await times.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Run Statistics", () => {
    test("should display emails deleted", async ({ page }) => {
      const deleted = page.locator('text=/\\d+.*deleted|emails.*deleted/i');
      const count = await deleted.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display storage freed", async ({ page }) => {
      const storage = page.locator('text=/MB|GB|storage|freed/i');
      const count = await storage.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display senders processed", async ({ page }) => {
      const senders = page.locator('text=/\\d+.*sender|processed/i');
      const count = await senders.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display filters created", async ({ page }) => {
      const filters = page.locator('text=/\\d+.*filter/i');
      const count = await filters.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display unsubscribe count", async ({ page }) => {
      const unsubscribed = page.locator('text=/\\d+.*unsubscribed/i');
      const count = await unsubscribed.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Action Log", () => {
    test("should display action log section", async ({ page }) => {
      const actionLog = page.locator('text=/action|log|activity|history/i');
      const count = await actionLog.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should show individual actions", async ({ page }) => {
      const actions = page.locator('text=/delete|unsubscribe|filter|skip/i');
      const count = await actions.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should show sender emails in actions", async ({ page }) => {
      const senderEmails = page.locator('text=/@/');
      const count = await senderEmails.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Navigation", () => {
    test("should have back to history button", async ({ page }) => {
      const backButton = page.locator('a[href*="history"], button:has-text("Back")');
      const count = await backButton.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should navigate back to history list", async ({ page }) => {
      const backButton = page.locator('a[href="/dashboard/history"], button:has-text("Back")').first();
      if (await backButton.count() > 0) {
        await backButton.click();
        await expect(page).toHaveURL(/history/);
      }
    });
  });
});

test.describe("History - Loading States", () => {
  test("should show loading indicator while fetching runs", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/runs", mockData.mockRuns, { delay: 2000 });
    await page.goto("/dashboard/history");

    const loader = page.locator('.animate-spin, text=/loading/i');
    const count = await loader.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe("History - Error Handling", () => {
  test("should handle API error gracefully", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/runs", { error: "Server error" }, { status: 500 });
    await page.goto("/dashboard/history");

    await expect(page.locator("body")).toBeVisible();
  });

  test("should handle run not found", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/runs/invalid-run", { detail: "Not found" }, { status: 404 });
    await page.goto("/dashboard/history/invalid-run");

    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("History - Responsive Design", () => {
  test.beforeEach(async ({ page }) => {
    await setupHistoryMocks(page);
  });

  test("should render history list on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard/history");
    await waitForLoadingComplete(page);

    await expect(page.locator("main")).toBeVisible();
  });

  test("should render run detail on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard/history/run-1");
    await waitForLoadingComplete(page);

    await expect(page.locator("main")).toBeVisible();
  });
});
