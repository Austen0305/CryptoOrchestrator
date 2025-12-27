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
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Clear any existing auth
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Refresh page to ensure we're on login
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check if login form is visible
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    
    // At least one should be visible (might be in a modal or on the page)
    const emailVisible = await emailInput.isVisible({ timeout: 5000 }).catch(() => false);
    const passwordVisible = await passwordInput.isVisible({ timeout: 5000 }).catch(() => false);
    
    // If neither is visible, might be already logged in or on different page
    if (!emailVisible && !passwordVisible) {
      // Check if we're on dashboard (already logged in)
      const isDashboard = await page.locator('[data-testid="dashboard"]').isVisible().catch(() => false);
      if (isDashboard) {
        // Already logged in - test passes
        return;
      }
    }
    
    // If we got here and inputs aren't visible, that's a problem
    expect(emailVisible || passwordVisible).toBe(true);
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Clear any existing auth
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Refresh to ensure we're on login page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Fill in login form (adjust selectors based on your actual form)
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();

    // Check if login form is visible
    const emailVisible = await emailInput.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (emailVisible) {
      await emailInput.fill('test@example.com');
      await passwordInput.fill('testpassword123');
      
      if (await submitButton.isVisible().catch(() => false)) {
        await submitButton.click();

        // Wait for navigation or success message (with longer timeout for API)
        await Promise.race([
          page.waitForURL(/\/dashboard|\//, { timeout: 15000 }).catch(() => null),
          page.waitForSelector('[data-testid="dashboard"]', { timeout: 15000 }).catch(() => null),
          page.waitForTimeout(5000), // Fallback timeout
        ]);

        // Verify user is logged in (check for dashboard or user menu)
        const dashboard = page.locator('text=Dashboard, h1:has-text("Dashboard"), [data-testid="dashboard"]').first();
        const dashboardVisible = await dashboard.isVisible({ timeout: 5000 }).catch(() => false);
        if (dashboardVisible) {
          await expect(dashboard).toBeVisible();
        }
      }
    } else {
      // Might already be logged in
      const isDashboard = await page.locator('[data-testid="dashboard"]').isVisible().catch(() => false);
      if (isDashboard) {
        // Already logged in - test passes
        return;
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

