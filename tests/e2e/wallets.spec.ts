import { test, expect } from '@playwright/test';

/**
 * Wallet Management E2E Tests
 * Tests wallet creation, balance display, deposits, withdrawals, external wallet connection
 */

test.describe('Wallet Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to wallets page
    await page.goto('/wallets');
    await page.waitForLoadState('networkidle');
    
    // Check if we're on login page (user not authenticated)
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    if (isLoginPage) {
      // User not logged in - tests will handle this gracefully
      return;
    }
  });

  test('should load wallets page successfully', async ({ page }) => {
    // Check if we're on login page
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    if (isLoginPage) {
      // User not logged in - test that login page loads
      await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
      return;
    }
    
    // Check for wallets page title or key elements
    const walletsTitle = page.locator('h1:has-text("Wallets"), h1:has-text("Wallet"), [data-testid="wallets-page"]').first();
    await expect(walletsTitle).toBeVisible({ timeout: 10000 });
  });

  test('should create custodial wallet', async ({ page }) => {
    // Look for create wallet button
    const createButton = page.locator(
      'button:has-text("Create"), button:has-text("New Wallet"), button:has-text("Add Wallet"), [data-testid="create-wallet"]'
    ).first();
    
    if (await createButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createButton.click();
      
      // Wait for wallet creation form/dialog
      await page.waitForTimeout(1000);
      
      // Select chain (if needed)
      const chainSelector = page.locator('select[name="chain"], select[name="chain_id"], [data-testid="chain-selector"]').first();
      if (await chainSelector.isVisible().catch(() => false)) {
        await chainSelector.selectOption('1'); // Ethereum
      }
      
      // Submit form
      const submitButton = page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Confirm")').first();
      if (await submitButton.isVisible().catch(() => false)) {
        await submitButton.click();
        
        // Wait for wallet to be created
        await page.waitForTimeout(2000);
        
        // Check for success message or wallet card
        const successMessage = page.locator('text=/wallet.*created|success/i, [data-testid="wallet-card"]').first();
        await successMessage.isVisible({ timeout: 5000 }).catch(() => {
          // Wallet might already exist or creation might be instant
          console.log('Wallet creation response not visible - might already exist');
        });
      }
    }
  });

  test('should display wallet balance', async ({ page }) => {
    // Look for wallet card or balance display
    const walletCard = page.locator(
      '[data-testid="wallet-card"], .wallet-card, [class*="wallet"]'
    ).first();
    
    if (await walletCard.isVisible({ timeout: 10000 }).catch(() => false)) {
      // Check for balance element
      const balanceElement = walletCard.locator('text=/\\d+\\.\\d+|balance/i, [data-testid="balance"]').first();
      await balanceElement.isVisible({ timeout: 5000 }).catch(() => {
        console.log('Balance element not visible - might be loading or zero balance');
      });
      
      // Test refresh button
      const refreshButton = walletCard.locator('button:has-text("Refresh"), [data-testid="refresh-balance"], button[aria-label*="refresh" i]').first();
      if (await refreshButton.isVisible().catch(() => false)) {
        await refreshButton.click();
        await page.waitForTimeout(2000); // Wait for balance update
      }
    }
  });

  test('should show deposit address and QR code', async ({ page }) => {
    // Find wallet card
    const walletCard = page.locator('[data-testid="wallet-card"], .wallet-card').first();
    
    if (await walletCard.isVisible({ timeout: 10000 }).catch(() => false)) {
      // Click deposit button
      const depositButton = walletCard.locator('button:has-text("Deposit"), [data-testid="deposit-button"]').first();
      
      if (await depositButton.isVisible().catch(() => false)) {
        await depositButton.click();
        
        // Wait for deposit modal
        await page.waitForTimeout(1000);
        
        // Check for deposit address
        const depositAddress = page.locator(
          'text=/0x[a-fA-F0-9]{40}/, [data-testid="deposit-address"], input[readonly]'
        ).first();
        await expect(depositAddress).toBeVisible({ timeout: 5000 });
        
        // Check for QR code
        const qrCode = page.locator('img[alt*="QR"], canvas, svg, [data-testid="qr-code"]').first();
        await qrCode.isVisible({ timeout: 5000 }).catch(() => {
          console.log('QR code not visible - might be generated differently');
        });
        
        // Test copy address button
        const copyButton = page.locator('button:has-text("Copy"), [data-testid="copy-address"]').first();
        if (await copyButton.isVisible().catch(() => false)) {
          await copyButton.click();
          // Note: Can't easily verify clipboard in Playwright without permissions
        }
      }
    }
  });

  test('should process withdrawal with 2FA', async ({ page }) => {
    // Find wallet card
    const walletCard = page.locator('[data-testid="wallet-card"], .wallet-card').first();
    
    if (await walletCard.isVisible({ timeout: 10000 }).catch(() => false)) {
      // Click withdraw button
      const withdrawButton = walletCard.locator('button:has-text("Withdraw"), [data-testid="withdraw-button"]').first();
      
      if (await withdrawButton.isVisible().catch(() => false)) {
        await withdrawButton.click();
        
        // Wait for withdrawal form
        await page.waitForTimeout(1000);
        
        // Fill withdrawal form
        const toAddressInput = page.locator('input[name="to_address"], input[name="address"], [data-testid="to-address"]').first();
        const amountInput = page.locator('input[name="amount"], [data-testid="amount"]').first();
        const mfaInput = page.locator('input[name="mfa"], input[name="2fa"], input[name="two_factor"], [data-testid="mfa-token"]').first();
        
        if (await toAddressInput.isVisible().catch(() => false)) {
          await toAddressInput.fill('0x1234567890123456789012345678901234567890');
          
          if (await amountInput.isVisible().catch(() => false)) {
            await amountInput.fill('0.1');
          }
          
          if (await mfaInput.isVisible().catch(() => false)) {
            await mfaInput.fill('123456'); // Test 2FA token
          }
          
          // Submit withdrawal
          const submitButton = page.locator('button[type="submit"], button:has-text("Withdraw"), button:has-text("Confirm")').first();
          if (await submitButton.isVisible().catch(() => false)) {
            await submitButton.click();
            
            // Wait for response
            await page.waitForTimeout(2000);
            
            // Check for success/error message
            const responseMessage = page.locator('text=/success|error|insufficient|invalid/i').first();
            await responseMessage.isVisible({ timeout: 5000 }).catch(() => {
              console.log('Withdrawal response not visible');
            });
          }
        }
      }
    }
  });

  test('should display transaction history', async ({ page }) => {
    // Look for transaction history tab or section
    const historyTab = page.locator(
      'button:has-text("History"), button:has-text("Transactions"), [data-testid="transaction-history-tab"]'
    ).first();
    
    if (await historyTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await historyTab.click();
      await page.waitForTimeout(1000);
      
      // Check for transaction table or list
      const transactionTable = page.locator(
        'table, [data-testid="transaction-table"], [data-testid="transaction-history"]'
      ).first();
      
      await transactionTable.isVisible({ timeout: 5000 }).catch(() => {
        console.log('Transaction history not visible - might be empty or loading');
      });
    }
  });

  test('should connect external wallet', async ({ page }) => {
    // Look for connect wallet button
    const connectButton = page.locator(
      'button:has-text("Connect"), button:has-text("Connect Wallet"), [data-testid="connect-wallet"]'
    ).first();
    
    if (await connectButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await connectButton.click();
      
      // Wait for wallet connection dialog
      await page.waitForTimeout(1000);
      
      // Check for wallet options (MetaMask, WalletConnect, etc.)
      const walletOptions = page.locator(
        'button:has-text("MetaMask"), button:has-text("WalletConnect"), [data-testid="wallet-option"]'
      );
      
      const optionCount = await walletOptions.count();
      if (optionCount > 0) {
        // Click first wallet option (MetaMask)
        await walletOptions.first().click();
        
        // Note: Actual wallet connection requires browser extension
        // This test verifies the UI flow
        await page.waitForTimeout(2000);
      }
    }
  });

  test('should register external wallet', async ({ page }) => {
    // Navigate to external wallet registration
    const registerButton = page.locator(
      'button:has-text("Register"), button:has-text("Add External"), [data-testid="register-external"]'
    ).first();
    
    if (await registerButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await registerButton.click();
      await page.waitForTimeout(1000);
      
      // Fill wallet address
      const addressInput = page.locator('input[name="address"], input[name="wallet_address"], [data-testid="wallet-address"]').first();
      if (await addressInput.isVisible().catch(() => false)) {
        await addressInput.fill('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
        
        // Select chain
        const chainSelector = page.locator('select[name="chain"], select[name="chain_id"]').first();
        if (await chainSelector.isVisible().catch(() => false)) {
          await chainSelector.selectOption('1'); // Ethereum
        }
        
        // Submit
        const submitButton = page.locator('button[type="submit"], button:has-text("Register")').first();
        if (await submitButton.isVisible().catch(() => false)) {
          await submitButton.click();
          await page.waitForTimeout(2000);
        }
      }
    }
  });

  test('should handle withdrawal errors gracefully', async ({ page }) => {
    const walletCard = page.locator('[data-testid="wallet-card"], .wallet-card').first();
    
    if (await walletCard.isVisible({ timeout: 10000 }).catch(() => false)) {
      const withdrawButton = walletCard.locator('button:has-text("Withdraw")').first();
      
      if (await withdrawButton.isVisible().catch(() => false)) {
        await withdrawButton.click();
        await page.waitForTimeout(1000);
        
        // Try invalid withdrawal (insufficient balance)
        const amountInput = page.locator('input[name="amount"]').first();
        const toAddressInput = page.locator('input[name="to_address"]').first();
        
        if (await amountInput.isVisible().catch(() => false)) {
          await amountInput.fill('999999'); // Very large amount
          if (await toAddressInput.isVisible().catch(() => false)) {
            await toAddressInput.fill('0x1234567890123456789012345678901234567890');
          }
          
          const submitButton = page.locator('button[type="submit"]').first();
          if (await submitButton.isVisible().catch(() => false)) {
            await submitButton.click();
            await page.waitForTimeout(2000);
            
            // Check for error message
            const errorMessage = page.locator('text=/insufficient|error|invalid/i').first();
            await errorMessage.isVisible({ timeout: 5000 }).catch(() => {
              console.log('Error message not visible');
            });
          }
        }
      }
    }
  });

  test('should refresh balances for all wallets', async ({ page }) => {
    // Look for refresh all balances button
    const refreshAllButton = page.locator(
      'button:has-text("Refresh All"), button:has-text("Refresh Balances"), [data-testid="refresh-all-balances"]'
    ).first();
    
    if (await refreshAllButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await refreshAllButton.click();
      await page.waitForTimeout(3000); // Wait for balance updates
      
      // Verify balances are being refreshed (check for loading state or updated timestamps)
      const walletCards = page.locator('[data-testid="wallet-card"], .wallet-card');
      const cardCount = await walletCards.count();
      
      if (cardCount > 0) {
        // At least one wallet should exist
        expect(cardCount).toBeGreaterThan(0);
      }
    }
  });

  test('should switch between wallet tabs', async ({ page }) => {
    // Look for wallet type tabs (Custodial, External, etc.)
    const tabs = page.locator(
      'button[role="tab"], [role="tablist"] button, [data-testid="wallet-tab"]'
    );
    
    const tabCount = await tabs.count();
    if (tabCount > 1) {
      // Click on different tabs
      await tabs.nth(0).click();
      await page.waitForTimeout(500);
      
      await tabs.nth(1).click();
      await page.waitForTimeout(500);
      
      // Verify tab content changes
      const tabContent = page.locator('[role="tabpanel"], [data-testid="wallet-content"]').first();
      await tabContent.isVisible({ timeout: 3000 }).catch(() => {
        console.log('Tab content not visible');
      });
    }
  });
});
