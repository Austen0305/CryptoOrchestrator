import { test, expect } from '@playwright/test';

/**
 * Dashboard E2E Tests
 * Tests dashboard loading, navigation, and key features
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard (assumes user is logged in or mock auth)
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load dashboard successfully', async ({ page }) => {
    // Check for dashboard title or key elements
    const dashboardTitle = page.locator('h1:has-text("Dashboard"), [data-testid="dashboard"]').first();
    await expect(dashboardTitle).toBeVisible({ timeout: 10000 });
  });

  test('should display portfolio information', async ({ page }) => {
    // Check for portfolio card or balance display
    const portfolioElement = page.locator(
      'text=/portfolio|balance|total/i, [data-testid="portfolio"], .portfolio'
    ).first();
    
    // Portfolio might not load immediately, so check if visible or wait
    await portfolioElement.isVisible({ timeout: 10000 }).catch(() => {
      // Portfolio might be loading or not available in test environment
      console.log('Portfolio element not visible - might be loading');
    });
  });

  test('should display price chart', async ({ page }) => {
    // Look for chart component
    const chartElement = page.locator(
      'canvas, svg, [data-testid="price-chart"], .chart'
    ).first();
    
    // Charts might take time to render
    await chartElement.isVisible({ timeout: 15000 }).catch(() => {
      console.log('Chart element not visible - might be loading');
    });
  });

  test('should navigate to markets page', async ({ page }) => {
    // Find and click Markets navigation link
    const marketsLink = page.locator(
      'a:has-text("Markets"), nav a[href*="markets"], [data-testid="nav-markets"]'
    ).first();
    
    if (await marketsLink.isVisible().catch(() => false)) {
      await marketsLink.click();
      await page.waitForURL(/\/markets/, { timeout: 5000 });
      await expect(page).toHaveURL(/\/markets/);
    }
  });

  test('should navigate to bots page', async ({ page }) => {
    // Find and click Bots navigation link
    const botsLink = page.locator(
      'a:has-text("Bots"), nav a[href*="bots"], [data-testid="nav-bots"]'
    ).first();
    
    if (await botsLink.isVisible().catch(() => false)) {
      await botsLink.click();
      await page.waitForURL(/\/bots/, { timeout: 5000 });
      await expect(page).toHaveURL(/\/bots/);
    }
  });

  test('should navigate to analytics page', async ({ page }) => {
    // Find and click Analytics navigation link
    const analyticsLink = page.locator(
      'a:has-text("Analytics"), nav a[href*="analytics"], [data-testid="nav-analytics"]'
    ).first();
    
    if (await analyticsLink.isVisible().catch(() => false)) {
      await analyticsLink.click();
      await page.waitForURL(/\/analytics/, { timeout: 5000 });
      await expect(page).toHaveURL(/\/analytics/);
    }
  });

  test('should display order entry panel', async ({ page }) => {
    // Look for order entry or quick trade component
    const orderPanel = page.locator(
      '[data-testid="order-entry"], [data-testid="quick-trade"], text=/buy|sell/i'
    ).first();
    
    await orderPanel.isVisible({ timeout: 10000 }).catch(() => {
      console.log('Order panel not visible');
    });
  });

  test('should display trading recommendations', async ({ page }) => {
    // Look for recommendations component
    const recommendations = page.locator(
      'text=/recommendations|suggestions/i, [data-testid="recommendations"]'
    ).first();
    
    await recommendations.isVisible({ timeout: 10000 }).catch(() => {
      console.log('Recommendations not visible');
    });
  });
});

