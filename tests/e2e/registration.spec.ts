import { test, expect } from '@playwright/test';

/**
 * Registration E2E Tests
 * Tests the complete registration flow
 */

test.describe('Registration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Clear any existing auth tokens
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('should complete registration flow successfully', async ({ page }) => {
    // Generate unique email for this test
    const timestamp = Date.now();
    const testEmail = `test${timestamp}@example.com`;
    const testPassword = 'TestPassword123!';
    const testName = 'Test User';

    // Find and click register tab/button if it exists
    const registerTab = page.locator('button:has-text("Register"), [role="tab"]:has-text("Register")').first();
    if (await registerTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await registerTab.click();
    }

    // Wait for registration form to be visible
    const nameInput = page.locator('input[type="text"]#name, input[name="name"], label:has-text("Full Name") + input').first();
    const emailInput = page.locator('input[type="email"]#email, input[name="email"], label:has-text("Email") + input').first();
    const passwordInput = page.locator('input[type="password"]#password, input[name="password"], label:has-text("Password") + input').first();
    const submitButton = page.locator('button[type="submit"]:has-text("Create Account"), button:has-text("Register")').first();

    // Fill in the registration form
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill(testName);
    
    await expect(emailInput).toBeVisible({ timeout: 5000 });
    await emailInput.fill(testEmail);
    
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await passwordInput.fill(testPassword);

    // Submit the form
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    
    // Click submit and wait for loading to complete
    await submitButton.click();
    
    // Wait for either success (modal closes) or error message
    await Promise.race([
      // Success: Modal closes (dialog no longer visible)
      page.waitForSelector('[role="dialog"]', { state: 'hidden', timeout: 15000 }).catch(() => null),
      // Error: Error message appears
      page.waitForSelector('[role="alert"], .alert-destructive', { timeout: 15000 }).catch(() => null),
    ]);

    // Check if there's an error message
    const errorAlert = page.locator('[role="alert"], .alert-destructive').first();
    if (await errorAlert.isVisible({ timeout: 2000 }).catch(() => false)) {
      const errorText = await errorAlert.textContent();
      throw new Error(`Registration failed with error: ${errorText}`);
    }

    // Verify registration was successful by checking:
    // 1. Modal is closed (if it was a modal)
    // 2. Or user is redirected
    // 3. Or auth token exists in storage
    
    // Check if auth token exists
    const hasToken = await page.evaluate(() => {
      return !!(localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token'));
    });
    
    expect(hasToken).toBe(true);
  });

  test('should show error for duplicate email', async ({ page }) => {
    // First, register a user
    const timestamp = Date.now();
    const testEmail = `duplicate${timestamp}@example.com`;
    const testPassword = 'TestPassword123!';
    const testName = 'Test User';

    // Register first user (reuse the successful registration test logic)
    const registerTab = page.locator('button:has-text("Register"), [role="tab"]:has-text("Register")').first();
    if (await registerTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await registerTab.click();
    }

    const nameInput = page.locator('input[type="text"]#name, input[name="name"]').first();
    const emailInput = page.locator('input[type="email"]#email, input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"]#password, input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"]:has-text("Create Account")').first();

    await nameInput.fill(testName);
    await emailInput.fill(testEmail);
    await passwordInput.fill(testPassword);
    await submitButton.click();
    
    // Wait for first registration to complete
    await page.waitForTimeout(3000);

    // Try to register again with the same email
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    if (await registerTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await registerTab.click();
    }

    await nameInput.fill('Another User');
    await emailInput.fill(testEmail); // Same email
    await passwordInput.fill('DifferentPassword123!');
    await submitButton.click();

    // Should show error message
    const errorAlert = page.locator('[role="alert"], .alert-destructive').first();
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
    
    const errorText = await errorAlert.textContent();
    expect(errorText?.toLowerCase()).toContain('already exists');
  });

  test('should validate password strength', async ({ page }) => {
    const registerTab = page.locator('button:has-text("Register"), [role="tab"]:has-text("Register")').first();
    if (await registerTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await registerTab.click();
    }

    const nameInput = page.locator('input[type="text"]#name, input[name="name"]').first();
    const emailInput = page.locator('input[type="email"]#email, input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"]#password, input[name="password"]').first();
    const submitButton = page.locator('button[type="submit"]:has-text("Create Account")').first();

    await nameInput.fill('Test User');
    await emailInput.fill('weakpass@example.com');
    await passwordInput.fill('123'); // Weak password
    await submitButton.click();

    // Should show validation error
    const errorAlert = page.locator('[role="alert"], .alert-destructive').first();
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
  });
});

