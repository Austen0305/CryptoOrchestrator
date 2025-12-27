#!/usr/bin/env node
/**
 * Comprehensive Check Utility
 * Runs all verification and quality checks
 */

import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = dirname(dirname(__dirname));

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCheck(name, command, description) {
  log(`\n${'='.repeat(80)}`, 'cyan');
  log(`${name}`, 'bold');
  log(`${'='.repeat(80)}`, 'cyan');
  log(description, 'blue');
  log('');

  try {
    execSync(command, {
      cwd: projectRoot,
      stdio: 'inherit',
    });
    log(`\n✓ ${name} completed`, 'green');
    return true;
  } catch (error) {
    log(`\n✗ ${name} failed`, 'red');
    return false;
  }
}

async function main() {
  log('\n' + '='.repeat(80), 'bold');
  log('COMPREHENSIVE PROJECT CHECK', 'bold');
  log('='.repeat(80) + '\n', 'bold');

  const checks = [
    {
      name: 'Startup Verification',
      command: 'npm run verify:startup',
      description: 'Verifying startup configuration and dependencies',
    },
    {
      name: 'Feature Verification',
      command: 'npm run verify:features',
      description: 'Verifying all features are working',
    },
    {
      name: 'Performance Analysis',
      command: 'npm run analyze:performance',
      description: 'Analyzing application performance',
    },
    {
      name: 'Dependency Check',
      command: 'npm run check:dependencies',
      description: 'Checking for outdated or missing dependencies',
    },
    {
      name: 'Code Quality Check',
      command: 'npm run check:quality',
      description: 'Checking code quality and best practices',
    },
  ];

  const results = [];
  for (const check of checks) {
    const success = runCheck(check.name, check.command, check.description);
    results.push({ ...check, success });
  }

  log('\n' + '='.repeat(80), 'bold');
  log('SUMMARY', 'bold');
  log('='.repeat(80) + '\n', 'bold');

  const passed = results.filter((r) => r.success).length;
  const total = results.length;

  for (const result of results) {
    const status = result.success ? '✓' : '✗';
    const color = result.success ? 'green' : 'red';
    log(`${status} ${result.name}`, color);
  }

  log('');
  log(`${'='.repeat(80)}`, 'bold');
  log(`Results: ${passed}/${total} checks passed`, passed === total ? 'green' : 'yellow');
  log('='.repeat(80) + '\n', 'bold');

  if (passed === total) {
    log('All checks passed! Project is in excellent condition.', 'green');
    process.exit(0);
  } else {
    log('Some checks failed. Please review the output above.', 'yellow');
    process.exit(1);
  }
}

main().catch((err) => {
  log(`Error: ${err.message}`, 'red');
  process.exit(1);
});

