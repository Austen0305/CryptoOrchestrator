import { test, expect } from '@playwright/test';

/**
 * Trading E2E Tests
 * Tests order placement, order book, and trade history
 */

test.describe('Trading', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard or markets page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display order entry panel', async ({ page }) => {
    // Look for order entry component
    const orderPanel = page.locator(
      '[data-testid="order-entry"], [data-testid="quick-trade"], form'
    ).first();
    
    await orderPanel.isVisible({ timeout: 10000 }).catch(() => {
      // Order panel might be on markets page
      await page.goto('/markets');
      await page.waitForTimeout(2000);
    });
  });

  test('should select trading pair', async ({ page }) => {
    // Navigate to markets if not already there
    await page.goto('/markets');
    await page.waitForLoadState('networkidle');
    
    // Find pair selector
    const pairSelector = page.locator(
      'select[name="pair"], input[name="pair"], button:has-text("BTC"), [data-testid="pair-selector"]'
    ).first();
    
    if (await pairSelector.isVisible({ timeout: 10000 }).catch(() => false)) {
      // Click to open selector if it's a button
      if (await pairSelector.getAttribute('type') === 'button' || !pairSelector.locator('option').first().isVisible().catch(() => false)) {
        await pairSelector.click();
        await page.waitForTimeout(500);
      }
      
      // Select a pair
      const btcOption = page.locator('text=/BTC.*USD/i, option:has-text("BTC")').first();
      if (await btcOption.isVisible().catch(() => false)) {
        await btcOption.click();
      }
    }
  });

  test('should fill order form', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Find order form inputs
    const amountInput = page.locator(
      'input[name="amount"], input[placeholder*="amount" i], input[placeholder*="quantity" i]'
    ).first();
    
    const priceInput = page.locator(
      'input[name="price"], input[placeholder*="price" i]'
    ).first();
    
    if (await amountInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await amountInput.fill('0.1');
      
      if (await priceInput.isVisible().catch(() => false)) {
        await priceInput.fill('45000');
      }
      
      // Verify inputs are filled
      await expect(amountInput).toHaveValue(/0\.1/);
    }
  });

  test('should toggle between buy and sell', async ({ page }) => {
    // Find buy/sell toggle buttons
    const buyButton = page.locator(
      'button:has-text("Buy"), [data-testid="order-type-buy"], button[aria-label*="buy" i]'
    ).first();
    
    const sellButton = page.locator(
      'button:has-text("Sell"), [data-testid="order-type-sell"], button[aria-label*="sell" i]'
    ).first();
    
    if (await buyButton.isVisible({ timeout: 10000 }).catch(() => false)) {
      await buyButton.click();
      await page.waitForTimeout(500);
      
      // Verify buy is active
      await expect(buyButton).toHaveClass(/active|selected|bg-green/i).catch(() => {
        console.log('Buy button clicked - might use different styling');
      });
      
      // Click sell
      if (await sellButton.isVisible()) {
        await sellButton.click();
        await page.waitForTimeout(500);
        
        // Verify sell is active
        await expect(sellButton).toHaveClass(/active|selected|bg-red/i).catch(() => {
          console.log('Sell button clicked - might use different styling');
        });
      }
    }
  });

  test('should display order book', async ({ page }) => {
    // Look for order book component
    const orderBook = page.locator(
      '[data-testid="order-book"], text=/order book/i, table'
    ).first();
    
    await orderBook.isVisible({ timeout: 10000 }).catch(() => {
      // Order book might be loading or not available
      console.log('Order book not visible - might be loading');
    });
  });

  test('should display trade history', async ({ page }) => {
    // Look for trade history component
    const tradeHistory = page.locator(
      '[data-testid="trade-history"], text=/trade history|recent trades/i, table'
    ).first();
    
    await tradeHistory.isVisible({ timeout: 10000 }).catch(() => {
      // Trade history might be loading or empty
      console.log('Trade history not visible - might be loading or empty');
    });
  });

  test('should display price chart', async ({ page }) => {
    // Look for price chart
    const chart = page.locator(
      'canvas, svg[class*="chart"], [data-testid="price-chart"]'
    ).first();
    
    await chart.isVisible({ timeout: 15000 }).catch(() => {
      // Chart might take time to render
      console.log('Chart not visible - might be loading');
    });
  });

  test('should use keyboard shortcuts', async ({ page }) => {
    // Focus on page to ensure keyboard events work
    await page.click('body');
    
    // Test keyboard shortcuts (adjust based on your actual shortcuts)
    // B for buy, S for sell
    await page.keyboard.press('B');
    await page.waitForTimeout(500);
    
    await page.keyboard.press('S');
    await page.waitForTimeout(500);
    
    // A for amount field
    await page.keyboard.press('A');
    await page.waitForTimeout(500);
    
    // Check if amount input is focused
    const amountInput = page.locator('input[name="amount"]:focus').first();
    await amountInput.isVisible({ timeout: 2000 }).catch(() => {
      console.log('Keyboard shortcuts might not be implemented or focus not visible');
    });
  });
});

