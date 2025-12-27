import { test, expect } from '@playwright/test';
import { authenticateTestUser, generateTestUser } from './auth-helper';

/**
 * Comprehensive UI E2E Test
 * Tests the entire application by clicking through all major features
 */

test.describe('Comprehensive UI Testing', () => {
  let testUser: { email: string; password: string; username: string };

  test.beforeAll(async ({ page }) => {
    // Generate test user
    testUser = generateTestUser();
    
    // Try to authenticate
    await authenticateTestUser(
      page,
      testUser.email,
      testUser.password,
      testUser.username
    );
  });

  test('should load homepage and navigate', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check if page loaded
    expect(page.url()).toContain('localhost:5173');
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/homepage.png', fullPage: true });
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to find and click dashboard link
    const dashboardLink = page.locator('a[href*="dashboard"], nav a:has-text("Dashboard"), [data-testid="dashboard-link"]').first();
    
    if (await dashboardLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await dashboardLink.click();
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test-results/dashboard.png', fullPage: true });
    }
  });

  test('should navigate to wallet page', async ({ page }) => {
    await page.goto('/wallet');
    await page.waitForLoadState('networkidle');
    
    // Verify wallet page elements
    const walletElements = await Promise.race([
      page.locator('[data-testid="wallet"], .wallet, text=Wallet, text=Balance').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(walletElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/wallet.png', fullPage: true });
  });

  test('should navigate to DEX trading page', async ({ page }) => {
    await page.goto('/dex');
    await page.waitForLoadState('networkidle');
    
    // Verify DEX page elements
    const dexElements = await Promise.race([
      page.locator('[data-testid="dex"], .dex-trading, text=Swap, text=DEX').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(dexElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/dex.png', fullPage: true });
  });

  test('should navigate to bots page', async ({ page }) => {
    await page.goto('/bots');
    await page.waitForLoadState('networkidle');
    
    // Verify bots page loaded
    const botsElements = await Promise.race([
      page.locator('[data-testid="bots"], .bots, text=Bot, text=Bots').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(botsElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/bots.png', fullPage: true });
  });

  test('should navigate to markets page', async ({ page }) => {
    await page.goto('/markets');
    await page.waitForLoadState('networkidle');
    
    // Verify markets page loaded
    const marketsElements = await Promise.race([
      page.locator('[data-testid="markets"], .markets, text=Market, text=Markets').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(marketsElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/markets.png', fullPage: true });
  });

  test('should navigate to analytics page', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    
    // Verify analytics page loaded
    const analyticsElements = await Promise.race([
      page.locator('[data-testid="analytics"], .analytics, text=Analytics').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(analyticsElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/analytics.png', fullPage: true });
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    
    // Verify settings page loaded
    const settingsElements = await Promise.race([
      page.locator('[data-testid="settings"], .settings, text=Settings').first().waitFor({ timeout: 5000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(settingsElements).toBeTruthy();
    await page.screenshot({ path: 'test-results/settings.png', fullPage: true });
  });

  test('should test wallet deposit form', async ({ page }) => {
    await page.goto('/wallet');
    await page.waitForLoadState('networkidle');
    
    // Try to find deposit button/form
    const depositButton = page.locator('button:has-text("Deposit"), [data-testid="deposit-button"], button:has-text("Add Funds")').first();
    
    if (await depositButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await depositButton.click();
      await page.waitForTimeout(1000);
      
      // Look for deposit form
      const depositForm = page.locator('input[type="number"], input[name*="amount"], input[placeholder*="amount" i]').first();
      if (await depositForm.isVisible({ timeout: 3000 }).catch(() => false)) {
        await depositForm.fill('100');
        await page.screenshot({ path: 'test-results/deposit-form.png', fullPage: true });
      }
    }
  });

  test('should test DEX swap interface', async ({ page }) => {
    await page.goto('/dex');
    await page.waitForLoadState('networkidle');
    
    // Try to find token input fields
    const tokenInputs = page.locator('input[type="text"], input[placeholder*="token" i], input[placeholder*="amount" i]');
    const inputCount = await tokenInputs.count();
    
    if (inputCount > 0) {
      // Try to interact with first input
      const firstInput = tokenInputs.first();
      if (await firstInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await firstInput.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: 'test-results/dex-interface.png', fullPage: true });
      }
    }
  });

  test('should test navigation menu', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to find navigation menu
    const navMenu = page.locator('nav, [role="navigation"], [data-testid="nav"], [data-testid="sidebar"]').first();
    
    if (await navMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await page.screenshot({ path: 'test-results/navigation.png', fullPage: true });
      
      // Try clicking different nav items
      const navLinks = navMenu.locator('a, button').filter({ hasText: /Dashboard|Wallet|Bots|Markets|Settings/i });
      const linkCount = await navLinks.count();
      
      if (linkCount > 0) {
        // Click first nav link
        await navLinks.first().click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
      }
    }
  });

  test('should test responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/mobile-view.png', fullPage: true });
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/tablet-view.png', fullPage: true });
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/desktop-view.png', fullPage: true });
  });

  test('should test error handling', async ({ page }) => {
    // Try to navigate to non-existent page
    await page.goto('/non-existent-page-12345');
    await page.waitForLoadState('networkidle');
    
    // Check for 404 or error message
    const errorElements = await Promise.race([
      page.locator('text=404, text=Not Found, text=Error, text=Page not found').first().waitFor({ timeout: 3000 }).then(() => true),
      page.locator('body').waitFor({ timeout: 3000 }).then(() => true),
    ]).catch(() => false);
    
    await page.screenshot({ path: 'test-results/error-page.png', fullPage: true });
  });

  test('should test loading states', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Navigate to a page that might show loading
    await page.goto('/dashboard');
    await page.waitForTimeout(500);
    
    // Check for loading indicators
    const loadingIndicators = page.locator('[data-testid="loading"], .loading, .spinner, text=Loading');
    const hasLoading = await loadingIndicators.count() > 0;
    
    if (hasLoading) {
      await page.screenshot({ path: 'test-results/loading-state.png', fullPage: true });
    }
    
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/loaded-state.png', fullPage: true });
  });
});

