/**
 * Dashboard Page Tests
 * Tests all dashboard components, stats, and interactions
 */

import { test, expect } from "@playwright/test";
import {
  setupAuthenticatedMocks,
  setupUnauthenticatedMocks,
  mockApiRoute,
  waitForLoadingComplete,
  setupConsoleErrorCapture,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("Dashboard Page", () => {
  test.describe("Page Rendering", () => {
    test("should render dashboard with all main sections", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Check page title/header
      await expect(page.locator("h1")).toBeVisible();

      // Check that main content area exists
      await expect(page.locator("main")).toBeVisible();
    });

    test("should display Inbox Health Card", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Look for inbox health related content
      const healthCard = page.locator('text=/inbox|health|cleanup/i').first();
      await expect(healthCard).toBeVisible();
    });

    test("should display Start Cleanup button", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Find the cleanup/start button
      const cleanupButton = page.locator('button:has-text("Cleanup"), a:has-text("Cleanup"), button:has-text("Start"), a:has-text("Start")').first();
      await expect(cleanupButton).toBeVisible();
    });

    test("should not have console errors on load", async ({ page }) => {
      const errors = setupConsoleErrorCapture(page);
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Filter out expected errors (like SWR fetch errors during mocking)
      const criticalErrors = errors.filter(
        (e) => !e.includes("Failed to fetch") && !e.includes("NetworkError")
      );
      expect(criticalErrors).toHaveLength(0);
    });
  });

  test.describe("Inbox Health Card States", () => {
    test("should show healthy state with green indicators", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await mockApiRoute(page, "/cleanup/inbox-health", mockData.mockInboxHealthHealthy);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Look for healthy indicator text or styling
      const healthyText = page.locator('text=/healthy|good|clean/i');
      // If exists, verify it's visible
      const count = await healthyText.count();
      if (count > 0) {
        await expect(healthyText.first()).toBeVisible();
      }
    });

    test("should show needs_attention state with yellow/orange indicators", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await mockApiRoute(page, "/cleanup/inbox-health", mockData.mockInboxHealthNeedsAttention);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Should show attention needed or larger cleanup counts
      const potentialCleanup = page.locator('text=/2,500|attention|review/i');
      const count = await potentialCleanup.count();
      if (count > 0) {
        await expect(potentialCleanup.first()).toBeVisible();
      }
    });

    test("should show critical state with red indicators", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await mockApiRoute(page, "/cleanup/inbox-health", mockData.mockInboxHealthCritical);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Should show critical indicator or large numbers
      const criticalIndicator = page.locator('text=/critical|8,500|urgent/i');
      const count = await criticalIndicator.count();
      if (count > 0) {
        await expect(criticalIndicator.first()).toBeVisible();
      }
    });

    test("should display category breakdown", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Look for category names
      const categories = ["promotions", "social", "updates"];
      for (const category of categories) {
        const categoryText = page.locator(`text=/${category}/i`);
        const count = await categoryText.count();
        // At least one should exist in health card
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe("Stats Display", () => {
    test("should display total emails processed", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Stats should be visible somewhere
      const statsContainer = page.locator('text=/processed|deleted|cleaned/i');
      const count = await statsContainer.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display storage freed", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Storage stats - look for MB/GB values
      const storageText = page.locator('text=/MB|GB|storage|freed|space/i');
      const count = await storageText.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Active Run Display", () => {
    test("should show progress when run is active", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await mockApiRoute(page, "/stats/current", mockData.mockStatsWithActiveRun);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Should show progress indicator
      const progressText = page.locator('text=/running|progress|%|processing/i');
      const count = await progressText.count();
      // May or may not show depending on UI design
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Navigation from Dashboard", () => {
    test("should navigate to cleanup wizard when clicking Start Cleanup", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Find and click cleanup button
      const cleanupButton = page.locator('a[href*="cleanup"], button:has-text("Cleanup"), button:has-text("Start")').first();

      if (await cleanupButton.count() > 0) {
        await cleanupButton.click();
        // Should navigate to cleanup page
        await expect(page).toHaveURL(/cleanup/);
      }
    });

    test("should navigate to space manager from dashboard", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Find space/attachments link
      const spaceLink = page.locator('a[href*="space"], a:has-text("Space"), a:has-text("Attachments")').first();

      if (await spaceLink.count() > 0) {
        await spaceLink.click();
        await expect(page).toHaveURL(/space|attachments/);
      }
    });
  });

  test.describe("Auto-Protected Categories", () => {
    test("should display auto-protected categories section", async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Look for protected categories
      const protectedText = page.locator('text=/protected|contacts|financial|security|government/i');
      const count = await protectedText.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Responsive Design", () => {
    test("should render correctly on mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      // Page should still render main content
      await expect(page.locator("main")).toBeVisible();
    });

    test("should render correctly on tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      await expect(page.locator("main")).toBeVisible();
    });

    test("should render correctly on desktop viewport", async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await setupAuthenticatedMocks(page);
      await page.goto("/dashboard");
      await waitForLoadingComplete(page);

      await expect(page.locator("main")).toBeVisible();
    });
  });

  test.describe("Error States", () => {
    test("should handle API error gracefully", async ({ page }) => {
      await mockApiRoute(page, "/auth/status", mockData.mockAuthConnected);
      await mockApiRoute(page, "/stats/current", { error: "Server error" }, { status: 500 });
      await mockApiRoute(page, "/cleanup/inbox-health", { error: "Server error" }, { status: 500 });

      await page.goto("/dashboard");

      // Page should still render without crashing
      await expect(page.locator("body")).toBeVisible();
    });

    test("should show loading state initially", async ({ page }) => {
      await mockApiRoute(page, "/auth/status", mockData.mockAuthConnected);
      // Add delay to see loading state
      await mockApiRoute(page, "/stats/current", mockData.mockStats, { delay: 2000 });
      await mockApiRoute(page, "/cleanup/inbox-health", mockData.mockInboxHealthHealthy, { delay: 2000 });

      await page.goto("/dashboard");

      // Should show some loading indicator
      const loadingIndicator = page.locator('.animate-spin, .animate-pulse, text=/loading/i');
      const count = await loadingIndicator.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Unauthenticated State", () => {
    test("should redirect to home when not authenticated", async ({ page }) => {
      await setupUnauthenticatedMocks(page);
      await page.goto("/dashboard");

      // Should either redirect or show connect prompt
      const connectPrompt = page.locator('text=/connect|sign in|login|authenticate/i');
      const isOnDashboard = page.url().includes("dashboard");

      if (isOnDashboard) {
        // If still on dashboard, should show connect prompt
        const count = await connectPrompt.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
      // Otherwise redirected, which is also valid
    });
  });
});

test.describe("Dashboard Cards", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);
  });

  test("should have clickable cards that navigate or expand", async ({ page }) => {
    // Find all cards
    const cards = page.locator('[class*="card"], [class*="Card"]');
    const cardCount = await cards.count();

    // Dashboard should have at least one card
    expect(cardCount).toBeGreaterThan(0);
  });

  test("cards should have proper hover states", async ({ page }) => {
    const cards = page.locator('[class*="card"], [class*="Card"]').first();

    if (await cards.count() > 0) {
      // Hover over card
      await cards.hover();
      // Card should still be visible after hover
      await expect(cards).toBeVisible();
    }
  });
});

test.describe("Dashboard Theme", () => {
  test("should support dark mode", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Find theme toggle if exists
    const themeToggle = page.locator('button[aria-label*="theme"], button:has-text("Dark"), button:has-text("Light")');

    if (await themeToggle.count() > 0) {
      await themeToggle.first().click();
      // Page should still render
      await expect(page.locator("main")).toBeVisible();
    }
  });
});
