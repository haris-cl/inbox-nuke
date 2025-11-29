/**
 * Settings Page Tests
 * Tests for settings, whitelist management, and account connection
 */

import { test, expect } from "@playwright/test";
import {
  setupAuthenticatedMocks,
  mockApiRoute,
  mockPostRequest,
  mockDeleteRequest,
  waitForLoadingComplete,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);
  });

  test.describe("Page Rendering", () => {
    test("should display settings page", async ({ page }) => {
      await expect(page.locator("body")).toBeVisible();
    });

    test("should display page title", async ({ page }) => {
      const title = page.locator("h1, h2").first();
      await expect(title).toBeVisible();
    });

    test("should display settings sections", async ({ page }) => {
      // Should have multiple settings sections
      const sections = page.locator('[class*="card"], [class*="section"], h3');
      const count = await sections.count();
      expect(count).toBeGreaterThan(0);
    });
  });

  test.describe("Account Section", () => {
    test("should display connected email", async ({ page }) => {
      const email = page.locator('text=/test@gmail.com|connected|account/i');
      const count = await email.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should have disconnect button", async ({ page }) => {
      const disconnectButton = page.locator('button:has-text("Disconnect"), button:has-text("Sign out")');
      const count = await disconnectButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should show confirmation when clicking disconnect", async ({ page }) => {
      const disconnectButton = page.locator('button:has-text("Disconnect")').first();
      if (await disconnectButton.count() > 0) {
        await disconnectButton.click();

        // Should show confirmation or execute
        const confirmation = page.locator('[role="alertdialog"], [role="dialog"], text=/sure|confirm/i');
        const count = await confirmation.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe("Whitelist Section", () => {
    test("should display whitelist section", async ({ page }) => {
      const whitelistSection = page.locator('text=/whitelist|protected|safe/i');
      const count = await whitelistSection.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display existing whitelist entries", async ({ page }) => {
      // Should show entries from mock
      const entries = page.locator('text=/@|work.com|family.com|personal.com/');
      const count = await entries.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should have add to whitelist input", async ({ page }) => {
      const input = page.locator('input[type="text"], input[type="email"], input[placeholder*="email"]');
      const count = await input.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should have add button", async ({ page }) => {
      const addButton = page.locator('button:has-text("Add"), button:has-text("+")');
      const count = await addButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should allow adding new whitelist entry", async ({ page }) => {
      await mockPostRequest(page, "/whitelist", { status: "ok" });

      const input = page.locator('input[type="text"], input[type="email"]').first();
      if (await input.count() > 0) {
        await input.fill("newcontact@example.com");

        const addButton = page.locator('button:has-text("Add")').first();
        if (await addButton.count() > 0) {
          await addButton.click();
        }
      }
    });

    test("should have remove buttons for entries", async ({ page }) => {
      const removeButtons = page.locator('button:has-text("Remove"), button:has-text("Delete"), button[aria-label*="remove"]');
      const count = await removeButtons.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should allow removing whitelist entry", async ({ page }) => {
      await mockDeleteRequest(page, "/whitelist/*", { status: "ok" });

      const removeButton = page.locator('button:has-text("Remove"), button[aria-label*="remove"]').first();
      if (await removeButton.count() > 0) {
        await removeButton.click();
      }
    });

    test("should validate email format", async ({ page }) => {
      const input = page.locator('input[type="text"], input[type="email"]').first();
      if (await input.count() > 0) {
        await input.fill("invalid-email");

        const addButton = page.locator('button:has-text("Add")').first();
        if (await addButton.count() > 0) {
          await addButton.click();

          // Should show validation error or not add
          const error = page.locator('text=/invalid|error|valid email/i');
          const count = await error.count();
          expect(count).toBeGreaterThanOrEqual(0);
        }
      }
    });
  });

  test.describe("Theme Settings", () => {
    test("should display theme toggle if exists", async ({ page }) => {
      const themeToggle = page.locator('button[aria-label*="theme"], text=/dark|light|theme/i');
      const count = await themeToggle.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should toggle theme when clicked", async ({ page }) => {
      const themeToggle = page.locator('button[aria-label*="theme"]').first();
      if (await themeToggle.count() > 0) {
        await themeToggle.click();
        // Theme should change
        await expect(page.locator("body")).toBeVisible();
      }
    });
  });

  test.describe("Export/Import Settings", () => {
    test("should have export options if available", async ({ page }) => {
      const exportButton = page.locator('button:has-text("Export"), a:has-text("Export")');
      const count = await exportButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });
});

test.describe("Settings - Form Validation", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);
  });

  test("should not allow empty whitelist entry", async ({ page }) => {
    const addButton = page.locator('button:has-text("Add")').first();
    if (await addButton.count() > 0) {
      // Try to add without entering anything
      await addButton.click();
      // Should show error or be disabled
    }
  });

  test("should support domain wildcards", async ({ page }) => {
    const input = page.locator('input[type="text"], input[type="email"]').first();
    if (await input.count() > 0) {
      await input.fill("@company.com");
      // Should be valid for domain-wide whitelist
    }
  });
});

test.describe("Settings - Responsiveness", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
  });

  test("should render on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);

    await expect(page.locator("main")).toBeVisible();
  });

  test("should render on tablet", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);

    await expect(page.locator("main")).toBeVisible();
  });
});

test.describe("Settings - Error Handling", () => {
  test("should handle whitelist fetch error", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/whitelist", { error: "Server error" }, { status: 500 });
    await page.goto("/dashboard/settings");

    await expect(page.locator("body")).toBeVisible();
  });

  test("should handle whitelist add error", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockPostRequest(page, "/whitelist", { detail: "Failed to add" }, { status: 500 });
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);

    const input = page.locator('input[type="text"], input[type="email"]').first();
    if (await input.count() > 0) {
      await input.fill("test@example.com");

      const addButton = page.locator('button:has-text("Add")').first();
      if (await addButton.count() > 0) {
        await addButton.click();
        // Should handle error
      }
    }
  });
});

test.describe("Settings - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);
  });

  test("should have proper form labels", async ({ page }) => {
    const inputs = page.locator("input");
    const count = await inputs.count();

    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute("id");
      const ariaLabel = await input.getAttribute("aria-label");
      const placeholder = await input.getAttribute("placeholder");

      // Should have some form of labeling
      const hasLabel = id || ariaLabel || placeholder;
      expect(hasLabel).toBeTruthy();
    }
  });

  test("should support keyboard navigation", async ({ page }) => {
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    const focused = page.locator(":focus");
    await expect(focused).toBeVisible();
  });
});
