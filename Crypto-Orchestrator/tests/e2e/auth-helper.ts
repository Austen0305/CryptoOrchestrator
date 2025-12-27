/**
 * Authentication Helper for E2E Tests
 * Provides reusable authentication functions for Playwright tests
 */

import { Page, expect } from '@playwright/test';

/**
 * Register a new test user
 */
export async function registerTestUser(
  page: Page,
  email: string,
  password: string,
  username: string
): Promise<boolean> {
  try {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    // Fill registration form
    await page.fill('[name="name"]', 'Test User');
    await page.fill('[name="username"]', username);
    await page.fill('[name="email"]', email);
    await page.fill('[name="password"]', password);
    await page.fill('[name="confirmPassword"]', password);

    // Accept terms checkbox
    const acceptTermsCheckbox = page.locator(
      'input[name="acceptTerms"], input[id="acceptTerms"], input[type="checkbox"][name*="terms"]'
    ).first();

    const checkboxVisible = await acceptTermsCheckbox.isVisible({ timeout: 5000 }).catch(() => false);
    if (checkboxVisible) {
      const isChecked = await acceptTermsCheckbox.isChecked().catch(() => false);
      if (!isChecked) {
        await acceptTermsCheckbox.check();
        await page.waitForTimeout(300);
      }
    }

    // Wait for submit button to be enabled
    const submitButton = page.locator('button[type="submit"]').first();
    let buttonEnabled = false;
    for (let i = 0; i < 20; i++) {
      const isEnabled = await submitButton.isEnabled().catch(() => false);
      if (isEnabled) {
        buttonEnabled = true;
        break;
      }
      await page.waitForTimeout(500);
    }

    if (!buttonEnabled) {
      throw new Error('Submit button not enabled after filling form');
    }

    await submitButton.click();

    // Wait for redirect to dashboard or login
    await page.waitForTimeout(2000);
    const currentUrl = page.url();
    
    // If redirected to login, registration succeeded but need to login
    if (currentUrl.includes('login')) {
      return true; // Registration successful, will login next
    }
    
    // If redirected to dashboard, registration and auto-login succeeded
    if (currentUrl.includes('dashboard')) {
      return true;
    }

    return false;
  } catch (error) {
    console.error('Registration failed:', error);
    return false;
  }
}

/**
 * Login with existing credentials
 * Enhanced with better error handling and multiple verification methods
 */
export async function loginTestUser(
  page: Page,
  email: string,
  password: string
): Promise<boolean> {
  try {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill login form - try multiple selectors
    const emailInput = page.locator('[name="email"], input[type="email"], input[id="email"]').first();
    const passwordInput = page.locator('[name="password"], input[type="password"], input[id="password"]').first();
    
    await emailInput.fill(email);
    await page.waitForTimeout(200); // Wait for validation
    await passwordInput.fill(password);
    await page.waitForTimeout(200); // Wait for validation

    // Wait for submit button to be enabled
    const submitButton = page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")').first();
    
    // Wait for button to be enabled with retry
    let buttonEnabled = false;
    for (let i = 0; i < 10; i++) {
      const isEnabled = await submitButton.isEnabled().catch(() => false);
      if (isEnabled) {
        buttonEnabled = true;
        break;
      }
      await page.waitForTimeout(300);
    }
    
    if (!buttonEnabled) {
      console.warn('Submit button not enabled after filling form');
      // Try clicking anyway
    }
    
    await submitButton.click();

    // Wait for navigation - try multiple methods
    try {
      await Promise.race([
        page.waitForURL(/.*dashboard/, { timeout: 10000 }),
        page.waitForURL(/.*\/$/, { timeout: 10000 }), // Root URL
        page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 }),
        page.waitForSelector('nav, [role="navigation"]', { timeout: 10000 }), // Any navigation element
      ]);
    } catch (e) {
      // Navigation might have happened, check current state
      await page.waitForTimeout(1000);
    }

    // Verify we're authenticated by checking multiple indicators
    const currentUrl = page.url();
    const hasDashboard = currentUrl.includes('dashboard') || currentUrl === 'http://localhost:5173/' || currentUrl.endsWith('/');
    const hasDashboardElement = await page.locator('[data-testid="dashboard"]').count() > 0;
    const hasNav = await page.locator('nav, [role="navigation"]').count() > 0;
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    
    // Authenticated if we have dashboard/nav and not on login page
    const authenticated = (hasDashboard || hasDashboardElement || hasNav) && !isLoginPage;
    
    if (authenticated) {
      console.log('✅ Login successful');
    } else {
      console.warn('Login verification failed:', { currentUrl, hasDashboard, hasDashboardElement, hasNav, isLoginPage });
    }
    
    return authenticated;
  } catch (error) {
    console.error('Login failed:', error);
    return false;
  }
}

/**
 * Register and login a test user (complete auth flow)
 * Enhanced with better error handling and retry logic
 */
export async function authenticateTestUser(
  page: Page,
  email: string,
  password: string,
  username: string
): Promise<boolean> {
  try {
    // First, try to login (user might already exist)
    const loginSuccess = await loginTestUser(page, email, password);
    if (loginSuccess) {
      return true;
    }

    // If login failed, try to register
    const registered = await registerTestUser(page, email, password, username);
    
    if (!registered) {
      console.warn('Registration failed, attempting direct login');
      // Try login again in case registration succeeded but didn't redirect
      return await loginTestUser(page, email, password);
    }

    // If redirected to login, complete login
    if (page.url().includes('login')) {
      return await loginTestUser(page, email, password);
    }

    // If already on dashboard, we're done
    if (page.url().includes('dashboard')) {
      return true;
    }

    // Final check: navigate to dashboard and verify
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    return !isLoginPage && !page.url().includes('login');
  } catch (error) {
    console.error('Authentication failed:', error);
    return false;
  }
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    return !isLoginPage && !page.url().includes('login');
  } catch {
    return false;
  }
}

/**
 * Generate unique test user credentials
 */
export function generateTestUser(): { email: string; password: string; username: string } {
  const timestamp = Date.now();
  return {
    email: `test${timestamp}@example.com`,
    password: 'SecurePass123!',
    username: `testuser${timestamp}`,
  };
}
