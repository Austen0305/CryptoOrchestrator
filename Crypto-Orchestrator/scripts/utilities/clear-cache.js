#!/usr/bin/env node
/**
 * Clear Cache Utility
 * Clears application caches (Redis, in-memory, etc.)
 */

import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = path.join(__dirname, '../..');

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

async function clearRedisCache() {
  try {
    log('Clearing Redis cache...', 'blue');
    execSync('redis-cli FLUSHALL', { stdio: 'inherit' });
    log('✓ Redis cache cleared', 'green');
    return true;
  } catch (err) {
    log('⚠ Redis not available or not running', 'yellow');
    return false;
  }
}

function clearNodeCache() {
  try {
    log('Clearing Node.js cache...', 'blue');
    const cacheDirs = [
      path.join(projectRoot, 'node_modules/.cache'),
      path.join(projectRoot, 'client/node_modules/.vite'),
      path.join(projectRoot, '.vite'),
    ];

    for (const dir of cacheDirs) {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
        log(`✓ Cleared ${path.basename(dir)}`, 'green');
      }
    }
    return true;
  } catch (err) {
    log(`⚠ Error clearing Node cache: ${err.message}`, 'yellow');
    return false;
  }
}

function clearPythonCache() {
  try {
    log('Clearing Python cache...', 'blue');
    const cacheDirs = [
      path.join(projectRoot, '__pycache__'),
      path.join(projectRoot, 'server_fastapi/__pycache__'),
    ];

    for (const dir of cacheDirs) {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
        log(`✓ Cleared ${path.basename(dir)}`, 'green');
      }
    }

    // Clear .pyc files
    execSync('find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true', {
      cwd: projectRoot,
      stdio: 'inherit',
    });
    return true;
  } catch (err) {
    log(`⚠ Error clearing Python cache: ${err.message}`, 'yellow');
    return false;
  }
}

async function main() {
  log('Clear Cache Utility', 'bold');
  log('===================', 'bold');
  log('');

  const results = {
    redis: await clearRedisCache(),
    node: clearNodeCache(),
    python: clearPythonCache(),
  };

  log('');
  log('===================', 'bold');
  const allOk = Object.values(results).some((r) => r);
  if (allOk) {
    log('Cache clearing complete!', 'green');
  } else {
    log('No caches found to clear', 'yellow');
  }
}

main().catch((err) => {
  log(`Error: ${err.message}`, 'red');
  process.exit(1);
});

