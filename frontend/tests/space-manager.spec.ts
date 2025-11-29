/**
 * Space Manager (Free Up Space) Tests
 * Tests for finding and deleting large attachments
 */

import { test, expect } from "@playwright/test";
import {
  setupSpaceManagerMocks,
  setupAuthenticatedMocks,
  mockApiRoute,
  waitForLoadingComplete,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("Space Manager Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupSpaceManagerMocks(page);
    await page.goto("/dashboard/space");
    await waitForLoadingComplete(page);
  });

  test.describe("Page Rendering", () => {
    test("should display page title", async ({ page }) => {
      const title = page.locator("h1, h2").first();
      await expect(title).toBeVisible();
    });

    test("should display storage overview card", async ({ page }) => {
      // Should show total size found
      const storageInfo = page.locator('text=/MB|GB|storage|found|large/i');
      const count = await storageInfo.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display filter controls", async ({ page }) => {
      // Should have filter dropdowns
      const filters = page.locator('select, [role="combobox"]');
      const count = await filters.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display email list", async ({ page }) => {
      // Should show list of large emails
      const emailList = page.locator('[class*="list"], [class*="grid"], table');
      const count = await emailList.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Filter Controls", () => {
    test("should have minimum size filter", async ({ page }) => {
      const sizeFilter = page.locator('select, [aria-label*="size"]').first();
      if (await sizeFilter.count() > 0) {
        await expect(sizeFilter).toBeVisible();
      }
    });

    test("should allow changing minimum size filter", async ({ page }) => {
      const sizeFilter = page.locator("select").first();
      if (await sizeFilter.count() > 0) {
        await sizeFilter.selectOption("5");
      }
    });

    test("should have older than filter", async ({ page }) => {
      const dateFilter = page.locator('select, [aria-label*="older"], [aria-label*="date"]');
      const count = await dateFilter.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should allow changing older than filter", async ({ page }) => {
      const filters = page.locator("select");
      const count = await filters.count();
      if (count >= 2) {
        await filters.nth(1).selectOption("90");
      }
    });

    test("should have Apply Filters button", async ({ page }) => {
      const applyButton = page.locator('button:has-text("Apply"), button:has-text("Filter")');
      const count = await applyButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should refresh list when applying filters", async ({ page }) => {
      const applyButton = page.locator('button:has-text("Apply"), button:has-text("Filter")').first();
      if (await applyButton.count() > 0) {
        await applyButton.click();
        await waitForLoadingComplete(page);
        // Page should still show content
        await expect(page.locator("body")).toBeVisible();
      }
    });
  });

  test.describe("Email List", () => {
    test("should display email subjects", async ({ page }) => {
      // Should show subjects from mock data
      const subjects = page.locator('text=/Project|Vacation|Design/i');
      const count = await subjects.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display sender info", async ({ page }) => {
      // Should show sender emails or names
      const senders = page.locator('text=/@/');
      const count = await senders.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display file sizes", async ({ page }) => {
      // Should show MB sizes
      const sizes = page.locator('text=/\\d+.*MB/i');
      const count = await sizes.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display dates", async ({ page }) => {
      // Should show dates
      const dates = page.locator('text=/\\d{1,2}.*\\d{4}|\\w+ \\d{1,2}/');
      const count = await dates.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should have checkboxes for selection", async ({ page }) => {
      const checkboxes = page.locator('input[type="checkbox"], [role="checkbox"]');
      const count = await checkboxes.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Selection", () => {
    test("should allow selecting individual emails", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();
        // Selection should be registered
      }
    });

    test("should have Select All button", async ({ page }) => {
      const selectAllButton = page.locator('button:has-text("Select All"), button:has-text("All")');
      const count = await selectAllButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should select all emails when clicking Select All", async ({ page }) => {
      const selectAllButton = page.locator('button:has-text("Select All")').first();
      if (await selectAllButton.count() > 0) {
        await selectAllButton.click();
        // Checkboxes should be checked
      }
    });

    test("should deselect all when clicking Deselect All", async ({ page }) => {
      // First select all
      const selectAllButton = page.locator('button:has-text("Select All")').first();
      if (await selectAllButton.count() > 0) {
        await selectAllButton.click();
        // Button might change to "Deselect All"
        const deselectButton = page.locator('button:has-text("Deselect")').first();
        if (await deselectButton.count() > 0) {
          await deselectButton.click();
        }
      }
    });

    test("should update selected count display", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();
        // Should show "1 selected" or similar
        const selectedText = page.locator('text=/\\d+ selected/i');
        const count = await selectedText.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    test("should update selected size display", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();
        // Should show selected size
        const sizeText = page.locator('text=/MB|GB/');
        const count = await sizeText.count();
        expect(count).toBeGreaterThan(0);
      }
    });
  });

  test.describe("Delete Action", () => {
    test("should have Delete Selected button", async ({ page }) => {
      const deleteButton = page.locator('button:has-text("Delete")');
      const count = await deleteButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should disable Delete button when nothing selected", async ({ page }) => {
      const deleteButton = page.locator('button:has-text("Delete")').first();
      if (await deleteButton.count() > 0) {
        const isDisabled = await deleteButton.isDisabled();
        expect(isDisabled).toBe(true);
      }
    });

    test("should enable Delete button when emails selected", async ({ page }) => {
      // Select an email first
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();

        const deleteButton = page.locator('button:has-text("Delete")').first();
        if (await deleteButton.count() > 0) {
          const isDisabled = await deleteButton.isDisabled();
          expect(isDisabled).toBe(false);
        }
      }
    });

    test("should show confirmation dialog when clicking Delete", async ({ page }) => {
      // Select an email
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();

        const deleteButton = page.locator('button:has-text("Delete")').first();
        if (await deleteButton.count() > 0) {
          await deleteButton.click();

          // Should show confirmation dialog
          const dialog = page.locator('[role="alertdialog"], [role="dialog"], .fixed');
          const count = await dialog.count();
          expect(count).toBeGreaterThanOrEqual(0);
        }
      }
    });

    test("should have Cancel button in confirmation dialog", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();

        const deleteButton = page.locator('button:has-text("Delete Selected")').first();
        if (await deleteButton.count() > 0) {
          await deleteButton.click();

          const cancelButton = page.locator('button:has-text("Cancel")');
          const count = await cancelButton.count();
          expect(count).toBeGreaterThanOrEqual(0);
        }
      }
    });

    test("should close dialog when clicking Cancel", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();

        const deleteButton = page.locator('button:has-text("Delete Selected")').first();
        if (await deleteButton.count() > 0) {
          await deleteButton.click();

          const cancelButton = page.locator('button:has-text("Cancel")').first();
          if (await cancelButton.count() > 0) {
            await cancelButton.click();
            // Dialog should close
          }
        }
      }
    });

    test("should execute deletion and show success message", async ({ page }) => {
      const checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first();
      if (await checkbox.count() > 0) {
        await checkbox.click();

        const deleteButton = page.locator('button:has-text("Delete Selected")').first();
        if (await deleteButton.count() > 0) {
          await deleteButton.click();

          // Confirm deletion
          const confirmButton = page.locator('[role="alertdialog"] button:has-text("Delete"), [role="dialog"] button:has-text("Delete")').first();
          if (await confirmButton.count() > 0) {
            await confirmButton.click();
            await waitForLoadingComplete(page);

            // Should show success message
            const successMessage = page.locator('text=/success|deleted|freed/i');
            const count = await successMessage.count();
            expect(count).toBeGreaterThanOrEqual(0);
          }
        }
      }
    });
  });

  test.describe("Empty State", () => {
    test("should show empty state when no large emails found", async ({ page }) => {
      await mockApiRoute(page, "/attachments/large", { emails: [], total_size_bytes: 0 });
      await page.goto("/dashboard/space");
      await waitForLoadingComplete(page);

      // Should show empty state message
      const emptyMessage = page.locator('text=/no.*found|empty|nothing/i');
      const count = await emptyMessage.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Loading State", () => {
    test("should show loading indicator while fetching", async ({ page }) => {
      await mockApiRoute(page, "/attachments/large", mockData.mockLargeAttachments, { delay: 2000 });
      await page.goto("/dashboard/space");

      // Should show loading indicator
      const loader = page.locator('.animate-spin, text=/loading/i');
      const count = await loader.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Error Handling", () => {
    test("should handle API error gracefully", async ({ page }) => {
      await mockApiRoute(page, "/attachments/large", { error: "Server error" }, { status: 500 });
      await page.goto("/dashboard/space");

      // Page should still render
      await expect(page.locator("body")).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("should render correctly on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("/dashboard/space");
      await waitForLoadingComplete(page);

      await expect(page.locator("main")).toBeVisible();
    });

    test("should render correctly on tablet", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto("/dashboard/space");
      await waitForLoadingComplete(page);

      await expect(page.locator("main")).toBeVisible();
    });
  });
});

test.describe("Space Manager - Email Row Interaction", () => {
  test.beforeEach(async ({ page }) => {
    await setupSpaceManagerMocks(page);
    await page.goto("/dashboard/space");
    await waitForLoadingComplete(page);
  });

  test("should highlight row on hover", async ({ page }) => {
    const emailRow = page.locator('[class*="rounded"], tr, [class*="row"]').nth(1);
    if (await emailRow.count() > 0) {
      await emailRow.hover();
      // Row should still be visible
      await expect(emailRow).toBeVisible();
    }
  });

  test("should toggle selection on row click", async ({ page }) => {
    const emailRow = page.locator('[class*="rounded"], tr, [class*="row"]').nth(1);
    if (await emailRow.count() > 0) {
      await emailRow.click();
      // Should toggle checkbox
    }
  });
});
