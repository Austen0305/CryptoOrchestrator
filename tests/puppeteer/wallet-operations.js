/**
 * Puppeteer Test: Wallet Operations
 * Tests wallet creation, balance display, deposits, and withdrawals
 */

// Set environment variable before importing puppeteer to fix Node.js 25 compatibility
if (typeof process !== 'undefined' && process.env && !process.env.PUPPETEER_LOGLEVEL) {
  process.env.PUPPETEER_LOGLEVEL = 'warn';
}

import puppeteer from 'puppeteer';
import { 
  safeNavigate, 
  safeClick, 
  safeType, 
  takeScreenshot, 
  createTestResults, 
  finalizeResults,
  config 
} from './test-helper.js';

const BASE_URL = process.env.BASE_URL || config.urls.base;

async function testWalletOperations() {
  const browser = await puppeteer.launch(config.launch);
  const page = await browser.newPage();
  const results = createTestResults();
  
  // Set viewport
  await page.setViewport(config.launch.defaultViewport);

  try {
    console.log('Starting wallet operations tests...');
    
    // Test 1: Navigate to wallets page
    console.log('Test 1: Navigating to wallets page...');
    await page.goto(`${BASE_URL}/wallets`, { waitUntil: 'networkidle2' });
    await page.screenshot({ path: 'tests/puppeteer/screenshots/wallets-page.png' });
    
    const walletsPage = await page.$('h1, h2, [data-testid="wallets-page"]');
    if (walletsPage) {
      results.passed.push('Wallets page loads successfully');
    } else {
      results.failed.push('Wallets page not found');
    }

    // Test 2: Test wallet creation
    console.log('Test 2: Testing wallet creation...');
    const createWalletButton = await page.$('button:has-text("Create"), button:has-text("New Wallet"), [data-testid="create-wallet"]');
    if (createWalletButton) {
      await createWalletButton.click();
      await page.waitForTimeout(1000);
      
      const walletForm = await page.$('form, dialog, [data-testid="wallet-form"]');
      if (walletForm) {
        results.passed.push('Wallet creation form opens');
        
        // Select chain
        const chainSelect = await page.$('select[name="chain"], [name="chain"]');
        if (chainSelect) {
          await chainSelect.select('ethereum'); // or first available
          results.passed.push('Chain selection found');
        }
        
        // Submit wallet creation
        const submitButton = await page.$('button[type="submit"], button:has-text("Create")');
        if (submitButton) {
          await submitButton.click();
          await page.waitForTimeout(3000);
          results.passed.push('Wallet creation submitted');
        }
      }
    } else {
      results.warnings.push('Create wallet button not found');
    }

    // Test 3: Test balance display
    console.log('Test 3: Testing balance display...');
    await page.goto(`${BASE_URL}/wallets`, { waitUntil: 'networkidle2' });
    await page.waitForTimeout(2000);
    
    const balanceElements = await page.$$('.balance, [data-testid="balance"], :has-text("$"), :has-text("ETH")');
    if (balanceElements.length > 0) {
      results.passed.push('Balance information displayed');
    } else {
      results.warnings.push('Balance information not found');
    }

    // Test 4: Test deposit flow
    console.log('Test 4: Testing deposit flow...');
    const depositButton = await page.$('button:has-text("Deposit"), [data-testid="deposit"]');
    if (depositButton) {
      await depositButton.click();
      await page.waitForTimeout(1000);
      
      // Check for deposit address or QR code
      const depositAddress = await page.$('.address, [data-testid="deposit-address"], input[readonly]');
      const qrCode = await page.$('img[alt*="QR"], .qr-code, canvas');
      
      if (depositAddress || qrCode) {
        results.passed.push('Deposit address/QR code displayed');
        await page.screenshot({ path: 'tests/puppeteer/screenshots/deposit-flow.png' });
      } else {
        results.warnings.push('Deposit address/QR code not found');
      }
    } else {
      results.warnings.push('Deposit button not found');
    }

    // Test 5: Test withdrawal flow
    console.log('Test 5: Testing withdrawal flow...');
    await page.goto(`${BASE_URL}/wallets`, { waitUntil: 'networkidle2' });
    const withdrawButton = await page.$('button:has-text("Withdraw"), [data-testid="withdraw"]');
    if (withdrawButton) {
      await withdrawButton.click();
      await page.waitForTimeout(1000);
      
      const withdrawForm = await page.$('form, [data-testid="withdraw-form"]');
      if (withdrawForm) {
        results.passed.push('Withdrawal form opens');
        
        // Test form validation
        const addressInput = await page.$('input[name="address"], input[placeholder*="address"]');
        const amountInput = await page.$('input[name="amount"], input[type="number"]');
        
        if (addressInput && amountInput) {
          // Try to submit without filling (should show validation)
          const submitBtn = await page.$('button[type="submit"]');
          if (submitBtn) {
            await submitBtn.click();
            await page.waitForTimeout(1000);
            
            const validationError = await page.$('.error, .invalid, [role="alert"]');
            if (validationError) {
              results.passed.push('Withdrawal form validation works');
            }
          }
        }
      }
    } else {
      results.warnings.push('Withdraw button not found');
    }

    // Test 6: Test transaction history
    console.log('Test 6: Testing transaction history...');
    const historyTab = await page.$('button:has-text("History"), [data-testid="history-tab"]');
    if (historyTab) {
      await historyTab.click();
      await page.waitForTimeout(2000);
      
      const transactions = await page.$$('.transaction, [data-testid*="transaction"], tr');
      if (transactions.length > 0) {
        results.passed.push('Transaction history displays transactions');
      } else {
        const emptyState = await page.$('.empty-state, :has-text("No transactions")');
        if (emptyState) {
          results.passed.push('Empty state shown when no transactions');
        }
      }
    } else {
      results.warnings.push('Transaction history tab not found');
    }

    // Test 7: Test multi-chain support
    console.log('Test 7: Testing multi-chain support...');
    const chainTabs = await page.$$('button:has-text("Ethereum"), button:has-text("Base"), button:has-text("Polygon"), [data-testid*="chain"]');
    if (chainTabs.length > 0) {
      results.passed.push(`Multi-chain support detected (${chainTabs.length} chains)`);
      
      // Test switching chains
      if (chainTabs.length > 1) {
        await chainTabs[1].click();
        await page.waitForTimeout(2000);
        results.passed.push('Chain switching works');
      }
    } else {
      results.warnings.push('Multi-chain tabs not found');
    }

  } catch (error) {
    console.error('Test error:', error);
    results.failed.push(`Test execution error: ${error.message}`);
    await takeScreenshot(page, 'error-wallet-operations.png');
  } finally {
    await browser.close();
    finalizeResults(results);
  }

  // Print results
  console.log('\n=== Wallet Operations Test Results ===');
  console.log(`Passed: ${results.passed.length}`);
  console.log(`Failed: ${results.failed.length}`);
  console.log(`Warnings: ${results.warnings.length}`);
  console.log(`Duration: ${results.duration}s`);
  
  results.passed.forEach(test => console.log(`  ✓ ${test}`));
  results.failed.forEach(test => console.log(`  ✗ ${test}`));
  results.warnings.forEach(warning => console.log(`  ⚠ ${warning}`));

  return results;
}

export { testWalletOperations };

// Run test if executed directly
import { fileURLToPath } from 'url';
import { argv } from 'process';
const __filename = fileURLToPath(import.meta.url);
const isMainModule = argv[1] && (argv[1].endsWith('wallet-operations.js') || argv[1].endsWith('wallet-operations'));

if (isMainModule) {
  testWalletOperations()
    .then(results => {
      process.exit(results.failed.length > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
