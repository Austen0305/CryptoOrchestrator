/**
 * Global E2E Test Setup
 * Runs before all E2E tests to set up test environment
 * Updated: December 6, 2025 - Improved with database migrations and better error handling
 * Enhanced: Better error handling, service dependency checks, and Windows compatibility
 */

import { FullConfig } from '@playwright/test';
import { spawn, ChildProcess, execSync, execFile } from 'child_process';
import path from 'path';
import { promisify } from 'util';
import { existsSync, unlinkSync } from 'fs';

const sleep = promisify(setTimeout);

let fastapiProcess: ChildProcess | null = null;
let frontendProcess: ChildProcess | null = null;

const isWindows = process.platform === 'win32';
const pythonCommand = isWindows ? 'python' : 'python3';

/**
 * Wait for a URL to be ready with retries and exponential backoff
 */
async function waitForUrl(
  url: string,
  maxRetries: number = 30,
  initialRetryDelay: number = 1000
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      
      if (response.ok) {
        return true;
      }
    } catch (error: any) {
      // URL not ready yet, continue retrying
      if (i % 5 === 0 && i > 0) {
        console.log(`[INFO] Still waiting for ${url}... (attempt ${i + 1}/${maxRetries})`);
      }
    }
    
    if (i < maxRetries - 1) {
      // Exponential backoff with max delay of 5 seconds
      const delay = Math.min(initialRetryDelay * Math.pow(1.5, i), 5000);
      await sleep(delay);
    }
  }
  return false;
}

/**
 * Check if a port is available
 */
function isPortAvailable(port: number): boolean {
  try {
    if (isWindows) {
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

/**
 * Check service dependencies before starting
 */
async function checkDependencies(): Promise<void> {
  console.log('[INFO] Checking dependencies...');
  
  // Check Python
  try {
    const pythonVersion = execSync(`${pythonCommand} --version`, { 
      encoding: 'utf-8', 
      stdio: 'pipe' 
    });
    console.log(`[INFO] Python found: ${pythonVersion.trim()}`);
  } catch (error) {
    throw new Error('Python is not installed or not in PATH. Install Python 3.12+');
  }
  
  // Check ports
  if (!isPortAvailable(8000)) {
    console.warn('[WARN] Port 8000 is already in use. This may cause issues.');
  }
  
  if (!isPortAvailable(5173)) {
    console.warn('[WARN] Port 5173 is already in use. This may cause issues.');
  }
  
  console.log('[SUCCESS] Dependencies check passed');
}

/**
 * Setup test database with migrations
 */
async function setupTestDatabase(): Promise<void> {
  console.log('[INFO] Setting up test database...');
  
  const testDbPath = path.join(process.cwd(), 'test_e2e.db');
  
  // Clean up old test database if exists
  if (existsSync(testDbPath)) {
    try {
      // On Windows, files can be locked. Try multiple times with delays
      let deleted = false;
      for (let attempt = 0; attempt < 5; attempt++) {
        try {
          unlinkSync(testDbPath);
          deleted = true;
          console.log('[INFO] Cleaned up old test database');
          break;
        } catch (error: any) {
          if (error.code === 'EBUSY' || error.code === 'ENOENT') {
            // File is locked or already deleted
            if (attempt < 4) {
              console.log(`[INFO] Database file locked, waiting ${(attempt + 1) * 500}ms before retry...`);
              await sleep((attempt + 1) * 500);
            } else {
              console.warn('[WARN] Could not delete locked test database, will use existing one');
              console.warn('[WARN] This is OK - the database will be reset during setup');
            }
          } else {
            throw error;
          }
        }
      }
      if (!deleted) {
        console.warn('[WARN] Using existing test database (could not delete locked file)');
      }
    } catch (error: any) {
      // If file is locked, that's OK - we'll use the existing database
      if (error.code === 'EBUSY') {
        console.warn('[WARN] Test database file is locked, will use existing database');
      } else {
        console.warn('[WARN] Could not clean up old test database:', error.message);
      }
    }
  }

  // Run database setup script
  const setupScriptPath = path.join(process.cwd(), 'scripts', 'testing', 'test_db_setup.py');
  
  if (!existsSync(setupScriptPath)) {
    throw new Error(`Database setup script not found: ${setupScriptPath}`);
  }
  
  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      DATABASE_URL: 'sqlite+aiosqlite:///./test_e2e.db',
      TESTING: 'true',
      PYTHONUNBUFFERED: '1',
    };

    let stdout = '';
    let stderr = '';

    // Use execFile on Windows to properly handle paths with spaces
    // execFile doesn't use a shell, so it handles paths correctly
    const setupProcess = isWindows
      ? execFile(
          pythonCommand,
          [setupScriptPath],
          {
            cwd: process.cwd(),
            env,
            encoding: 'utf8',
          },
          (error, stdoutData, stderrData) => {
            stdout = stdoutData || '';
            stderr = stderrData || '';
            
            if (stdout) {
              console.log(stdout.trim());
            }
            if (stderr) {
              console.error(stderr.trim());
            }

            if (error) {
              console.error(`[ERROR] Test database setup failed: ${error.message}`);
              console.error('stdout:', stdout);
              console.error('stderr:', stderr);
              if ((error as any).code === 'ENOENT') {
                reject(new Error(`Python command '${pythonCommand}' not found. Install Python 3.12+ and ensure it's in PATH.`));
              } else {
                reject(new Error(`Database setup failed: ${error.message}`));
              }
            } else {
              console.log('[SUCCESS] Test database setup complete');
              resolve(undefined);
            }
          }
        )
      : spawn(pythonCommand, [setupScriptPath], {
          cwd: process.cwd(),
          stdio: 'pipe',
          env,
        });

    // Handle spawn (non-Windows) case
    if (!isWindows && 'stdout' in setupProcess) {
      setupProcess.stdout?.on('data', (data: Buffer) => {
        stdout += data.toString();
        console.log(data.toString().trim());
      });

      setupProcess.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString();
        console.error(data.toString().trim());
      });

      setupProcess.on('close', (code) => {
        if (code === 0) {
          console.log('[SUCCESS] Test database setup complete');
          resolve(undefined);
        } else {
          console.error(`[ERROR] Test database setup failed with code ${code}`);
          console.error('stdout:', stdout);
          console.error('stderr:', stderr);
          const errorMsg = `Database setup failed with exit code ${code}. Check the output above for details.`;
          reject(new Error(errorMsg));
        }
      });

      setupProcess.on('error', (error: any) => {
        console.error('[ERROR] Failed to start database setup process:', error.message);
        if (error.code === 'ENOENT') {
          reject(new Error(`Python command '${pythonCommand}' not found. Install Python 3.12+ and ensure it's in PATH.`));
        } else {
          reject(error);
        }
      });
    }
  });
}

/**
 * Start FastAPI backend with retry logic
 */
async function startBackend(): Promise<void> {
  console.log('[INFO] Starting FastAPI backend...');
  
  const fastapiPath = path.join(process.cwd(), 'server_fastapi');
  const testDbUrl = 'sqlite+aiosqlite:///./test_e2e.db';

  // Verify server_fastapi directory exists
  if (!existsSync(fastapiPath)) {
    throw new Error(`FastAPI directory not found: ${fastapiPath}`);
  }
  
  return new Promise((resolve, reject) => {
    // Ensure PYTHONPATH includes project root for imports
    const pythonPath = process.cwd();
    const fastapiPathFull = path.join(process.cwd(), 'server_fastapi');
    
    // Build environment with proper paths
    const env = {
      ...process.env,
      TESTING: 'true',
      DATABASE_URL: testDbUrl,
      NODE_ENV: 'test', // Use 'test' not 'production' to avoid strict validation
      PYTHONUNBUFFERED: '1',
      PYTHONPATH: `${pythonPath}${path.delimiter}${fastapiPathFull}`, // Ensure Python can find modules
      // Disable CUDA/GPU for testing
      CUDA_VISIBLE_DEVICES: '',
      TF_CPP_MIN_LOG_LEVEL: '3',
      // Disable strict validation for testing
      ENABLE_OPENTELEMETRY: 'false',
      ENABLE_DISTRIBUTED_RATE_LIMIT: 'false',
    };
    
    console.log(`[INFO] Starting backend with DATABASE_URL: ${testDbUrl}`);
    console.log(`[INFO] Working directory: ${fastapiPathFull}`);
    console.log(`[INFO] PYTHONPATH: ${env.PYTHONPATH}`);
    
    fastapiProcess = spawn(pythonCommand, ['-m', 'uvicorn', 'main:app', '--port', '8000', '--host', '127.0.0.1'], {
      cwd: fastapiPathFull,
      stdio: 'pipe',
      shell: isWindows, // Use shell on Windows for better compatibility
      env: env,
    });

    let startupComplete = false;
    let errorOutput = '';

    fastapiProcess.stdout?.on('data', (data: Buffer) => {
      const output = data.toString();
      // Log all output for debugging
      console.log(`[Backend stdout] ${output.trim()}`);
      if (output.includes('Application startup complete') || output.includes('Uvicorn running') || output.includes('Started server process')) {
        if (!startupComplete) {
          startupComplete = true;
          console.log('[SUCCESS] FastAPI backend started');
        }
      }
      // Log important messages
      if (output.includes('error') || output.includes('Error') || output.includes('ERROR')) {
        console.error(`[Backend error] ${output.trim()}`);
      }
    });

    fastapiProcess.stderr?.on('data', (data: Buffer) => {
      const output = data.toString();
      errorOutput += output;
      // Log all stderr for debugging (filter out known harmless warnings)
      if (!output.includes('GetPrototype') && !output.includes('MessageFactory') && !output.includes('DeprecationWarning')) {
        console.error(`[Backend stderr] ${output.trim()}`);
      }
    });

    fastapiProcess.on('error', (error: any) => {
      console.error('[ERROR] Failed to start FastAPI backend:', error.message);
      if (error.code === 'ENOENT') {
        reject(new Error(`Python command '${pythonCommand}' not found. Install Python 3.12+ and ensure it's in PATH.`));
      } else {
        reject(error);
      }
    });

    fastapiProcess.on('exit', (code, signal) => {
      if (code !== null && code !== 0 && !startupComplete) {
        console.error(`[ERROR] FastAPI backend exited with code ${code}${signal ? ` (signal: ${signal})` : ''}`);
        console.error('Error output:', errorOutput);
        const errorMsg = `Backend exited with code ${code}. Check the output above for details. Common issues: missing dependencies (run 'pip install -r requirements.txt'), incorrect DATABASE_URL, or port conflicts.`;
        reject(new Error(errorMsg));
      }
    });

    // Wait for backend to be ready with longer initial delay
    setTimeout(async () => {
      const isReady = await waitForUrl('http://localhost:8000/health', 60, 2000); // Increased to 60 retries, 2s initial delay
      if (isReady) {
        console.log('[SUCCESS] Backend health check passed');
        resolve();
      } else {
        console.error('[ERROR] Backend not responding after 60 retries');
        console.error('Error output:', errorOutput);
        console.error('[INFO] Backend process status:', fastapiProcess?.killed ? 'killed' : 'running');
        reject(new Error('Backend health check failed'));
      }
    }, 5000); // Give backend 5 seconds to start before checking (increased from 2s)
  });
}

/**
 * Check if frontend is already running
 */
async function checkFrontend(baseURL: string): Promise<boolean> {
  try {
    const response = await fetch(baseURL, { signal: AbortSignal.timeout(2000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function globalSetup(config: FullConfig) {
  console.log('[INFO] Starting global E2E test setup...');
  console.log(`Date: ${new Date().toISOString()}`);
  console.log(`Platform: ${process.platform}`);
  console.log(`Node version: ${process.version}`);

  try {
    // Step 0: Check dependencies
    await checkDependencies();

    // Step 1: Setup test database with migrations
    await setupTestDatabase();

    // Step 2: Start FastAPI backend
    await startBackend();

    // Step 3: Frontend is handled by Playwright's webServer configuration
    // No need to start it manually here
    console.log('[INFO] Frontend will be started by Playwright webServer configuration');

    console.log('[SUCCESS] Global E2E test setup complete');
  } catch (error: any) {
    console.error('[ERROR] Global setup failed:', error.message);
    if (error.stack) {
      console.error('[ERROR] Stack trace:', error.stack);
    }
    
    // Cleanup on failure
    if (fastapiProcess) {
      try {
        fastapiProcess.kill('SIGTERM');
        // Wait a bit for graceful shutdown
        await sleep(1000);
        if (fastapiProcess.killed === false) {
          fastapiProcess.kill('SIGKILL');
        }
      } catch (cleanupError) {
        console.warn('[WARN] Error during cleanup:', cleanupError);
      }
    }
    
    throw error;
  }
}

export default globalSetup;
