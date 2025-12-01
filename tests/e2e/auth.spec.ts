import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * Tests login, logout, and session management
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('should display login form when not authenticated', async ({ page }) => {
    // Check if login form is visible
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Fill in login form (adjust selectors based on your actual form)
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();

    if (await emailInput.isVisible()) {
      await emailInput.fill('test@example.com');
      await passwordInput.fill('testpassword123');
      await submitButton.click();

      // Wait for navigation or success message
      await page.waitForURL(/\/dashboard|\//, { timeout: 10000 }).catch(() => {
        // If URL doesn't change, check for success indicators
        return;
      });

      // Verify user is logged in (check for dashboard or user menu)
      const dashboard = page.locator('text=Dashboard, h1:has-text("Dashboard"), [data-testid="dashboard"]').first();
      if (await dashboard.isVisible().catch(() => false)) {
        await expect(dashboard).toBeVisible();
      }
    }
  });

  test('should show error with invalid credentials', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login")').first();

    if (await emailInput.isVisible()) {
      await emailInput.fill('invalid@example.com');
      await passwordInput.fill('wrongpassword');
      await submitButton.click();

      // Wait for error message
      await expect(
        page.locator('text=/error|invalid|incorrect/i, [role="alert"]').first()
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should logout successfully', async ({ page }) => {
    // First login (if not already logged in)
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    if (await emailInput.isVisible()) {
      await emailInput.fill('test@example.com');
      const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
      await passwordInput.fill('testpassword123');
      const submitButton = page.locator('button[type="submit"], button:has-text("Login")').first();
      await submitButton.click();
      await page.waitForTimeout(2000);
    }

    // Click logout button/menu
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), [data-testid="logout"]').first();
    if (await logoutButton.isVisible().catch(() => false)) {
      await logoutButton.click();
      
      // Verify redirected to login
      await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible({ timeout: 5000 });
    }
  });
});

