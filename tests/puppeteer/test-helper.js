/**
 * Puppeteer Test Helper Utilities
 * Provides retry logic, consistent result format, and error handling
 */

import config from '../../puppeteer.config.js';
import { mkdirSync, existsSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Ensure screenshots directory exists
const screenshotsDir = path.join(__dirname, 'screenshots');
if (!existsSync(screenshotsDir)) {
  mkdirSync(screenshotsDir, { recursive: true });
}

/**
 * Retry a function with exponential backoff
 * Enhanced with max delay cap and better error handling
 */
async function retry(fn, maxRetries = 5, delay = 1000) {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        // Exponential backoff with max delay of 8 seconds (increased from 5s)
        const waitTime = Math.min(delay * Math.pow(2, i), 8000);
        console.log(`[RETRY] Attempt ${i + 1}/${maxRetries} failed, retrying in ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }
  console.error(`[RETRY] All ${maxRetries} attempts failed`);
  throw lastError;
}

/**
 * Wait for element with timeout and retry
 */
async function waitForElement(page, selector, options = {}) {
  const timeout = options.timeout || config.test.timeout;
  const visible = options.visible !== false;
  
  try {
    if (visible) {
      await page.waitForSelector(selector, { timeout, visible: true });
    } else {
      await page.waitForSelector(selector, { timeout });
    }
    return await page.$(selector);
  } catch (error) {
    return null;
  }
}

/**
 * Safe click with retry
 */
async function safeClick(page, selector, options = {}) {
  return retry(async () => {
    const element = await waitForElement(page, selector, options);
    if (!element) {
      throw new Error(`Element not found: ${selector}`);
    }
    await element.click();
    await page.waitForTimeout(options.waitAfter || config.waits.short);
  }, options.maxRetries || 3);
}

/**
 * Safe type with retry
 */
async function safeType(page, selector, text, options = {}) {
  return retry(async () => {
    const element = await waitForElement(page, selector, options);
    if (!element) {
      throw new Error(`Element not found: ${selector}`);
    }
    await element.click({ clickCount: 3 }); // Select all
    await element.type(text, { delay: options.delay || 50 });
    await page.waitForTimeout(options.waitAfter || config.waits.short);
  }, options.maxRetries || 3);
}

/**
 * Take screenshot with error handling
 */
async function takeScreenshot(page, filename) {
  try {
    const filepath = path.join(screenshotsDir, filename);
    await page.screenshot({ 
      path: filepath,
      fullPage: config.screenshot.fullPage 
    });
    return filepath;
  } catch (error) {
    console.warn(`Failed to take screenshot: ${error.message}`);
    return null;
  }
}

/**
 * Create consistent test result object
 */
function createTestResults() {
  return {
    passed: [],
    failed: [],
    warnings: [],
    startTime: Date.now(),
    endTime: null,
    duration: null,
  };
}

/**
 * Finalize test results
 */
function finalizeResults(results) {
  results.endTime = Date.now();
  results.duration = ((results.endTime - results.startTime) / 1000).toFixed(2);
  return results;
}

/**
 * Safe navigation with retry
 */
async function safeNavigate(page, url, options = {}) {
  return retry(async () => {
    await page.goto(url, { 
      waitUntil: options.waitUntil || 'networkidle2',
      timeout: options.timeout || config.test.timeout 
    });
    await page.waitForTimeout(options.waitAfter || config.waits.medium);
  }, options.maxRetries || 3);
}

export {
  retry,
  waitForElement,
  safeClick,
  safeType,
  takeScreenshot,
  createTestResults,
  finalizeResults,
  safeNavigate,
  config,
  screenshotsDir,
};
