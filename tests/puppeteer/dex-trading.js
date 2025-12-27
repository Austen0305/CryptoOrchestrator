/**
 * Puppeteer Test: DEX Trading Flow
 * Tests token swaps, price fetching, and transaction status
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

async function testDEXTrading() {
  const browser = await puppeteer.launch(config.launch);
  const page = await browser.newPage();
  const results = createTestResults();
  
  // Set viewport
  await page.setViewport(config.launch.defaultViewport);

  try {
    console.log('Starting DEX trading tests...');
    
    // Test 1: Navigate to DEX trading page
    console.log('Test 1: Navigating to DEX trading page...');
    await page.goto(`${BASE_URL}/dex-trading`, { waitUntil: 'networkidle2' });
    await page.screenshot({ path: 'tests/puppeteer/screenshots/dex-trading-page.png' });
    
    const dexPage = await page.$('h1, h2, [data-testid="dex-trading-page"]');
    if (dexPage) {
      results.passed.push('DEX trading page loads successfully');
    } else {
      results.failed.push('DEX trading page not found');
    }

    // Test 2: Test token selection
    console.log('Test 2: Testing token selection...');
    const fromTokenSelect = await page.$('input[placeholder*="From"], select[name="fromToken"], [data-testid="from-token"]');
    const toTokenSelect = await page.$('input[placeholder*="To"], select[name="toToken"], [data-testid="to-token"]');
    
    if (fromTokenSelect && toTokenSelect) {
      results.passed.push('Token selection inputs found');
      
      // Try to select tokens
      await fromTokenSelect.click();
      await page.waitForTimeout(500);
      const tokenOptions = await page.$$('.token-option, [role="option"], li');
      if (tokenOptions.length > 0) {
        await tokenOptions[0].click();
        results.passed.push('From token selection works');
      }
    } else {
      results.warnings.push('Token selection inputs not found');
    }

    // Test 3: Test amount input
    console.log('Test 3: Testing amount input...');
    const amountInput = await page.$('input[name="amount"], input[placeholder*="Amount"], input[type="number"]');
    if (amountInput) {
      await amountInput.type('100');
      results.passed.push('Amount input found and accepts input');
      
      // Test validation (negative numbers, etc.)
      await amountInput.click({ clickCount: 3 });
      await amountInput.type('-10');
      await page.waitForTimeout(500);
      const validationError = await page.$('.error, .invalid, [role="alert"]');
      if (validationError) {
        results.passed.push('Amount validation works');
      }
    } else {
      results.warnings.push('Amount input not found');
    }

    // Test 4: Test price fetching
    console.log('Test 4: Testing price fetching...');
    await page.waitForTimeout(2000); // Wait for price to load
    const priceDisplay = await page.$('.price, [data-testid="price"], :has-text("$"), :has-text("per")');
    if (priceDisplay) {
      const priceText = await priceDisplay.textContent();
      results.passed.push(`Price displayed: ${priceText}`);
    } else {
      results.warnings.push('Price display not found');
    }

    // Test 5: Test slippage settings
    console.log('Test 5: Testing slippage settings...');
    const slippageInput = await page.$('input[name="slippage"], input[placeholder*="slippage"], [data-testid="slippage"]');
    if (slippageInput) {
      await slippageInput.type('1');
      results.passed.push('Slippage input found and accepts input');
    } else {
      results.warnings.push('Slippage input not found');
    }

    // Test 6: Test price impact warning
    console.log('Test 6: Testing price impact warning...');
    await page.waitForTimeout(2000);
    const priceImpactWarning = await page.$('.warning, .price-impact, [data-testid="price-impact"]');
    if (priceImpactWarning) {
      results.passed.push('Price impact warning displayed when applicable');
    } else {
      results.warnings.push('Price impact warning not found (may not be applicable)');
    }

    // Test 7: Test swap button (don't actually execute)
    console.log('Test 7: Testing swap button...');
    const swapButton = await page.$('button:has-text("Swap"), button:has-text("Execute"), [data-testid="swap-button"]');
    if (swapButton) {
      const isDisabled = await swapButton.evaluate(el => el.disabled);
      if (isDisabled) {
        results.passed.push('Swap button is disabled when form is invalid');
      } else {
        results.warnings.push('Swap button is enabled (may execute real transaction)');
      }
    } else {
      results.warnings.push('Swap button not found');
    }

    // Test 8: Test transaction status (if transaction exists)
    console.log('Test 8: Testing transaction status...');
    const transactionStatus = await page.$('.transaction-status, [data-testid="tx-status"], :has-text("Pending"), :has-text("Confirmed")');
    if (transactionStatus) {
      results.passed.push('Transaction status display found');
    } else {
      results.warnings.push('Transaction status not found (no active transactions)');
    }

    // Test 9: Test multi-chain support
    console.log('Test 9: Testing multi-chain support...');
    const chainSelect = await page.$('select[name="chain"], button:has-text("Ethereum"), [data-testid="chain-select"]');
    if (chainSelect) {
      results.passed.push('Chain selection found');
    } else {
      results.warnings.push('Chain selection not found');
    }

  } catch (error) {
    console.error('Test error:', error);
    results.failed.push(`Test execution error: ${error.message}`);
    await takeScreenshot(page, 'error-dex-trading.png');
  } finally {
    await browser.close();
    finalizeResults(results);
  }

  // Print results
  console.log('\n=== DEX Trading Test Results ===');
  console.log(`Passed: ${results.passed.length}`);
  console.log(`Failed: ${results.failed.length}`);
  console.log(`Warnings: ${results.warnings.length}`);
  console.log(`Duration: ${results.duration}s`);
  
  results.passed.forEach(test => console.log(`  ✓ ${test}`));
  results.failed.forEach(test => console.log(`  ✗ ${test}`));
  results.warnings.forEach(warning => console.log(`  ⚠ ${warning}`));

  return results;
}

export { testDEXTrading };

// Run test if executed directly
import { fileURLToPath } from 'url';
import { argv } from 'process';
const __filename = fileURLToPath(import.meta.url);
const isMainModule = argv[1] && (argv[1].endsWith('dex-trading.js') || argv[1].endsWith('dex-trading'));

if (isMainModule) {
  testDEXTrading()
    .then(results => {
      process.exit(results.failed.length > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
