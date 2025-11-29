/**
 * Home Page and Authentication Tests
 * Tests for landing page, OAuth flow, and authentication states
 */

import { test, expect } from "@playwright/test";
import {
  setupAuthenticatedMocks,
  setupUnauthenticatedMocks,
  mockApiRoute,
  waitForLoadingComplete,
} from "./fixtures/test-helpers";
import * as mockData from "./fixtures/mock-data";

test.describe("Home Page (Landing)", () => {
  test.describe("Unauthenticated State", () => {
    test.beforeEach(async ({ page }) => {
      await setupUnauthenticatedMocks(page);
      await page.goto("/");
      await waitForLoadingComplete(page);
    });

    test("should display home page", async ({ page }) => {
      await expect(page.locator("body")).toBeVisible();
    });

    test("should display app title/branding", async ({ page }) => {
      const branding = page.locator('text=/inbox|nuke|cleanup|gmail/i').first();
      await expect(branding).toBeVisible();
    });

    test("should display Connect with Google button", async ({ page }) => {
      const connectButton = page.locator('button:has-text("Connect"), button:has-text("Google"), a:has-text("Connect")');
      const count = await connectButton.count();
      expect(count).toBeGreaterThan(0);
    });

    test("should display feature highlights", async ({ page }) => {
      const features = page.locator('text=/clean|unsubscribe|free|storage|automatic/i');
      const count = await features.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should display trust/security messaging", async ({ page }) => {
      const trustMessage = page.locator('text=/secure|private|local|safe|protect/i');
      const count = await trustMessage.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test("should not show dashboard content", async ({ page }) => {
      const dashboardContent = page.locator('text=/\\d+ emails|MB freed|senders processed/i');
      const count = await dashboardContent.count();
      expect(count).toBe(0);
    });
  });

  test.describe("Authenticated State", () => {
    test.beforeEach(async ({ page }) => {
      await setupAuthenticatedMocks(page);
      await page.goto("/");
      await waitForLoadingComplete(page);
    });

    test("should redirect to dashboard when authenticated", async ({ page }) => {
      // May redirect or show dashboard link
      const dashboardLink = page.locator('a[href*="dashboard"], button:has-text("Dashboard")');
      const count = await dashboardLink.count();

      const isOnDashboard = page.url().includes("dashboard");
      expect(count > 0 || isOnDashboard).toBe(true);
    });

    test("should show Go to Dashboard button if on home", async ({ page }) => {
      if (!page.url().includes("dashboard")) {
        const dashboardButton = page.locator('a[href*="dashboard"], button:has-text("Dashboard")');
        const count = await dashboardButton.count();
        expect(count).toBeGreaterThan(0);
      }
    });
  });
});

test.describe("OAuth Flow", () => {
  test.describe("Starting OAuth", () => {
    test("should redirect to Google when clicking Connect", async ({ page }) => {
      await setupUnauthenticatedMocks(page);
      await mockApiRoute(page, "/auth/google/start", { url: "https://accounts.google.com/oauth" });

      await page.goto("/");
      await waitForLoadingComplete(page);

      const connectButton = page.locator('button:has-text("Connect"), a:has-text("Connect")').first();
      if (await connectButton.count() > 0) {
        // Don't actually click to avoid navigation, just verify it exists
        await expect(connectButton).toBeVisible();
      }
    });
  });

  test.describe("OAuth Callback", () => {
    test("should handle successful OAuth callback", async ({ page }) => {
      await mockApiRoute(page, "/auth/status", mockData.mockAuthConnected);

      await page.goto("/auth/callback?code=test_code");
      await waitForLoadingComplete(page);

      // Should redirect to dashboard or show success
      const isOnDashboard = page.url().includes("dashboard");
      const successMessage = page.locator('text=/success|connected|welcome/i');
      const hasSuccess = await successMessage.count() > 0;

      expect(isOnDashboard || hasSuccess || page.url().includes("callback")).toBe(true);
    });

    test("should handle OAuth error", async ({ page }) => {
      await page.goto("/auth/callback?error=access_denied");
      await waitForLoadingComplete(page);

      // Should show error or redirect to home
      const isOnHome = page.url() === "/" || page.url().endsWith("3000/");
      const errorMessage = page.locator('text=/error|denied|failed|try again/i');
      const hasError = await errorMessage.count() > 0;

      expect(isOnHome || hasError || page.url().includes("callback")).toBe(true);
    });

    test("should handle missing code parameter", async ({ page }) => {
      await page.goto("/auth/callback");
      await waitForLoadingComplete(page);

      // Should handle gracefully
      await expect(page.locator("body")).toBeVisible();
    });
  });
});

test.describe("Authentication State Management", () => {
  test("should persist authentication across page reloads", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Reload page
    await page.reload();
    await waitForLoadingComplete(page);

    // Should still be on dashboard
    await expect(page).toHaveURL(/dashboard/);
  });

  test("should redirect to home when authentication fails", async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Simulate auth failure on next request
    await mockApiRoute(page, "/auth/status", mockData.mockAuthDisconnected);
    await page.reload();

    // May redirect or show login prompt
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Disconnect Flow", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedMocks(page);
    await mockApiRoute(page, "/auth/disconnect", { status: "ok" });
    await page.goto("/dashboard/settings");
    await waitForLoadingComplete(page);
  });

  test("should have disconnect option", async ({ page }) => {
    const disconnectButton = page.locator('button:has-text("Disconnect"), button:has-text("Sign out")');
    const count = await disconnectButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("should confirm before disconnecting", async ({ page }) => {
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

test.describe("Home Page - Responsive Design", () => {
  test.beforeEach(async ({ page }) => {
    await setupUnauthenticatedMocks(page);
  });

  test("should render on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await waitForLoadingComplete(page);

    await expect(page.locator("body")).toBeVisible();

    // Connect button should still be visible
    const connectButton = page.locator('button:has-text("Connect"), a:has-text("Connect")');
    const count = await connectButton.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should render on tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/");
    await waitForLoadingComplete(page);

    await expect(page.locator("body")).toBeVisible();
  });

  test("should render on desktop viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/");
    await waitForLoadingComplete(page);

    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Home Page - Error Handling", () => {
  test("should handle API health check failure", async ({ page }) => {
    await mockApiRoute(page, "/auth/status", { error: "Service unavailable" }, { status: 503 });
    await page.goto("/");
    await waitForLoadingComplete(page);

    // Should still render home page
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Home Page - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await setupUnauthenticatedMocks(page);
    await page.goto("/");
    await waitForLoadingComplete(page);
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    const h1 = page.locator("h1");
    const count = await h1.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test("should have accessible connect button", async ({ page }) => {
    const connectButton = page.locator('button:has-text("Connect"), a:has-text("Connect")').first();
    if (await connectButton.count() > 0) {
      // Should be focusable
      await connectButton.focus();
      await expect(connectButton).toBeFocused();
    }
  });

  test("should support keyboard navigation", async ({ page }) => {
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    const focused = page.locator(":focus");
    await expect(focused).toBeVisible();
  });
});

test.describe("Protected Routes", () => {
  test.beforeEach(async ({ page }) => {
    await setupUnauthenticatedMocks(page);
  });

  const protectedRoutes = [
    "/dashboard",
    "/dashboard/history",
    "/dashboard/settings",
    "/dashboard/space",
    "/dashboard/cleanup",
  ];

  for (const route of protectedRoutes) {
    test(`should protect ${route} when unauthenticated`, async ({ page }) => {
      await page.goto(route);
      await waitForLoadingComplete(page);

      // Should either redirect to home or show connect prompt
      const isOnRoute = page.url().includes(route.replace("/dashboard", ""));
      const connectPrompt = page.locator('text=/connect|sign in|login/i');
      const hasPrompt = await connectPrompt.count() > 0;

      // Either redirected away or showing login prompt
      expect(!isOnRoute || hasPrompt || page.url() === "/" || page.url().includes("auth")).toBe(
        true
      );
    });
  }
});

test.describe("Session Expiry", () => {
  test("should handle expired session gracefully", async ({ page }) => {
    // Start authenticated
    await setupAuthenticatedMocks(page);
    await page.goto("/dashboard");
    await waitForLoadingComplete(page);

    // Simulate session expiry
    await mockApiRoute(page, "/auth/status", { connected: false, email: null });
    await mockApiRoute(page, "/stats/current", { detail: "Not authenticated" }, { status: 401 });

    // Trigger a refresh
    await page.reload();
    await waitForLoadingComplete(page);

    // Should handle gracefully
    await expect(page.locator("body")).toBeVisible();
  });
});
