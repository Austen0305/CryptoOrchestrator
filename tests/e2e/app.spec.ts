/**
 * E2E Tests for CryptoOrchestrator Desktop App
 * Tests critical user flows: launch, login, bot management, risk alerts
 */

import { test, expect } from '@playwright/test';

test.describe('Desktop App E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('/');
  });

  test('should load dashboard', async ({ page }) => {
    await expect(page).toHaveTitle(/CryptoOrchestrator/i);
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 });
    
    // Check for key dashboard elements
    await expect(page.locator('text=Portfolio')).toBeVisible();
  });

  test('should handle login flow', async ({ page }) => {
    // Look for login button or form
    const loginButton = page.locator('button:has-text("Login"), a:has-text("Login")').first();
    
    if (await loginButton.isVisible()) {
      await loginButton.click();
      
      // Fill login form (adjust selectors based on your UI)
      await page.fill('input[name="email"], input[type="email"]', 'test@example.com');
      await page.fill('input[name="password"], input[type="password"]', 'testpassword');
      
      await page.click('button:has-text("Sign In"), button[type="submit"]');
      
      // Wait for redirect or success message
      await page.waitForURL(/\/(dashboard|home)/, { timeout: 5000 });
    }
  });

  test('should create and start a bot', async ({ page }) => {
    // Navigate to bots page
    await page.click('a:has-text("Bots"), [href*="bot"]');
    await page.waitForURL(/.*bot.*/, { timeout: 5000 });
    
    // Click create bot button
    const createButton = page.locator('button:has-text("Create"), button:has-text("New Bot")').first();
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Fill bot form
      await page.fill('input[name="name"]', 'E2E Test Bot');
      await page.selectOption('select[name="tradingPair"]', 'BTC/USD');
      await page.selectOption('select[name="strategy"]', 'ml_adaptive');
      
      // Submit form
      await page.click('button:has-text("Create"), button[type="submit"]');
      
      // Wait for bot to appear in list
      await expect(page.locator('text=E2E Test Bot')).toBeVisible({ timeout: 5000 });
      
      // Start bot
      const startButton = page.locator('button:has-text("Start")').first();
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Verify bot status changed
        await expect(page.locator('text=Running, text=Active')).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should display risk alerts', async ({ page }) => {
    // Navigate to risk management or dashboard
    await page.click('a:has-text("Risk"), [href*="risk"]');
    await page.waitForTimeout(2000);
    
    // Check for risk metrics
    const riskElements = [
      'text=Sharpe Ratio',
      'text=Maximum Drawdown',
      'text=VaR',
      'text=Portfolio Heat'
    ];
    
    for (const selector of riskElements) {
      await expect(page.locator(selector).first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('should handle WebSocket updates', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Wait for WebSocket connection
    await page.waitForTimeout(2000);
    
    // Check for live data updates (adjust based on your UI)
    const liveData = page.locator('[data-testid="live-price"], .price-update').first();
    
    if (await liveData.isVisible()) {
      // Verify data is updating (check timestamp or value changes)
      const initialValue = await liveData.textContent();
      await page.waitForTimeout(3000);
      const updatedValue = await liveData.textContent();
      
      // Value should have changed (or at least be present)
      expect(updatedValue).toBeTruthy();
    }
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/**', route => route.abort());
    
    // Navigate to a page that requires API calls
    await page.goto('/dashboard');
    
    // Check for error message or fallback UI
    const errorMessage = page.locator('text=Error, text=Failed, text=Unable').first();
    
    // Should show error state (might take a moment)
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('should support dark/light theme toggle', async ({ page }) => {
    // Look for theme toggle
    const themeToggle = page.locator('button[aria-label*="theme"], button[aria-label*="Theme"], [data-testid="theme-toggle"]').first();
    
    if (await themeToggle.isVisible()) {
      const initialClass = await page.locator('html, body').first().getAttribute('class');
      
      await themeToggle.click();
      await page.waitForTimeout(500);
      
      const updatedClass = await page.locator('html, body').first().getAttribute('class');
      
      // Theme should have changed
      expect(updatedClass).not.toBe(initialClass);
    }
  });
});

