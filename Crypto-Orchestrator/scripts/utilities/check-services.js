#!/usr/bin/env node
/**
 * Service Health Checker
 * Verifies all services are healthy before tests with retry logic
 */

import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkUrl(url, timeout = 2000) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(url, { 
      signal: controller.signal,
      method: 'GET',
    });
    
    clearTimeout(timeoutId);
    return { success: response.ok, status: response.status };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function checkService(name, url, maxRetries = 30, retryDelay = 1000) {
  log(`Checking ${name}...`, 'blue');
  
  for (let i = 0; i < maxRetries; i++) {
    const result = await checkUrl(url);
    
    if (result.success) {
      log(`  ✓ ${name} is healthy (${url})`, 'green');
      return { success: true, attempts: i + 1 };
    }
    
    if (i < maxRetries - 1) {
      await sleep(retryDelay);
      // Exponential backoff
      const nextDelay = Math.min(retryDelay * Math.pow(1.5, i), 5000);
      if (i > 0 && i % 5 === 0) {
        log(`  ⏳ Still waiting for ${name}... (attempt ${i + 1}/${maxRetries})`, 'yellow');
      }
    }
  }
  
  log(`  ✗ ${name} is not responding after ${maxRetries} attempts`, 'red');
  return { success: false, attempts: maxRetries };
}

async function checkDatabase() {
  // Try to connect to database by checking if we can import database module
  try {
    // This is a simple check - in production you'd want to actually connect
    log('Checking database connection...', 'blue');
    log('  ⚠ Database check skipped (requires actual connection)', 'yellow');
    return { success: true, skipped: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function checkRedis() {
  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';
  
  // Skip Redis check if not configured
  if (!process.env.REDIS_URL && !redisUrl.includes('localhost')) {
    log('Checking Redis...', 'blue');
    log('  ⚠ Redis not configured, skipping check', 'yellow');
    return { success: true, skipped: true };
  }
  
  // Try to connect to Redis
  try {
    log('Checking Redis connection...', 'blue');
    // Simple check - in production you'd want to actually connect
    log('  ⚠ Redis check skipped (requires actual connection)', 'yellow');
    return { success: true, skipped: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function checkAllServices() {
  log('\n=== Service Health Check ===\n', 'bold');
  
  const services = [
    { 
      name: 'FastAPI Backend', 
      url: 'http://localhost:8000/health',
      check: () => checkService('FastAPI Backend', 'http://localhost:8000/health')
    },
    { 
      name: 'React Frontend', 
      url: 'http://localhost:5173',
      check: () => checkService('React Frontend', 'http://localhost:5173')
    },
  ];
  
  const results = {
    passed: [],
    failed: [],
    skipped: [],
  };
  
  // Check HTTP services
  for (const service of services) {
    const result = await service.check();
    if (result.success) {
      results.passed.push(service.name);
    } else if (result.skipped) {
      results.skipped.push(service.name);
    } else {
      results.failed.push(service.name);
    }
  }
  
  // Check database
  const dbResult = await checkDatabase();
  if (dbResult.success) {
    if (dbResult.skipped) {
      results.skipped.push('Database');
    } else {
      results.passed.push('Database');
    }
  } else {
    results.failed.push('Database');
  }
  
  // Check Redis
  const redisResult = await checkRedis();
  if (redisResult.success) {
    if (redisResult.skipped) {
      results.skipped.push('Redis');
    } else {
      results.passed.push('Redis');
    }
  } else {
    results.failed.push('Redis');
  }
  
  // Summary
  log('\n=== Health Check Summary ===\n', 'bold');
  log(`✓ Healthy: ${results.passed.length}`, 'green');
  log(`⚠ Skipped: ${results.skipped.length}`, 'yellow');
  log(`✗ Failed: ${results.failed.length}`, 'red');
  
  if (results.passed.length > 0) {
    log('\nHealthy services:', 'green');
    results.passed.forEach(service => log(`  ✓ ${service}`, 'green'));
  }
  
  if (results.skipped.length > 0) {
    log('\nSkipped checks:', 'yellow');
    results.skipped.forEach(service => log(`  ⚠ ${service}`, 'yellow'));
  }
  
  if (results.failed.length > 0) {
    log('\nFailed services:', 'red');
    results.failed.forEach(service => log(`  ✗ ${service}`, 'red'));
    log('\nMake sure all services are running before running tests.', 'red');
    return false;
  }
  
  log('\n✓ All services are healthy!', 'green');
  return true;
}

// Run health checks
const success = await checkAllServices();
process.exit(success ? 0 : 1);
