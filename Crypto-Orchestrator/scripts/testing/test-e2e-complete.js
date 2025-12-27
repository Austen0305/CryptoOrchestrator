#!/usr/bin/env node
/**
 * Unified E2E Test Runner
 * Runs Playwright and Puppeteer tests with combined reporting
 */

import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, mkdirSync } from 'fs';
import { promisify } from 'util';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

const sleep = promisify(setTimeout);

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  bold: '\x1b[1m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function validateEnvironment() {
  log('Step 1: Validating environment...', 'blue');
  try {
    execSync('node scripts/utilities/validate-environment.js', { 
      cwd: projectRoot,
      stdio: 'inherit' 
    });
    return true;
  } catch (error) {
    log('  ⚠ Environment validation had warnings (continuing)', 'yellow');
    return true;
  }
}

async function stopExistingServices() {
  log('Checking for existing services...', 'blue');
  try {
    const { execSync } = await import('child_process');
    const isWindows = process.platform === 'win32';
    
    // Check and stop processes on ports 8000 and 5173
    try {
      if (isWindows) {
        // Find processes using ports
        const port8000 = execSync('netstat -ano | findstr ":8000" | findstr LISTENING', { encoding: 'utf-8', stdio: 'pipe' }).trim();
        const port5173 = execSync('netstat -ano | findstr ":5173" | findstr LISTENING', { encoding: 'utf-8', stdio: 'pipe' }).trim();
        
        if (port8000) {
          const pid = port8000.split(/\s+/).pop();
          if (pid) {
            log(`  Stopping process ${pid} on port 8000...`, 'yellow');
            try {
              execSync(`taskkill /F /PID ${pid}`, { stdio: 'pipe' });
              log(`  ✓ Stopped process on port 8000`, 'green');
            } catch (e) {
              // Process may have already stopped
            }
          }
        }
        
        if (port5173) {
          const pid = port5173.split(/\s+/).pop();
          if (pid) {
            log(`  Stopping process ${pid} on port 5173...`, 'yellow');
            try {
              execSync(`taskkill /F /PID ${pid}`, { stdio: 'pipe' });
              log(`  ✓ Stopped process on port 5173`, 'green');
            } catch (e) {
              // Process may have already stopped
            }
          }
        }
      }
      
      // Wait a moment for ports to be released
      await sleep(2000);
    } catch (error) {
      // Ignore errors - ports may not be in use
    }
  } catch (error) {
    // Ignore errors
  }
}

async function startServices() {
  log('\nStep 2: Starting services...', 'blue');
  try {
    // Stop existing services first
    await stopExistingServices();
    
    // Import service manager
    const serviceManagerModule = await import('../utilities/service-manager.js');
    const ServiceManager = serviceManagerModule.default || serviceManagerModule;
    const manager = new ServiceManager();
    
    const { success } = await manager.startAll();
    if (!success) {
      log('  ✗ Some services failed to start', 'red');
      return false;
    }
    
    // Wait for services to be ready
    log('  Waiting for services to be ready...', 'blue');
    const ready = await manager.waitForServices(60000);
    
    if (!ready) {
      log('  ✗ Services did not become ready in time', 'red');
      return false;
    }
    
    log('  ✓ All services started and ready', 'green');
    return true;
  } catch (error) {
    log(`  ✗ Failed to start services: ${error.message}`, 'red');
    return false;
  }
}

async function runPlaywrightTests() {
  log('\nStep 3: Running Playwright E2E tests...', 'blue');
  
  return new Promise((resolve) => {
    const process = spawn('npm', ['run', 'test:e2e'], {
      cwd: projectRoot,
      shell: true,
      stdio: 'inherit',
    });

    process.on('close', (code) => {
      resolve({ success: code === 0, exitCode: code });
    });

    process.on('error', (error) => {
      resolve({ success: false, error: error.message });
    });
  });
}

async function runPuppeteerTests() {
  log('\nStep 4: Running Puppeteer tests...', 'blue');
  
  return new Promise((resolve) => {
    const process = spawn('node', ['scripts/testing/run-puppeteer-tests.js'], {
      cwd: projectRoot,
      stdio: 'inherit',
    });

    process.on('close', (code) => {
      resolve({ success: code === 0, exitCode: code });
    });

    process.on('error', (error) => {
      resolve({ success: false, error: error.message });
    });
  });
}

async function generateCombinedReport() {
  log('\nStep 5: Generating combined test report...', 'blue');
  
  try {
    // Import report generator
    const { generateReport } = await import('./generate-test-report.js');
    await generateReport();
    return true;
  } catch (error) {
    log(`  ⚠ Report generation failed: ${error.message}`, 'yellow');
    return false;
  }
}

async function cleanupServices() {
  log('\nStep 6: Cleaning up services...', 'blue');
  try {
    const serviceManagerModule = await import('../utilities/service-manager.js');
    const ServiceManager = serviceManagerModule.default || serviceManagerModule;
    const manager = new ServiceManager();
    manager.stopAll();
    log('  ✓ Services stopped', 'green');
  } catch (error) {
    log(`  ⚠ Cleanup error: ${error.message}`, 'yellow');
  }
}

async function main() {
  const startTime = Date.now();
  
  log('\n' + '='.repeat(60), 'bold');
  log('Complete E2E Test Suite', 'bold');
  log('='.repeat(60) + '\n', 'bold');

  const results = {
    playwright: null,
    puppeteer: null,
    environment: false,
    services: false,
  };

  try {
    // Step 1: Validate environment
    results.environment = await validateEnvironment();
    if (!results.environment) {
      log('\n✗ Environment validation failed', 'red');
      process.exit(1);
    }

    // Step 2: Start services
    results.services = await startServices();
    if (!results.services) {
      log('\n✗ Failed to start services', 'red');
      process.exit(1);
    }

    // Step 3: Run Playwright tests
    results.playwright = await runPlaywrightTests();

    // Step 4: Run Puppeteer tests
    results.puppeteer = await runPuppeteerTests();

    // Step 5: Generate combined report
    await generateCombinedReport();

    // Step 6: Cleanup
    await cleanupServices();

    // Summary
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    
    log('\n' + '='.repeat(60), 'bold');
    log('Test Suite Summary', 'bold');
    log('='.repeat(60), 'bold');
    log(`\nDuration: ${duration}s`, 'blue');
    log(`Environment: ${results.environment ? '✓' : '✗'}`, results.environment ? 'green' : 'red');
    log(`Services: ${results.services ? '✓' : '✗'}`, results.services ? 'green' : 'red');
    log(`Playwright: ${results.playwright?.success ? '✓' : '✗'}`, results.playwright?.success ? 'green' : 'red');
    log(`Puppeteer: ${results.puppeteer?.success ? '✓' : '✗'}`, results.puppeteer?.success ? 'green' : 'red');

    const allPassed = 
      results.environment &&
      results.services &&
      results.playwright?.success &&
      results.puppeteer?.success;

    if (allPassed) {
      log('\n✓ All tests passed!', 'green');
      process.exit(0);
    } else {
      log('\n✗ Some tests failed', 'red');
      process.exit(1);
    }
  } catch (error) {
    log(`\n✗ Fatal error: ${error.message}`, 'red');
    console.error(error);
    
    // Cleanup on error
    await cleanupServices();
    process.exit(1);
  }
}

main();
