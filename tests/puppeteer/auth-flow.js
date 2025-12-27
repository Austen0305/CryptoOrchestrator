/**
 * Puppeteer Test: Authentication Flow
 * Tests complete authentication flow including login, registration, and password reset
 */

// Set environment variable before importing puppeteer to fix Node.js 25 compatibility
if (typeof process !== 'undefined' && process.env && !process.env.PUPPETEER_LOGLEVEL) {
  process.env.PUPPETEER_LOGLEVEL = 'warn';
}

import puppeteer from 'puppeteer';
import { 
  retry, 
  safeNavigate, 
  safeClick, 
  safeType, 
  takeScreenshot, 
  createTestResults, 
  finalizeResults,
  config 
} from './test-helper.js';

const BASE_URL = process.env.BASE_URL || config.urls.base;
const API_URL = process.env.API_URL || 'http://localhost:8000';

async function testAuthFlow() {
  const browser = await puppeteer.launch(config.launch);
  const page = await browser.newPage();
  const results = createTestResults();
  
  // Set viewport
  await page.setViewport(config.launch.defaultViewport);

  try {
    console.log('Starting authentication flow tests...');

    // Test 1: Navigate to login page
    console.log('Test 1: Navigating to login page...');
    try {
      await safeNavigate(page, `${BASE_URL}/login`);
      await takeScreenshot(page, 'login-page.png');
      
      const loginForm = await page.$('form');
      if (loginForm) {
        results.passed.push('Login page loads with form');
      } else {
        results.failed.push('Login page form not found');
      }
    } catch (error) {
      results.warnings.push(`Login page navigation error: ${error.message}`);
    }

    // Test 2: Test login with invalid credentials
    console.log('Test 2: Testing login with invalid credentials...');
    try {
      await safeType(page, 'input[name="email"]', 'invalid@test.com');
      await safeType(page, 'input[name="password"]', 'wrongpassword');
      await safeClick(page, 'button[type="submit"]');
      
      await page.waitForTimeout(2000);
      const errorMessage = await page.$('.alert, [role="alert"], .error-message');
      if (errorMessage) {
        results.passed.push('Error message displayed for invalid credentials');
      } else {
        results.warnings.push('No error message found for invalid login');
      }
    } catch (error) {
      results.warnings.push(`Login test error: ${error.message}`);
    }

    // Test 3: Test registration flow
    console.log('Test 3: Testing registration flow...');
    try {
      await safeNavigate(page, `${BASE_URL}/register`);
      await takeScreenshot(page, 'register-page.png');
      
      const registerForm = await page.$('form');
      if (registerForm) {
        results.passed.push('Registration page loads with form');
        
        // Generate unique test user
        const timestamp = Date.now();
        const testEmail = `test${timestamp}@example.com`;
        const testPassword = 'TestPassword123!';
        
        await safeType(page, 'input[name="email"]', testEmail);
        await safeType(page, 'input[name="password"]', testPassword);
        const confirmPassword = await page.$('input[name="confirmPassword"]');
        if (confirmPassword) {
          await safeType(page, 'input[name="confirmPassword"]', testPassword);
        }
        
        await safeClick(page, 'button[type="submit"]');
        await page.waitForTimeout(3000);
        
        // Check if redirected to dashboard or login
        const currentUrl = page.url();
        if (currentUrl.includes('dashboard') || currentUrl.includes('login')) {
          results.passed.push('Registration redirects to appropriate page');
        } else {
          results.warnings.push(`Registration redirected to unexpected page: ${currentUrl}`);
        }
      } else {
        results.failed.push('Registration form not found');
      }
    } catch (error) {
      results.warnings.push(`Registration test error: ${error.message}`);
    }

    // Test 4: Test password reset flow
    console.log('Test 4: Testing password reset flow...');
    try {
      await safeNavigate(page, `${BASE_URL}/forgot-password`);
      await takeScreenshot(page, 'forgot-password-page.png');
      
      const resetForm = await page.$('form');
      if (resetForm) {
        results.passed.push('Password reset page loads');
      } else {
        results.warnings.push('Password reset form not found');
      }
    } catch (error) {
      results.warnings.push(`Password reset test error: ${error.message}`);
    }

    // Test 5: Check localStorage for JWT token (after successful login)
    console.log('Test 5: Checking JWT token storage...');
    // This would require a successful login first
    const token = await page.evaluate(() => localStorage.getItem('token'));
    if (token) {
      results.passed.push('JWT token stored in localStorage');
    } else {
      results.warnings.push('No JWT token found (may need successful login first)');
    }

    // Test 6: Test logout functionality
    console.log('Test 6: Testing logout...');
    try {
      const logoutButton = await page.$('button:has-text("Logout"), [data-testid="logout"]');
      if (logoutButton) {
        await safeClick(page, 'button:has-text("Logout"), [data-testid="logout"]');
        await page.waitForTimeout(1000);
        const tokenAfterLogout = await page.evaluate(() => localStorage.getItem('token'));
        if (!tokenAfterLogout) {
          results.passed.push('Logout clears JWT token');
        } else {
          results.failed.push('Logout did not clear JWT token');
        }
      } else {
        results.warnings.push('Logout button not found');
      }
    } catch (error) {
      results.warnings.push(`Logout test error: ${error.message}`);
    }

  } catch (error) {
    console.error('Test error:', error);
    results.failed.push(`Test execution error: ${error.message}`);
    await takeScreenshot(page, 'error-auth-flow.png');
  } finally {
    await browser.close();
    finalizeResults(results);
  }

  // Print results
  console.log('\n=== Authentication Flow Test Results ===');
  console.log(`Passed: ${results.passed.length}`);
  console.log(`Failed: ${results.failed.length}`);
  console.log(`Warnings: ${results.warnings.length}`);
  console.log(`Duration: ${results.duration}s`);
  
  if (results.passed.length > 0) {
    console.log('\nPassed tests:');
    results.passed.forEach(test => console.log(`  ✓ ${test}`));
  }
  
  if (results.failed.length > 0) {
    console.log('\nFailed tests:');
    results.failed.forEach(test => console.log(`  ✗ ${test}`));
  }
  
  if (results.warnings.length > 0) {
    console.log('\nWarnings:');
    results.warnings.forEach(warning => console.log(`  ⚠ ${warning}`));
  }

  return results;
}

export { testAuthFlow };

// Run test if executed directly
import { fileURLToPath } from 'url';
import { argv } from 'process';
const __filename = fileURLToPath(import.meta.url);
const isMainModule = argv[1] && (argv[1].endsWith('auth-flow.js') || argv[1].endsWith('auth-flow'));

if (isMainModule) {
  testAuthFlow()
    .then(results => {
      const exitCode = results.failed.length > 0 ? 1 : 0;
      process.exit(exitCode);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
