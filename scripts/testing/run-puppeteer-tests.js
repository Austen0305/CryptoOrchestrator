#!/usr/bin/env node
/**
 * Puppeteer Test Runner
 * Executes all Puppeteer tests with reporting
 */

import { readdir, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join, isAbsolute, basename } from 'path';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..', '..');
const puppeteerTestsDir = join(projectRoot, 'tests', 'puppeteer');
const screenshotsDir = join(puppeteerTestsDir, 'screenshots');

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

async function ensureScreenshotsDir() {
  if (!existsSync(screenshotsDir)) {
    await mkdir(screenshotsDir, { recursive: true });
    log(`Created screenshots directory: ${screenshotsDir}`, 'blue');
  }
}

async function getPuppeteerTests() {
  try {
    const files = await readdir(puppeteerTestsDir);
    return files
      .filter(file => file.endsWith('.js') && file !== 'test-helper.js' && file !== 'index.js')
      .map(file => ({
        name: file.replace('.js', ''),
        path: join(puppeteerTestsDir, file),
      }));
  } catch (error) {
    log(`Error reading Puppeteer tests directory: ${error.message}`, 'red');
    return [];
  }
}

function runTest(testPath, testName) {
  return new Promise((resolve) => {
    log(`\nRunning ${testName}...`, 'blue');
    
    const startTime = Date.now();
    // Convert to absolute path for reliability
    const absoluteTestPath = isAbsolute(testPath) ? testPath : join(puppeteerTestsDir, basename(testPath));
    const testProcess = spawn('node', [absoluteTestPath], {
      cwd: projectRoot,
      stdio: 'pipe',
      env: {
        ...process.env,
        BASE_URL: process.env.BASE_URL || 'http://localhost:5173',
        API_URL: process.env.API_URL || 'http://localhost:8000',
      },
    });

    let stdout = '';
    let stderr = '';

    testProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      // Show important output
      if (output.includes('✓') || output.includes('✗') || output.includes('⚠')) {
        process.stdout.write(output);
      }
    });

    testProcess.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
      process.stderr.write(output);
    });

    testProcess.on('close', (code) => {
      const duration = ((Date.now() - startTime) / 1000).toFixed(2);
      
      if (code === 0) {
        log(`  ✓ ${testName} passed (${duration}s)`, 'green');
        resolve({
          name: testName,
          success: true,
          duration: parseFloat(duration),
          output: stdout,
        });
      } else {
        log(`  ✗ ${testName} failed (${duration}s)`, 'red');
        resolve({
          name: testName,
          success: false,
          duration: parseFloat(duration),
          output: stdout,
          error: stderr,
          exitCode: code,
        });
      }
    });

    testProcess.on('error', (error) => {
      log(`  ✗ ${testName} error: ${error.message}`, 'red');
      resolve({
        name: testName,
        success: false,
        error: error.message,
      });
    });
  });
}

async function generateReport(results) {
  const total = results.length;
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  const totalDuration = results.reduce((sum, r) => sum + (r.duration || 0), 0).toFixed(2);

  log('\n' + '='.repeat(60), 'bold');
  log('Puppeteer Test Report', 'bold');
  log('='.repeat(60), 'bold');
  log(`\nTotal Tests: ${total}`, 'blue');
  log(`✓ Passed: ${passed}`, 'green');
  log(`✗ Failed: ${failed}`, failed > 0 ? 'red' : 'green');
  log(`Duration: ${totalDuration}s`, 'blue');

  if (passed > 0) {
    log('\nPassed Tests:', 'green');
    results.filter(r => r.success).forEach(result => {
      log(`  ✓ ${result.name} (${result.duration}s)`, 'green');
    });
  }

  if (failed > 0) {
    log('\nFailed Tests:', 'red');
    results.filter(r => !r.success).forEach(result => {
      log(`  ✗ ${result.name}`, 'red');
      if (result.error) {
        log(`    Error: ${result.error}`, 'red');
      }
      if (result.exitCode !== undefined) {
        log(`    Exit Code: ${result.exitCode}`, 'red');
      }
    });
  }

  // Generate JSON report
  const reportPath = join(projectRoot, 'test-results', 'puppeteer-results.json');
  const reportDir = join(projectRoot, 'test-results');
  
  if (!existsSync(reportDir)) {
    await mkdir(reportDir, { recursive: true });
  }

  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      total,
      passed,
      failed,
      duration: parseFloat(totalDuration),
    },
    results: results.map(r => ({
      name: r.name,
      success: r.success,
      duration: r.duration,
      error: r.error,
      exitCode: r.exitCode,
    })),
  };

  const { writeFileSync } = await import('fs');
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  log(`\nJSON report saved to: ${reportPath}`, 'blue');

  return { total, passed, failed, report };
}

async function main() {
  log('\n' + '='.repeat(60), 'bold');
  log('Puppeteer Test Runner', 'bold');
  log('='.repeat(60) + '\n', 'bold');

  // Ensure screenshots directory exists
  await ensureScreenshotsDir();

  // Get all Puppeteer tests
  const tests = await getPuppeteerTests();

  if (tests.length === 0) {
    log('No Puppeteer tests found!', 'yellow');
    process.exit(0);
  }

  log(`Found ${tests.length} test file(s):`, 'blue');
  tests.forEach(test => log(`  - ${test.name}`, 'blue'));

  // Run tests sequentially
  const results = [];
  for (const test of tests) {
    const result = await runTest(test.path, test.name);
    results.push(result);
  }

  // Generate report
  const report = await generateReport(results);

  // Exit with appropriate code
  if (report.failed > 0) {
    log('\n✗ Some tests failed', 'red');
    process.exit(1);
  } else {
    log('\n✓ All tests passed!', 'green');
    process.exit(0);
  }
}

main().catch(error => {
  log(`\n✗ Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
