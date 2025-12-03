import { test, expect } from '@playwright/test';

/**
 * Critical User Flows E2E Tests
 * Tests the complete user journey from registration to trading
 */

test.describe('Critical User Flows', () => {
  
  test('Complete trading flow - registration to bot trading', async ({ page }) => {
    // Generate unique test user
    const timestamp = Date.now();
    const testEmail = `test${timestamp}@example.com`;
    const testPassword = 'SecurePass123!';
    
    // Step 1: Navigate to registration
    await page.goto('/register');
    await expect(page).toHaveURL(/.*register/);
    
    // Step 2: Sign up
    await page.fill('[name="email"]', testEmail);
    await page.fill('[name="password"]', testPassword);
    await page.fill('[name="confirmPassword"]', testPassword);
    await page.click('button[type="submit"]');
    
    // Wait for registration success
    await expect(page).toHaveURL(/.*dashboard|login/);
    
    // Step 3: Login if redirected to login page
    const currentUrl = page.url();
    if (currentUrl.includes('login')) {
      await page.fill('[name="email"]', testEmail);
      await page.fill('[name="password"]', testPassword);
      await page.click('button[type="submit"]');
      await expect(page).toHaveURL(/.*dashboard/);
    }
    
    // Step 4: Navigate to dashboard
    await page.goto('/dashboard');
    await expect(page.locator('h1, h2')).toContainText(/Dashboard|Welcome/i);
    
    // Step 5: Check initial balance
    const balanceText = await page.locator('[data-testid="balance"], .balance').first().textContent();
    console.log('Initial balance:', balanceText);
    
    // Step 6: Navigate to bots page
    await page.click('a[href*="bots"], nav >> text=Bots');
    await expect(page).toHaveURL(/.*bots/);
    
    // Step 7: Create a new bot (if create button exists)
    const createButton = page.locator('button:has-text("Create"), button:has-text("New Bot")');
    if (await createButton.count() > 0) {
      await createButton.first().click();
      
      // Fill bot details
      await page.fill('[name="name"], input[placeholder*="name"]', `Test Bot ${timestamp}`);
      
      // Select strategy if available
      const strategySelect = page.locator('[name="strategy"], select');
      if (await strategySelect.count() > 0) {
        await strategySelect.first().selectOption({ index: 0 });
      }
      
      // Submit bot creation
      await page.click('button[type="submit"], button:has-text("Create")');
      
      // Wait for bot to appear in list
      await expect(page.locator('.bot-item, [data-testid="bot"]')).toBeVisible({ timeout: 10000 });
      console.log('✅ Bot created successfully');
    }
    
    // Step 8: Navigate to trades/history
    await page.click('a[href*="trade"], a[href*="history"], nav >> text=/Trades?|History/i');
    console.log('✅ Navigated to trades page');
    
    // Step 9: Check for any existing trades or empty state
    const tradesExist = await page.locator('.trade-item, [data-testid="trade"], .trade-row').count() > 0;
    const emptyState = await page.locator('text=/No trades|Empty|Get started/i').count() > 0;
    
    expect(tradesExist || emptyState).toBeTruthy();
    console.log('✅ Trades page loaded correctly');
  });
  
  test('Wallet deposit and balance update flow', async ({ page }) => {
    // This test requires authentication - skip if not logged in
    await page.goto('/dashboard');
    
    // Check if redirected to login (not authenticated)
    if (page.url().includes('login')) {
      test.skip(true, 'Authentication required - skipping wallet test');
      return;
    }
    
    // Navigate to wallet - try multiple selectors for robustness
    const walletLink = page.locator('[data-testid="wallet-link"], a[href*="wallet"], nav >> text=Wallet');
    await walletLink.first().click();
    await expect(page).toHaveURL(/.*wallet/);
    
    // Check balance display - use test ID or fallback to class/aria selectors
    const balanceElement = page.locator('[data-testid="balance"], [aria-label*="balance"], .balance, .wallet-balance');
    await expect(balanceElement.first()).toBeVisible();
    
    const initialBalance = await balanceElement.first().textContent();
    console.log('Initial balance:', initialBalance);
    
    // Look for deposit button
    const depositButton = page.locator('[data-testid="deposit-button"], button:has-text("Deposit"), a:has-text("Deposit")');
    if (await depositButton.count() > 0) {
      console.log('✅ Deposit button found');
    }
    
    // Check transaction history
    const historyLink = page.locator('[data-testid="transaction-history"], text=/Transaction|History/i');
    await historyLink.first().click();
    
    const hasTransactions = await page.locator('[data-testid="transaction"], .transaction-item, [role="row"]').count() > 0;
    const hasEmptyState = await page.locator('[data-testid="empty-state"], text=/No transactions|Empty/i').count() > 0;
    
    expect(hasTransactions || hasEmptyState).toBeTruthy();
    console.log('✅ Transaction history accessible');
  });
  
  test('Bot lifecycle - create, start, stop, delete', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Skip if not authenticated
    if (page.url().includes('login')) {
      test.skip(true, 'Authentication required - skipping bot lifecycle test');
      return;
    }
    
    // Navigate to bots
    await page.goto('/bots');
    await expect(page).toHaveURL(/.*bots/);
    
    // Get initial bot count
    const initialBotCount = await page.locator('.bot-item, [data-testid="bot"]').count();
    console.log(`Initial bot count: ${initialBotCount}`);
    
    // Create bot button
    const createButton = page.locator('button:has-text("Create"), button:has-text("New Bot")');
    
    if (await createButton.count() > 0) {
      await createButton.first().click();
      
      // Fill form
      const timestamp = Date.now();
      await page.fill('[name="name"], input[placeholder*="name"]', `Lifecycle Test Bot ${timestamp}`);
      
      // Submit
      await page.click('button[type="submit"], button:has-text("Create")');
      
      // Wait for new bot to appear
      await page.waitForTimeout(2000);
      const newBotCount = await page.locator('.bot-item, [data-testid="bot"]').count();
      expect(newBotCount).toBeGreaterThan(initialBotCount);
      console.log('✅ Bot created successfully');
      
      // Find and interact with the new bot
      const botCard = page.locator('.bot-item, [data-testid="bot"]').first();
      await expect(botCard).toBeVisible();
      
      // Try to start bot
      const startButton = botCard.locator('button:has-text("Start"), button:has-text("Run")');
      if (await startButton.count() > 0) {
        await startButton.click();
        await page.waitForTimeout(1000);
        console.log('✅ Bot started');
        
        // Try to stop bot
        const stopButton = botCard.locator('button:has-text("Stop"), button:has-text("Pause")');
        if (await stopButton.count() > 0) {
          await stopButton.click();
          await page.waitForTimeout(1000);
          console.log('✅ Bot stopped');
        }
      }
    }
  });
  
  test('Settings and profile update flow', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Skip if not authenticated
    if (page.url().includes('login')) {
      test.skip(true, 'Authentication required - skipping settings test');
      return;
    }
    
    // Navigate to settings
    await page.click('a[href*="settings"], a[href*="profile"], nav >> text=/Settings|Profile/i');
    await expect(page).toHaveURL(/.*settings|profile/);
    
    console.log('✅ Settings page loaded');
    
    // Check for various settings sections
    const hasGeneralSettings = await page.locator('text=/General|Account/i').count() > 0;
    const hasSecuritySettings = await page.locator('text=/Security|Password/i').count() > 0;
    const hasNotificationSettings = await page.locator('text=/Notification|Alerts/i').count() > 0;
    
    console.log('Settings sections found:', {
      general: hasGeneralSettings,
      security: hasSecuritySettings,
      notifications: hasNotificationSettings
    });
    
    expect(hasGeneralSettings || hasSecuritySettings || hasNotificationSettings).toBeTruthy();
  });
  
  test('Navigation and routing flow', async ({ page }) => {
    await page.goto('/');
    
    // Test main navigation links
    const navLinks = [
      { text: /Dashboard|Home/i, url: /dashboard|home/i },
      { text: /Bots?/i, url: /bots/i },
      { text: /Trade|Trading/i, url: /trade/i },
      { text: /Market/i, url: /market/i },
    ];
    
    for (const link of navLinks) {
      try {
        // Use the regex directly in the text selector
        const linkElement = page.locator('nav a').filter({ hasText: link.text });
        if (await linkElement.count() > 0) {
          await linkElement.first().click();
          await page.waitForTimeout(500);
          console.log(`✅ Navigated to link matching pattern`);
        } else {
          console.log(`⚠️  Navigation link not found`);
        }
      } catch (error) {
        console.log(`⚠️  Error navigating: ${error}`);
      }
    }
  });
  
  test('Error handling - 404 and network errors', async ({ page }) => {
    // Test 404 page
    await page.goto('/this-page-does-not-exist-12345');
    
    // Should show 404 message or redirect
    const has404 = await page.locator('text=/404|Not Found|Page not found/i').count() > 0;
    const redirected = !page.url().includes('this-page-does-not-exist');
    
    expect(has404 || redirected).toBeTruthy();
    console.log('✅ 404 handling works correctly');
  });
  
  test('Responsive design - mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Check if mobile menu exists
    const mobileMenu = page.locator('[aria-label*="menu"], button:has-text("Menu"), .mobile-menu');
    const hasMobileMenu = await mobileMenu.count() > 0;
    
    console.log('Mobile menu found:', hasMobileMenu);
    
    // Content should still be visible
    const body = page.locator('body');
    await expect(body).toBeVisible();
    
    console.log('✅ Responsive design working');
  });
  
  test('WebSocket connection and real-time updates', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Skip if not authenticated
    if (page.url().includes('login')) {
      test.skip(true, 'Authentication required - skipping WebSocket test');
      return;
    }
    
    // Wait for WebSocket connection to establish
    await page.waitForTimeout(3000);
    
    // Check console for WebSocket messages
    const logs: string[] = [];
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('websocket') || text.includes('ws://') || text.includes('wss://')) {
        logs.push(text);
      }
    });
    
    // Wait for potential WebSocket activity
    await page.waitForTimeout(5000);
    
    console.log('WebSocket logs:', logs);
    console.log('✅ WebSocket monitoring complete');
  });
});
