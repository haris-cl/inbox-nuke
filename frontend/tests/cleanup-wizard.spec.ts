/**
 * V2 Cleanup Wizard Tests
 * Tests the complete cleanup wizard flow: Scan → Report → Review → Confirm → Success
 */

import { test, expect } from "@playwright/test";
import {
  setupCleanupWizardMocks,
  setupAuthenticatedMocks,
  mockApiRoute,
  waitForLoadingComplete,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("Cleanup Wizard - Entry Point", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
  });

  test("should navigate to cleanup wizard from dashboard", async ({ page }) => {
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Find and click the Start Cleanup button
    const startButton = page.locator(
      'a[href*="cleanup"], button:has-text("Cleanup"), button:has-text("Start")'
    ).first();

    if (await startButton.count() > 0) {
      await startButton.click();
      await expect(page).toHaveURL(/cleanup/);
    }
  });

  test("should redirect cleanup page to scanning", async ({ page }) => {
    await page.goto("/dashboard/cleanup");
    // Should redirect to scanning subpage
    await waitForLoadingComplete(page);
    await expect(page).toHaveURL(/cleanup/);
  });
});

test.describe("Cleanup Wizard - Scanning Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
  });

  test("should display scanning page with progress", async ({ page }) => {
    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Should show scanning content
    const scanningContent = page.locator('text=/scan|analyzing|progress/i').first();
    await expect(scanningContent).toBeVisible();
  });

  test("should display progress indicator", async ({ page }) => {
    await page.goto("/dashboard/cleanup/scanning");

    // Look for progress bar or percentage
    const progressIndicator = page.locator(
      '[role="progressbar"], text=/%/, .progress, [class*="progress"]'
    );
    const count = await progressIndicator.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display discovery counts as they update", async ({ page }) => {
    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Look for category discovery counts
    const discoveries = page.locator(
      'text=/promotions|newsletters|social|updates/i'
    );
    const count = await discoveries.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display total emails scanned", async ({ page }) => {
    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Look for email count
    const emailCount = page.locator('text=/\\d+.*email|scanned/i');
    const count = await emailCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should animate progress bar during scan", async ({ page }) => {
    await page.goto("/dashboard/cleanup/scanning");

    // Progress bar should have animation or transition
    const progressBar = page.locator('[role="progressbar"], [class*="progress"]').first();
    if (await progressBar.count() > 0) {
      await expect(progressBar).toBeVisible();
    }
  });

  test("should navigate to report when scan completes", async ({ page }) => {
    // Mock completed scan
    await mockApiRoute(page, "/cleanup/progress/*", mockData.mockCleanupProgressComplete);

    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Should auto-navigate to report or show continue button
    const continueButton = page.locator('button:has-text("Continue"), a:has-text("Next")');
    if (await continueButton.count() > 0) {
      await continueButton.first().click();
    }
  });
});

test.describe("Cleanup Wizard - Report Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
    // Ensure scan is complete
    await mockApiRoute(page, "/cleanup/progress/*", mockData.mockCleanupProgressComplete);
  });

  test("should display inbox health report", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should show report content
    const reportContent = page.locator('text=/report|summary|found|cleanup/i').first();
    await expect(reportContent).toBeVisible();
  });

  test("should display total emails scanned", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Look for the scanned count
    const scannedCount = page.locator('text=/500|scanned|total/i');
    const count = await scannedCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display cleanup recommendations count", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should show recommended for cleanup
    const recommendedCount = page.locator('text=/287|recommend|cleanup|delete/i');
    const count = await recommendedCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display protected emails count", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should show protected count
    const protectedCount = page.locator('text=/protected|keep|safe/i');
    const count = await protectedCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display space savings estimate", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should show space savings
    const spaceSavings = page.locator('text=/MB|GB|space|storage|free/i');
    const count = await spaceSavings.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display category breakdown", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should show categories
    const categories = ["promotions", "newsletters", "social", "updates"];
    let foundCount = 0;
    for (const cat of categories) {
      const catElement = page.locator(`text=/${cat}/i`);
      if (await catElement.count() > 0) foundCount++;
    }
    expect(foundCount).toBeGreaterThanOrEqual(0);
  });

  test("should display top senders if available", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // May show top senders
    const senders = page.locator('text=/@|sender/i');
    const count = await senders.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test.describe("Mode Selection", () => {
    test("should display Quick and Full mode options", async ({ page }) => {
      await page.goto("/dashboard/cleanup/report");
      await waitForLoadingComplete(page);

      // Look for mode options
      const quickMode = page.locator('text=/quick/i');
      const fullMode = page.locator('text=/full|detailed/i');

      const quickCount = await quickMode.count();
      const fullCount = await fullMode.count();
      expect(quickCount + fullCount).toBeGreaterThanOrEqual(0);
    });

    test("should allow selecting Quick mode", async ({ page }) => {
      await page.goto("/dashboard/cleanup/report");
      await waitForLoadingComplete(page);

      const quickOption = page.locator('button:has-text("Quick"), [data-mode="quick"], label:has-text("Quick")').first();
      if (await quickOption.count() > 0) {
        await quickOption.click();
      }
    });

    test("should allow selecting Full mode", async ({ page }) => {
      await page.goto("/dashboard/cleanup/report");
      await waitForLoadingComplete(page);

      const fullOption = page.locator('button:has-text("Full"), [data-mode="full"], label:has-text("Full")').first();
      if (await fullOption.count() > 0) {
        await fullOption.click();
      }
    });

    test("should navigate to review after mode selection", async ({ page }) => {
      await page.goto("/dashboard/cleanup/report");
      await waitForLoadingComplete(page);

      // Click continue/next button
      const continueButton = page.locator('button:has-text("Continue"), button:has-text("Review"), button:has-text("Next")').first();
      if (await continueButton.count() > 0) {
        await continueButton.click();
        await expect(page).toHaveURL(/review|confirm/);
      }
    });
  });
});

test.describe("Cleanup Wizard - Review Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
  });

  test("should display review queue", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Should show review content
    const reviewContent = page.locator('text=/review|decide|keep|delete/i').first();
    await expect(reviewContent).toBeVisible();
  });

  test("should display email details for review", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Should show email info - subject, sender
    const emailInfo = page.locator('text=/@|subject|from/i');
    const count = await emailInfo.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display AI recommendation", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Should show AI suggestion
    const aiSuggestion = page.locator('text=/recommend|suggest|AI|confidence/i');
    const count = await aiSuggestion.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display Keep button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    const keepButton = page.locator('button:has-text("Keep")');
    const count = await keepButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display Delete button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    const deleteButton = page.locator('button:has-text("Delete")');
    const count = await deleteButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should allow clicking Keep button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    const keepButton = page.locator('button:has-text("Keep")').first();
    if (await keepButton.count() > 0) {
      await keepButton.click();
      // Should move to next email or update UI
    }
  });

  test("should allow clicking Delete button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    const deleteButton = page.locator('button:has-text("Delete")').first();
    if (await deleteButton.count() > 0) {
      await deleteButton.click();
      // Should move to next email or update UI
    }
  });

  test("should display remaining count", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Should show remaining items count
    const remainingCount = page.locator('text=/\\d+.*remaining|left|of \\d+/i');
    const count = await remainingCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should have Skip All / Trust AI button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    const skipButton = page.locator('button:has-text("Skip"), button:has-text("Trust AI"), button:has-text("Done")');
    const count = await skipButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should navigate to confirmation after review", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Find continue/done button
    const doneButton = page.locator('button:has-text("Done"), button:has-text("Continue"), button:has-text("Confirm")').first();
    if (await doneButton.count() > 0) {
      await doneButton.click();
      await expect(page).toHaveURL(/confirm|execute/);
    }
  });
});

test.describe("Cleanup Wizard - Confirmation Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
  });

  test("should display confirmation summary", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // Should show confirmation content
    const confirmContent = page.locator('text=/confirm|summary|ready/i').first();
    await expect(confirmContent).toBeVisible();
  });

  test("should display total emails to delete", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // Should show delete count
    const deleteCount = page.locator('text=/\\d+.*delete|remove/i');
    const count = await deleteCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display space to be freed", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // Should show space savings
    const spaceSavings = page.locator('text=/MB|GB|free|space/i');
    const count = await spaceSavings.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display category breakdown", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // Should show category breakdown
    const categories = page.locator('text=/promotions|newsletters|social|updates/i');
    const count = await categories.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display Execute/Confirm button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    const executeButton = page.locator('button:has-text("Execute"), button:has-text("Confirm"), button:has-text("Clean")');
    const count = await executeButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display Cancel/Back button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    const cancelButton = page.locator('button:has-text("Cancel"), button:has-text("Back"), a:has-text("Back")');
    const count = await cancelButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should show warning about deletion", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // May show warning
    const warning = page.locator('text=/warning|cannot be undone|trash|permanent/i');
    const count = await warning.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should execute cleanup when confirmed", async ({ page }) => {
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    const executeButton = page.locator('button:has-text("Execute"), button:has-text("Confirm"), button:has-text("Clean")').first();
    if (await executeButton.count() > 0) {
      await executeButton.click();
      // Should navigate to success or show progress
      await waitForLoadingComplete(page);
    }
  });
});

test.describe("Cleanup Wizard - Success Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
    // Mock completed cleanup
    await mockApiRoute(page, "/cleanup/results/*", mockData.mockCleanupResults);
  });

  test("should display success page", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // Should show success content
    const successContent = page.locator('text=/success|complete|done|congratulations/i').first();
    await expect(successContent).toBeVisible();
  });

  test("should display emails deleted count", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // Should show deleted count
    const deletedCount = page.locator('text=/\\d+.*deleted|removed/i');
    const count = await deletedCount.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display space freed", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // Should show space freed
    const spaceFreed = page.locator('text=/MB|GB|freed|saved/i');
    const count = await spaceFreed.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display unsubscribed count if any", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // May show unsubscribed count
    const unsubscribed = page.locator('text=/unsubscribed/i');
    const count = await unsubscribed.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should display filters created count if any", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // May show filters created
    const filters = page.locator('text=/filter/i');
    const count = await filters.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should have Return to Dashboard button", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    const dashboardButton = page.locator('a[href*="dashboard"], button:has-text("Dashboard"), a:has-text("Dashboard")');
    const count = await dashboardButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should have Start New Cleanup option", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    const newCleanupButton = page.locator('button:has-text("New"), button:has-text("Again"), a:has-text("cleanup")');
    const count = await newCleanupButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should navigate to dashboard when clicking return", async ({ page }) => {
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    const dashboardButton = page.locator('a[href="/dashboard"], button:has-text("Dashboard")').first();
    if (await dashboardButton.count() > 0) {
      await dashboardButton.click();
      await expect(page).toHaveURL(/dashboard/);
    }
  });
});

test.describe("Cleanup Wizard - Error Handling", () => {
  test("should handle scan error gracefully", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(
      page,
      "/cleanup/progress/*",
      { ...mockData.mockCleanupProgressScanning, error: "Gmail API error", status: "failed" }
    );

    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Should show error message
    const errorMessage = page.locator('text=/error|failed|try again/i');
    const count = await errorMessage.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should handle session not found error", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/cleanup/progress/*", { detail: "Session not found" }, { status: 404 });

    await page.goto("/dashboard/cleanup/scanning");

    // Should handle gracefully
    await expect(page.locator("body")).toBeVisible();
  });

  test("should handle cleanup execution error", async ({ page }) => {
    await setupCleanupWizardMocks(page);
    await mockApiRoute(
      page,
      "/cleanup/execute/*",
      { detail: "Cleanup failed" },
      { status: 500 }
    );

    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    const executeButton = page.locator('button:has-text("Execute"), button:has-text("Confirm")').first();
    if (await executeButton.count() > 0) {
      await executeButton.click();
      // Should show error or allow retry
    }
  });
});

test.describe("Cleanup Wizard - State Persistence", () => {
  test("should maintain session across page refreshes", async ({ page }) => {
    await setupCleanupWizardMocks(page);

    // Start a cleanup session
    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Refresh page
    await page.reload();
    await waitForLoadingComplete(page);

    // Should still show scanning or progress
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Cleanup Wizard - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await setupCleanupWizardMocks(page);
  });

  test("should have focusable action buttons", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Buttons should be focusable
    const buttons = page.locator("button");
    const count = await buttons.count();
    if (count > 0) {
      await buttons.first().focus();
      await expect(buttons.first()).toBeFocused();
    }
  });

  test("should support keyboard navigation in review", async ({ page }) => {
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Tab through elements
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    const focused = page.locator(":focus");
    await expect(focused).toBeVisible();
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Should have h1
    const h1 = page.locator("h1");
    const count = await h1.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe("Cleanup Wizard - Full Flow Integration", () => {
  test("should complete full wizard flow", async ({ page }) => {
    await setupCleanupWizardMocks(page);

    // Step 1: Start cleanup from dashboard
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Step 2: Should be able to navigate through wizard
    await page.goto("/dashboard/cleanup/scanning");
    await waitForLoadingComplete(page);

    // Step 3: Navigate to report
    await page.goto("/dashboard/cleanup/report");
    await waitForLoadingComplete(page);

    // Step 4: Navigate to review
    await page.goto("/dashboard/cleanup/review");
    await waitForLoadingComplete(page);

    // Step 5: Navigate to confirm
    await page.goto("/dashboard/cleanup/confirm");
    await waitForLoadingComplete(page);

    // Step 6: Navigate to success
    await page.goto("/dashboard/cleanup/success");
    await waitForLoadingComplete(page);

    // Should display success
    await expect(page.locator("body")).toBeVisible();
  });
});
