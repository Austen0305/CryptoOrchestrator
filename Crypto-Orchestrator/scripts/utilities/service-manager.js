#!/usr/bin/env node
/**
 * Service Manager
 * Start/stop all services (PostgreSQL, Redis, FastAPI, Frontend) with dependency management
 */

import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

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

class ServiceManager {
  constructor() {
    this.processes = new Map();
    this.isWindows = process.platform === 'win32';
  }

  async checkDockerAvailable() {
    try {
      execSync('docker --version', { stdio: 'pipe' });
      return true;
    } catch {
      return false;
    }
  }

  async startPostgreSQL() {
    log('Starting PostgreSQL...', 'blue');
    
    // Check if Docker is available
    const dockerAvailable = await this.checkDockerAvailable();
    
    if (dockerAvailable) {
      try {
        // Check if container already exists
        try {
          execSync('docker ps -a --filter name=crypto-postgres --format {{.Names}}', { stdio: 'pipe' });
          log('  Starting existing PostgreSQL container...', 'blue');
          execSync('docker start crypto-postgres', { stdio: 'inherit' });
        } catch {
          log('  Creating new PostgreSQL container...', 'blue');
          execSync(
            'docker run -d --name crypto-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=cryptoorchestrator -p 5432:5432 postgres:15-alpine',
            { stdio: 'inherit' }
          );
        }
        log('  ✓ PostgreSQL started', 'green');
        return { success: true };
      } catch (error) {
        log(`  ✗ Failed to start PostgreSQL: ${error.message}`, 'red');
        return { success: false, error: error.message };
      }
    } else {
      log('  ⚠ Docker not available, assuming PostgreSQL is running locally', 'yellow');
      return { success: true, skipped: true };
    }
  }

  async startRedis() {
    log('Starting Redis...', 'blue');
    
    const dockerAvailable = await this.checkDockerAvailable();
    
    if (dockerAvailable) {
      try {
        // Check if container already exists
        try {
          execSync('docker ps -a --filter name=crypto-redis --format {{.Names}}', { stdio: 'pipe' });
          log('  Starting existing Redis container...', 'blue');
          execSync('docker start crypto-redis', { stdio: 'inherit' });
        } catch {
          log('  Creating new Redis container...', 'blue');
          execSync(
            'docker run -d --name crypto-redis -p 6379:6379 redis:7-alpine',
            { stdio: 'inherit' }
          );
        }
        log('  ✓ Redis started', 'green');
        return { success: true };
      } catch (error) {
        log(`  ✗ Failed to start Redis: ${error.message}`, 'red');
        return { success: false, error: error.message };
      }
    } else {
      log('  ⚠ Docker not available, assuming Redis is running locally', 'yellow');
      return { success: true, skipped: true };
    }
  }

  startFastAPI() {
    log('Starting FastAPI backend...', 'blue');
    
    return new Promise((resolve) => {
      const command = this.isWindows ? 'python' : 'python3';
      const args = ['-m', 'uvicorn', 'server_fastapi.main:app', '--host', '0.0.0.0', '--port', '8000'];
      
      const childProcess = spawn(command, args, {
        cwd: projectRoot,
        env: { 
          ...process.env, 
          PYTHONUNBUFFERED: '1',
          PYTHONPATH: projectRoot
        },
        stdio: 'pipe',
      });
      
      this.processes.set('fastapi', childProcess);
      
      let startupComplete = false;
      
      childProcess.stdout.on('data', (data) => {
        const output = data.toString();
        if (output.includes('Application startup complete') || output.includes('Uvicorn running')) {
          if (!startupComplete) {
            startupComplete = true;
            log('  ✓ FastAPI backend started', 'green');
            resolve({ success: true });
          }
        }
      });
      
      childProcess.stderr.on('data', (data) => {
        const output = data.toString();
        if (!output.includes('GetPrototype') && !output.includes('MessageFactory')) {
          console.error(`  [FastAPI] ${output.trim()}`);
        }
      });
      
      childProcess.on('error', (error) => {
        log(`  ✗ Failed to start FastAPI: ${error.message}`, 'red');
        resolve({ success: false, error: error.message });
      });
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (!startupComplete) {
          log('  ⚠ FastAPI startup timeout (may still be starting)', 'yellow');
          resolve({ success: true, timeout: true });
        }
      }, 30000);
    });
  }

  startFrontend() {
    log('Starting React frontend...', 'blue');
    
    return new Promise((resolve) => {
      const childProcess = spawn('npm', ['run', 'dev'], {
        cwd: projectRoot,
        shell: true,
        stdio: 'pipe',
      });
      
      this.processes.set('frontend', childProcess);
      
      let startupComplete = false;
      
      childProcess.stdout.on('data', (data) => {
        const output = data.toString();
        if (output.includes('Local:') || output.includes('localhost:5173')) {
          if (!startupComplete) {
            startupComplete = true;
            log('  ✓ React frontend started', 'green');
            resolve({ success: true });
          }
        }
      });
      
      childProcess.stderr.on('data', (data) => {
        console.error(`  [Frontend] ${data.toString().trim()}`);
      });
      
      childProcess.on('error', (error) => {
        log(`  ✗ Failed to start frontend: ${error.message}`, 'red');
        resolve({ success: false, error: error.message });
      });
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (!startupComplete) {
          log('  ⚠ Frontend startup timeout (may still be starting)', 'yellow');
          resolve({ success: true, timeout: true });
        }
      }, 30000);
    });
  }

  async startAll() {
    log('\n=== Starting All Services ===\n', 'bold');
    
    const results = {
      postgresql: await this.startPostgreSQL(),
      redis: await this.startRedis(),
      fastapi: await this.startFastAPI(),
      frontend: await this.startFrontend(),
    };
    
    log('\n=== Service Startup Summary ===\n', 'bold');
    
    let allSuccess = true;
    for (const [service, result] of Object.entries(results)) {
      if (result.success) {
        log(`✓ ${service}: Started`, 'green');
      } else {
        log(`✗ ${service}: Failed`, 'red');
        allSuccess = false;
      }
    }
    
    return { success: allSuccess, results };
  }

  stopAll() {
    log('\n=== Stopping All Services ===\n', 'bold');
    
    // Stop Node processes
    for (const [name, childProcess] of this.processes.entries()) {
      log(`Stopping ${name}...`, 'blue');
      try {
        childProcess.kill('SIGTERM');
        log(`  ✓ ${name} stopped`, 'green');
      } catch (error) {
        log(`  ✗ Failed to stop ${name}: ${error.message}`, 'red');
      }
    }
    
    this.processes.clear();
    
    // Stop Docker containers if they exist
    try {
      execSync('docker stop crypto-postgres crypto-redis 2>/dev/null || true', { stdio: 'pipe' });
      log('  ✓ Docker containers stopped', 'green');
    } catch {
      // Ignore errors
    }
  }

  async waitForServices(maxWait = 60000) {
    log('\nWaiting for services to be ready...', 'blue');
    
    const startTime = Date.now();
    const services = [
      { name: 'FastAPI', url: 'http://localhost:8000/health' },
      { name: 'Frontend', url: 'http://localhost:5173' },
    ];
    
    for (const service of services) {
      let ready = false;
      let attempts = 0;
      const maxAttempts = maxWait / 1000;
      
      while (!ready && attempts < maxAttempts) {
        try {
          const response = await fetch(service.url, { signal: AbortSignal.timeout(2000) });
          if (response.ok) {
            ready = true;
            log(`  ✓ ${service.name} is ready`, 'green');
          }
        } catch {
          // Not ready yet
        }
        
        if (!ready) {
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      if (!ready) {
        log(`  ✗ ${service.name} did not become ready in time`, 'red');
        return false;
      }
    }
    
    return true;
  }
}

// Export for use in other scripts
export default ServiceManager;

// CLI usage - check if this is the main module
const currentFile = fileURLToPath(import.meta.url);
const scriptFile = process.argv[1] ? process.argv[1].replace(/\\/g, '/') : '';

if (currentFile.endsWith(scriptFile) || process.argv[1]?.includes('service-manager.js')) {
  const manager = new ServiceManager();
  const command = process.argv[2] || 'start';
  
  if (command === 'start') {
    manager.startAll().then(({ success }) => {
      if (success) {
        log('\n✓ All services started successfully!', 'green');
        process.exit(0);
      } else {
        log('\n✗ Some services failed to start', 'red');
        process.exit(1);
      }
    }).catch(error => {
      log(`\n✗ Error: ${error.message}`, 'red');
      process.exit(1);
    });
  } else if (command === 'stop') {
    manager.stopAll();
    process.exit(0);
  } else {
    log('Usage: node service-manager.js [start|stop]', 'yellow');
    process.exit(1);
  }
}
