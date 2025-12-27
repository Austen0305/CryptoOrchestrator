#!/usr/bin/env node
/**
 * Auto-Fix Script
 * Automatically fixes common issues
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { execSync } from 'child_process';

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

async function fixMissingEnv() {
  log('Fixing missing .env file...', 'blue');
  
  const envPath = join(projectRoot, '.env');
  const envExamplePath = join(projectRoot, '.env.example');
  
  if (!existsSync(envPath) && existsSync(envExamplePath)) {
    try {
      copyFileSync(envExamplePath, envPath);
      log('  ✓ Created .env file from .env.example', 'green');
      log('  ⚠ Remember to update values in .env with your actual credentials!', 'yellow');
      return true;
    } catch (error) {
      log(`  ✗ Failed to create .env: ${error.message}`, 'red');
      return false;
    }
  } else if (existsSync(envPath)) {
    log('  ✓ .env file already exists', 'green');
    return true;
  } else {
    log('  ⚠ .env.example not found, cannot create .env', 'yellow');
    return false;
  }
}

async function fixMissingDirectories() {
  log('Fixing missing directories...', 'blue');
  
  const directories = [
    'test-results',
    'tests/puppeteer/screenshots',
    'logs',
    'data',
  ];
  
  let fixed = 0;
  directories.forEach(dir => {
    const dirPath = join(projectRoot, dir);
    if (!existsSync(dirPath)) {
      try {
        mkdirSync(dirPath, { recursive: true });
        log(`  ✓ Created directory: ${dir}`, 'green');
        fixed++;
      } catch (error) {
        log(`  ✗ Failed to create ${dir}: ${error.message}`, 'red');
      }
    } else {
      log(`  ✓ Directory exists: ${dir}`, 'green');
    }
  });
  
  return fixed > 0;
}

async function fixMissingDependencies() {
  log('Checking dependencies...', 'blue');
  
  // Check Node modules
  const nodeModulesPath = join(projectRoot, 'node_modules');
  if (!existsSync(nodeModulesPath)) {
    log('  Installing Node.js dependencies...', 'blue');
    try {
      execSync('npm install', { 
        cwd: projectRoot,
        stdio: 'inherit' 
      });
      log('  ✓ Node.js dependencies installed', 'green');
      return true;
    } catch (error) {
      log(`  ✗ Failed to install Node.js dependencies: ${error.message}`, 'red');
      return false;
    }
  } else {
    log('  ✓ Node.js dependencies already installed', 'green');
  }
  
  // Check Python dependencies (optional, don't auto-install)
  try {
    execSync('python -m pip show fastapi', { stdio: 'pipe' });
    log('  ✓ Python dependencies appear to be installed', 'green');
  } catch {
    log('  ⚠ Python dependencies may be missing (run: pip install -r requirements.txt)', 'yellow');
  }
  
  return true;
}

async function generateSecureSecret(length = 32) {
  const crypto = await import('crypto');
  return crypto.randomBytes(length).toString('hex');
}

async function fixDefaultSecrets() {
  log('Checking for default secrets...', 'blue');
  
  const envPath = join(projectRoot, '.env');
  if (!existsSync(envPath)) {
    log('  ⚠ .env file not found, skipping secret fixes', 'yellow');
    return false;
  }
  
  let envContent = readFileSync(envPath, 'utf-8');
  let modified = false;
  
  // Fix JWT_SECRET
  if (envContent.includes('JWT_SECRET=dev-secret-change-me-in-production') || 
      envContent.includes('JWT_SECRET=change-me')) {
    const newSecret = await generateSecureSecret(32);
    envContent = envContent.replace(
      /JWT_SECRET=.*/,
      `JWT_SECRET=${newSecret}`
    );
    modified = true;
    log('  ✓ Generated new JWT_SECRET', 'green');
  }
  
  // Fix EXCHANGE_KEY_ENCRYPTION_KEY
  if (envContent.includes('EXCHANGE_KEY_ENCRYPTION_KEY=dev-key') ||
      envContent.includes('EXCHANGE_KEY_ENCRYPTION_KEY=change-me')) {
    const newKey = await generateSecureSecret(32);
    envContent = envContent.replace(
      /EXCHANGE_KEY_ENCRYPTION_KEY=.*/,
      `EXCHANGE_KEY_ENCRYPTION_KEY=${newKey}`
    );
    modified = true;
    log('  ✓ Generated new EXCHANGE_KEY_ENCRYPTION_KEY', 'green');
  }
  
  if (modified) {
    writeFileSync(envPath, envContent);
    log('  ✓ Updated .env file with secure secrets', 'green');
    return true;
  } else {
    log('  ✓ No default secrets found', 'green');
    return false;
  }
}

async function main() {
  log('\n' + '='.repeat(60), 'bold');
  log('Auto-Fix Script', 'bold');
  log('='.repeat(60) + '\n', 'bold');

  const fixes = {
    env: await fixMissingEnv(),
    directories: await fixMissingDirectories(),
    dependencies: await fixMissingDependencies(),
    secrets: await fixDefaultSecrets(),
  };

  log('\n=== Auto-Fix Summary ===\n', 'bold');
  
  let fixedCount = 0;
  Object.entries(fixes).forEach(([name, fixed]) => {
    if (fixed) {
      log(`✓ ${name}: Fixed`, 'green');
      fixedCount++;
    } else {
      log(`- ${name}: No fixes needed or failed`, 'blue');
    }
  });

  if (fixedCount > 0) {
    log(`\n✓ Fixed ${fixedCount} issue(s)`, 'green');
  } else {
    log('\n✓ No fixes were needed', 'green');
  }

  log('\nRun "node scripts/detect-issues.js" to check for remaining issues', 'blue');
}

main().catch(error => {
  log(`\n✗ Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
