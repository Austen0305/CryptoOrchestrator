#!/usr/bin/env node
/**
 * Health Check Utility
 * Quick health check for all services
 */

import { fileURLToPath } from 'url';
import { dirname } from 'path';
import http from 'http';

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

function checkService(url, name) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            resolve({ status: 'ok', data: json });
          } catch {
            resolve({ status: 'ok', data: null });
          }
        } else {
          resolve({ status: 'error', code: res.statusCode });
        }
      });
    });

    req.on('error', (err) => {
      resolve({ status: 'error', message: err.message });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ status: 'timeout' });
    });
  });
}

async function main() {
  log('Health Check Utility', 'bold');
  log('==================', 'bold');
  log('');

  const services = [
    { url: 'http://localhost:8000/health', name: 'Backend API' },
    { url: 'http://localhost:8000/healthz', name: 'Backend Healthz' },
    { url: 'http://localhost:5173', name: 'Frontend' },
  ];

  log('Checking services...', 'blue');
  log('');

  const results = [];
  for (const service of services) {
    const result = await checkService(service.url, service.name);
    results.push({ ...service, result });

    if (result.status === 'ok') {
      log(`✓ ${service.name}: OK`, 'green');
    } else if (result.status === 'timeout') {
      log(`⚠ ${service.name}: Timeout`, 'yellow');
    } else {
      log(`✗ ${service.name}: ${result.message || `Error ${result.code || 'Unknown'}`}`, 'red');
    }
  }

  log('');
  log('==================', 'bold');
  const allOk = results.every((r) => r.result.status === 'ok');
  if (allOk) {
    log('All services are healthy!', 'green');
    process.exit(0);
  } else {
    log('Some services are not responding', 'yellow');
    process.exit(1);
  }
}

main().catch((err) => {
  log(`Error: ${err.message}`, 'red');
  process.exit(1);
});

