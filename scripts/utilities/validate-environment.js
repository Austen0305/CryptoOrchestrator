#!/usr/bin/env node
/**
 * Environment Validator Script
 * Validates all required environment variables, dependencies, and port availability
 * before server startup
 */

import { readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..', '..');

// Colors for terminal output
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

function checkPort(port) {
  try {
    const result = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf-8', stdio: 'pipe' });
    return result.trim().length > 0;
  } catch {
    return false;
  }
}

function checkPortUnix(port) {
  try {
    execSync(`lsof -i :${port}`, { encoding: 'utf-8', stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function isPortAvailable(port) {
  if (process.platform === 'win32') {
    return !checkPort(port);
  }
  return !checkPortUnix(port);
}

function checkPythonInstalled() {
  try {
    const version = execSync('python --version', { encoding: 'utf-8', stdio: 'pipe' });
    return { installed: true, version: version.trim() };
  } catch {
    try {
      const version = execSync('python3 --version', { encoding: 'utf-8', stdio: 'pipe' });
      return { installed: true, version: version.trim() };
    } catch {
      return { installed: false };
    }
  }
}

function checkNodeInstalled() {
  try {
    const version = execSync('node --version', { encoding: 'utf-8', stdio: 'pipe' });
    return { installed: true, version: version.trim() };
  } catch {
    return { installed: false };
  }
}

function checkDependenciesInstalled(type) {
  try {
    if (type === 'node') {
      const packageJson = JSON.parse(readFileSync(join(projectRoot, 'package.json'), 'utf-8'));
      const nodeModulesExists = existsSync(join(projectRoot, 'node_modules'));
      return { installed: nodeModulesExists };
    } else if (type === 'python') {
      try {
        execSync('pip show fastapi', { encoding: 'utf-8', stdio: 'pipe' });
        return { installed: true };
      } catch {
        return { installed: false };
      }
    }
  } catch {
    return { installed: false };
  }
}

function loadEnvFile() {
  const envPath = join(projectRoot, '.env');
  const env = {};
  
  if (existsSync(envPath)) {
    const content = readFileSync(envPath, 'utf-8');
    content.split('\n').forEach(line => {
      line = line.trim();
      if (line && !line.startsWith('#') && line.includes('=')) {
        const [key, ...valueParts] = line.split('=');
        env[key.trim()] = valueParts.join('=').trim();
      }
    });
  }
  
  return env;
}

function validateEnvironment() {
  const results = {
    errors: [],
    warnings: [],
    success: [],
  };

  log('\n=== Environment Validation ===\n', 'bold');

  // Check Python installation
  log('Checking Python installation...', 'blue');
  const python = checkPythonInstalled();
  if (python.installed) {
    log(`  ✓ Python installed: ${python.version}`, 'green');
    results.success.push('Python installed');
  } else {
    log('  ✗ Python not found', 'red');
    results.errors.push('Python is not installed. Install Python 3.12+');
  }

  // Check Node.js installation
  log('\nChecking Node.js installation...', 'blue');
  const node = checkNodeInstalled();
  if (node.installed) {
    log(`  ✓ Node.js installed: ${node.version}`, 'green');
    results.success.push('Node.js installed');
  } else {
    log('  ✗ Node.js not found', 'red');
    results.errors.push('Node.js is not installed. Install Node.js 18+');
  }

  // Check Node dependencies
  log('\nChecking Node.js dependencies...', 'blue');
  const nodeDeps = checkDependenciesInstalled('node');
  if (nodeDeps.installed) {
    log('  ✓ Node.js dependencies installed', 'green');
    results.success.push('Node.js dependencies installed');
  } else {
    log('  ✗ Node.js dependencies not installed', 'red');
    results.errors.push('Run: npm install');
  }

  // Check Python dependencies
  log('\nChecking Python dependencies...', 'blue');
  const pythonDeps = checkDependenciesInstalled('python');
  if (pythonDeps.installed) {
    log('  ✓ Python dependencies installed', 'green');
    results.success.push('Python dependencies installed');
  } else {
    log('  ⚠ Python dependencies may not be installed', 'yellow');
    results.warnings.push('Run: pip install -r requirements.txt');
  }

  // Check ports
  log('\nChecking port availability...', 'blue');
  const ports = [
    { port: 8000, service: 'FastAPI Backend' },
    { port: 5173, service: 'React Frontend' },
  ];

  ports.forEach(({ port, service }) => {
    if (isPortAvailable(port)) {
      log(`  ✓ Port ${port} available (${service})`, 'green');
      results.success.push(`Port ${port} available`);
    } else {
      log(`  ✗ Port ${port} is in use (${service})`, 'red');
      results.errors.push(`Port ${port} is already in use. Stop the service using it or change the port.`);
    }
  });

  // Check environment variables
  log('\nChecking environment variables...', 'blue');
  const env = loadEnvFile();
  const envVars = process.env;

  const requiredVars = [
    { key: 'DATABASE_URL', optional: false, description: 'Database connection URL' },
    { key: 'JWT_SECRET', optional: false, description: 'JWT secret key' },
  ];

  const recommendedVars = [
    { key: 'NODE_ENV', optional: true, description: 'Node environment' },
    { key: 'REDIS_URL', optional: true, description: 'Redis connection URL' },
  ];

  requiredVars.forEach(({ key, description }) => {
    const value = env[key] || envVars[key];
    if (!value) {
      log(`  ✗ ${key}: MISSING (${description})`, 'red');
      results.errors.push(`${key} is required but not set`);
    } else if (value.includes('change-me') || value.includes('your-')) {
      log(`  ⚠ ${key}: Using default value (NOT PRODUCTION SAFE)`, 'yellow');
      results.warnings.push(`${key} is using a default value. Change it for production.`);
    } else {
      log(`  ✓ ${key}: Configured`, 'green');
      results.success.push(`${key} configured`);
    }
  });

  recommendedVars.forEach(({ key, description }) => {
    const value = env[key] || envVars[key];
    if (!value) {
      log(`  ⚠ ${key}: Not set (recommended: ${description})`, 'yellow');
      results.warnings.push(`${key} is recommended but not set`);
    } else {
      log(`  ✓ ${key}: ${value}`, 'green');
      results.success.push(`${key} configured`);
    }
  });

  // Check .env file exists
  log('\nChecking .env file...', 'blue');
  const envPath = join(projectRoot, '.env');
  const envExamplePath = join(projectRoot, '.env.example');
  
  if (existsSync(envPath)) {
    log('  ✓ .env file exists', 'green');
    results.success.push('.env file exists');
  } else {
    if (existsSync(envExamplePath)) {
      log('  ⚠ .env file not found, but .env.example exists', 'yellow');
      results.warnings.push('Create .env file from .env.example: cp .env.example .env');
    } else {
      log('  ✗ .env file not found', 'red');
      results.errors.push('.env file is missing');
    }
  }

  // Summary
  log('\n=== Validation Summary ===\n', 'bold');
  log(`✓ Passed: ${results.success.length}`, 'green');
  log(`⚠ Warnings: ${results.warnings.length}`, 'yellow');
  log(`✗ Errors: ${results.errors.length}`, 'red');

  if (results.errors.length > 0) {
    log('\nErrors that must be fixed:', 'red');
    results.errors.forEach(error => log(`  - ${error}`, 'red'));
  }

  if (results.warnings.length > 0) {
    log('\nWarnings (recommended fixes):', 'yellow');
    results.warnings.forEach(warning => log(`  - ${warning}`, 'yellow'));
  }

  if (results.errors.length === 0) {
    log('\n✓ Environment validation passed!', 'green');
    if (results.warnings.length > 0) {
      log('⚠ Review warnings before production deployment', 'yellow');
    }
    return true;
  } else {
    log('\n✗ Environment validation failed', 'red');
    log('\nFix the errors above and run this script again.', 'red');
    return false;
  }
}

// Run validation
const success = validateEnvironment();
process.exit(success ? 0 : 1);
