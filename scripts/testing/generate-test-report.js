#!/usr/bin/env node
/**
 * Test Report Generator
 * Combines Playwright and Puppeteer results into HTML/JSON reports
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

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

function loadPlaywrightResults() {
  const playwrightResultsPath = join(projectRoot, 'test-results', 'results.json');
  
  if (!existsSync(playwrightResultsPath)) {
    return null;
  }
  
  try {
    const content = readFileSync(playwrightResultsPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    log(`Failed to load Playwright results: ${error.message}`, 'yellow');
    return null;
  }
}

function loadPuppeteerResults() {
  const puppeteerResultsPath = join(projectRoot, 'test-results', 'puppeteer-results.json');
  
  if (!existsSync(puppeteerResultsPath)) {
    return null;
  }
  
  try {
    const content = readFileSync(puppeteerResultsPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    log(`Failed to load Puppeteer results: ${error.message}`, 'yellow');
    return null;
  }
}

function generateHTMLReport(combinedResults) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2E Test Report - ${new Date().toLocaleString()}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .timestamp {
            color: #666;
            margin-bottom: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .summary-card.total { background: #e3f2fd; }
        .summary-card.passed { background: #e8f5e9; }
        .summary-card.failed { background: #ffebee; }
        .summary-card.duration { background: #fff3e0; }
        .summary-card h3 {
            font-size: 32px;
            margin-bottom: 5px;
        }
        .summary-card.passed h3 { color: #2e7d32; }
        .summary-card.failed h3 { color: #c62828; }
        .summary-card p {
            color: #666;
            font-size: 14px;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .test-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid #ddd;
        }
        .test-item.passed {
            background: #e8f5e9;
            border-left-color: #4caf50;
        }
        .test-item.failed {
            background: #ffebee;
            border-left-color: #f44336;
        }
        .test-item h4 {
            margin-bottom: 5px;
        }
        .test-item .duration {
            color: #666;
            font-size: 12px;
        }
        .test-item .error {
            color: #c62828;
            font-size: 14px;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>E2E Test Report</h1>
        <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>${combinedResults.summary.total}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>${combinedResults.summary.passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>${combinedResults.summary.failed}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card duration">
                <h3>${combinedResults.summary.duration}s</h3>
                <p>Duration</p>
            </div>
        </div>
        
        ${combinedResults.playwright ? `
        <div class="section">
            <h2>Playwright Tests</h2>
            ${combinedResults.playwright.results.map(test => `
                <div class="test-item ${test.status === 'passed' ? 'passed' : 'failed'}">
                    <h4>${test.title || test.name}</h4>
                    <div class="duration">Duration: ${test.duration || 0}s</div>
                    ${test.error ? `<div class="error">${test.error}</div>` : ''}
                </div>
            `).join('')}
        </div>
        ` : ''}
        
        ${combinedResults.puppeteer ? `
        <div class="section">
            <h2>Puppeteer Tests</h2>
            ${combinedResults.puppeteer.results.map(test => `
                <div class="test-item ${test.success ? 'passed' : 'failed'}">
                    <h4>${test.name}</h4>
                    <div class="duration">Duration: ${test.duration || 0}s</div>
                    ${test.error ? `<div class="error">${test.error}</div>` : ''}
                </div>
            `).join('')}
        </div>
        ` : ''}
    </div>
</body>
</html>`;

  return html;
}

export async function generateReport() {
  log('Generating combined test report...', 'blue');

  // Ensure test-results directory exists
  const testResultsDir = join(projectRoot, 'test-results');
  if (!existsSync(testResultsDir)) {
    mkdirSync(testResultsDir, { recursive: true });
  }

  // Load results
  const playwrightResults = loadPlaywrightResults();
  const puppeteerResults = loadPuppeteerResults();

  // Combine results
  const combinedResults = {
    timestamp: new Date().toISOString(),
    summary: {
      total: 0,
      passed: 0,
      failed: 0,
      duration: 0,
    },
    playwright: null,
    puppeteer: null,
  };

  if (playwrightResults) {
    const stats = playwrightResults.stats || {};
    combinedResults.playwright = {
      summary: {
        total: stats.total || 0,
        passed: stats.passed || 0,
        failed: stats.failed || 0,
        duration: stats.duration || 0,
      },
      results: playwrightResults.suites?.flatMap(suite => 
        suite.specs?.flatMap(spec => 
          spec.tests?.map(test => ({
            name: spec.title || test.title,
            status: test.results?.[0]?.status || 'unknown',
            duration: test.results?.[0]?.duration || 0,
            error: test.results?.[0]?.error?.message,
          }))
        ) || []
      ) || [],
    };
    
    combinedResults.summary.total += combinedResults.playwright.summary.total;
    combinedResults.summary.passed += combinedResults.playwright.summary.passed;
    combinedResults.summary.failed += combinedResults.playwright.summary.failed;
    combinedResults.summary.duration += combinedResults.playwright.summary.duration;
  }

  if (puppeteerResults) {
    combinedResults.puppeteer = puppeteerResults;
    combinedResults.summary.total += puppeteerResults.summary.total;
    combinedResults.summary.passed += puppeteerResults.summary.passed;
    combinedResults.summary.failed += puppeteerResults.summary.failed;
    combinedResults.summary.duration += puppeteerResults.summary.duration;
  }

  // Generate JSON report
  const jsonPath = join(testResultsDir, 'combined-results.json');
  writeFileSync(jsonPath, JSON.stringify(combinedResults, null, 2));
  log(`  ✓ JSON report saved: ${jsonPath}`, 'green');

  // Generate HTML report
  const htmlPath = join(testResultsDir, 'combined-report.html');
  const html = generateHTMLReport(combinedResults);
  writeFileSync(htmlPath, html);
  log(`  ✓ HTML report saved: ${htmlPath}`, 'green');

  // Print summary
  log('\n=== Combined Test Report ===', 'bold');
  log(`Total Tests: ${combinedResults.summary.total}`, 'blue');
  log(`Passed: ${combinedResults.summary.passed}`, 'green');
  log(`Failed: ${combinedResults.summary.failed}`, combinedResults.summary.failed > 0 ? 'red' : 'green');
  log(`Duration: ${combinedResults.summary.duration.toFixed(2)}s`, 'blue');

  return combinedResults;
}

// CLI usage
const currentFile = fileURLToPath(import.meta.url);
const scriptFile = process.argv[1] ? process.argv[1].replace(/\\/g, '/') : '';

if (currentFile.endsWith(scriptFile) || process.argv[1]?.includes('generate-test-report.js')) {
  generateReport().catch(error => {
    log(`Error generating report: ${error.message}`, 'red');
    process.exit(1);
  });
}
