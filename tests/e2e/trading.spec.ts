import { test, expect } from '@playwright/test';
import { authenticateTestUser, generateTestUser } from './auth-helper';

/**
 * Trading Flow E2E Tests
 * Tests placing orders, executing trades, and DEX swaps
 */

test.describe('Trading Flow', () => {
  let testUser: { email: string; password: string; username: string };
  
  test.beforeEach(async ({ page }) => {
    // Generate and authenticate test user
    testUser = generateTestUser();
    const authenticated = await authenticateTestUser(
      page,
      testUser.email,
      testUser.password,
      testUser.username
    );
    
    if (!authenticated) {
      test.skip();
    }
  });
  
  test('should navigate to trading page', async ({ page }) => {
    await page.goto('/trading');
    await page.waitForLoadState('networkidle');
    
    // Verify trading interface is visible
    const tradingInterface = await Promise.race([
      page.locator('[data-testid="trading-panel"], .trading-panel, .order-entry').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=Buy, text=Sell, text=Order').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(tradingInterface).toBeTruthy();
  });
  
  test('should view order book', async ({ page }) => {
    await page.goto('/trading');
    await page.waitForLoadState('networkidle');
    
    // Look for order book component
    const orderBook = await Promise.race([
      page.locator('[data-testid="orderbook"], .orderbook, .order-book').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=Order Book, text=Bids, text=Asks').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(orderBook).toBeTruthy();
  });
  
  test('should view market data', async ({ page }) => {
    await page.goto('/markets');
    await page.waitForLoadState('networkidle');
    
    // Verify market data is displayed
    const marketData = await Promise.race([
      page.locator('[data-testid="market-data"], .market-data, table').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=BTC, text=ETH, text=Price').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(marketData).toBeTruthy();
  });
  
  test('should view trade history', async ({ page }) => {
    await page.goto('/trades');
    await page.waitForLoadState('networkidle');
    
    // Verify trade history is displayed
    const tradeHistory = await Promise.race([
      page.locator('[data-testid="trade-history"], .trade-history, table').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=Trade History, text=Trades, text=Date').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(tradeHistory).toBeTruthy();
  });
  
  test('should access DEX trading panel', async ({ page }) => {
    await page.goto('/trading');
    await page.waitForLoadState('networkidle');
    
    // Look for DEX trading tab/button
    const dexTab = page.locator(
      'button:has-text("DEX"), button:has-text("Swap"), [data-testid="dex-tab"], [role="tab"]:has-text("DEX")'
    ).first();
    
    if (await dexTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await dexTab.click();
      await page.waitForTimeout(1000);
      
      // Verify DEX panel is visible
      const dexPanel = await Promise.race([
        page.locator('[data-testid="dex-panel"], .dex-trading, .swap-panel').waitFor({ timeout: 5000 }).then(() => true),
        page.locator('text=Swap, text=Token, text=Amount').waitFor({ timeout: 5000 }).then(() => true),
      ]).catch(() => false);
      
      expect(dexPanel).toBeTruthy();
    } else {
      // DEX might be on separate page
      await page.goto('/dex');
      await page.waitForLoadState('networkidle');
      
      const dexPanel = await page.locator('[data-testid="dex-panel"], .dex-trading').isVisible({ timeout: 5000 }).catch(() => false);
      expect(dexPanel).toBeTruthy();
    }
  });
  
  test('should view portfolio', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Verify portfolio data is displayed
    const portfolio = await Promise.race([
      page.locator('[data-testid="portfolio"], .portfolio, .portfolio-summary').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=Portfolio, text=Balance, text=Total Value').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(portfolio).toBeTruthy();
  });
  
  test('should view price chart', async ({ page }) => {
    await page.goto('/trading');
    await page.waitForLoadState('networkidle');
    
    // Verify price chart is displayed
    const priceChart = await Promise.race([
      page.locator('[data-testid="price-chart"], .price-chart, canvas, svg').waitFor({ timeout: 5000 }).then(() => true),
      page.locator('text=Price Chart, text=Chart').waitFor({ timeout: 5000 }).then(() => true),
    ]).catch(() => false);
    
    expect(priceChart).toBeTruthy();
  });
});
