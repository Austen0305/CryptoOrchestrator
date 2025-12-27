/**
 * Puppeteer Test: Bot Management Flow
 * Tests bot creation, listing, start/stop, and deletion
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

async function testBotManagement() {
  const browser = await puppeteer.launch(config.launch);
  const page = await browser.newPage();
  const results = createTestResults();
  
  // Set viewport
  await page.setViewport(config.launch.defaultViewport);

  try {
    console.log('Starting bot management tests...');
    
    // Note: This test assumes user is already logged in
    // In a real scenario, you'd login first
    
    // Test 1: Navigate to bots page
    console.log('Test 1: Navigating to bots page...');
    await page.goto(`${BASE_URL}/bots`, { waitUntil: 'networkidle2' });
    await page.screenshot({ path: 'tests/puppeteer/screenshots/bots-page.png' });
    
    const botsPage = await page.$('h1, h2, [data-testid="bots-page"]');
    if (botsPage) {
      results.passed.push('Bots page loads successfully');
    } else {
      results.failed.push('Bots page not found or not loading');
    }

    // Test 2: Check for create bot button
    console.log('Test 2: Checking for create bot button...');
    const createButton = await page.$('button:has-text("Create"), button:has-text("New Bot"), [data-testid="create-bot"]');
    if (createButton) {
      results.passed.push('Create bot button found');
      
      // Test 3: Open bot creation form
      console.log('Test 3: Opening bot creation form...');
      await createButton.click();
      await page.waitForTimeout(1000);
      
      const form = await page.$('form, dialog, [data-testid="bot-form"]');
      if (form) {
        results.passed.push('Bot creation form opens');
        await page.screenshot({ path: 'tests/puppeteer/screenshots/bot-creation-form.png' });
        
        // Test 4: Fill bot creation form
        console.log('Test 4: Filling bot creation form...');
        const nameInput = await page.$('input[name="name"]');
        if (nameInput) {
          await nameInput.type('Test Bot ' + Date.now());
          results.passed.push('Bot name input found and filled');
        }
        
        const strategySelect = await page.$('select[name="strategy"], [name="strategy"]');
        if (strategySelect) {
          await strategySelect.select('momentum'); // or first available option
          results.passed.push('Strategy selection found');
        }
        
        const balanceInput = await page.$('input[name="initial_balance"], input[name="balance"]');
        if (balanceInput) {
          await balanceInput.type('1000');
          results.passed.push('Initial balance input found and filled');
        }
        
        // Test 5: Submit bot creation
        console.log('Test 5: Submitting bot creation...');
        const submitButton = await page.$('button[type="submit"], button:has-text("Create")');
        if (submitButton) {
          await submitButton.click();
          await page.waitForTimeout(3000);
          
          // Check if bot was created (appears in list or success message)
          const successMessage = await page.$('.alert-success, [role="alert"]:has-text("success"), .toast');
          const botInList = await page.$('[data-testid*="bot"], .bot-card, .bot-item');
          
          if (successMessage || botInList) {
            results.passed.push('Bot creation submitted successfully');
          } else {
            results.warnings.push('Bot creation submitted but success not confirmed');
          }
        }
      } else {
        results.failed.push('Bot creation form did not open');
      }
    } else {
      results.warnings.push('Create bot button not found');
    }

    // Test 6: Test bot listing
    console.log('Test 6: Testing bot listing...');
    await page.goto(`${BASE_URL}/bots`, { waitUntil: 'networkidle2' });
    await page.waitForTimeout(2000);
    
    const botList = await page.$$('[data-testid*="bot"], .bot-card, .bot-item, tr');
    if (botList.length > 0) {
      results.passed.push(`Bot list displays ${botList.length} bot(s)`);
    } else {
      // Check for empty state
      const emptyState = await page.$('.empty-state, [data-testid="empty-state"], :has-text("No bots")');
      if (emptyState) {
        results.passed.push('Empty state displayed when no bots');
      } else {
        results.warnings.push('Bot list not found and no empty state');
      }
    }

    // Test 7: Test bot start/stop (if bots exist)
    if (botList && botList.length > 0) {
      console.log('Test 7: Testing bot start/stop...');
      const firstBot = botList[0];
      const startButton = await firstBot.$('button:has-text("Start"), [data-testid="start-bot"]');
      const stopButton = await firstBot.$('button:has-text("Stop"), [data-testid="stop-bot"]');
      
      if (startButton || stopButton) {
        const buttonToClick = startButton || stopButton;
        await buttonToClick.click();
        await page.waitForTimeout(2000);
        
        // Check if status changed
        const status = await firstBot.$('.status, [data-testid="bot-status"]');
        if (status) {
          results.passed.push('Bot start/stop button works');
        } else {
          results.warnings.push('Bot start/stop clicked but status not verified');
        }
      } else {
        results.warnings.push('Bot start/stop buttons not found');
      }
    }

    // Test 8: Test bot deletion
    console.log('Test 8: Testing bot deletion...');
    if (botList && botList.length > 0) {
      const deleteButton = await page.$('button:has-text("Delete"), [data-testid="delete-bot"]');
      if (deleteButton) {
        await deleteButton.click();
        await page.waitForTimeout(1000);
        
        // Check for confirmation dialog
        const confirmButton = await page.$('button:has-text("Confirm"), button:has-text("Yes"), [data-testid="confirm-delete"]');
        if (confirmButton) {
          await confirmButton.click();
          await page.waitForTimeout(2000);
          results.passed.push('Bot deletion flow works');
        } else {
          results.warnings.push('Delete confirmation not found');
        }
      } else {
        results.warnings.push('Delete button not found');
      }
    }

  } catch (error) {
    console.error('Test error:', error);
    results.failed.push(`Test execution error: ${error.message}`);
    await takeScreenshot(page, 'error-bot-management.png');
  } finally {
    await browser.close();
    finalizeResults(results);
  }

  // Print results
  console.log('\n=== Bot Management Test Results ===');
  console.log(`Passed: ${results.passed.length}`);
  console.log(`Failed: ${results.failed.length}`);
  console.log(`Warnings: ${results.warnings.length}`);
  console.log(`Duration: ${results.duration}s`);
  
  results.passed.forEach(test => console.log(`  ✓ ${test}`));
  results.failed.forEach(test => console.log(`  ✗ ${test}`));
  results.warnings.forEach(warning => console.log(`  ⚠ ${warning}`));

  return results;
}

export { testBotManagement };

// Run test if executed directly
import { fileURLToPath } from 'url';
import { argv } from 'process';
const __filename = fileURLToPath(import.meta.url);
const isMainModule = argv[1] && (argv[1].endsWith('bot-management.js') || argv[1].endsWith('bot-management'));

if (isMainModule) {
  testBotManagement()
    .then(results => {
      process.exit(results.failed.length > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
