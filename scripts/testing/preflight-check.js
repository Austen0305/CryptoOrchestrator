#!/usr/bin/env node
/**
 * Pre-Flight Check
 * Validates readiness before running tests
 */

import { execSync } from 'child_process';
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

async function checkDependencies() {
  log('Checking dependencies...', 'blue');
  
  // Check Node.js
  try {
    const nodeVersion = execSync('node --version', { encoding: 'utf-8' }).trim();
    log(`  ✓ Node.js: ${nodeVersion}`, 'green');
  } catch {
    log('  ✗ Node.js not found', 'red');
    return false;
  }
  
  // Check Python
  try {
    const pythonVersion = execSync('python --version', { encoding: 'utf-8' }).trim();
    log(`  ✓ Python: ${pythonVersion}`, 'green');
  } catch {
    try {
      const pythonVersion = execSync('python3 --version', { encoding: 'utf-8' }).trim();
      log(`  ✓ Python: ${pythonVersion}`, 'green');
    } catch {
      log('  ✗ Python not found', 'red');
      return false;
    }
  }
  
  return true;
}

async function checkEnvironment() {
  log('Checking environment configuration...', 'blue');
  
  try {
    execSync('node scripts/validate-environment.js', { 
      cwd: projectRoot,
      stdio: 'pipe' 
    });
    log('  ✓ Environment validation passed', 'green');
    return true;
  } catch {
    log('  ✗ Environment validation failed', 'red');
    return false;
  }
}

async function checkServices() {
  log('Checking if services can start...', 'blue');
  
  // Check ports
  function isPortAvailable(port) {
    try {
      if (process.platform === 'win32') {
        const result = execSync(`netstat -ano | findstr :${port}`, { 
          encoding: 'utf-8', 
          stdio: 'pipe' 
        });
        return result.trim().length === 0;
      } else {
        execSync(`lsof -i :${port}`, { encoding: 'utf-8', stdio: 'pipe' });
        return false;
      }
    } catch {
      return true;
    }
  }
  
  const ports = [
    { port: 8000, service: 'FastAPI' },
    { port: 5173, service: 'Frontend' },
  ];
  
  let allAvailable = true;
  ports.forEach(({ port, service }) => {
    if (isPortAvailable(port)) {
      log(`  ✓ Port ${port} available (${service})`, 'green');
    } else {
      log(`  ⚠ Port ${port} in use (${service})`, 'yellow');
      allAvailable = false;
    }
  });
  
  return allAvailable;
}

async function checkDatabase() {
  log('Checking database accessibility...', 'blue');
  
  // This is a basic check - in production you'd actually try to connect
  const databaseUrl = process.env.DATABASE_URL;
  if (databaseUrl) {
    log('  ✓ DATABASE_URL configured', 'green');
    return true;
  } else {
    log('  ⚠ DATABASE_URL not set', 'yellow');
    return false;
  }
}

async function main() {
  log('\n' + '='.repeat(60), 'bold');
  log('Pre-Flight Check', 'bold');
  log('='.repeat(60) + '\n', 'bold');

  const checks = {
    dependencies: await checkDependencies(),
    environment: await checkEnvironment(),
    services: await checkServices(),
    database: await checkDatabase(),
  };

  log('\n=== Pre-Flight Check Summary ===\n', 'bold');
  
  let allPassed = true;
  Object.entries(checks).forEach(([name, passed]) => {
    if (passed) {
      log(`✓ ${name}: Ready`, 'green');
    } else {
      log(`✗ ${name}: Not ready`, 'red');
      allPassed = false;
    }
  });

  if (allPassed) {
    log('\n✓ All pre-flight checks passed! Ready to run tests.', 'green');
    process.exit(0);
  } else {
    log('\n✗ Some pre-flight checks failed. Fix issues before running tests.', 'red');
    log('\nRun "node scripts/auto-fix.js" to automatically fix some issues', 'blue');
    process.exit(1);
  }
}

main().catch(error => {
  log(`\n✗ Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
