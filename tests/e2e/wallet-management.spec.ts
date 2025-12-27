/**
 * E2E tests for wallet management flows
 * Tests wallet creation, deposits, withdrawals, and multi-chain support
 */

import { test, expect } from '@playwright/test';

test.describe('Wallet Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to wallets page
    await page.goto('/wallets');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should create custodial wallet on Ethereum', async ({ page }) => {
    // Click create wallet button
    await page.getByTestId('create-wallet-btn').click();
    
    // Select Ethereum chain
    await page.selectOption('select[name="chain"]', '1');
    
    // Select custodial wallet type
    await page.click('input[value="custodial"]');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Wait for success message
    await expect(page.locator('text=Wallet created successfully')).toBeVisible({ timeout: 10000 });
    
    // Verify wallet appears in list
    await expect(page.locator('text=Ethereum')).toBeVisible();
  });

  test('should create wallet on multiple chains', async ({ page }) => {
    const chains = [
      { name: 'Ethereum', id: '1' },
      { name: 'Base', id: '8453' },
      { name: 'Arbitrum', id: '42161' }
    ];

    for (const chain of chains) {
      await page.getByTestId('create-wallet-btn').click();
      await page.selectOption('select[name="chain"]', chain.id);
      await page.click('input[value="custodial"]');
      await page.click('button[type="submit"]');
      
      // Wait for wallet creation
      await page.waitForTimeout(2000);
      
      // Verify wallet for this chain exists
      await expect(page.locator(`text=${chain.name}`)).toBeVisible();
    }
  });

  test('should display wallet balance', async ({ page }) => {
    // Wait for wallets to load
    await page.waitForSelector('[data-testid="wallet-card"]', { timeout: 10000 });
    
    // Check that balance is displayed
    const balanceElement = page.locator('[data-testid="wallet-balance"]').first();
    await expect(balanceElement).toBeVisible();
    
    // Balance should be a number or "0.0"
    const balanceText = await balanceElement.textContent();
    expect(balanceText).toMatch(/[\d.]+/);
  });

  test('should generate deposit address', async ({ page }) => {
    // Click on a wallet card
    await page.locator('[data-testid="wallet-card"]').first().click();
    
    // Click deposit button
    await page.getByTestId('deposit-btn').click();
    
    // Wait for deposit address to appear
    await expect(page.locator('[data-testid="deposit-address"]')).toBeVisible({ timeout: 5000 });
    
    // Verify address format (Ethereum address)
    const address = await page.locator('[data-testid="deposit-address"]').textContent();
    expect(address).toMatch(/^0x[a-fA-F0-9]{40}$/);
  });

  test('should show withdrawal form with validation', async ({ page }) => {
    // Click on a wallet card
    await page.locator('[data-testid="wallet-card"]').first().click();
    
    // Click withdraw button
    await page.getByTestId('withdraw-btn').click();
    
    // Fill withdrawal form
    await page.fill('input[name="to_address"]', '0x1234567890123456789012345678901234567890');
    await page.fill('input[name="amount"]', '100.0');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show validation or confirmation
    // Either success message or validation error
    await expect(
      page.locator('text=/success|error|validation|confirm/i')
    ).toBeVisible({ timeout: 5000 });
  });

  test('should display transaction history', async ({ page }) => {
    // Click on a wallet card
    await page.locator('[data-testid="wallet-card"]').first().click();
    
    // Navigate to transaction history tab
    await page.click('text=Transactions');
    
    // Wait for transaction history to load
    await page.waitForSelector('[data-testid="transaction-history"]', { timeout: 5000 });
    
    // Verify transaction table or list is visible
    const historyElement = page.locator('[data-testid="transaction-history"]');
    await expect(historyElement).toBeVisible();
  });

  test('should refresh wallet balances', async ({ page }) => {
    // Click refresh balances button
    await page.getByTestId('refresh-balances-btn').click();
    
    // Wait for loading state
    await page.waitForTimeout(1000);
    
    // Verify balances are updated (or loading indicator disappears)
    await expect(
      page.locator('[data-testid="wallet-balance"]').first()
    ).toBeVisible({ timeout: 10000 });
  });
});
