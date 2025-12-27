#!/usr/bin/env node
/**
 * Unified Startup Script
 * Starts all services in correct order with health checks
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
// Script is in scripts/utilities/, so go up 2 levels to project root
const projectRoot = join(__dirname, '..', '..');

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
  log('Validating environment...', 'blue');
  
  try {
    // Import and run environment validator
    const { execSync } = await import('child_process');
    const validateScript = join(projectRoot, 'scripts', 'utilities', 'validate-environment.js');
    execSync(`node "${validateScript}"`, { 
      cwd: projectRoot,
      stdio: 'inherit' 
    });
    return true;
  } catch (error) {
    log('  ⚠ Environment validation had warnings (continuing anyway)', 'yellow');
    return true; // Continue even with warnings
  }
}

async function checkDatabaseInitialized() {
  log('Checking database initialization...', 'blue');
  
  try {
    const { execSync } = await import('child_process');
    // Check if database is initialized (non-blocking check)
    try {
      execSync('python scripts/setup/init_database.py --skip-create --skip-migrations', {
        cwd: projectRoot,
        stdio: 'pipe',
        timeout: 5000
      });
      log('  ✅ Database initialized', 'green');
      return true;
    } catch (error) {
      log('  ⚠ Database may need initialization (run: npm run setup:db)', 'yellow');
      return true; // Continue anyway, user can initialize later
    }
  } catch (error) {
    log('  ⚠ Could not check database status (continuing anyway)', 'yellow');
    return true; // Continue even if check fails
  }
}

function setupGracefulShutdown(manager) {
  const shutdown = () => {
    log('\n\nShutting down services...', 'yellow');
    manager.stopAll();
    process.exit(0);
  };
  
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
  process.on('exit', () => {
    manager.stopAll();
  });
}

async function main() {
  log('\n' + '='.repeat(60), 'bold');
  log('CryptoOrchestrator - Service Startup', 'bold');
  log('='.repeat(60) + '\n', 'bold');
  
  // Step 1: Validate environment
  const envValid = await validateEnvironment();
  if (!envValid) {
    log('\n✗ Environment validation failed. Fix errors and try again.', 'red');
    process.exit(1);
  }
  
  // Step 1.5: Check database initialization (non-blocking)
  await checkDatabaseInitialized();
  
  // Step 2: Start services
  const ServiceManagerModule = await import('./service-manager.js');
  const ServiceManager = ServiceManagerModule.default || ServiceManagerModule;
  const manager = new ServiceManager();
  setupGracefulShutdown(manager);
  
  log('\nStarting services...\n', 'blue');
  const { success } = await manager.startAll();
  
  if (!success) {
    log('\n✗ Some services failed to start', 'red');
    process.exit(1);
  }
  
  // Step 3: Wait for services to be ready
  log('\nWaiting for services to be ready...', 'blue');
  const servicesReady = await manager.waitForServices(60000);
  
  if (!servicesReady) {
    log('\n✗ Services did not become ready in time', 'red');
    log('Check logs above for errors', 'yellow');
    process.exit(1);
  }
  
  // Step 4: Success message
  log('\n' + '='.repeat(60), 'green');
  log('✓ All services started successfully!', 'green');
  log('='.repeat(60), 'green');
  log('\nServices running:', 'blue');
  log('  • FastAPI Backend: http://localhost:8000', 'green');
  log('  • React Frontend: http://localhost:5173', 'green');
  log('  • API Docs: http://localhost:8000/docs', 'green');
  log('\nPress Ctrl+C to stop all services\n', 'yellow');
  
  // Keep process alive
  process.stdin.resume();
}

main().catch(error => {
  log(`\n✗ Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
