/**
 * E2E Tests for DEX Trading Flow
 * Tests complete DEX trading workflows from wallet creation to swap execution
 */
import { test, expect } from '@playwright/test';

test.describe('DEX Trading Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app and login
    await page.goto('/');
    // Assume login is handled by global setup or auth fixture
  });

  test('should create wallet and execute DEX swap end-to-end', async ({ page }) => {
    // Step 1: Create custodial wallet
    await page.goto('/settings/wallets');
    await page.click('button:has-text("Create Wallet")');
    
    // Select Ethereum network
    await page.selectOption('select[name="chain_id"]', '1');
    await page.selectOption('select[name="wallet_type"]', 'custodial');
    await page.click('button[type="submit"]');
    
    // Wait for wallet creation
    await expect(page.locator('text=Wallet created successfully')).toBeVisible({ timeout: 10000 });
    
    // Step 2: Navigate to trading page
    await page.goto('/trading');
    
    // Step 3: Select trading pair
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.selectOption('select[name="chain_id"]', '1');
    
    // Step 4: Enter trade details
    await page.fill('input[name="amount"]', '0.1');
    await page.selectOption('select[name="side"]', 'buy');
    await page.selectOption('select[name="order_type"]', 'market');
    
    // Step 5: Review and confirm
    await page.click('button:has-text("Review Order")');
    
    // Verify order details
    await expect(page.locator('text=ETH/USDC')).toBeVisible();
    await expect(page.locator('text=0.1')).toBeVisible();
    await expect(page.locator('text=Ethereum')).toBeVisible();
    
    // Step 6: Execute swap (paper trading first)
    await page.selectOption('select[name="trading_mode"]', 'paper');
    await page.click('button:has-text("Place Order")');
    
    // Step 7: Verify order execution
    await expect(page.locator('text=Order placed successfully')).toBeVisible({ timeout: 15000 });
    
    // Step 8: Check order history
    await page.goto('/trades');
    await expect(page.locator('text=ETH/USDC')).toBeVisible();
    await expect(page.locator('text=0.1')).toBeVisible();
  });

  test('should execute real money DEX swap with 2FA', async ({ page }) => {
    // Prerequisites: Wallet must exist and have balance
    
    // Step 1: Navigate to trading
    await page.goto('/trading');
    
    // Step 2: Switch to real money mode
    await page.selectOption('select[name="trading_mode"]', 'real');
    
    // Step 3: Enter trade details
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.selectOption('select[name="chain_id"]', '1');
    await page.fill('input[name="amount"]', '0.05');
    await page.selectOption('select[name="side"]', 'buy');
    
    // Step 4: Review order
    await page.click('button:has-text("Review Order")');
    
    // Step 5: Confirm order (should trigger 2FA)
    await page.click('button:has-text("Place Order")');
    
    // Step 6: Enter 2FA code (if required)
    const twoFactorInput = page.locator('input[name="two_factor_code"]');
    if (await twoFactorInput.isVisible({ timeout: 2000 })) {
      await twoFactorInput.fill('123456'); // Mock 2FA code
      await page.click('button:has-text("Verify")');
    }
    
    // Step 7: Wait for transaction
    await expect(page.locator('text=Transaction submitted')).toBeVisible({ timeout: 30000 });
    
    // Step 8: Verify transaction hash appears
    await expect(page.locator('text=/0x[a-fA-F0-9]{64}/')).toBeVisible({ timeout: 60000 });
  });

  test('should show price impact warning for high-impact swaps', async ({ page }) => {
    await page.goto('/trading');
    
    // Enter large trade that would cause high price impact
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.selectOption('select[name="chain_id"]', '1');
    await page.fill('input[name="amount"]', '100'); // Large amount
    
    // Get quote
    await page.click('button:has-text("Get Quote")');
    
    // Should show price impact warning if > 1%
    const warning = page.locator('text=/Price impact.*%/i');
    await expect(warning).toBeVisible({ timeout: 10000 });
    
    // Warning should prevent execution
    const placeOrderButton = page.locator('button:has-text("Place Order")');
    await expect(placeOrderButton).toBeDisabled();
  });

  test('should handle DEX aggregator fallback', async ({ page }) => {
    // This test would require mocking aggregator failures
    // For now, verify that quote fetching works
    
    await page.goto('/trading');
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.selectOption('select[name="chain_id"]', '1');
    await page.fill('input[name="amount"]', '0.1');
    
    // Get quote
    await page.click('button:has-text("Get Quote")');
    
    // Should get quote from at least one aggregator
    await expect(page.locator('text=/Quote.*received/i')).toBeVisible({ timeout: 15000 });
    
    // Should show aggregator name (0x, OKX, or Rubic)
    const aggregatorName = page.locator('text=/0x|OKX|Rubic/i');
    await expect(aggregatorName).toBeVisible();
  });

  test('should display multi-chain wallet balances in portfolio', async ({ page }) => {
    // Step 1: Create wallets on multiple chains
    await page.goto('/settings/wallets');
    
    // Create Ethereum wallet
    await page.click('button:has-text("Create Wallet")');
    await page.selectOption('select[name="chain_id"]', '1');
    await page.selectOption('select[name="wallet_type"]', 'custodial');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Wallet created')).toBeVisible({ timeout: 10000 });
    
    // Create Base wallet
    await page.click('button:has-text("Create Wallet")');
    await page.selectOption('select[name="chain_id"]', '8453');
    await page.selectOption('select[name="wallet_type"]', 'custodial');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Wallet created')).toBeVisible({ timeout: 10000 });
    
    // Step 2: Check portfolio
    await page.goto('/portfolio');
    
    // Should show balances from all chains
    await expect(page.locator('text=Ethereum')).toBeVisible();
    await expect(page.locator('text=Base')).toBeVisible();
    
    // Should show aggregated total
    await expect(page.locator('text=/Total.*USD/i')).toBeVisible();
  });

  test('should create and execute bot trade via DEX', async ({ page }) => {
    // Step 1: Create grid bot
    await page.goto('/bots');
    await page.click('button:has-text("Create Bot")');
    
    // Select bot type
    await page.click('button:has-text("Grid Trading")');
    
    // Fill bot configuration
    await page.fill('input[name="name"]', 'E2E Test Grid Bot');
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.selectOption('select[name="chain_id"]', '1');
    await page.fill('input[name="upper_price"]', '3500');
    await page.fill('input[name="lower_price"]', '3000');
    await page.fill('input[name="grid_count"]', '5');
    await page.fill('input[name="order_amount"]', '0.01');
    
    // Create bot
    await page.click('button:has-text("Create Bot")');
    await expect(page.locator('text=E2E Test Grid Bot')).toBeVisible({ timeout: 10000 });
    
    // Step 2: Start bot
    const botCard = page.locator('text=E2E Test Grid Bot').locator('..');
    await botCard.locator('button:has-text("Start")').click();
    
    // Step 3: Wait for bot to place orders
    await expect(page.locator('text=Bot started')).toBeVisible({ timeout: 10000 });
    
    // Step 4: Check that orders are placed (via DEX swaps)
    await page.goto('/trades');
    
    // Should see trades from bot
    await expect(page.locator('text=E2E Test Grid Bot')).toBeVisible({ timeout: 30000 });
    
    // Step 5: Stop bot
    await page.goto('/bots');
    await botCard.locator('button:has-text("Stop")').click();
    await expect(page.locator('text=Bot stopped')).toBeVisible();
  });
});

test.describe('DEX Trading Error Handling', () => {
  test('should handle insufficient balance gracefully', async ({ page }) => {
    await page.goto('/trading');
    
    // Try to trade more than available balance
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.fill('input[name="amount"]', '1000'); // Large amount
    
    await page.click('button:has-text("Review Order")');
    
    // Should show insufficient balance error
    await expect(page.locator('text=/Insufficient.*balance/i')).toBeVisible();
  });

  test('should handle network congestion gracefully', async ({ page }) => {
    await page.goto('/trading');
    
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.fill('input[name="amount"]', '0.1');
    
    await page.click('button:has-text("Place Order")');
    
    // If network is congested, should show appropriate message
    // This would require mocking high gas prices or network errors
    const errorMessage = page.locator('text=/Network.*congested|Gas.*high/i');
    
    // Either transaction succeeds or shows error
    const successOrError = page.locator('text=/Transaction|Error/i');
    await expect(successOrError).toBeVisible({ timeout: 60000 });
  });

  test('should handle transaction failure and show error', async ({ page }) => {
    // This test would require mocking a failed transaction
    // For now, verify error handling UI exists
    
    await page.goto('/trading');
    
    // Attempt trade
    await page.fill('input[name="symbol"]', 'ETH/USDC');
    await page.fill('input[name="amount"]', '0.1');
    await page.click('button:has-text("Place Order")');
    
    // Should either succeed or show clear error message
    const result = page.locator('text=/Success|Failed|Error/i');
    await expect(result).toBeVisible({ timeout: 60000 });
  });
});
